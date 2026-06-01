"""Pinpoint Python server SDK.

A thin, typed wrapper over the Pinpoint REST API.

    from pinpoint_sdk import PinpointClient

    with PinpointClient("pk_live_...", base_url="https://api.pinpoint.ng") as pp:
        hits = pp.geocode("blue gate opp zenith bank awolowo", area={"lga": "Eti-Osa"})
        print(hits["results"][0]["code"])

Errors (HTTP >= 400) raise PinpointError with .status and .detail.
"""

from __future__ import annotations

import httpx


class PinpointError(Exception):
    def __init__(self, status: int, detail: str):
        self.status = status
        self.detail = detail
        super().__init__(f"{status}: {detail}")


def _detail(response: httpx.Response) -> str:
    try:
        return response.json().get("detail", response.text)
    except Exception:
        return response.text


class PinpointClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:8000",
        *,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 10.0,
    ):
        self._http = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
            transport=transport,
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> PinpointClient:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def _request(self, method: str, path: str, json: dict | None = None) -> dict:
        r = self._http.request(method, path, json=json)
        if r.status_code >= 400:
            raise PinpointError(r.status_code, _detail(r))
        return r.json()

    # --- geocoding -------------------------------------------------------
    def geocode(self, query: str, *, area: dict | None = None, limit: int = 3) -> dict:
        body: dict = {"query": query, "limit": limit}
        if area:
            body["area"] = area
        return self._request("POST", "/v1/geocode", body)

    def reverse(self, lat: float, lng: float, *, limit: int = 3, radius_m: int = 2000) -> dict:
        return self._request(
            "POST", "/v1/reverse", {"lat": lat, "lng": lng, "limit": limit, "radius_m": radius_m}
        )

    # --- addresses -------------------------------------------------------
    def create_address(self, lat: float, lng: float, **fields) -> dict:
        return self._request("POST", "/v1/addresses", {"lat": lat, "lng": lng, **fields})

    def get_address(self, code: str) -> dict:
        return self._request("GET", f"/v1/addresses/{code}")

    def claim_address(self, code: str, *, alias: str | None = None) -> dict:
        return self._request("POST", f"/v1/addresses/{code}/claim", {"alias": alias})

    # --- verification / deliveries / usage -------------------------------
    def verify(
        self,
        *,
        code: str | None = None,
        lat: float | None = None,
        lng: float | None = None,
        mode: str = "basic",
        **fields,
    ) -> dict:
        body: dict = {"mode": mode, **fields}
        if code is not None:
            body["code"] = code
        if lat is not None:
            body["lat"] = lat
        if lng is not None:
            body["lng"] = lng
        return self._request("POST", "/v1/verify", body)

    def record_delivery(self, code: str, status: str, **fields) -> dict:
        return self._request("POST", "/v1/deliveries", {"code": code, "status": status, **fields})

    def usage(self) -> dict:
        return self._request("GET", "/v1/usage")
