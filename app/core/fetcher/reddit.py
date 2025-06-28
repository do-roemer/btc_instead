import praw
import datetime as dt
import logging
import re
import os
from typing import List
import pandas as pd
from app.core.app_config import get_config

app_config = get_config()

logging.basicConfig(
    level=logging.INFO,
    format=app_config.get('logging').get('format'),
)


class RedditFetcher():
    def __init__(
            self,
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT"),
            username=os.getenv("REDDIT_USERNAME"),
            password=os.getenv("REDDIT_PASSWORD")):
        """
        Initialize the RedditRetriever with client credentials.
        Args:
            client_id (str): The client ID for Reddit API.
            client_secret (str): The client secret for Reddit API.
            user_agent (str): The user agent for Reddit API.
        """
        try:
            logging.info(f"""Attempting to connect to praw API with
                username: {username}""")

            self.client = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
                username=username,
                password=password
            )
        except Exception as e:
            logging.error(
                f"""Failed to connect to praw API: {e}""")
            raise

    def get_reddit_post_id_from_url(self, url: str) -> str:
        """
        Extract the Reddit post ID from a given URL.

        Args:
            url (str): The URL of the Reddit post.

        Returns:
            str: The Reddit post ID.
        """
        try:
            submission = self.client.submission(url=url)
            return submission.id
        except Exception as e:
            logging.error(f"Failed to extract post ID from URL {url}: {e}")
            return None

    def fetching_posts(self, subreddit, limit=10):
        """
        Retrieve posts from a given subreddit.

        Args:
            subreddit (str): The name of the subreddit to retrieve posts from.
            limit (int): The maximum number of posts to retrieve.

        Returns:
            list: A list of posts from the subreddit.
        """
        subreddit_instance = self.reddit_client.subreddit(subreddit)
        posts = subreddit_instance.new(limit=limit)
        return [post.title for post in posts]

    def fetch_posts_by_post_url(
            self,
            url: str) -> dict:
        try:
            submission = self.client.submission(url=url)
            fetched_post_data = self.get_post_data(submission)
            logging.info(f"Fetched post: {fetched_post_data['title']}")
        except Exception as e:
            logging.error(f"An unexpected error occurred for {url}: {e}")
        return fetched_post_data

    def get_new_posts(
            self,
            subreddit_name: str,
            limit=None) -> list:

        logging.info(
            f"Fetching new posts from subreddit: {subreddit_name}")
        try:
            submissions = self.client.subreddit(
                    subreddit_name).new(limit=limit)
            post_data = []
            for submission in submissions:
                # Date of each posts' creation
                post_data.append(self.get_post_data(
                        submission))
                logging.info(f"Fetched post: {submission.title}")
            logging.info(
                f"""Fetched {submissions.yielded}
                posts from subreddit: {subreddit_name}""")
        except praw.exceptions.PRAWException as e:
            logging.error(
                f"""PRAW API error while fetching posts: {e}""")
            post_data = []
        except Exception as e:
            logging.error(
                f"""An unexpected error occurred: {e}""")
            post_data = []
        return post_data

    def get_post_data(self, submission):

        markdown_image_regex = re.compile(r'!\[.*?\]\((.*?)\)')

        # --- Image Extraction Logic ---
        markdown_image_urls = []
        gallery_image_urls = []
        preview_image_url = None
        inline_image_urls = []
        is_direct_image_post = False  # Flag for direct image posts
        is_gallery = False  # Flag for gallery posts

        # 1. Check for Markdown images in selftext
        # (only relevant for self posts)
        if submission.is_self and submission.selftext:
            markdown_image_urls = markdown_image_regex.findall(
                submission.selftext)

        # 2. Check for inline images (uploaded via Reddit's editor)
        if hasattr(submission, 'media_metadata')\
                and submission.media_metadata:
            inline_image_urls = self.get_inline_images(submission)

        # 3. Check if it's a gallery post. If yes also get the urls
        if hasattr(submission, 'is_gallery') and submission.is_gallery:
            is_gallery = True
            if hasattr(submission, "media_metadata"):
                for item_id, item_data in submission.media_metadata.items():
                    if item_data.get('e') == 'Image':
                        source_image = item_data.get('s')
                        if source_image and source_image.get('u'):
                            # URL might have escaped '&', replace with '&'
                            url = source_image['u'].replace('&', '&')
                            gallery_image_urls.append(url)

        # 4 Check if post has direct image link
        if not submission.is_self and submission.url:
            is_direct_image_post = True
            url = submission.url
            # Simple check for common image extensions or Reddit's image host
            if url.endswith(('.jpg', '.jpeg', '.png', '.gif')) \
                    or 'i.redd.it' in url:
                preview_image_url = [url]
            elif hasattr(submission, "preview")\
                and submission.preview \
                    and 'images' \
                        in submission.preview:
                # Get the source image URL from the preview data
                preview_url = submission.preview['images'][0]['source']['url']\
                        .replace('&', '&')
                print(f"  Found preview image URL: {preview_url}")
                preview_image_url = [preview_url]
            else:
                pass

        created_date_ect = dt.datetime.utcfromtimestamp(
            submission.created_utc).strftime("%Y-%m-%d")
        post_data = {
            "post_id": submission.id,
            "title": submission.title,
            "username": str(submission.author),
            "created_utc": submission.created_utc,
            "created_date": created_date_ect,
            "score": submission.score,
            "upvote_ratio": submission.upvote_ratio,
            "num_comments": submission.num_comments,
            "permalink": f"""https://www.reddit.com{
                    submission.permalink}""",
            "user_url": f"https://www.reddit.com/user/{submission.author}"
                        if submission.author else None,
            "subreddit": submission.subreddit.display_name,
            "post_text": submission.selftext,
            "is_self": submission.is_self,
            "stickied": submission.stickied,
            "spoiler": submission.spoiler,
            "locked": submission.locked,
            "is_gallery": is_gallery,
            "gallery_img_urls": gallery_image_urls,  # new
            "is_direct_image_post": is_direct_image_post,
            "image_post_url": preview_image_url,  # new
            "flair_text": submission.link_flair_text,
            "inline_images_in_text": inline_image_urls,
            "markdown_image_urls": markdown_image_urls
        }
        return post_data

    @staticmethod
    def get_timestamp_in_utc(start_date: str, end_date: str):
        # Parse the start_date and end_date strings into datetime objects
        start_day, start_month, start_year = map(int, start_date.split('.'))
        end_day, end_month, end_year = map(int, end_date.split('.'))

        # Create datetime objects with the parsed values
        start_date_utc = dt.datetime(
            start_year, start_month, start_day, 0, 0, 0,
            tzinfo=dt.timezone.utc)
        end_date_utc = dt.datetime(
            end_year, end_month, end_day, 23, 59, 59,
            tzinfo=dt.timezone.utc)
        # Convert dates to Unix timestamps (integers)
        #  required by Reddit's search
        start_timestamp = int(start_date_utc.timestamp())
        end_timestamp = int(end_date_utc.timestamp())
        return start_timestamp, end_timestamp

    @staticmethod
    def get_inline_images(submission) -> list:
        # Extract inline images from the submission
        inline_images = []
        if hasattr(submission, 'media_metadata'):
            for media_id, metadata in submission.media_metadata.items():
                if metadata.get('e') == 'Image' or\
                        metadata.get('e') == 'AnimatedImage':
                    image_info = metadata.get('s')
                    if image_info:
                        url = image_info.get('u')
                        if not url and image_info.get('gif'):
                            url = image_info.get('gif')
                        if url:
                            inline_images.append(url.replace('&', '&'))
        return inline_images


if __name__ == "__main__":
    fetcher = RedditFetcher(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT")
        )

    posts = fetcher.get_new_posts(
        subreddit_name="test",
        limit=10
    )
    posts_df = pd.DataFrame(posts)
    print(posts_df)