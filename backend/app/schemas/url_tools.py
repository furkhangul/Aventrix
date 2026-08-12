from pydantic import BaseModel, Field


class UrlAnalyzeRequest(BaseModel):
    url: str = Field(max_length=2048)


class UrlAnalyzeResponse(BaseModel):
    final_url: str
    status_code: int
    redirect_count: int
    elapsed_ms: float
    content_type: str | None
    title: str | None
    description: str | None
    favicon_url: str | None


class RedirectCheckRequest(BaseModel):
    url: str = Field(max_length=2048)


class RedirectHopResponse(BaseModel):
    url: str
    status_code: int
    location: str | None
    elapsed_ms: float


class RedirectCheckResponse(BaseModel):
    hops: list[RedirectHopResponse]
    final_url: str
    final_status_code: int
