from app.core.app_config import get_config
from app.core.database.db_interface import DatabaseInterface
from app.core.database.reddit_post_db_handler import (
    insert_reddit_posts_to_db
)
from app.core.fetcher.reddit import RedditFetcher
import app.core.secret_handler as secrets
from app.core.utils.utils import set_logger

logger = set_logger(name=__name__)
secret_config = secrets.get_config()
app_config = get_config()


async def redditpost2db_pipeline(
        url: str,
        db_interface: DatabaseInterface,
        reddit_fetcher: RedditFetcher
):

    fetched_posts_data = None

    try:
        fetched_posts_data = reddit_fetcher.fetch_posts_by_post_url(
            urls=[url]
        )
        # --- Insert data into Database ---
        if fetched_posts_data:
            logger.info(
                f"""Attempting to insert
                {len(fetched_posts_data)} posts into database...""")
            try:
                inserted_count = insert_reddit_posts_to_db(
                    db_interface=db_interface,
                    reddit_posts=fetched_posts_data
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
