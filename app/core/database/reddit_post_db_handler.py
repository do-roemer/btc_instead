import logging
import json

from app.core.app_config import get_config
from app.core.entities.reddit_post import RedditPost
from app.core.database.queries import (
    INSERT_REDDIT_POST_UPDATE_TEMPLATE,
    UPDATE_PORTFOLIO_STATUS_OF_POST
)
app_config = get_config()

logging.basicConfig(
    level=logging.INFO,
    format=app_config.get('logging').get('format'),
)


def get_unprocessed_reddit_posts(db_interface, n_posts):
    # Query remains the same
    query = f"""
        SELECT * FROM {db_interface.tables["reddit_posts"].name}
        WHERE processed = 0
        ORDER BY created_utc ASC
        LIMIT {n_posts};
        """
    results = db_interface.execute_query(query)
    if results:
        logging.info(
            f"""Fetched {len(results)} unprocessed reddit posts
            from {db_interface.tables["reddit_posts"].name}
            (PyMySQL).""")
        reddit_posts = []
        for post in results:
            reddit_posts.append(RedditPost.from_db_row(post))
        return reddit_posts
    else:
        logging.warning("No unprocessed posts found.")
        return []


def delete_reddit_posts(db_interface, post_ids: list[str]):
    if not post_ids:
        logging.warning("No post IDs provided for deletion.")
        return 0

    # Use a parameterized query to prevent SQL injection
    delete_query = f"""
        DELETE FROM {db_interface.tables["reddit_posts"].name}
        WHERE post_id IN ({','.join(['%s'] * len(post_ids))})
    """
    db_interface.execute_query(delete_query)


def update_portfolio_status_in_db(
        db_interface,
        post_id: RedditPost,
        is_portfolio: bool,
        failed: bool,
        processed: bool = True
):
    """
    Process the reddit posts and update the database.
    """
    try:
        query = UPDATE_PORTFOLIO_STATUS_OF_POST.format(
            table_name=db_interface.tables["reddit_posts"].name
        )
        values = (
            processed,
            is_portfolio,
            failed,
            post_id
        )
        db_interface.execute_query(query, values)
        logging.info(f"Updated is_portfolio for post_id: {post_id}")
    except Exception as e:
        logging.error(
            f"""Failed to update is_portfolio
            for post_id: {post_id}. Error: {e}""")


def insert_reddit_posts_to_db(
    db_interface,
    reddit_posts: list[dict]
):
    logging.info(
            f"Starting to insert {len(reddit_posts)} reddit posts into DB.")
    processed_posts = []
    if db_interface.tables["reddit_posts"].columns:
        json_columns = db_interface.tables["reddit_posts"].\
                get_json_columns()
        for post in reddit_posts:
            processed_post = post.copy()
            for column in json_columns:
                if column in processed_post and\
                        processed_post[column] is not None:
                    # Ensure data is not already a string before dumping
                    if not isinstance(processed_post[column], str):
                        processed_post[column] = json.dumps(
                                processed_post[column])
            processed_posts.append(processed_post)
    else:
        logging.error(
            "Cannot insert reddit posts: table columns not loaded.")
        return None
    post_data_tuples = [
        (
            p.get('post_id'), p.get('title'), p.get('username'),
            p.get('created_utc'), p.get('created_date'), p.get('score'),
            p.get('upvote_ratio'), p.get('num_comments'),
            p.get('permalink'), p.get('user_url'), p.get('subreddit'),
            p.get('post_text'), p.get('is_self'), p.get('stickied'),
            p.get('spoiler'), p.get('locked'), p.get('is_gallery'),
            p.get('is_direct_image_post'), p.get('flair_text'),
            p.get('inline_images_in_text'), p.get('markdown_image_urls'),
            p.get('gallery_img_urls'), p.get('image_post_url')
        )
        for p in processed_posts
    ]

    if not post_data_tuples:
        logging.warning(
            "No valid post data tuples to insert after processing.")
        return None

    # Query formatting remains the same
    final_query = INSERT_REDDIT_POST_UPDATE_TEMPLATE.format(
        table_name=db_interface.tables["reddit_posts"].name)
    logging.info(
        f"""Inserting {len(post_data_tuples)} reddit posts
        into {db_interface.tables["reddit_posts"].name} (PyMySQL).""")
    for post_data in post_data_tuples:
        _ = db_interface.execute_query(
            final_query, post_data)
    

def get_reddit_posts(
        db_interface,
        post_ids: list[str]
) -> list[RedditPost]:
    if not post_ids:
        logging.warning("No post IDs provided for retrieval.")
        return []

    # Use a parameterized query to prevent SQL injection
    select_query = f"""
        SELECT * FROM {db_interface.tables["reddit_posts"].name}
        WHERE post_id IN ({','.join(['%s'] * len(post_ids))})
    """
    logging.info(
        f"""Fetching reddit posts by post_id from {
            db_interface.tables["reddit_posts"].name}
        (PyMySQL).""")            
    results = db_interface.execute_query(select_query, post_ids)
    reddit_posts = []
    for post in results:
        reddit_posts.append(RedditPost.from_db_row(post))
    return reddit_posts
