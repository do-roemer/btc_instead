from fastapi import APIRouter, HTTPException, status, Body, Depends

from app.core.utils.utils import set_logger
from app.api.models import PipelineRequest, PipelineResponse
from app.core.pipelines.api_pipelines import (
    redditpost_url2db_pipeline
)
from app.api.dependencies import (
    get_db,
    get_reddit_fetcher
 )
from app.core.database.db_interface import \
    DatabaseInterface
from app.core.fetcher.reddit import RedditFetcher

logger = set_logger(name=__name__)

router = APIRouter()


@router.post(
    "/execute-redditurl2db",
    response_model=PipelineResponse,
    summary="Take reddit post url  and upload the post into db",
    tags=["Pipeline Operations"]
)
async def run_redditpost_url2db_pipeline(
    payload: PipelineRequest = Body(...),
    db: DatabaseInterface = Depends(get_db),
    fetcher: RedditFetcher = Depends(get_reddit_fetcher)
):
    """
    Accepts a URL and an optional custom parameter, then executes
    the predefined pipeline from `app.core`.

    - **url**: The URL to process.
    - **custom_parameter**: An optional parameter for the pipeline.
    """
    try:
        print(f"API: Received request to process URL: {payload.url}")
        # Pass parameters to your core pipeline function as needed
        pipeline_result = await redditpost_url2db_pipeline(
            url=str(payload.url),
            db_interface=db,
            reddit_fetcher=fetcher
        )
        return PipelineResponse(
            status="success",
            message="Pipeline executed successfully.",
            result=pipeline_result
        )
    except ValueError as ve:
        # Catch specific errors from your pipeline that indicate a processing issue
        print(f"API: Value error during pipeline execution: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pipeline error: {str(ve)}"
        )
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"API: Unexpected error during pipeline execution: {e}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected internal server error occurred: {str(e)}"
        )