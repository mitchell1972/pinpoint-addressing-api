from typing import Literal

from pydantic import BaseModel, model_validator


class VerifyRequest(BaseModel):
    code: str | None = None
    lat: float | None = None
    lng: float | None = None
    mode: Literal["basic", "kyc"] = "basic"
    device: str | None = None  # evidence captured for KYC mode
    agent: str | None = None  # optional agent attestation for KYC mode

    @model_validator(mode="after")
    def _require_target(self):
        if not self.code and (self.lat is None or self.lng is None):
            raise ValueError("Provide either 'code' or both 'lat' and 'lng'.")
        return self


class VerifyResponse(BaseModel):
    exists: bool
    confidence: float  # combined score: stored confidence x freshness (+ track record)
    freshness: float  # 1.0 = freshly verified, decays toward 0
    stale: bool  # past the re-verification threshold
    mode: str
    code: str | None = None
    evidence_ref: str | None = None  # KYC: the tamper-evident ledger hash
    verification_id: str | None = None
