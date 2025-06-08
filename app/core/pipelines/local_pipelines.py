import json

from app.core.utils.utils import set_logger
import app.core.secret_handler as secrets
from app.core.services.process_reddit_posts import RedditPostProcessor
from app.core.services.process_portfolio import PortfolioProcessor
from app.core.services.process_asset import AssetProcessor
from app.core.fetcher.reddit import RedditFetcher
from app.core.database.db_interface import DatabaseInterface
from app.core.fetcher.crypto_currency import CryptoCurrencyFetcher
from app.core.database.asset_db_handler import (
    get_tracked_crypto_currency_in_db
)
from app.core.app_config import get_config

app_config = get_config()
secret_config = secrets.get_config()
logger = set_logger(name=__name__)


def redditposts_processor_pipeline(
    reddit_ids: list[str],
    rp_processor: RedditPostProcessor,
    portfolio_processor: PortfolioProcessor,
    asset_processor:  AssetProcessor,
    cc_fetcher: CryptoCurrencyFetcher,
):
    reddit_process_results = rp_processor.process(
        reddit_post_ids=reddit_ids
    )

    # Initialize portfolios in the database for each processed Reddit post
    if not app_config["debug"]["is_debug"]:
        for result in reddit_process_results:
            if result["is_portfolio"]:
                portfolio_processor.initialize_portfolio_in_db(
                    source="reddit",
                    source_id=result["source_id"],
                    created_date=result["created_date"]
                )
    for result in reddit_process_results:
        if result["result"]["is_portfolio"]:
            init_asset_into_db_pipeline(
                asset_data=result["result"]["positions"],
                cc_fetcher=cc_fetcher,
                asset_processor=asset_processor
            )
    logger.info("Initialized portfolios.")


def upload_portfolio_purchases_to_db_pipeline(
        portfolio_processor: PortfolioProcessor,
        purchases: dict = None,
):
    with open("data/mock/reddit_post_process_results.json", "r") as f:
        process_result_dicts = json.load(f)
    
    print("end")


def init_asset_into_db_pipeline(
        asset_data: list[dict],
        cc_fetcher: CryptoCurrencyFetcher,
        asset_processor: AssetProcessor
):
    """
    Initialize assets into the database.
    """
    for asset in asset_data:
        cmc_coin_id = cc_fetcher.find_coin_id(
            name=asset["name"],
            abbreviation=asset["abbreviation"],
            provider="coin_market_cap"
        )
        gecko_coin_id = cc_fetcher.find_coin_id(
            name=asset["name"],
            abbreviation=asset["abbreviation"],
            provider="coin_gecko"
        )
        asset_processor.insert_or_update_asset(
            name=asset["name"],
            abbreviation=asset["abbreviation"],
            provider_coin_id={
                "coin_market_cap": cmc_coin_id,
                "coin_gecko": gecko_coin_id
            }
        )


def fetch_and_upload_weeklsy_crypto_prices_to_db_pipeline(
    db_interface: DatabaseInterface,
    asset_processor: AssetProcessor
):
    """
    Fetch and upload weekly crypto prices to the database.
    """
    logger.info("Fetching weekly crypto prices.")
    tracked_ccs = get_tracked_crypto_currency_in_db(
        db_interface=db_interface
    )
    failed_assets = []
    if not tracked_ccs:
        logger.warning("No tracked crypto currencies found in the database.")
        return
    else:
        for coin_data in tracked_ccs:
            asset_processed = asset_processor.process_asset(
                name=coin_data["name"],
                abbreviation=coin_data["abbreviation"]
            )
            if not asset_processed:
                failed_assets.append(coin_data["abbreviation"])
    if len(failed_assets) > 0:
        logger.warning(
            f"Failed to process the following assets: {failed_assets}"
        )            
    logger.info("Uploaded weekly crypto prices to the database.")


def fetch_reddit_posts_from_url_pipeline(
    urls: list[str],
    reddit_fetcher: RedditFetcher
):
    """
    Fetch Reddit posts by IDs and process them.
    """
    results = reddit_fetcher.fetch_posts_by_post_url(
        urls=urls
    )
    print(f"Fetched {len(results)} posts from URLs: {urls}")
    print("Results:", results[0])