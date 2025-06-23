import datetime as dt

from app.core.utils.utils import set_logger
from app.core.app_config import get_config
from app.core.database.db_interface import DatabaseInterface
from app.core.database.asset_db_handler import (
    insert_crypto_currency_price_to_db,
    crypto_currency_is_tracked_in_db,
    track_crypto_currency_in_db,
    get_coin_ids_for_providers,
    crypto_currency_is_tracked_in_db,
    get_single_asset_from_db,
    cc_price_is_tracked_in_db
)
from app.core.fetcher.crypto_currency import CryptoCurrencyFetcher

app_config = get_config()
logger = set_logger(name=__name__)


class AssetProcessor:
    def __init__(
        self,
        db_interface: DatabaseInterface
    ):
        self.db_interface = db_interface  # Placeholder for database interface
        self.cc_fetcher = CryptoCurrencyFetcher()

    def upload_crypto_currency_price_to_db(
        self,
        name: str,
        abbreviation: str,
        price: float,
        date: str,
        iso_week: int = dt.date.today().isocalendar()[1],
        iso_year: int = dt.date.today().isocalendar()[0],
        currency: str = 'usd'
    ):
        # Placeholder for processing logic
        uploaded_status = insert_crypto_currency_price_to_db(
                self.db_interface,
                name=name,
                abbreviation=abbreviation,
                price=price,
                date=date,
                iso_week=iso_week,
                iso_year=iso_year,
                currency=currency
        )
        return uploaded_status

    def get_provider_coin_ids(
        self,
        name: str,
        abbreviation: str
    ) -> dict:
        if not self.crypto_currency_is_tracked(
                name=name,
                abbreviation=abbreviation
        ):
            coin_ids = {}
            for provider in self.cc_fetcher.providers:
                coin_ids[provider] = self.cc_fetcher.find_coin_id(
                    name=name,
                    abbreviation=abbreviation,
                    provider=provider
                )
            # Check if the coin_ids are empty
            # If all providers failed to find the coin ID, log an error
            if not any(coin_ids.values()):
                logger.error(
                    f"Failed to find coin IDs for {name} ({abbreviation}) "
                    "from all providers."
                )
                return None
            else:
                # Track the crypto currency in the database
                _ = track_crypto_currency_in_db(
                    self.db_interface,
                    name=name,
                    abbreviation=abbreviation,
                    provider_coin_id=coin_ids
                )

        else:
            # Get the provider coin_ids from CMC and Coin Gecko to
            # get the price from API
            coin_ids = get_coin_ids_for_providers(
                self.db_interface,
                name=name,
                abbreviation=abbreviation
            )
        return coin_ids

    def process_asset(
        self,
        name: str,
        abbreviation: str,
        currency: str = 'usd'
    ):
        """
        Process the asset data and upload it to the database.
        """
        asset_processed = False

        provider_coin_ids = self.get_provider_coin_ids(
            name=name,
            abbreviation=abbreviation,
        )
        if not provider_coin_ids:
            logger.error(
                f"Failed to find coin IDs for {name} ({abbreviation})"
            )
            return asset_processed

        # get the prices from API
        coin_data = self.cc_fetcher.fetch_current_coin_price(
            coin_ids=provider_coin_ids,
            vs_currency=currency
        )

        if coin_data.get("is_error"):
            logger.error(
                f"Error fetching data for {name} ({abbreviation}): "
                f"{coin_data.get('error_message')}"
            )
            return asset_processed
        else:
            iso_year, iso_week, _ = dt.date.fromisoformat(
                    coin_data.get("date")).isocalendar()

            uploaded_status = self.upload_crypto_currency_price_to_db(
                name=name,
                abbreviation=abbreviation,
                price=coin_data.get("price"),
                date=coin_data.get("date"),
                iso_week=iso_week,
                iso_year=iso_year,
                currency=currency
            )

            if uploaded_status:
                logger.info(
                    f"Uploaded {name} ({abbreviation}) price to DB: "
                    f"{coin_data.get('price')}"
                )
                asset_processed = True
            else:
                logger.error(
                    f"Failed to upload {name} ({abbreviation}) price to DB"
                )
        return asset_processed

    def fetch_and_upload_crypto_currency_price_of_current_week(
        self,
        cc_abbreviations,
    ):
        """
        Fetch the crypto currency price and upload it to the database.
        """
        for abbreviation in cc_abbreviations:
            # Fetch the crypto currency price
            cc_data = self.cc_fetcher.fetch_current_week_data(
                cc_abbreviation=abbreviation,
            )

            # Upload the price to the database
            self.upload_crypto_currency_price_to_db(
                abbreviation=abbreviation,
                price=cc_data.get("price"),
                date=cc_data.get("date")
            )

    def insert_or_update_asset(
            self,
            name: str,
            abbreviation: str,
            provider_coin_id: dict
    ):
        """
        Insert or update asset data in the database.
        """
        if not self.crypto_currency_is_tracked(
            name=name,
            abbreviation=abbreviation
        ):
            # If the asset is not tracked, insert it into the database
            logger.info(
                f"Tracking new crypto currency: {name} ({abbreviation})"
            )
            track_crypto_currency_in_db(
                db_interface=self.db_interface,
                name=name,
                abbreviation=abbreviation,
                provider_coin_id=provider_coin_id
            )

    def cc_price_is_tracked(
        self,
        name: str,
        abbreviation: str,
        iso_week: int,
        iso_year: int
    ) -> bool:
        """
        Check if the crypto currency price is tracked in the database.
        """
        return cc_price_is_tracked_in_db(
            db_interface=self.db_interface,
            name=name,
            abbreviation=abbreviation,
            iso_week=iso_week,
            iso_year=iso_year
        )

    def crypto_currency_is_tracked(
        self,
        name: str,
        abbreviation: str
    ) -> bool:
        """
        Check if the crypto currency is tracked in the database.
        """
        return crypto_currency_is_tracked_in_db(
            db_interface=self.db_interface,
            name=name,
            abbreviation=abbreviation
        )

    def get_asset_from_db(
        self,
        name: str,
        abbreviation: str = None
    ):
        """
        Get the asset from the database.
        """
        asset_data = get_single_asset_from_db(
            db_interface=self.db_interface,
            name=name,
            abbreviation=abbreviation,
            dictionary_cursor=True
        )
        if not asset_data:
            logger.warning(
                f"No asset found for {name} ({abbreviation}) in the database."
            )
            return None
        return asset_data