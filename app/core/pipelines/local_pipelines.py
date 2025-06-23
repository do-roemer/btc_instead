import json
from datetime import timedelta
from datetime import datetime 
import time

from app.core.utils.utils import set_logger
import app.core.secret_handler as secrets
from app.core.services.process_reddit_posts import RedditPostProcessor
from app.core.services.process_portfolio import PortfolioProcessor
from app.core.services.process_asset import AssetProcessor
from app.core.fetcher.reddit import RedditFetcher
from app.core.database.db_interface import DatabaseInterface
from app.core.fetcher.crypto_currency import CryptoCurrencyFetcher
from app.core.entities.purchase import Purchase
from app.core.database.asset_db_handler import (
    get_tracked_crypto_currency_in_db,
    get_asset_price_from_db_by_iso_week_year
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
            if result['result']["is_portfolio"]:
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


def evaluate_portfolio_pipeline(
    source: str,
    source_id: str,
    portfolio_processor: PortfolioProcessor,
    cc_fetcher: CryptoCurrencyFetcher,
    asset_processor: AssetProcessor
):
    """
    Evaluate portfolios based on source IDs.
    """
    portfolio = portfolio_processor.get_portfolio_by_source_id_from_db(
            source=source,
            source_id=source_id
        )
    purchases = portfolio_processor.get_purchases_for_portfolio_from_db(
        source=source,
        source_id=source_id
    )

    for purchase in purchases:
        coinids = asset_processor.get_provider_coin_ids(
            name=purchase.name,
            abbreviation=purchase.abbreviation
        )
        if not coinids:
            logger.error(
                f"Coin IDs for {purchase.name} ({purchase.abbreviation}) "
                f"not found in the database."
            )
            continue
        current_value_dict = cc_fetcher.fetch_current_coin_price(coinids)
        purchase.update_values(
            current_value=current_value_dict["price"]
        )
        portfolio.add_purchase(purchase)

    current_btc_price = cc_fetcher.fetch_current_coin_price(
        asset_processor.get_provider_coin_ids(
            name='bitcoin',
            abbreviation='btc'
        )
    )

    past_btc_price = get_asset_price_from_db_by_iso_week_year(
        db_interface=portfolio_processor.db_interface,
        name="bitcoin",
        abbreviation="btc",
        iso_week=portfolio.created_date.isocalendar()[1],
        iso_year=portfolio.created_date.isocalendar()[0],
        dictionary_cursor=True
    )
    if not past_btc_price:
        logger.error(
            f"Bitcoin price for week {portfolio.created_date.isocalendar()[1]} "
            f"of year {portfolio.created_date.isocalendar()[0]} not found in the database."
        )
        return None
    portfolio = portfolio_processor.evaluate_portfolio(
        portfolio,
        current_btc_price["price"],
        past_btc_price["price"]
        )


def extract_and_save_cc_prices_of_past_year_pipeline(
    asset_processor: AssetProcessor,
    cc_fetcher: CryptoCurrencyFetcher,
    name: str,
    abbreviation: str,
    currency: str
):
    today = datetime.today()
    asset_data = asset_processor.get_asset_from_db(
        name=name,
        abbreviation=abbreviation
    )
    if not asset_data:
        logger.error(
            f"Asset {name} ({abbreviation}) not found in the database."
        )
        return None
    for i in range(52):
        week_date = today - timedelta(weeks=i)
        # Get Monday of the week
        monday = week_date - timedelta(days=week_date.weekday())
        iso_year, iso_week, _ = monday.isocalendar()
        cc_price = \
            cc_fetcher.fetch_cc_data_for_iso_week_from_coin_gecko(
                coin_id=asset_data["coin_gecko_id"],
                iso_week=iso_week,
                iso_year=iso_year
            )
        if asset_processor.cc_price_is_tracked(
            name=name,
            abbreviation=asset_data["abbreviation"],
            iso_week=iso_week,
            iso_year=iso_year
        ):
            logger.info(
                f"Crypto currency {name} ({abbreviation}) price for "
                f"week {iso_week} of {iso_year} is already tracked."
            )
            continue
        asset_processor.upload_crypto_currency_price_to_db(
                name=name,
                abbreviation=asset_data["abbreviation"],
                price=cc_price,
                date=monday,
                iso_week=iso_week,
                iso_year=iso_year,
                currency=currency
            )
        time.sleep(10)      


def upload_portfolio_purchases_to_db_pipeline(
        portfolio_processor: PortfolioProcessor,
        purchases: list[Purchase] = None
):
    if app_config["debug"]["is_debug"]:
        with open("data/mock/reddit_post_process_results.json", "r") as f:
            process_result_dicts = json.load(f)
            for portfolio_data in process_result_dicts:
                for purchase in portfolio_data['result']["positions"]:
                    purchase_instance = portfolio_processor.create_purchase(
                            source="reddit",
                            source_id=portfolio_data["source_id"],
                            name=purchase["name"],
                            abbreviation=purchase["abbreviation"],
                            amount=purchase["amount"],
                            total_purchase_value=purchase["price"],
                            purchase_date=portfolio_data['created_date'].split("T")[0],
                            currency=purchase.get("currency", "usd"),
                        )
                    portfolio_processor.purchase_to_db(
                        purchase_instance
                    )
    else:
        if purchases is None:
            logger.error("No purchases provided to upload to the database.")
            return
        for purchase in purchases:
            purchase_instance = portfolio_processor.create_purchase(
                source=purchase["source"],
                source_id=purchase["source_id"],
                name=purchase["name"],
                abbreviation=purchase["abbreviation"],
                amount=purchase["amount"],
                total_purchase_value=purchase["total_purchase_value"],
                purchase_date=purchase["purchase_date"],
                currency=purchase.get("currency", "usd"),
            )
            portfolio_processor.purchase_to_db(
                purchase_instance
            )


def init_asset_into_db_pipeline(
        asset_data: list[dict],
        cc_fetcher: CryptoCurrencyFetcher,
        asset_processor: AssetProcessor
):
    """
    Initialize assets into the database.
    """
    for asset in asset_data:
        if asset_processor.crypto_currency_is_tracked(
            name=asset["name"],
            abbreviation=asset["abbreviation"]
        ):
            logger.info(
                f"Crypto currency {asset['name']} ({asset['abbreviation']}) is already tracked."
            )
            continue
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