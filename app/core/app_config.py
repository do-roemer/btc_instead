# shared_code/config.py
from dotenv import load_dotenv

load_dotenv()

MYSQL_COLUMN_FORMAT = {
    "date": "%Y-%m-%d",
}


MYSQL_TABLES = {
    "tables": {
        "reddit_posts": "RedditPosts",
        "portfolios": "Portfolios",
        "crypto_currency_prices": "CCPrices",
        "purchases": "Purchases",
        "crypto_assets": "CCAssets",
        }
    }

DEBUG = {
    'is_debug': True,
    'print_debug': False
}

REDDIT_FETCHER_CONFIG = {
    "sleep_time": 0.5,
    "post_limit": 5,
    "subreddits": ["WallStreetBetsCrypto"]
}

LOGGING = {
    "format": "%(asctime)s - %(levelname)s - %(message)s",
}

CONFIG = {
    "mysql": MYSQL_TABLES,
    "mysql_column_format": MYSQL_COLUMN_FORMAT,
    "reddit_fetcher": REDDIT_FETCHER_CONFIG,
    "logging": LOGGING,
    "debug": DEBUG
}


def get_config():
    """Retrieve the application configuration."""
    _config = CONFIG
    return _config