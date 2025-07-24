from fastapi import APIRouter, HTTPException, status, Body, Depends

from app.core.utils.utils import set_logger
from app.api.models import PipelineRequest, PipelineResponse
from app.core.pipelines.api_pipelines import (
    redditpost_url_evaluation_pipeline
)
from app.api.dependencies import (
    get_reddit_post_processor,
    get_portfolio_processor,
    get_asset_processor,
    get_crypto_currency_fetcher,
    get_reddit_fetcher
)
from app.core.services.process_reddit_posts import RedditPostProcessor
from app.core.services.process_portfolio import PortfolioProcessor
from app.core.services.process_asset import AssetProcessor
from app.core.fetcher.crypto_currency import CryptoCurrencyFetcher
from app.core.fetcher.reddit import RedditFetcher

logger = set_logger(name=__name__)

router = APIRouter()


@router.post(
    "/execute-reddit-url-evaluation",
    response_model=PipelineResponse,
    summary="""Take reddit post URL and evaluate the
        portfolio mentioned in the post""",
    tags=["Portfolio Evaluation"]
)
async def run_reddit_url_evaluation_pipeline(
    payload: PipelineRequest = Body(...),
    rp_processor: RedditPostProcessor = Depends(get_reddit_post_processor),
    portfolio_processor: PortfolioProcessor = Depends(get_portfolio_processor),
    asset_processor: AssetProcessor = Depends(get_asset_processor),
    cc_fetcher: CryptoCurrencyFetcher = Depends(get_crypto_currency_fetcher),
    reddit_fetcher: RedditFetcher = Depends(get_reddit_fetcher)
):
    """
    Accepts a Reddit post URL and executes the complete evaluation pipeline:
    1. Fetches the Reddit post
    2. Uploads it to the database
    3. Processes the portfolio mentioned in the post
    4. Evaluates the portfolio performance

    - **url**: The Reddit post URL to process and evaluate.
    - **custom_parameter**: An optional parameter for the pipeline.
    """
    try:
        logger.info(f"API: Starting Reddit URL evaluation for: {payload.url}")
        
        # Execute the complete evaluation pipeline
        pipeline_result = await redditpost_url_evaluation_pipeline(
            url=str(payload.url),
            rp_processor=rp_processor,
            portfolio_processor=portfolio_processor,
            asset_processor=asset_processor,
            cc_fetcher=cc_fetcher,
            reddit_fetcher=reddit_fetcher
        )

        logger.info(
            "API: Successfully completed Reddit URL evaluation for:"
            f"{payload.url}"
        )

        return PipelineResponse(
            status="success",
            message="Reddit URL evaluation pipeline executed successfully.",
            result=pipeline_result
        )

    except ValueError as ve:
        # Handle specific validation errors from the pipeline
        logger.warning(
            f"API: Validation error during Reddit URL evaluation: {ve}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(ve)}"
        )
    except FileNotFoundError as fe:
        # Handle cases where Reddit post is not found or URL is invalid
        logger.warning(f"API: Reddit post not found: {fe}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reddit post not found: {str(fe)}"
        )
    except PermissionError as pe:
        # Handle authentication/permission issues with Reddit API
        logger.error(f"API: Permission error accessing Reddit: {pe}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: {str(pe)}"
        )
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(
            f"API: Unexpected error during Reddit URL evaluation: {e}",
            exc_info=True
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected internal server error occurred: {str(e)}"
        )
