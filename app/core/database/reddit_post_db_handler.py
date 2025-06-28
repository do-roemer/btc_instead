import json

from app.core.utils.utils import set_logger
from app.core.app_config import get_config
from app.core.entities.reddit_post import RedditPost
from app.core.database.queries import (
    INSERT_REDDIT_POST_UPDATE_TEMPLATE,
    UPDATE_PORTFOLIO_STATUS_OF_POST_TEMPLATE
)
app_config = get_config()
logger = set_logger(name=__name__)


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
        logger.info(
            f"""Fetched {len(results)} unprocessed reddit posts
            from {db_interface.tables["reddit_posts"].name}
            (PyMySQL).""")
        reddit_posts = []
        for post in results:
            reddit_posts.append(RedditPost.from_db_row(post))
        return reddit_posts
    else:
        logger.warning("No unprocessed posts found.")
        return []


def delete_reddit_posts(db_interface, post_ids: list[str]):
    if not post_ids:
        logger.warning("No post IDs provided for deletion.")
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
    Update the portfolio status of a Reddit post in the database.
    """
    try:
        query = UPDATE_PORTFOLIO_STATUS_OF_POST_TEMPLATE.format(
            table_name=db_interface.tables["reddit_posts"].name
        )
        values = (
            processed,
            is_portfolio,
            failed,
            post_id
        )
        db_interface.execute_query(query, values)
        logger.info(f"Updated is_portfolio for post_id: {post_id}")
    except Exception as e:
        logger.error(
            f"""Failed to update is_portfolio
            for post_id: {post_id}. Error: {e}""")


def insert_reddit_posts_to_db(
    db_interface,
    reddit_post: dict
):
    logger.debug("Starting to insert reddit post into DB.")
    processed_post = reddit_post.copy()
    if db_interface.tables["reddit_posts"].columns:
        json_columns = db_interface.tables["reddit_posts"].\
                get_json_columns()
        for column in json_columns:
            if column in processed_post and\
                    processed_post[column] is not None:
                # Ensure data is not already a string before dumping
                if not isinstance(processed_post[column], str):
                    processed_post[column] = json.dumps(
                            processed_post[column])
    else:
        logger.error("Cannot insert reddit post: Table columns not loaded.")
        return None
    post_data_tuple = (
            processed_post.get('post_id'), processed_post.get('title'), processed_post.get('username'),
            processed_post.get('created_utc'), processed_post.get('created_date'), processed_post.get('score'),
            processed_post.get('upvote_ratio'), processed_post.get('num_comments'),
            processed_post.get('permalink'), processed_post.get('user_url'), processed_post.get('subreddit'),
            processed_post.get('post_text'), processed_post.get('is_self'), processed_post.get('stickied'),
            processed_post.get('spoiler'), processed_post.get('locked'), processed_post.get('is_gallery'),
            processed_post.get('is_direct_image_post'), processed_post.get('flair_text'),
            processed_post.get('inline_images_in_text'), processed_post.get('markdown_image_urls'),
            processed_post.get('gallery_img_urls'), processed_post.get('image_post_url')
        )

    if not post_data_tuple:
        logger.warning(
            "No valid post data tuples to insert after processing.")
        return None

    # Query formatting remains the same
    final_query = INSERT_REDDIT_POST_UPDATE_TEMPLATE.format(
        table_name=db_interface.tables["reddit_posts"].name)
    
        
    _ = db_interface.execute_query(final_query, post_data_tuple)
    logger.info(
        f"""Inserted reddit post {processed_post.get('post_id')}
        into {db_interface.tables["reddit_posts"].name} (PyMySQL).""")


def get_reddit_post_by_id_from_db(
        db_interface,
        post_id: str
) -> RedditPost | None:
    if not post_id:
        logger.warning("No post ID provided for retrieval.")
        return None

    # Use a parameterized query to prevent SQL injection
    select_query = f"""
        SELECT * FROM {db_interface.tables["reddit_posts"].name}
        WHERE post_id = %s
    """
    logger.info(
        f"""Fetching reddit post by post_id from {
            db_interface.tables["reddit_posts"].name}
        (PyMySQL).""")
    result = db_interface.execute_query(select_query, (post_id,))
    
    if result:
        return RedditPost.from_db_row(result[0])
    else:
        logger.warning(f"No post found with post_id: {post_id}")
        return None

 
def get_reddit_posts(
        db_interface,
        post_ids: list[str]
) -> list[RedditPost]:
    if not post_ids:
        logger.warning("No post IDs provided for retrieval.")
        return []

    # Use a parameterized query to prevent SQL injection
    select_query = f"""
        SELECT * FROM {db_interface.tables["reddit_posts"].name}
        WHERE post_id IN ({','.join(['%s'] * len(post_ids))})
    """
    logger.info(
        f"""Fetching reddit posts by post_id from {
            db_interface.tables["reddit_posts"].name}
        (PyMySQL).""")            
    results = db_interface.execute_query(select_query, post_ids)
    reddit_posts = []
    for post in results:
        reddit_posts.append(RedditPost.from_db_row(post))
    return reddit_posts
