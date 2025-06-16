from datetime import datetime

from app.core.utils.utils import set_logger
from app.core.fetcher.fiat_exchange import (
    get_historical_exchange_rate_for_usd
)
import app.core.secret_handler as secrets
from app.core.app_config import get_config
from app.core.entities.portfolio import (
    Portfolio,
    Purchase
)
from app.core.database.db_interface import DatabaseInterface
from app.core.database.portfolio_db_handler import (
    insert_portfolio_to_db,
    upload_purchase_to_db,
    get_purchases_for_portfolio,
    get_portfolio_by_source_id
)
secret_config = secrets.get_config()
app_config = get_config()
logger = set_logger(name=__name__)


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

    def evaluate_portfolio(
            self,
            source: str,
            source_id: str
    ):
        portfolio = self.get_portfolio_by_source_id_from_db(
            source=source,
            source_id=source_id
        )
        purchases = self.get_purchases_for_portfolio_from_db(
            source=source,
            source_id=source_id
        )
        if not purchases:
            logger.warning(
                f"No purchases found for portfolio {source} - {source_id}."
            )
            return None
        
        


        print(f"Total investment: {total_investment}")

    def calculate_portfolio_values(
            self,
            portfolio: Portfolio,
            purchases: list[Purchase]
    ) -> Portfolio:
        """
        Calculate the current value and profit of the portfolio.
        """
        total_investment = sum(purchase.total_purchase_value for purchase in purchases)
        current_value = sum(purchase.amount for purchase in purchases)
        profit_total = current_value - total_investment
        profit_percentage = (profit_total / total_investment) * 100
        start_value = sum(purchase.amount for purchase in purchases)
        update_date = datetime.now().strftime("%Y-%m-%d")

        portfolio.update_values(
            {
                "start_value": start_value,
                "current_value": current_value,
                "profit_percentage": profit_percentage,
                "profit_total": profit_total,
                "total_investment": portfolio.total_investment,
                "updated_date": update_date
            }
        )
        return portfolio

    def get_purchases_for_portfolio_from_db(
            self,
            source: str,
            source_id: str
    ) -> list[Purchase]:
        """
        Get all purchases for a portfolio by source and source_id.
        """
        purchases_data = get_purchases_for_portfolio(
            db_interface=self.db_interface,
            source=source,
            source_id=source_id
        )
        if not purchases_data:
            logger.warning(
                f"No purchases found for portfolio {source} - {source_id}."
            )
            return []
        purchases = [
            Purchase(
                source=purchase['source'],
                source_id=purchase['source_id'],
                name=purchase['name'],
                abbreviation=purchase['abbreviation'],
                amount=purchase['amount'],
                total_purchase_value=purchase['total_purchase_value'],
                purchase_date=purchase['purchase_date']
            ) for purchase in purchases_data
        ]
        return purchases

    def get_portfolio_by_source_id_from_db(
            self,
            source: str,
            source_id: str
    ) -> Portfolio:
        """
        Get a portfolio by source and source_id.
        """
        portfolio_data = get_portfolio_by_source_id(
            db_interface=self.db_interface,
            source=source,
            source_id=source_id
        )
        if not portfolio_data:
            logger.warning(
                f"No portfolio found for source id: {source_id}"
            )
            return None
        portfolio = Portfolio(
            source=portfolio_data['source'],
            source_id=portfolio_data['source_id'],
            total_investment=portfolio_data['total_investment'],
            start_value=portfolio_data['start_value'],
            current_value=portfolio_data['current_value'],
            profit_percentage=portfolio_data['profit_percentage'],
            profit_total=portfolio_data['profit_total'],
            btci_current_value=portfolio_data['btci_current_value'],
            btci_profit_percentage=portfolio_data['btci_profit_percentage'],
            btci_profit_total=portfolio_data['btci_profit_total'],
            created_date=portfolio_data['created_date'],
            updated_date=portfolio_data['updated_date']
        )
        return portfolio

    def purchase_to_db(
            self,
            purchase: Purchase
    ):
        """
        Upload a purchase to the database.
        """
        _ = upload_purchase_to_db(
            db_interface=self.db_interface,
            source=purchase.source,
            source_id=purchase.source_id,
            name=purchase.name,
            abbreviation=purchase.abbreviation,
            amount=purchase.amount,
            purchase_price_per_unit=purchase.purchase_price_per_unit,
            purchase_date=purchase.purchase_date,
            total_purchase_value=purchase.total_purchase_value
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
        total_purchase_value: float
    ):
        """
        Create an purchase object.
        """
        purchase_date = purchase_date.split("T")[0]
        if currency not in ["USD", "usd"]:
            # Get the exchange rate for the purchase date
            exchange_rate = get_historical_exchange_rate_for_usd(
                date_str=purchase_date,
                base_currency=currency
            )
            if exchange_rate is None:
                logger.error(
                    f"Error: Could not fetch exchange rate "
                    f"""for {currency} on {purchase_date}."""
                    f" Using 1.0 as a fallback."
                )
                exchange_rate = 1.0
            amount = amount * exchange_rate
            total_purchase_value = total_purchase_value / exchange_rate

        return Purchase(
            source=source,
            source_id=source_id,
            name=name,
            abbreviation=abbreviation,
            amount=amount,
            total_purchase_value=total_purchase_value,
            purchase_date=purchase_date
        )
