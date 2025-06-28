import json

from app.core.database.db_interface import DatabaseInterface
from app.core.utils.utils import set_logger
from app.core.entities.portfolio import Portfolio
from app.core.app_config import get_config
from app.core.database.queries import (
    INSERT_NEW_PORTFOLIO_TEMPLATE,
    UPDATE_PORTFOLIO_TEMPLATE,
    INSERT_NEW_PURCHASE_TEMPLATE,
    GET_PURCHASES_BY_SOURCE_ID_TEMPLATE,
    GET_PORTFOLIO_BY_SOURCE_ID_TEMPLATE
)
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


def upload_purchase_to_db(
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
    """
    Insert a purchase into the database.
    """
    logger.info(
        f"""Uploading purchase to DB for source id: {source_id}"""
    )
    error = False
    try:
        purchase_data_tuple = (
            source,
            source_id,
            name,
            abbreviation,
            amount,
            purchase_price_per_unit,
            purchase_date,
            total_purchase_value
        )

        sql_query = INSERT_NEW_PURCHASE_TEMPLATE.format(
            table_name=db_interface.tables["purchases"].name
        )
        _ = db_interface.execute_query(
            sql_query, purchase_data_tuple)

    except Exception as e:
        logger.error(
            f"Error inserting purchase: {e}",
            exc_info=True
        )
        error = True
    return error


def get_purchases_for_portfolio(
        db_interface: DatabaseInterface,
        source: str,
        source_id: str
):
    """
    Evaluate the portfolio and return the evaluation result.
    This function is a placeholder for future implementation.
    """
    logger.info(
        f"""Evaluating portfolio for source id: {source_id}"""
    )
    sql_query = GET_PURCHASES_BY_SOURCE_ID_TEMPLATE.format(
        table_name=db_interface.tables["purchases"].name
    )

    purchases = db_interface.execute_query(
        sql_query,
        (source, source_id),
        dictionary_cursor=True
    )
    if not purchases:
        logger.warning(
            f"""No purchases found for source id: {source_id}"""
        )
        return None
    return purchases


def get_portfolio_by_source_id(
        db_interface: DatabaseInterface,
        source: str,
        source_id: str
):
    """
    Get the portfolio by source and source_id.
    """
    logger.info(
        f"""Getting portfolio for source id: {source_id}"""
    )
    sql_query = GET_PORTFOLIO_BY_SOURCE_ID_TEMPLATE.format(
        table_name=db_interface.tables["portfolios"].name
    )

    portfolio = db_interface.execute_query(
        sql_query,
        (source, source_id),
        dictionary_cursor=True
    )
    if not portfolio:
        logger.warning(
            f"""No portfolio found for source id: {source_id}"""
        )
        return None
    return portfolio[0]


def update_portfolio_in_db(
        db_interface: DatabaseInterface,
        portfolio: Portfolio
):
    """
    Update the portfolio in the database.
    """
    logger.info(
        f"""Updating portfolio for source id: {portfolio.source_id}"""
    )
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
            processed_portfolio.total_investment,
            processed_portfolio.current_value,
            processed_portfolio.profit_percentage,
            processed_portfolio.profit_total,
            processed_portfolio.btci_current_value,
            processed_portfolio.btci_profit_percentage,
            processed_portfolio.btci_profit_total,
            processed_portfolio.updated_date,
            processed_portfolio.btci_start_amount,
            processed_portfolio.source,
            processed_portfolio.source_id
        )

        sql_query = UPDATE_PORTFOLIO_TEMPLATE.format(
            table_name=db_interface.tables["portfolios"].name,
        )

        db_interface.execute_query(
            sql_query, portfolio_data_tuple
        )
        logger.info(
            f"""Portfolio updated successfully for source
             {portfolio.source} and id: {portfolio.source_id}"""
        )
    except Exception as e:
        logger.error(
            f"Error updating portfolio: {e}",
            exc_info=True
        )
        raise


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
                processed_portfolio.btci_current_value
            )

            if is_new:
                sql_query = INSERT_NEW_PORTFOLIO_TEMPLATE

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
