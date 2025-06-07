from pydantic import BaseModel, HttpUrl, Field
from typing import Optional


class PipelineRequest(BaseModel):
    url: HttpUrl = Field(
        examples=[
            "https://www.reddit.com/r/WallStreetBetsCrypto/comments/1i9txgu/hi_everyone_please_rate_my_portfolio_and/"
            ]
        )    


class PipelineResponse(BaseModel):
    status: str
    message: str
    error_details: Optional[str] = None
