from fastapi import FastAPI
from app.api.v1.endpoints import (
    url2db_ep,
    reddit_url2portfolio_ep
)

app = FastAPI(
    title="btc-instead-api",
    description="API to trigger core processing pipelines for btc instea.",
    version="0.1.0"
)

app.include_router(
    url2db_ep.router,
    prefix="/api/v1/url-processor",
    tags=["Reddit url uploading to db"]
)

app.include_router(
    reddit_url2portfolio_ep.router,
    prefix="/api/v1/url-processor",
    tags=["Portfolio Evaluation"]
)


# A simple root endpoint for health check or basic info
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the BTC instead API!"}
