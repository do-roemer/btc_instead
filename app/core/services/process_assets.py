from app.core.utils.utils import set_logger
from app.core.database.db_interface import DatabaseInterface
from app.core.database.asset_db_handler import (
    track_crypto_currency_in_db,
    crypto_currency_is_tracked_in_db,
    get_coin_ids_for_providers
)

logger = set_logger(name=__name__)


class AssetProcessor:
    def __init__(
            self,
            db_interface: DatabaseInterface,
    ):
        self.db_interface = db_interface

    def insert_or_update_asset(
            self,
            name: str,
            abbreviation: str,
            provider_coin_id: dict
    ):
        """
        Insert or update asset data in the database.
        """
        track_crypto_currency_in_db(
            db_interface=self.db_interface,
            name=name,
            abbreviation=abbreviation,
            provider_coin_id=provider_coin_id
        )