from datetime import timedelta
from datetime import datetime
import time

from app.core.entities.portfolio import Portfolio
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
    get_tracked_crypto_currency_in_db
)
from app.core.entities.portfolio import Portfolio
from app.core.app_config import get_config

app_config = get_config()
secret_config = secrets.get_config()
logger = set_logger(name=__name__)


def reddit_posts_to_portfolio_processor_pipeline(
    reddit_id: str,
    rp_processor: RedditPostProcessor,
    portfolio_processor: PortfolioProcessor,
    asset_processor:  AssetProcessor,
    cc_fetcher: CryptoCurrencyFetcher
):
    """
    Takes a reddit post id, get its data from the DB, runs
    a portfolio process on it and uploads the portfolio to the DB.
    """
    reddit_process_result = rp_processor.process(
        reddit_post_id=reddit_id
    )

    portfolio_processor.upload_reddit_post_purchase_data_to_db_pipeline(
        reddit_post_result_dict=reddit_process_result
    )

    # Initialize portfolios in the database for each processed Reddit post
    if not app_config["debug"]["is_debug"]:
        if reddit_process_result['result']["is_portfolio"]:
            portfolio_processor.initialize_portfolio_in_db(
                source="reddit",
                source_id=reddit_process_result["source_id"],
                created_date=reddit_process_result["created_date"]
            )
    if reddit_process_result["result"]["is_portfolio"]:
        init_asset_into_db_pipeline(
            asset_data=reddit_process_result["result"]["purchases"],
            cc_fetcher=cc_fetcher,
            asset_processor=asset_processor
        )
    logger.info(f"Initialized portfolio from reddit for id: {reddit_id}.")


def run_url_to_portfolio_evaluation_pipeline(
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
        url=[0]
    )
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

        evaluate_portfolio_pipeline(
            source="reddit",
            source_id=uploaded_reddit_id,
            portfolio_processor=portfolio_processor,
            cc_fetcher=cc_fetcher,
            asset_processor=asset_processor
        )


def process_purchases_pipeline(
    purchases: list[Purchase],
    asset_processor: AssetProcessor,
    cc_fetcher: CryptoCurrencyFetcher
) -> list[Purchase]:
    current_date = datetime.today()
    for purchase in purchases:

        if asset_processor.cc_price_of_current_iso_week_is_tracked(
            name=purchase.name,
            abbreviation=purchase.abbreviation,
            iso_week=current_date.isocalendar()[1],
            iso_year=current_date.isocalendar()[0]
        ):
            current_asset_price_data = asset_processor.\
                get_asset_price_from_db_by_iso_week_year(
                    name=purchase.name,
                    abbreviation=purchase.abbreviation,
                    iso_week=current_date.isocalendar()[1],
                    iso_year=current_date.isocalendar()[0]
                )
            current_asset_price = current_asset_price_data["price"]
        else:
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
            _ = asset_processor.upload_crypto_currency_price_to_db(
                name=purchase.name,
                abbreviation=purchase.abbreviation,
                price=current_value_dict["price"],
                date=current_date,
                iso_week=current_date.isocalendar()[1],
                iso_year=current_date.isocalendar()[0],
                currency=current_value_dict.get("currency", "usd")
            )
            current_asset_price = current_value_dict["price"]
        if current_asset_price is None:
            logger.warning(
                f"Can't fetch current {purchase.name} price."
                " Abort pipeline."
            )
            return None
        purchase.update_values(
            current_value=current_asset_price
        )
    return purchases


