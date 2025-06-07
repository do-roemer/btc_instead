from app.core.database.db_interface import DatabaseInterface
import app.core.secret_handler as secrets
from app.core.services.process_reddit_posts import RedditPostProcessor
from app.core.fetcher.reddit import RedditFetcher
from app.core.pipelines.local_pipelines import (
    redditposts_processor_pipeline,
    fetch_reddit_posts_from_url_pipeline
)
secret_config = secrets.get_config()

db_interface = DatabaseInterface(
        host=secret_config.get("MYSQL_HOST"),
        user=secret_config.get("MYSQL_USERNAME"),
        password=secret_config.get("MYSQL_KEY"),
        database=secret_config.get("MYSQL_DBNAME"),
        is_ssh_tunnel=True if secret_config.get("ENVIRONMENT") == "local" else False,
    )
rp_processor = RedditPostProcessor(
        db_interface=db_interface
)

reddit_fetcher = RedditFetcher(
                client_id=secret_config.get("REDDIT_CLIENT_ID"),
                client_secret=secret_config.get("REDDIT_CLIENT_SECRET"),
                user_agent=secret_config.get("REDDIT_USER_AGENT"),
                username=secret_config.get("REDDIT_USERNAME"),
                password=secret_config.get("REDDIT_PASSWORD")
            )

redditposts_processor_pipeline(
    rp_processor=rp_processor,
    reddit_ids=[
        "1l1smbv",
        "1i9txgu"      
    ]
)
