from app.core.app_config import get_config
import praw
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


try:
    logger.info("Try initializing database interface...")
    db_interface = DatabaseInterface(
        host=secret_config.get("MYSQL_HOST"),
        user=secret_config.get("MYSQL_USERNAME"),
        password=secret_config.get("MYSQL_KEY"),
        database=secret_config.get("MYSQL_DBNAME"),
        is_ssh_tunnel=True
        if secret_config.get("ENVIRONMENT") == "local" else False,
    )
    logger.info("DatabaseInterface initialized.")
except Exception as e:
    logger.error(
        f"CRITICAL: Failed to initialize DatabaseInterface: {e}",
        exc_info=True)
    raise

try:
    reddit_fetcher = RedditFetcher(
        client_id=secret_config.get("REDDIT_CLIENT_ID"),
        client_secret=secret_config.get("REDDIT_CLIENT_SECRET"),
        user_agent=secret_config.get("REDDIT_USER_AGENT"),
        username=secret_config.get("REDDIT_USERNAME"),
        password=secret_config.get("REDDIT_PASSWORD")
    )
    logger.info("RedditFetcher initialized.")
except Exception as e:
    logger.error(
        f"CRITICAL: Failed to initialize RedditFetcher: {e}",
        exc_info=True)
    raise


# --- Lambda Handler ---
def pipeline():
    """
    AWS Lambda handler function to fetch hot posts from Reddit
    and store them in a database.
    """
    logger.info("--- Starting daily hot posts fetch execution ---")
    fetched_posts_data = []

    try:
        subreddits_to_fetch = app_config.get('reddit_fetcher').get('subreddits')
        limit = app_config.get('reddit_fetcher').get('post_limit')
        for subreddit in subreddits_to_fetch:
            logger.info(
                f"""Configuration loaded:
                subreddit='{subreddit}', limit={limit}""")

            logger.info(
                    f"Attempting to fetch posts from r/{subreddit}..."
            )
            try:
                fetched_posts_from_subreddit = reddit_fetcher.get_new_posts(
                    subreddit_name=subreddit,
                    limit=limit
                )
                logger.info(
                    f"""
                    Successfully fetched {len(fetched_posts_from_subreddit)}
                    posts from {subreddit}.""")
                fetched_posts_data += fetched_posts_from_subreddit
            except praw.exceptions.PRAWException as e:
                logger.error(
                        f"PRAW API error during fetch: {e}",
                        exc_info=True)
                return {'statusCode': 502,
                        'body': f'Reddit API error: {e}'}
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred during Reddit fetch: {e}",
                    exc_info=True)
                return {'statusCode': 500,
                        'body': f'Error fetching from Reddit: {e}'}

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
                return {
                    'statusCode': 500,
                    'body': f'Error inserting into database: {e}'}
        else:
            logger.warning(
                "No new post data fetched, skipping database insertion.")

        # --- Success ---
        logger.info("--- Daily hot posts fetch finished successfully ---")
        return {
            'statusCode': 200,
            'body':
                f"""Successfully processed {len(fetched_posts_data)}
                posts for {subreddits_to_fetch}"""
        }

    except Exception as e:
        # --- Catch-all for any unexpected errors during handler execution ---
        logger.error(
            f"An unhandled exception occurred in the lambda handler: {e}",
            exc_info=True)
        return {
            'statusCode': 500,
            'body': f"An unexpected server error occurred: {e}"
        }
