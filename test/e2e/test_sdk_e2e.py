import pytest

from pinpoint_sdk import PinpointClient

pytestmark = pytest.mark.e2e

DEMO_KEY = "pk_test_pinpoint_demo_0001"


def test_sdk_round_trip_against_live_server(live_server):
    """The sync SDK against the real running API (no browser)."""
    with PinpointClient(DEMO_KEY, base_url=live_server) as pp:
        hits = pp.geocode(
            "silverbird galleria ahmadu bello way", area={"state": "Lagos", "lga": "Eti-Osa"}
        )
        assert hits["results"][0]["code"] == "PIN-VIC-002"

        resolved = pp.get_address("PIN-VIC-002")
        assert resolved["code"] == "PIN-VIC-002"

        verified = pp.verify(code="PIN-VIC-002", mode="kyc", device="sdk-test/1.0")
        assert verified["exists"] is True
        assert len(verified["evidence_ref"]) == 64
