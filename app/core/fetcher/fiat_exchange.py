import requests
import logging
from datetime import date, timedelta

import src.secret_handler as secrets
from src.app_config import get_config

secret_config = secrets.get_config()
app_config = get_config()

logging.basicConfig(
    level=logging.INFO,
    format=app_config.get('logging').get('format'),
)


def get_historical_exchange_rate_for_usd(date_str, base_currency):
    """
    Gets the exchange rate for a specific date using the Frankfurter API.

    Args:
        date_str (str): The date in 'YYYY-MM-DD' format.
        base_currency (str): The 3-letter currency code of the base currency (e.g., 'USD').
        target_currency (str): The 3-letter currency code of the target currency (e.g., 'EUR').

    Returns:
        float: The exchange rate (how much 1 unit of base_currency is worth in target_currency),
            or None if an error occurs or data is unavailable.
    """
    # Split the date_str into date and time
    
    base_currency = base_currency.upper()
    target_currency = "USD"
    api_url = f"https://api.frankfurter.app/{date_str}"

    params = {
        'from': base_currency,
        'to': target_currency
    }

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()

        data = response.json()

        # Check if rates are present and the target currency is in the rates
        if 'rates' in data and target_currency in data['rates']:
            return data['rates'][target_currency]
        elif 'rates' in data and not data['rates']:
            logging.warning(
                f"Warning: No rate found for {target_currency} on {date_str}. "
                f"The API might have returned data for the previous business"
                f"day implicitly, "
                f"or the currency pair might not be supported for this date.")
            # Depending on API behavior, you might need to check data['date']
            # to see which date's rate was actually returned.
            # If the 'rates' dict itself is empty, we can't extract the rate.
            return None  # Or handle appropriately
        else:
            # If base_currency == target_currency, rates dict might be empty
            if base_currency == target_currency:
                return 1.0
            logging.error(
                f"Error: Could not find rate for {target_currency}"
                f" in API response.")
            logging.info(
                f"API Response: {data}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
