from pydantic import BaseModel


class UsageByEndpoint(BaseModel):
    endpoint: str
    units: int
    calls: int


class UsageResponse(BaseModel):
    account_id: str
    env: str
    total_units: int
    total_calls: int
    by_endpoint: list[UsageByEndpoint]
