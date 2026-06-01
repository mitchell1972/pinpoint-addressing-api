from typing import Literal

from pydantic import BaseModel, Field


class AccountCreate(BaseModel):
    name: str = Field(min_length=1)
    type: Literal["merchant", "courier", "bank"]
    tier: str = "free"


class AccountOut(BaseModel):
    id: str
    name: str
    type: str
    tier: str
    status: str


class KeyCreate(BaseModel):
    env: Literal["test", "live"] = "test"
    scope: Literal["read", "admin"] = "read"
    rate_limit: int = Field(default=60, ge=1, le=100000)


class KeyIssued(BaseModel):
    id: str
    key: str  # plaintext, shown exactly once
    key_prefix: str
    env: str
    scope: str
    rate_limit: int
