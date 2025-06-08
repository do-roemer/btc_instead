from app.core.database.db_interface import DatabaseInterface
import app.core.secret_handler as secrets
from app.core.services.process_reddit_posts import RedditPostProcessor
from app.core.services.process_asset import AssetProcessor
from app.core.fetcher.reddit import RedditFetcher
from app.core.services.process_portfolio import PortfolioProcessor
from app.core.fetcher.crypto_currency import CryptoCurrencyFetcher
from app.core.pipelines.local_pipelines import (
    redditposts_processor_pipeline,
    fetch_and_upload_weeklsy_crypto_prices_to_db_pipeline,
    upload_portfolio_purchases_to_db_pipeline
)
secret_config = secrets.get_config()

db_interface = DatabaseInterface(
        host=secret_config.get("MYSQL_HOST"),
        user=secret_config.get("MYSQL_USERNAME"),
        password=secret_config.get("MYSQL_KEY"),
        database=secret_config.get("MYSQL_DBNAME"),
        is_ssh_tunnel=True if secret_config.get("ENVIRONMENT") == "local" else False,
    )
rp_processor = RedditPostProcessor(
        db_interface=db_interface
)

portfolio_processor = PortfolioProcessor(
        db_interface=db_interface
)

cc_fetcher = CryptoCurrencyFetcher()

asset_processor = AssetProcessor(
        db_interface=db_interface
)

reddit_fetcher = RedditFetcher(
                client_id=secret_config.get("REDDIT_CLIENT_ID"),
                client_secret=secret_config.get("REDDIT_CLIENT_SECRET"),
                user_agent=secret_config.get("REDDIT_USER_AGENT"),
                username=secret_config.get("REDDIT_USERNAME"),
                password=secret_config.get("REDDIT_PASSWORD")
            )

upload_portfolio_purchases_to_db_pipeline(
    portfolio_processor
)

#redditposts_processor_pipeline(
#    rp_processor=rp_processor,
#    portfolio_processor=portfolio_processor,
#    cc_fetcher=cc_fetcher,
#    asset_processor=asset_processor,
#    reddit_ids=[
#        "1l1smbv",
#        "1i9txgu"      
#    ]
#)
