from database.db_interface import DatabaseInterface
import src.secret_handler as secrets
from fetcher.crypto_currency import CryptoCurrencyFetcher
from fetcher.reddit import RedditFetcher
from services.process_reddit_posts import RedditPostProcessor
secret_config = secrets.get_config()

pipeline()

def execute_reddit_post_process():
    db_interface = DatabaseInterface(
        host=secret_config.get("AWS_RDS_HOST"),
        user=secret_config.get("AWS_RDS_USERNAME"),
        password=secret_config.get("AWS_RDS_KEY"),
        database=secret_config.get("AWS_RDS_DBNAME"),
        ssh_host=secret_config.get("SSH_HOST_RDS_BASTION"),
        ssh_port=secret_config.get("SSH_PORT_RDS_BASTION"),
        ssh_user=secret_config.get("SSH_USER_RDS_BASTION"),
        ssh_private_key_path=secret_config.get("SSH_KEY_PATH_RDS_BASTION")
    )
    rp_processor = RedditPostProcessor(
            db_interface=db_interface
    )
    rp_processor.process(
        reddit_post_ids=[
            "1jwh2cw"
        ]
    )

def execute_cc_fetcher():
    cc_fetcher = CryptoCurrencyFetcher()
    cc_fetcher.fetch_weekly_data(
        cc_abbreviation="BTC",
    )


def test_cc_fetcher():
    cc_fetcher = CryptoCurrencyFetcher()
    coin_ids = {}
    price = cc_fetcher.get_current_week_price_from_cmc(
        coin_id="bitcoin",
        date="2025-04-11"
    )
    a = 1

def test_asset_processor():
    asset_processor = AssetProcessor(
        db_interface=DatabaseInterface(
            host=secret_config.get("AWS_RDS_HOST"),
            user=secret_config.get("AWS_RDS_USERNAME"),
            password=secret_config.get("AWS_RDS_KEY"),
            database=secret_config.get("AWS_RDS_DBNAME"),
            ssh_host=secret_config.get("SSH_HOST_RDS_BASTION"),
            ssh_port=secret_config.get("SSH_PORT_RDS_BASTION"),
            ssh_user=secret_config.get("SSH_USER_RDS_BASTION"),
            ssh_private_key_path=secret_config.get("SSH_KEY_PATH_RDS_BASTION")
        )
    )
    asset_processor.process_asset(
        name="bitcoin",
        abbreviation="BTC"
    )

test_asset_processor()

# execute_cc_fetcher()

# process_pipeline(["1jwh2cw"], debug=False)
