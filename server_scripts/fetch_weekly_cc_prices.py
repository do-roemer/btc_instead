from app.core.pipelines.pipelines import (
    fetch_and_upload_weeklsy_crypto_prices_to_db_pipeline
)
import app.core.secret_handler as secrets
from app.core.services.process_asset import AssetProcessor
from app.core.database.db_interface import DatabaseInterface
from app.core.utils.utils import set_logger

logger = set_logger(name=__name__)
secret_config = secrets.get_config()

try:
    db_interface = DatabaseInterface(
            host=secret_config.get("MYSQL_HOST"),
            user=secret_config.get("MYSQL_USERNAME"),
            password=secret_config.get("MYSQL_KEY"),
            database=secret_config.get("MYSQL_DBNAME"),
            is_ssh_tunnel=True if secret_config.get("ENVIRONMENT") == "local" else False,
    )
except Exception as e:
    logger.error(
        f"CRITICAL: Failed to initialize DatabaseInterface: {e}",
        exc_info=True)
    raise


asset_processor = AssetProcessor(
        db_interface=db_interface
)


def pipeline():

    logger.info("--- Starting weekly crypto prices fetch execution ---")
    fetch_and_upload_weeklsy_crypto_prices_to_db_pipeline(
        db_interface=db_interface,
        asset_processor=asset_processor
    )
    logger.info("Weekly crypto prices fetched and uploaded successfully.")
    return {
        "statusCode": 200,
        "body": "Weekly crypto prices fetched and uploaded successfully."
    }
