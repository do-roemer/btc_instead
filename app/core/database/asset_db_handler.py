from app.core.utils.utils import set_logger
from app.core.app_config import get_config
from app.core.database.queries import (
    INSERT_CRYPTO_CURRENCY_PRICE_TEMPLATE
)

app_config = get_config()
logger = set_logger(name=__name__)

PRICE_TABLE_NAME_KEY = "crypto_currency_prices"
COIN_ASSET_TABLE_NAME_KEY = "crypto_assets"


def crypto_currency_is_tracked_in_db(
        db_interface,
        name: str,
        abbreviation: str
):
    """
    Check if the crypto currency already exists in the database.
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
    Track the crypto currency in formation in the database (table:CCAssets).
    """
    if provider_coin_id.get("coin_market_cap") is None and provider_coin_id.get("coin_gecko") is None:
        logger.error(
            f"""Cannot track {name} ({abbreviation}) in DB.
            No coin ids provided."""
        )
        return False
    
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


def get_tracked_crypto_currency_in_db(
        db_interface,
        num_assets_limit: int = None
) -> list[dict]:
    """
    Get all tracked crypto currencies from the database.
    If num_assets_limit is provided, limit the number of assets returned.
    Input:
        db_interface: Database interface to execute queries.
        num_assets_limit: Optional limit on the number of assets to return.
    Output:
        A list of dictionaries containing the tracked crypto currencies.
        Each dictionary contains:
            - name: Name of the crypto currency
            - abbreviation: Abbreviation of the crypto currency
            - coin_market_cap: CoinMarketCap ID
            - coin_gecko: CoinGecko ID
    """
    sql_query = f"""
        SELECT * FROM {
            db_interface.tables[COIN_ASSET_TABLE_NAME_KEY].name
            }
    """
    if num_assets_limit:
        sql_query += f" LIMIT {num_assets_limit}"
    sql_query += ";"

    result = db_interface.execute_query(sql_query)
    return [
        {
            "name": row[1],
            "abbreviation": row[2],
            "coin_market_cap": row[3],
            "coin_gecko": row[4]
        } for row in result
    ]


def get_coin_ids_for_providers(
        db_interface,
        name: str,
        abbreviation: str
) -> dict:
    """
    Get the coin ids for the providers to store it in the DB (table:CCAssets).
    The ID is used to get the price from the API.
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
        name: str,
        abbreviation: str,
        price: float,
        date: str,
        iso_week: int,
        iso_year: int,
        currency: str = "usd"
):
    """
    Process the portfolio data from the Reddit post and
    update the database.
    """
    # Extract portfolio data from the Reddit post
    logger.info(
        f"""Uploading {abbreviation} price to DB"""
    )
    processed_finished = False
    try:
        portfolio_data_tuple = (
            name.lower(),
            abbreviation.lower(),
            price,
            currency.lower(),
            date,
            iso_week,
            iso_year
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
        logger.debug(
            f"""Inserted {abbreviation} price to DB: {price} on {date}"""
        )
    except Exception as e:
        logger.error(
            f"""Error inserting {abbreviation} price to DB: {e}"""
        )
    return processed_finished


def get_asset_price_from_db_by_iso_week_year(
        db_interface,
        name: str,
        abbreviation: str,
        iso_week: str,
        iso_year: int
):
    """
    Get the price of an asset from the database.
    """
    sql_query = f"""
        SELECT * FROM {
            db_interface.tables[PRICE_TABLE_NAME_KEY].name
            }
        WHERE name = %s AND abbreviation = %s AND iso_week = %s
        AND iso_year = %s
    """
    result = db_interface.execute_query(
        sql_query,
        (name.lower(), abbreviation.lower(), iso_week, iso_year)
    )
    if not result:
        return None
    return result[0]  # Return the first matching record