import google.generativeai as genai
import os
from dotenv import load_dotenv
from app.core.app_config import get_config
import app.core.secret_handler as secrets
import logging

secret_config = secrets.get_config()
app_config = get_config()

logging.basicConfig(
    level=logging.INFO,
    format=app_config.get('logging').get('format'),
)
load_dotenv()


class GeminiProVision():
    """
    A class to interact with the Gemini Pro Vision model.
    """

    def __init__(
        self,
        api_key: str = os.getenv("GOOGLE_API_KEY")
    ):
        """
        Initialize the GeminiProVision class with the provided API key.
        """
        self.model_name = 'gemini-1.5-flash'
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(self.model_name) 

    def get_response(
            self,
            prompt_text: str,
            img
            ):
        """
        Get a response from the Gemini Pro Vision model.
        
        Args:
            prompt_text (str): The text prompt to send to the model.
            img (PIL.Image): The image to send to the model.
        
        Returns:
            str: The response from the model.
        """
        try:
            input_parts = [prompt_text, img]
            response = self.client.generate_content(input_parts)
        except Exception as e:
            logging.error(f"google.generativeai API error: {e}")
            return None
        return response.text


class GeminiProText():
    """
    A class to interact with the Gemini Pro Vision model.
    """
    def __init__(
        self,
        api_key: str = os.getenv("GOOGLE_API_KEY")
    ):
        """
        Initialize the GeminiProVision class with the provided API key.
        """
        self.api_key = api_key
        self.model_name = 'gemini-1.5-flash'
        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(self.model_name) 

    def get_response(
            self,
            prompt_text: str
            ):
        """
        Get a response from the Gemini Pro Vision model.
        
        Args:
            prompt_text (str): The text prompt to send to the model.
        
        Returns:
            str: The response from the model.
        """
        try:
            input_parts = [prompt_text]
            response = self.client.generate_content(input_parts)
        except Exception as e:
            logging.error(f"google.generativeai API error: {e}")
            return None
        return response.text
