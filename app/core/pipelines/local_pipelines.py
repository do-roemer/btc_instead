import app.core.secret_handler as secrets
from app.core.services.process_reddit_posts import RedditPostProcessor
from app.core.fetcher.reddit import RedditFetcher
secret_config = secrets.get_config()


def redditposts_processor_pipeline(
    reddit_ids: list[str],
    rp_processor: RedditPostProcessor
):
    rp_processor.process(
        reddit_post_ids=reddit_ids
    )


def fetch_reddit_posts_from_url_pipeline(
    urls: list[str],
    reddit_fetcher: RedditFetcher
):
    """
    Fetch Reddit posts by IDs and process them.
    """
    results = reddit_fetcher.fetch_posts_by_post_url(
        urls=urls
    )
    print(f"Fetched {len(results)} posts from URLs: {urls}")
    print("Results:", results[0])