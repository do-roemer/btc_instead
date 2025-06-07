import logging
from dotenv import load_dotenv
import json
import requests
import re
import PIL
import io
from .service_prompts import (
    INTERPRET_IMAGE_FROM_REDDIT_POST,
    IMAGE_PORTFOLIO_REASONING_PROMPT
)
from app.core.database.reddit_post_db_handler import (
    get_reddit_posts,
    update_portfolio_status_in_db
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

logging.basicConfig(
    level=logging.INFO,
    format=app_config.get('logging').get('format'),
)


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
            logging.info("Image fetched and loaded successfully.")
            return img
        except requests.exceptions.RequestException as e:
            logging.error(
                f"Error fetching image from URL: {e}")
        except PIL.UnidentifiedImageError:
            logging.error(
                """Error: The content at the URL
                could not be identified as an image.""")
        except ValueError as e:
            logging.error(
                f"Error: {e}")
        except Exception as e:
            logging.error(
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

    def process_image_gallery(
            self,
            image_urls: list[str]
    ) -> list[dict]:
        """
        Process a list of image URLs to extract information from each image
        using a vision model. The function retrieves the images from their URLs,
        interprets them, and formats the results into a list of dictionaries.
        Args:
            image_urls (list[str]): A list of image URLs to process.
        Returns:
            list[dict]: A list of dictionaries containing the results and errors
            for each processed image.
        """
        logging.info(
            f"""Processing {len(image_urls)} images""")
        assets_list = []
        for img_url in image_urls:
            curr_result_dict = self.process_img_url(
                image_url=img_url
            )
            if curr_result_dict.get("error"):
                logging.error(
                    f"Error processing image URL {img_url}:"
                    f"{curr_result_dict.get('error')}"
                )
                return {
                    "error": True,
                    "result": None
                }
            else:
                result = curr_result_dict.get("result")
                if result["is_portfolio"]:
                    logging.info(
                        f"""Successfully processed image URL {img_url}""")
                    assets_list.extend(
                        result["positions"]
                    )
        return {
                    "error": False,
                    "result": {
                        "is_portfolio": True,
                        "positions": assets_list
                    }
                }

    def process_img_url(self, image_url: str) -> dict:
        result_dict = {}
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
        result_dict["error"] = json_process.get("error")
        result_dict["result"] = json_process.get("result")
        return result_dict

    def process(
        self,
        reddit_post_ids: list[str]
    ) -> list[dict]:
        """
        Process a list of Reddit post IDs to extract information from images
        associated with those posts. The function retrieves the posts from
        the database, reads the images from their URLs, and uses a vision
        model to interpret the images. The results are then formatted into
        a list of dictionaries containing the results and any errors encountered.
        Args:
            reddit_post_ids (list[str]): A list of Reddit post IDs to process.
        Returns:
            list[dict]: A list of dictionaries containing the results and errors
            for each processed Reddit post.
        """
        logging.info(
            f"""Processing {len(reddit_post_ids)}
            reddit posts""")
        reddit_post_data = get_reddit_posts(
            db_interface=self.db_interface,
            post_ids=reddit_post_ids
        )
        process_dicts = []
        for reddit_post in reddit_post_data:
            result_dict = {
                "result": None,
                "error": False,
                "source_id": reddit_post.post_id,
                "created_date": reddit_post.created_date
            }
            if reddit_post.is_gallery:
                result_dict = self.process_image_gallery(
                    eval(reddit_post.gallery_image_urls)
                )
            elif reddit_post.is_direct_image_post and not reddit_post.is_gallery:
                # If the post is a direct image post, process the image URL
                img_url = eval(reddit_post.image_post_url)[0]
                result_dict = self.process_img_url(
                    image_url=img_url
                )
            process_dicts.append(result_dict)
            update_portfolio_status_in_db(
                db_interface=self.db_interface,
                post_id=reddit_post.post_id,
                is_portfolio=result_dict.get("result").get(
                    "is_portfolio"),
                failed=result_dict.get("error"),
                processed=True
            )
        return process_dicts

    @staticmethod
    def extract_json_from_response(raw_response) -> dict:
        is_error = False
        # try to load the raw response already
        try:
            json_dict = json.loads(raw_response)
        except Exception as e:
            logging.error(f"""Attempt to load JSON
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
                    logging.error(f"Error decoding JSON: {e}")
                    logging.error(
                        f"Extracted string:\n>>>\n{json_string}\n<<<")
                    is_error = True
                except Exception as e:
                    logging.error(f"An unexpected error occurred: {e}")
                    is_error = True
            else:
                match = None
                logging.error(
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
        text_response = self.reasoning_model.get_response(prompt)
        return text_response

    
