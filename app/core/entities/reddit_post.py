import datetime
import json


class RedditPost():
    def __init__(
            self,
            post_id: str,
            title: str,
            username: str,
            created_utc: int,
            created_date: str,
            score: int,
            upvote_ratio: float,
            num_comments: int,
            permalink: str,
            user_url: str,
            subreddit: str,
            post_text: str,
            is_self: bool,
            stickied: bool,
            spoiler: bool,
            locked: bool,
            is_gallery: bool,
            is_direct_image_post: bool,
            flair_text: str,
            inline_images_in_text: list,
            markdown_image_urls: list,
            gallery_image_urls: list,
            image_post_url: list,
            processed: bool = False,
            is_portfolio: bool = False,
            failed: bool = False):
        self.post_id = post_id
        self.title = title
        self.username = username
        self.created_utc = created_utc
        self.created_date = created_date
        self.score = score
        self.upvote_ratio = upvote_ratio
        self.num_comments = num_comments
        self.permalink = permalink
        self.user_url = user_url
        self.subreddit = subreddit
        self.post_text = post_text
        self.is_self = is_self
        self.stickied = stickied
        self.spoiler = spoiler
        self.locked = locked
        self.is_gallery = is_gallery
        self.gallery_image_urls = gallery_image_urls
        self.is_direct_image_post = is_direct_image_post
        self.image_post_url = image_post_url
        self.flair_text = flair_text
        self.inline_images_in_text = inline_images_in_text if\
            isinstance(inline_images_in_text, list) else []
        self.markdown_image_urls = markdown_image_urls if\
            isinstance(markdown_image_urls, list) else []
        self.processed = processed
        self.is_portfolio = is_portfolio
        self.failed = failed

    @classmethod
    def from_db_row(cls, row: tuple):
        """Creates a RedditPost instance from a database row tuple."""
        if not isinstance(row, tuple) or len(row) < 22:
            raise ValueError("Invalid database row format or length")
        created_date_str = row[4].isoformat() if isinstance(
            row[4], datetime.datetime) else str(row[4])

        # Convert integer representations (0/1) to boolean
        is_self_bool = bool(row[12])
        stickied_bool = bool(row[13])
        spoiler_bool = bool(row[14])
        locked_bool = bool(row[15])
        is_gallery_bool = bool(row[16])
        is_direct_image_post_bool = bool(row[17])
        processed_bool = bool(row[23])

        # Convert JSON strings to lists (handle potential errors/None)
        try:
            inline_images = json.loads(row[19]) if row[19] else []
        except (json.JSONDecodeError, TypeError):
            inline_images = [] 
        try:
            markdown_urls = json.loads(row[20]) if row[20] else []
        except (json.JSONDecodeError, TypeError):
            markdown_urls = []
        flair_text_str = row[18] if row[18] is not None else ''

        return cls(
            post_id=row[0],
            title=row[1],
            username=row[2],
            created_utc=row[3],
            created_date=created_date_str,
            score=row[5],
            upvote_ratio=row[6],
            num_comments=row[7],
            permalink=row[8],
            user_url=row[9],
            subreddit=row[10],
            post_text=row[11],
            is_self=is_self_bool,
            stickied=stickied_bool,
            spoiler=spoiler_bool,
            locked=locked_bool,
            is_gallery=is_gallery_bool,
            is_direct_image_post=is_direct_image_post_bool,
            flair_text=flair_text_str,
            inline_images_in_text=inline_images,
            markdown_image_urls=markdown_urls,
            processed=processed_bool,
            gallery_image_urls=row[21] if row[21] else [],
            image_post_url=row[22] if row[22] else [],
            is_portfolio=row[24] if row[24] else False,
            failed=row[25] if row[25] else False
        )

    def to_dict(self):
        """Converts the RedditPost instance to a dictionary."""
        return {
            "post_id": self.post_id,
            "title": self.title,
            "username": self.username,
            "created_utc": self.created_utc,
            "created_date": self.created_date,
            "score": self.score,
            "upvote_ratio": self.upvote_ratio,
            "num_comments": self.num_comments,
            "permalink": self.permalink,
            "user_url": self.user_url,
            "subreddit": self.subreddit,
            "post_text": self.post_text,
            "is_self": self.is_self,
            "stickied": self.stickied,
            "spoiler": self.spoiler,
            "locked": self.locked,
            "is_gallery": self.is_gallery,
            "gallery_image_urls": self.gallery_image_urls,
            "is_direct_image_post": self.is_direct_image_post,
            "image_post_url": self.image_post_url,
            "flair_text": self.flair_text,
            "inline_images_in_text": self.inline_images_in_text,
            "markdown_image_urls": self.markdown_image_urls,
            "processed": self.processed,
            "is_portfolio": self.is_portfolio,
            "failed": self.failed
        }
    
    def __str__(self):
        return f"""
        Post ID: {self.post_id},
        Title: {self.title},
        User: {self.username},
        Subreddit: {self.subreddit},
        Created Date: {self.created_date},
        """