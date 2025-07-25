from pydantic import BaseModel, HttpUrl, Field
from typing import Dict, Optional, Dict, Any


class PipelineRequest(BaseModel):
    url: HttpUrl = Field(
        examples=[
            "https://www.reddit.com/r/WallStreetBetsCrypto/comments/1i9txgu/hi_everyone_please_rate_my_portfolio_and/"
            ]
        )
    custom_parameter: Optional[Dict[str, Any]] = None


class PipelineResponse(BaseModel):
    status: str
    message: str
    result: Dict[str, Any]
    error_details: Optional[str] = None
