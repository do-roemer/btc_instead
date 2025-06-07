from fastapi import HTTPException, status
from app.core.app_config import get_config
from app.core.database.db_interface import DatabaseInterface
from app.core.fetcher.reddit import RedditFetcher
import app.core.secret_handler as secrets
from app.core.utils.utils import set_logger

logger = set_logger(name=__name__) # Logger for dependency setup
secret_config = secrets.get_config()
app_config = get_config()

_reddit_fetcher_instance = None


def get_reddit_fetcher_instance() -> RedditFetcher:
    global _reddit_fetcher_instance
    if _reddit_fetcher_instance is None:
        try:
            logger.info("Initializing global RedditFetcher instance...")
            _reddit_fetcher_instance = RedditFetcher(
                client_id=secret_config.get("REDDIT_CLIENT_ID"),
                client_secret=secret_config.get("REDDIT_CLIENT_SECRET"),
                user_agent=secret_config.get("REDDIT_USER_AGENT"),
                username=secret_config.get("REDDIT_USERNAME"),
                password=secret_config.get("REDDIT_PASSWORD")
            )
            logger.info("Global RedditFetcher instance initialized.")
        except Exception as e:
            logger.error(f"CRITICAL: Failed to initialize RedditFetcher: {e}", exc_info=True)
            # This error will prevent the app from starting correctly if it's critical
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Reddit service connector not available."
            )
    return _reddit_fetcher_instance


async def get_db() -> DatabaseInterface:
    db = None
    try:
        db = DatabaseInterface(
            host=secret_config.get("MYSQL_HOST"),
            user=secret_config.get("MYSQL_USERNAME"),
            password=secret_config.get("MYSQL_KEY"),
            database=secret_config.get("MYSQL_DBNAME"),
            is_ssh_tunnel=True if secret_config.get("ENVIRONMENT") == "local" else False,
        )
        yield db
    except Exception as e:
        logger.error(f"Failed to initialize or connect DatabaseInterface: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service not available."
        )
    finally:
        if db:
            # logger.info("Closing DatabaseInterface for a request...") # Can be noisy
            try:
                # If your DatabaseInterface has an explicit close method:
                await db.close() # if it's an async close
                # or db.close() # if it's a sync close
            except Exception as e:
                logger.error(f"Error closing DatabaseInterface: {e}", exc_info=True)


async def get_reddit_fetcher() -> RedditFetcher:
    try:
        # logger.info("Initializing RedditFetcher for a request...")
        fetcher = RedditFetcher(
            client_id=secret_config.get("REDDIT_CLIENT_ID"),
            client_secret=secret_config.get("REDDIT_CLIENT_SECRET"),
            user_agent=secret_config.get("REDDIT_USER_AGENT"),
            username=secret_config.get("REDDIT_USERNAME"),
            password=secret_config.get("REDDIT_PASSWORD")
        )
        return fetcher
    except Exception as e:
        logger.error(f"Failed to initialize RedditFetcher: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reddit service connector not available."
        )