from dotenv import load_dotenv
from typing import Tuple
import json
import requests
import re
import PIL
import io

from app.core.utils.utils import set_logger
from .service_prompts import (
    INTERPRET_IMAGE_FROM_REDDIT_POST,
    IMAGE_PORTFOLIO_REASONING_PROMPT
)
from app.core.database.reddit_post_db_handler import (
    get_reddit_posts,
    get_reddit_post_by_id_from_db,
    update_portfolio_status_in_db,
    insert_reddit_posts_to_db
)
from app.core.database.db_interface import DatabaseInterface
import app.core.secret_handler as secrets
from app.core.app_config import get_config
from app.core.llm_interface.model_interface import (
        GeminiProVision,
        GeminiProText
)
secret_config = secrets.get_config()

load_dotenv()
app_config = get_config()

logger = set_logger(name=__name__)


class RedditPostProcessor:
    def __init__(
            self,
            db_interface: DatabaseInterface
    ):
        self.db_interface = db_interface
        self.vision_model = GeminiProVision(
            api_key=secret_config.get("GOOGLE_API_KEY")
        )
        self.reasoning_model = GeminiProText(
            api_key=secret_config.get("GOOGLE_API_KEY")
        )

    def reddit_post_processed(
        self,
        reddit_post_id: str,
    ) -> bool:
        """
        Check if a Reddit post has been processed.
        Args:
            reddit_post_id (str): The ID of the Reddit post.
        Returns:
            bool: True if the post has been processed, False otherwise.
        """
        posts = get_reddit_posts(
            db_interface=self.db_interface,
            post_ids=[reddit_post_id]
        )
        if not posts:
            return False
        return True if posts[0].processed else False

    def reddit_post_is_portfolio(
            self,
            reddit_post_id: str
    ) -> bool:
        """
        Check if a Reddit post is considered a portfolio.
        Args:
            reddit_post_id (str): The ID of the Reddit post.
        Returns:
            bool: True if the post is a portfolio, False otherwise.
        """
        posts = get_reddit_posts(
            db_interface=self.db_interface,
            post_ids=[reddit_post_id]
        )
        if not posts:
            return False
        return True if posts[0].is_portfolio else False

    def read_image_from_url(
            self,
            image_url: str
    ):
        """
        Get image data from a URL using Gemini Pro Vision.
        Args:
            url (str): The URL of the image.
        Returns:
            dict: The image data.
        """
        try:
            response = requests.get(image_url, stream=True)
            response.raise_for_status()

            content_type = response.headers.get('content-type')
            if not content_type or not content_type.startswith('image/'):
                raise ValueError(
                    f"URL does not point to a valid image. "
                    f"Content-Type: {content_type}"
                )
            # Read the image content (bytes)
            image_bytes = response.content

            # Load the bytes into a PIL Image object
            img = PIL.Image.open(io.BytesIO(image_bytes))
            logger.info("Image fetched and loaded successfully.")
            return img
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Error fetching image from URL: {e}")
        except PIL.UnidentifiedImageError:
            logger.error(
                """Error: The content at the URL
                could not be identified as an image.""")
        except ValueError as e:
            logger.error(
                f"Error: {e}")
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during image loading: {e}")

    def get_info_from_image(
            self,
            image,
            prompt_text: str = "What is the content of this image?"
    ):
        vision_response = self.vision_model.get_response(
            prompt_text=prompt_text,
            img=image
        )
        return vision_response

    def upload_reddit_post_to_db(self, reddit_post_data_dict: dict):
        insert_reddit_posts_to_db(
            self.db_interface,
            reddit_post_data_dict
        )

    def process_image_gallery(
            self,
            image_urls: list[str]
    ) -> Tuple[bool, list[dict]]:
        """
        Process a list of image URLs to extract information from each image
        using a vision model. The function retrieves the images from their
        URLs, interprets them, and formats the results into a list of
        dictionaries.
        Args:
            image_urls (list[str]): A list of image URLs to process.
        Returns:
            list[dict]: A list of dictionaries containing the results
            and errors for each processed image.
        """
        logger.info(
            f"""Processing {len(image_urls)} images""")
        error = False
        process_result_dict = {
            "is_portfolio": False,
            "purchases": [],
        }
        assets_list = []
        for img_url in image_urls:
            error, curr_result_dict = self.process_img_url(
                image_url=img_url
            )
            if error:
                logger.error(
                    f"Error processing image URL {img_url}:"
                    f"{curr_result_dict.get('error')}"
                )
                return error, process_result_dict
            else:
                if curr_result_dict["is_portfolio"]:
                    logger.info(
                        f"""Successfully processed image URL {img_url}""")
                    assets_list.extend(
                        curr_result_dict["purchases"]
                    )
        process_result_dict["is_portfolio"] = True if len(assets_list) \
            > 0 else False
        process_result_dict["purchases"] = assets_list
        return error, process_result_dict

    def process_img_url(
            self,
            image_url: str
    ) -> Tuple[bool, dict]:
        """
        Process a single image URL to extract information using a vision model.
        Args:
            image_url (str): The URL of the image to process.
        Returns:
            Tuple[bool, dict]: A tuple containing a boolean indicating if there
            was an error and a dictionary with the results or error message.
        """
        image_type = self.read_image_from_url(image_url)
        vision_response = self.get_info_from_image(
            prompt_text=INTERPRET_IMAGE_FROM_REDDIT_POST,
            image=image_type)
        process_output = self.interpret_vision_model_ouput(
            vision_model_response=vision_response
        )
        json_process = self.extract_json_from_response(
                process_output
        )
        error = json_process.get("error")
        process_result_dict = json_process.get("result")
        return error, process_result_dict

    def process(
        self,
        reddit_post_id: str
    ) -> dict:
        """
        Process a list of Reddit post IDs to extract information from images
        associated with those posts. The function retrieves the posts from
        the database, reads the images from their URLs, and uses a vision
        model to interpret the images. The results are then formatted into
        a list of dictionaries containing the results and any errors
        encountered.
        If the reddit post of the provided reddit ID is considered a portfolio
        it will be uploaded to DB.

        Args:
            reddit_post_ids (list[str]): A list of Reddit post IDs to process.
        Returns:
            list[dict]: A list of dictionaries containing the
            results and errors for each processed Reddit post.
        """
        if app_config["debug"]["is_debug"]:
            with open("data/mock/reddit_post_process_results.json", "r") as f:
                result_dict = json.load(f)
        else:

            logger.info(
                f"""Processing {reddit_post_id}"""
            )
            reddit_post_data = get_reddit_post_by_id_from_db(
                    db_interface=self.db_interface,
                    post_id=reddit_post_id
                )
            error = ""
            result_dict = {
                "result": None,
                "error": False,
                "source_id": reddit_post_data.post_id,
                "created_date": reddit_post_data.created_date
            }
            try:
                if reddit_post_data.is_gallery:
                    error, img_process_result_dict = \
                        self.process_image_gallery(
                            eval(reddit_post_data.gallery_image_urls)
                        )
                elif reddit_post_data.is_direct_image_post and not \
                        reddit_post_data.is_gallery:
                    # If the post is a direct image post, process the image URL
                    img_url = eval(reddit_post_data.image_post_url)[0]
                    error, img_process_result_dict = self.process_img_url(
                        image_url=img_url
                    )

                result_dict["error"] = error
                result_dict["result"] = img_process_result_dict

                update_portfolio_status_in_db(
                    db_interface=self.db_interface,
                    post_id=reddit_post_data.post_id,
                    is_portfolio=result_dict.get("result").get(
                        "is_portfolio"),
                    failed=result_dict.get("error"),
                    processed=True
                )

            except Exception as e:
                result_dict["error"] = \
                    f"Error during reddit post processor: {e}"
            with open("data/mock/reddit_post_process_results.json", "w") as f:
                json.dump(result_dict, f, indent=2)
        return result_dict

    @staticmethod
    def extract_json_from_response(raw_response) -> dict:
        is_error = False
        # try to load the raw response already
        try:
            json_dict = json.loads(raw_response)
        except Exception as e:
            logger.error(f"""Attempt to load JSON
            from raw string failed. Error: {e}""")
            json_dict = None

        # now try to find the JSON string in the raw_string
        if json_dict is None:
            match = re.search(
                r"```(?:json)?\s*(\{.*?\})\s*```",
                raw_response,
                re.DOTALL | re.IGNORECASE)
            if match:
                json_string = match.group(1)
                try:
                    json_dict = json.loads(json_string)
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON: {e}")
                    logger.error(
                        f"Extracted string:\n>>>\n{json_string}\n<<<")
                    is_error = True
                except Exception as e:
                    logger.error(f"An unexpected error occurred: {e}")
                    is_error = True
            else:
                match = None
                logger.error(
                    """Could not find JSON block within
                    ``` fences using regex.""")
        result_dict = {
            "result": json_dict,
            "error": is_error
        }
        return result_dict

    def interpret_vision_model_ouput(self, vision_model_response):
        prompt = IMAGE_PORTFOLIO_REASONING_PROMPT.format(
                vision_model_response=vision_model_response
        )
        text_response = self.reasoning_model.get_response(
            prompt,
            config={
                "response_schema": self.get_interpret_post_response_format(),
                "response_mime_type": "application/json",
            })
        return text_response

    @staticmethod
    def get_interpret_post_response_format() -> dict:
        return {
            "type": "object",
            "properties": {
                "is_portfolio": {
                    "type": "boolean",
                    "description":
                        "Indicates if the post is part of a portfolio."
                },
                "purchases": {
                    "type": "array",
                    "description": "List of purchases made in the portfolio.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the crypto currency."
                            },
                            "abbreviation": {
                                "type": "string",
                                "description":
                                    "Abbreviation of the crypto currency."
                            },
                            "amount": {
                                "type": "number",
                                "description":
                                    "Amount of the crypto currency."
                            },
                            "price": {
                                "type": "number",
                                "description":
                                    "Price of the crypto currency."
                            },
                            "currency": {
                                "type": "string",
                                "description":
                                    """Currency of the price like USD,
                                    EUR, CAD, etc."""
                            }
                        }
                    }
                }
            }
        }
