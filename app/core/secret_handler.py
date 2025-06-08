import os
from dotenv import load_dotenv

from app.core.utils.utils import set_logger
from app.core.app_config import get_config

logger = set_logger(__name__)
app_config = get_config()

REQUIRED_SECRETS = [
    "REDDIT_CLIENT_ID",
    "REDDIT_CLIENT_SECRET",
    "REDDIT_USER_AGENT",
    "REDDIT_USERNAME",
    "REDDIT_PASSWORD",
    "ENVIRONMENT",
    "MYSQL_HOST",
    "MYSQL_PORT",
    "MYSQL_DBNAME",
    "MYSQL_USERNAME",
    "MYSQL_KEY",
    'SSH_PRIVATE_KEY_PATH',
    'SSH_TUNNEL_PORT',
    'DROPLET_SSH_HOST',
    'DROPLET_SSH_USER',
    'COINMARKETCAP_API_KEY'
]

_cached_config = None 


def _load_config_from_env():
    """Loads configuration from a .env file for local execution."""
    logger.info("Attempting to load configuration from .env file...")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(current_dir, '.env')

    if not os.path.exists(dotenv_path):
        logger.warning(
            f""".env file not found at {dotenv_path}.
            Relying on environment variables.""")
        load_dotenv(dotenv_path=dotenv_path, override=False) 
    else:
        loaded = load_dotenv(dotenv_path=dotenv_path, override=True)
        if loaded:
            logger.info(
                f".env file loaded successfully from {dotenv_path}")
        else:
            logger.warning(
                f"""Could not load .env file from 
                {dotenv_path}, though it exists.""")

    config = {}
    missing_secrets = []
    for secret_name in REQUIRED_SECRETS:
        value = os.getenv(secret_name)
        if value:
            config[secret_name] = value
        else:
            missing_secrets.append(secret_name)

    if missing_secrets:
        logger.error(
            f"""Missing required secrets from .env/environment:
            {', '.join(missing_secrets)}""")

    logger.info("Local configuration processed.")
    return config


def get_config():
    """
    Loads configuration based on the environment (Lambda or local).
    Caches the result for subsequent calls within the same Lambda invocation.
    """
    global _cached_config
    # Check cache first (important for warm Lambda invocations)
    if _cached_config is not None:
        return _cached_config

    logger.info("Running in local environment.")
    _cached_config = _load_config_from_env()

    final_missing = [s for s in REQUIRED_SECRETS if s not in _cached_config]
    if final_missing:
        logger.error(
            f"""Configuration loading incomplete.
            Missing required secrets: {', '.join(final_missing)}""")
        raise ValueError(
            f"""Configuration loading incomplete.
            Missing required secrets: {', '.join(final_missing)}""")
    return _cached_config