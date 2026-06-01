"""Paystack webhook connector (example).

On a successful charge, verify the buyer's delivery address (KYC) so the record is
audit-ready. Minimal Flask handler; adapt to your framework. Verify the Paystack
signature in production (omitted here for brevity).
"""

import os

from flask import Flask, request

from pinpoint_sdk import PinpointClient  # ../clients/python

app = Flask(__name__)
pinpoint = PinpointClient(os.environ["PINPOINT_KEY"], base_url="https://api.pinpoint.ng")


@app.post("/webhooks/paystack")
def paystack_webhook():
    event = request.get_json(force=True)
    if event.get("event") == "charge.success":
        meta = event["data"].get("metadata", {})
        code = meta.get("pinpoint_address_code")
        if code:
            # KYC-grade check; evidence_ref is the tamper-evident ledger hash.
            result = pinpoint.verify(code=code, mode="kyc", device="paystack-webhook")
            # persist result["evidence_ref"] against the order/customer for AML records
            return {"verified": result["exists"], "evidence_ref": result.get("evidence_ref")}, 200
    return {"ok": True}, 200
