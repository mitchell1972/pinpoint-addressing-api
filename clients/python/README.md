# Pinpoint Python SDK

A thin, typed wrapper over the Pinpoint REST API (single file, depends only on `httpx`).

```python
from pinpoint_sdk import PinpointClient, PinpointError

with PinpointClient("pk_live_...", base_url="https://api.pinpoint.ng") as pp:
    # forward geocode
    hits = pp.geocode("eko hotel for VI adetokunbo", area={"lga": "Eti-Osa"})
    code = hits["results"][0]["code"]

    # resolve a code, verify it (KYC), record a delivery outcome
    pp.get_address(code)
    pp.verify(code=code, mode="kyc", device="rider-app/1.0")
    pp.record_delivery(code, "delivered", time_to_locate_seconds=90)

try:
    pp.geocode("x")
except PinpointError as e:
    print(e.status, e.detail)
```

Install: copy `pinpoint_sdk.py` into your project (or `pip install httpx` and vendor it).
Node and PHP server SDKs follow the same shape; see `../../connectors/` for platform glue.
