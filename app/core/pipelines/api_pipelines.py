from app.core.utils.utils import set_logger
from app.core.services.process_reddit_posts import RedditPostProcessor
from app.core.services.process_portfolio import PortfolioProcessor
from app.core.services.process_asset import AssetProcessor
from app.core.fetcher.reddit import RedditFetcher
from app.core.database.db_interface import DatabaseInterface
from app.core.fetcher.crypto_currency import CryptoCurrencyFetcher
from app.core.database.reddit_post_db_handler import (
    insert_reddit_posts_to_db
)
from app.core.pipelines.pipelines import (
    fetch_reddit_post_and_upload_to_db_pipeline,
    reddit_posts_to_portfolio_processor_pipeline,
    evaluate_portfolio_pipeline
)

logger = set_logger(name=__name__)


async def redditpost_url_evaluation_pipeline(
    url: str,
    rp_processor: RedditPostProcessor,
    portfolio_processor: PortfolioProcessor,
    asset_processor:  AssetProcessor,
    cc_fetcher: CryptoCurrencyFetcher,
    reddit_fetcher: RedditFetcher
):
    "Start with a reddit url, fetch the post, upload it to the db and"
    "evaluate the portfolio based on the post."

    reddit_post_id = reddit_fetcher.get_reddit_post_id_from_url(
        url=url
    )
    if not rp_processor.reddit_post_processed(reddit_post_id=reddit_post_id) \
            and not rp_processor.reddit_post_is_portfolio(
                reddit_post_id=reddit_post_id):
        if not portfolio_processor.portfolio_already_exists(
                "reddit",
                reddit_post_id
        ):
            uploaded_reddit_id = fetch_reddit_post_and_upload_to_db_pipeline(
                url=url,
                reddit_fetcher=reddit_fetcher,
                reddit_post_processor=rp_processor
            )

        if not portfolio_processor.portfolio_already_exists(
            "reddit",
            uploaded_reddit_id
        ):
            reddit_posts_to_portfolio_processor_pipeline(
                reddit_id=uploaded_reddit_id,
                rp_processor=rp_processor,
                portfolio_processor=portfolio_processor,
                asset_processor=asset_processor,
                cc_fetcher=cc_fetcher
            )
            processed_reddit_post_id = uploaded_reddit_id     
    else:
        logger.info(
            f"Reddit post with ID {reddit_post_id} has already been processed."
        )
        processed_reddit_post_id = reddit_post_id

    if rp_processor.reddit_post_is_portfolio(
                reddit_post_id=processed_reddit_post_id):
        evaluate_portfolio_pipeline(
            source="reddit",
            source_id=processed_reddit_post_id,
            portfolio_processor=portfolio_processor,
            cc_fetcher=cc_fetcher,
            asset_processor=asset_processor
        )
    else:
        logger.info(
            f"""Reddit post with ID {processed_reddit_post_id}
            is not a portfolio."""
        )


async def redditpost_url2db_pipeline(
        url: str,
        db_interface: DatabaseInterface,
        reddit_fetcher: RedditFetcher
):

    fetched_posts_data = None

    try:
        fetched_posts_data = reddit_fetcher.fetch_posts_by_post_url(
            url=url
        )
        # --- Insert data into Database ---
        if fetched_posts_data:
            logger.info(
                f"""Attempting to insert
                {len(fetched_posts_data)} posts into database...""")
            try:
                inserted_count = insert_reddit_posts_to_db(
                    db_interface=db_interface,
                    reddit_post=fetched_posts_data
                )
                logger.info(
                    f"Successfully inserted/updated {inserted_count} records.")
            except Exception as e:
                logger.error(
                    f"""An unexpected error occurred
                        during database insertion: {e}""",
                    exc_info=True)
                raise
        else:
            logger.warning(
                "No new post data fetched, skipping database insertion.")

        # --- Success ---
        logger.info("--- Daily hot posts fetch finished successfully ---")
        return {
            'statusCode': 200,
            'body':
                f"""Successfully processed {len(fetched_posts_data)}"""
        }

    except Exception as e:
        # --- Catch-all for any unexpected errors during handler execution ---
        logger.error(
            f"An unhandled exception occurred in the lambda handler: {e}",
            exc_info=True)
        raise
