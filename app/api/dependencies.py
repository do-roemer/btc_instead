from fastapi import HTTPException, status, Depends
from typing import AsyncGenerator

from app.core.database.db_interface import DatabaseInterface
import app.core.secret_handler as secrets
from app.core.services.process_reddit_posts import RedditPostProcessor
from app.core.services.process_asset import AssetProcessor
from app.core.fetcher.reddit import RedditFetcher
from app.core.services.process_portfolio import PortfolioProcessor
from app.core.fetcher.crypto_currency import CryptoCurrencyFetcher
from app.core.app_config import get_config
from app.core.utils.utils import set_logger

logger = set_logger(name=__name__)
secret_config = secrets.get_config()
app_config = get_config()


async def get_db() -> AsyncGenerator[DatabaseInterface, None]:
    db = None
    try:
        db = DatabaseInterface(
            host=secret_config.get("MYSQL_HOST"),
            user=secret_config.get("MYSQL_USERNAME"),
            password=secret_config.get("MYSQL_KEY"),
            database=secret_config.get("MYSQL_DBNAME"),
            is_ssh_tunnel=True if secret_config.get("ENVIRONMENT")
            == "local" else False,
        )
        yield db
    except Exception as e:
        logger.error(
            f"Failed to initialize or connect DatabaseInterface: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service not available."
        )


async def get_reddit_post_processor(
    db: DatabaseInterface = Depends(get_db)
) -> RedditPostProcessor:
    """
    Dependency to provide a RedditPostProcessor instance.
    """
    try:
        processor = RedditPostProcessor(db_interface=db)
        return processor
    except Exception as e:
        logger.error(
            f"Failed to initialize RedditPostProcessor: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reddit post processor service not available."
        )


async def get_portfolio_processor(
    db: DatabaseInterface = Depends(get_db)
) -> PortfolioProcessor:
    """
    Dependency to provide a PortfolioProcessor instance.
    """
    try:
        processor = PortfolioProcessor(db_interface=db)
        return processor
    except Exception as e:
        logger.error(
            f"Failed to initialize PortfolioProcessor: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Portfolio processor service not available."
        )


async def get_asset_processor(
    db: DatabaseInterface = Depends(get_db)
) -> AssetProcessor:
    """
    Dependency to provide an AssetProcessor instance.
    """
    try:
        processor = AssetProcessor(db_interface=db)
        return processor
    except Exception as e:
        logger.error(
            f"Failed to initialize AssetProcessor: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Asset processor service not available."
        )


async def get_crypto_currency_fetcher() -> CryptoCurrencyFetcher:
    """
    Dependency to provide a CryptoCurrencyFetcher instance.
    """
    try:
        fetcher = CryptoCurrencyFetcher()
        return fetcher
    except Exception as e:
        logger.error(
            f"Failed to initialize CryptoCurrencyFetcher: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Crypto currency fetcher service not available."
        )


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