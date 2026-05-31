from typing import Literal

from pydantic import BaseModel, model_validator


class VerifyRequest(BaseModel):
    code: str | None = None
    lat: float | None = None
    lng: float | None = None
    mode: Literal["basic", "kyc"] = "basic"

    @model_validator(mode="after")
    def _require_target(self):
        if not self.code and (self.lat is None or self.lng is None):
            raise ValueError("Provide either 'code' or both 'lat' and 'lng'.")
        return self


class VerifyResponse(BaseModel):
    exists: bool
    confidence: float
    mode: str
    code: str | None = None
    evidence_ref: str | None = None
    verification_id: str | None = None
