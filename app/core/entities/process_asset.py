import logging
import datetime as dt
from app_config import get_config
from database.db_interface import DatabaseInterface
from database.asset_db_handler import (
    insert_crypto_currency_price_to_db,
    crypto_currency_is_tracked_in_db,
    track_crypto_currency_in_db,
    get_coin_ids_for_providers
)
from fetcher.crypto_currency import CryptoCurrencyFetcher

app_config = get_config()

logging.basicConfig(
    level=logging.INFO,
    format=app_config.get('logging').get('format'),
)


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
    ):
        # Placeholder for processing logic
        uploaded_status = insert_crypto_currency_price_to_db(
                self.db_interface,
                abbreviation=abbreviation,
                price=price,
                date=date,
                iso_week=iso_week,
                iso_year=iso_year
        )
        return uploaded_status

    def get_provider_coin_ids(
        self,
        name: str,
        abbreviation: str
    ) -> dict:
        if not crypto_currency_is_tracked_in_db(
                self.db_interface,
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
                logging.error(
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
            logging.error(
                f"Failed to find coin IDs for {name} ({abbreviation})"
            )
            return asset_processed

        # get the prices from API
        coin_data = self.cc_fetcher.fetch_current_week_data(
            coin_ids=provider_coin_ids,
        )

        if coin_data.get("is_error"):
            logging.error(
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
                iso_year=iso_year
            )

            if uploaded_status:
                logging.info(
                    f"Uploaded {name} ({abbreviation}) price to DB: "
                    f"{coin_data.get('price')}"
                )
                asset_processed = True
            else:
                logging.error(
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
