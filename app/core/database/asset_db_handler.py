import logging

from entities.portfolio import Portfolio
from src.app_config import get_config
from database.queries import (
    INSERT_CRYPTO_CURRENCY_PRICE_TEMPLATE
)
app_config = get_config()

logging.basicConfig(
    level=logging.INFO,
    format=app_config.get('logging').get('format'),
)

PRICE_TABLE_NAME_KEY = "crypto_currency_prices"
COIN_ASSET_TABLE_NAME_KEY = "crypto_assets"


def crypto_currency_is_tracked_in_db(
        db_interface,
        name: str,
        abbreviation: str
):
    """
    Check if the crypto currency price already exists in the database.
    """
    sql_query = f"""
        SELECT * FROM {
            db_interface.tables[COIN_ASSET_TABLE_NAME_KEY].name
            }
        WHERE abbreviation = %s AND name = %s
    """
    result = db_interface.execute_query(
        sql_query,
        (abbreviation, name)
    )
    return len(result) > 0


def track_crypto_currency_in_db(
        db_interface,
        name: str,
        abbreviation: str,
        provider_coin_id: dict
):
    """
    Track the crypto currency in the database.
    """
    sql_query = f"""
        INSERT INTO {
            db_interface.tables[COIN_ASSET_TABLE_NAME_KEY].name
            } (
                name,
                abbreviation,
                cmc_id,
                coin_gecko_id
            )
        VALUES (%s, %s, %s, %s)
    """
    result = db_interface.execute_query(
        sql_query,
        (
            name,
            abbreviation,
            provider_coin_id.get("coin_market_cap"),
            provider_coin_id.get("coin_gecko"))
    )
    return result


def get_coin_ids_for_providers(
        db_interface,
        name: str,
        abbreviation: str
) -> dict:
    """
    Get the coin ids for the providers.
    """
    sql_query = f"""
        SELECT coin_gecko_id, cmc_id FROM `{
            db_interface.tables[COIN_ASSET_TABLE_NAME_KEY].name
            }`
        WHERE abbreviation = %s AND name = %s
    """
    result = db_interface.execute_query(
        sql_query,
        (abbreviation, name)
    )
    result = result[0]
    coin_gecko_id = result[0]
    cmc_id = result[1]
    return {
        "coin_market_cap": cmc_id,
        "coin_gecko": coin_gecko_id
    } 


def insert_crypto_currency_price_to_db(
        db_interface,
        abbreviation: str,
        price: float,
        date: str,
):
    """
    Process the portfolio data from the Reddit post and
    update the database.
    """
    # Extract portfolio data from the Reddit post
    logging.info(
        f"""Uploading {abbreviation} price to DB"""
    )
    processed_finished = False
    try:
        portfolio_data_tuple = (
            abbreviation.lower(),
            price,
            date
        )

        final_query = INSERT_CRYPTO_CURRENCY_PRICE_TEMPLATE.format(
            table_name=db_interface.tables[PRICE_TABLE_NAME_KEY].name,
            columns=", ".join(
                db_interface.tables[PRICE_TABLE_NAME_KEY].columns
            ),
        )
        _ = db_interface.execute_query(
                    final_query, portfolio_data_tuple)
        processed_finished = True
    except Exception as e:
        logging.error(
            f"""Error inserting {abbreviation} price to DB: {e}"""
        )
    return processed_finished
