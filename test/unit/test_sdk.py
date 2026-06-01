"""Unit tests for the Python SDK using httpx MockTransport — no server, no DB."""

import httpx
import pytest

from pinpoint_sdk import PinpointClient, PinpointError


def _client(handler):
    return PinpointClient(
        "pk_test_x", base_url="http://test", transport=httpx.MockTransport(handler)
    )


def test_geocode_builds_request_and_parses():
    seen = {}

    def handler(request):
        import json

        seen["path"] = request.url.path
        seen["auth"] = request.headers.get("authorization")
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "results": [
                    {"code": "PIN-1", "lat": 6.4, "lng": 3.4, "confidence": 0.9, "verified": True}
                ],
                "request_id": "req_1",
                "units": 1,
            },
        )

    with _client(handler) as c:
        out = c.geocode("silverbird", area={"state": "Lagos"}, limit=2)

    assert seen["path"] == "/v1/geocode"
    assert seen["auth"] == "Bearer pk_test_x"
    assert seen["body"] == {"query": "silverbird", "limit": 2, "area": {"state": "Lagos"}}
    assert out["results"][0]["code"] == "PIN-1"


def test_get_address_uses_path():
    def handler(request):
        assert request.url.path == "/v1/addresses/PIN-ABC"
        return httpx.Response(200, json={"code": "PIN-ABC"})

    with _client(handler) as c:
        assert c.get_address("PIN-ABC")["code"] == "PIN-ABC"


def test_http_error_raises_pinpoint_error():
    def handler(request):
        return httpx.Response(429, json={"detail": "Rate limit exceeded."})

    with _client(handler) as c, pytest.raises(PinpointError) as exc:
        c.geocode("x")
    assert exc.value.status == 429
    assert "Rate limit" in exc.value.detail


def test_verify_kyc_body():
    seen = {}

    def handler(request):
        import json

        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "exists": True,
                "confidence": 0.9,
                "freshness": 1.0,
                "stale": False,
                "mode": "kyc",
            },
        )

    with _client(handler) as c:
        c.verify(code="PIN-1", mode="kyc")
    assert seen["body"] == {"mode": "kyc", "code": "PIN-1"}