def evaluate_portfolio_pipeline(
    source: str,
    source_id: str,
    portfolio_processor: PortfolioProcessor,
    cc_fetcher: CryptoCurrencyFetcher,
    asset_processor: AssetProcessor
) -> Portfolio:
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

    process_purchases_pipeline(
        purchases=purchases,
        asset_processor=asset_processor,
        cc_fetcher=cc_fetcher
    )
    if purchases is None:
        logger.warning(
            "Failed to return a valid or complete list of purchases."
            " Abort pipeline."
        )
    for purchase in purchases:
        portfolio.add_purchase(purchase)

    current_btc_price, past_btc_price_data = get_current_and_past_btc_price(
        asset_processor=asset_processor,
        cc_fetcher=cc_fetcher,
        portfolio=portfolio,
        past_iso_week=portfolio.created_date.isocalendar()[1],
        past_iso_year=portfolio.created_date.isocalendar()[0]
    )
    if current_btc_price is None or past_btc_price_data is None:
        logger.warning("Can't fetch BTC price data. Abort pipeline.")
        return None

    portfolio = portfolio_processor.evaluate_portfolio(
        portfolio,
        current_btc_price,
        past_btc_price_data["price"]
        )

    portfolio_processor.update_portfolio_in_db(
        portfolio=portfolio
    )
    logger.info(
        f"Portfolio {source} ({source_id})"
        " evaluated and updated in the database."
    )

    print(portfolio.format_portfolio_summary())
    return portfolio


def get_current_and_past_btc_price(
        asset_processor: AssetProcessor,
        cc_fetcher: CryptoCurrencyFetcher,
        portfolio: Portfolio,
        past_iso_week: int,
        past_iso_year: int
):
    """Returns the current and past BTC price data."""
    current_date = datetime.today()
    current_btc_price = None
    past_btc_price_data = None
    # Get current BTC price data
    if asset_processor.cc_price_of_current_iso_week_is_tracked(
            name='bitcoin',
            abbreviation='btc',
            iso_week=current_date.isocalendar()[1],
            iso_year=current_date.isocalendar()[0]
    ):
        current_asset_price_data = asset_processor.\
                get_asset_price_from_db_by_iso_week_year(
                    name='bitcoin',
                    abbreviation='btc',
                    iso_week=current_date.isocalendar()[1],
                    iso_year=current_date.isocalendar()[0]
                )
    else:
        current_asset_price_data = cc_fetcher.fetch_current_coin_price(
            asset_processor.get_provider_coin_ids(
                name='bitcoin',
                abbreviation='btc'
            )
        )
    try:
        current_btc_price = current_asset_price_data["price"]
    except KeyError:
        logger.error("Can't fetch current BTC price. Abort pipeline.")
        return None, None
    if current_btc_price is None:
        logger.warning("Can't fetch current BTC price. Abort pipeline.")
        return None, None

    # Get past BTC price data
    past_btc_price_data = asset_processor.\
        get_asset_price_from_db_by_iso_week_year(
            name="bitcoin",
            abbreviation="btc",
            iso_week=past_iso_week,
            iso_year=past_iso_year
        )
    if not past_btc_price_data:
        logger.error(
            f"""Bitcoin price for week
            {portfolio.created_date.isocalendar()[1]}
            of year {portfolio.created_date.isocalendar()[0]}
            not found in the database.
            """
        )
        return None, None
    return current_btc_price, past_btc_price_data


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
) -> None:
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
                f"Crypto currency {asset['name']} ({asset['abbreviation']})"
                " is already tracked."
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
    Fetch Reddit posts by urls and process them.
    """
    results = []
    for url in urls:
        if not url.startswith("https://www.reddit.com/"):
            logger.error(
                f"Invalid Reddit URL: {url}. "
                "URLs must start with 'https://www.reddit.com/'."
            )
            return []
        result = reddit_fetcher.fetch_posts_by_post_url(
            url=url
        )
        if not result:
            logger.warning(f"No posts found for URL: {url}")
            continue
        results.extend(result)
    logger.info(f"Fetched {len(results)} posts from URLs: {urls}")
    logger.info("Results:", results[0])
    return results


def fetch_reddit_post_and_upload_to_db_pipeline(
        url: str,
        reddit_fetcher: RedditFetcher,
        reddit_post_processor: RedditPostProcessor
) -> str:
    """Takes a reddit url, fetches its data, uploads its info and returns
    the fetched and uploaded reddit post id"""

    result = reddit_fetcher.fetch_posts_by_post_url(
        url=url
    )
    if result:
        reddit_post_processor.upload_reddit_post_to_db(
            reddit_post_data_dict=result
        )
    return result["post_id"]
