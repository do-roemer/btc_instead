import json


from app.core.database.db_interface import DatabaseInterface
from app.core.utils.utils import set_logger
from app.core.entities.portfolio import Portfolio
from app.core.app_config import get_config
from app.core.database.queries import INSERT_NEW_PORTFOLIO_TEMPLATE
app_config = get_config()

logger = set_logger(name=__name__)


def portfolio_already_exists(
        db_interface,
        source: str,
        source_id: str
):
    """
    Check if the portfolio already exists in the database.
    """
    sql_query = f"""
        SELECT * FROM {db_interface.tables["portfolios"].name}
        WHERE source = %s AND source_id = %s
    """
    result = db_interface.execute_query(
        sql_query,
        (source, source_id)
    )
    return len(result) > 0

def purchase_to_db(
        db_interface: DatabaseInterface,
        source: str,
        source_id: str,
        name: str,
        abbreviation: str,
        amount: float,
        purchase_price_per_unit: float,
        purchase_date: str,
        total_purchase_value: float
):
    pass

def insert_portfolio_to_db(
        db_interface: DatabaseInterface,
        portfolio: Portfolio,
        is_new: bool = True
):
    """
    Process the portfolio data from the Reddit post and
    update the database.
    """
    # Extract portfolio data from the Reddit post
    logger.info(
        """Uploading portfolio to DB""" +
        f""" for source id: {portfolio.source_id}""")
    # TODO: Add logic to check if the portfolio already exists
    # and if it does just update it
    if is_new:
        try:
            if db_interface.tables["portfolios"].columns:
                json_columns = db_interface.tables["portfolios"].\
                        get_json_columns()
                processed_portfolio = portfolio
                for column in json_columns:
                    if column in processed_portfolio and\
                            processed_portfolio[column] is not None:
                        if not isinstance(processed_portfolio[column], str):
                            processed_portfolio[column] = json.dumps(
                                    processed_portfolio[column])

            portfolio_data_tuple = (
                processed_portfolio.source,
                processed_portfolio.source_id,
                processed_portfolio.total_investment,
                processed_portfolio.start_value,
                processed_portfolio.current_value,
                processed_portfolio.profit_percentage,
                processed_portfolio.profit_total,
                processed_portfolio.btci_current_value,
                processed_portfolio.btci_profit_percentage,
                processed_portfolio.btci_profit_total,
                processed_portfolio.created_date,
                processed_portfolio.updated_date,
            )

            if is_new:
                sql_query = INSERT_NEW_PORTFOLIO_TEMPLATE
            else:
                sql_query = INSERT_NEW_PORTFOLIO_TEMPLATE
                # TODO: Add update logic here
            final_query = sql_query.format(
                table_name=db_interface.tables["portfolios"].name
            )
            _ = db_interface.execute_query(
                final_query, portfolio_data_tuple)

        except Exception as e:
            logger.error(
                f"Error inserting : {e}",
                exc_info=True
            )
            raise
