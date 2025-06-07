import logging
from dotenv import load_dotenv

from fetcher.fiat_exchange import (
    get_historical_exchange_rate_for_usd
)
import app.core.secret_handler as secrets
from app.core.app_config import get_config
from entities.portfolio import (
    Portfolio,
    Purchase
)
from database.db_interface import DatabaseInterface
from database.portfolio_db_handler import (
    insert_portfolio_to_db
)
secret_config = secrets.get_config()

load_dotenv()
app_config = get_config()

logging.basicConfig(
    level=logging.INFO,
    format=app_config.get('logging').get('format'),
)


class PortfolioProcessor:
    def __init__(
            self,
            db_interface: DatabaseInterface,
    ):
        self.db_interface = db_interface

    def get_empty_portfolio(
        self,
        source: str,
        source_id: str,
        created_date: str = None,
    ):
        """
        Create an empty portfolio object.
        """
        return Portfolio(
            source=source,
            source_id=source_id,
            created_date=created_date,
        )

    def initialize_portfolio_in_db(
        self,
        source: str,
        source_id: str,
        created_date: str,
    ):
        """
        Insert an empty portfolio into the database.
        """
        empty_portfolio = self.get_empty_portfolio(
            source=source,
            source_id=source_id,
            created_date=created_date,
        )
        insert_portfolio_to_db(
            db_interface=self.db_interface,
            portfolio=empty_portfolio,
            is_new=True
        )

    def create_purchase(
        self,
        source: str,
        source_id: str,
        name: str,
        abbreviation: str,
        amount: float,
        currency: str,
        purchase_date: str,
        purchase_price_per_unit: float = None,
    ):
        """
        Create an purchase object.
        """
        purchase_date = purchase_date.split("T")[0]
        if currency != "USD":
            # Get the exchange rate for the purchase date
            exchange_rate = get_historical_exchange_rate_for_usd(
                date_str=purchase_date,
                base_currency=currency
            )
            if exchange_rate is None:
                logging.error(
                    f"Error: Could not fetch exchange rate "
                    f"""for {currency} on {purchase_date}."""
                    f" Using 1.0 as a fallback."
                )
                exchange_rate = 1.0
            amount = amount * exchange_rate
            purchase_price_per_unit = purchase_price_per_unit / exchange_rate

        return Purchase(
            source=source,
            source_id=source_id,
            name=name,
            abbreviation=abbreviation,
            amount=amount,
            purchase_price_per_unit=purchase_price_per_unit,
            purchase_date=purchase_date
        )