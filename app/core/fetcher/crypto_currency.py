import requests
from requests import Session
import pandas as pd
from datetime import datetime
import json

from app.core.utils.utils import set_logger
from app.core.app_config import get_config
import app.core.secret_handler as secrets

secret_config = secrets.get_config()
logger = set_logger(name=__name__)
app_config = get_config()


class CryptoCurrencyFetcher():
    def __init__(
        self
    ):
        self.request_info = {
            "coin_gecko": {
                "url": "https://api.coingecko.com/api/v3/coins/{coin_id}/history",
                "params_dict": """{{
                    "localization": {localization},
                    "date": "{date}"
                }}""",
                "mapping_file": "coingecko_mapping.csv"
            },
            "coin_market_cap": {
                "url": 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest',#"https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest",
                "params_dict": {
                    'start': '1',
                    'limit': '5000',
                    'convert': None
                },
                "headers": {
                    "Accepts": "application/json",
                    "X-CMC_PRO_API_KEY": None,
                },
                "mapping_file": "coinmarketcap_mapping.csv"
            }
        }
        self.providers = ["coin_gecko", "coin_market_cap"]

    def find_coin_id(
        self,
        name: str,
        abbreviation: str,
        provider: str
    ):
        mapping_df = pd.read_csv(
            f"./data/{self.request_info[provider]['mapping_file']}"
        )
        mapping_df["name"] = mapping_df["name"].str.capitalize()
        mapping_df["abbreviation"] = mapping_df["abbreviation"].str.upper()
        coin_match = mapping_df[
                (mapping_df["abbreviation"] == abbreviation.upper()) &
                (mapping_df["name"] == name.capitalize())
        ]
        if coin_match.empty:
            coin_match = mapping_df[
                (mapping_df["abbreviation"] == abbreviation.upper())
            ]
        if provider == "coin_gecko":
            try:
                coin_id = coin_match["id"].iloc[0]
            except IndexError:
                logger.warning(
                    f"Warning: Coin ID for {name} ({abbreviation}) not found in mapping file.")
                coin_id = None
        elif provider == "coin_market_cap":
            try:
                coin_id = coin_match["slug"].iloc[0]
            except IndexError:
                logger.warning(
                    f"Warning: Coin ID for {name} ({abbreviation}) not found in mapping file.")
                coin_id = None
        return coin_id

    def get_current_price_from_cmc(
        self,
        coin_id: str,
        vs_currency='USD'
    ):
        price = None
        api_url = self.request_info["coin_market_cap"]["url"].format(
                    coin_id=coin_id)
        params = self.request_info["coin_market_cap"]["params_dict"]
        params['convert'] = vs_currency.upper()

        headers = self.request_info["coin_market_cap"]["headers"]
        headers["X-CMC_PRO_API_KEY"] = \
            secret_config.get("COINMARKETCAP_API_KEY")
        try:
            session = Session()
            session.headers.update(headers)

            # Make the API request
            response = session.get(
                api_url,
                params=params
            )
            response.raise_for_status()

            data = pd.DataFrame(response.json()["data"])
            coin_data = data[data["slug"] == coin_id]
            try:
                price = coin_data["quote"].iloc[0][vs_currency.upper()]["price"]
            except KeyError:
                price = coin_data["quote"].iloc[0][vs_currency]["price"]
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from CoinMarketCap: {e}")
            price = None
        except KeyError as e:
            logger.error(f"Key error: {e}")
            price = None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            price = None
        return price

    def get_current_price_from_coin_gecko(
        self,
        coin_id: str,
        vs_currency='usd'
    ) -> dict:
        """
        Gets the price of a specific cryptocurrency from CoinGecko
        for the Monday of the current week.

        Args:
            coin_id (str): The CoinGecko ID of the cryptocurrency (e.g., 'bitcoin', 'ethereum').
            vs_currency (str): The currency to get the price in (e.g., 'usd', 'eur').

        Returns:
            float: The price on Monday, or None if an error occurs or data is unavailable.
                Returns the date string of Monday as well.
        """
        price = None
        try:
            date = datetime.today()
            # Format date as required by CoinGecko API: dd-mm-yyyy
            date_str = date.strftime('%d-%m-%Y')
            api_url = self.request_info["coin_gecko"]["url"].format(
                    coin_id=coin_id)
            params = self.request_info["coin_gecko"]["params_dict"].format(
                localization='false',
                date=date_str
            )
            params_dict = json.loads(params)

            headers = {
                'accept': 'application/json',
            }
            response = requests.get(
                api_url,
                params=params_dict,
                headers=headers,
                timeout=10
            )
            response.raise_for_status() 
            data = response.json()
            if 'market_data' in data and 'current_price' in data['market_data']:
                if vs_currency.lower() in data['market_data']['current_price']:
                    price = data['market_data']['current_price'][vs_currency.lower()]
            else:
                logger.warning(
                    f"Warning: No market data found for {coin_id} on {date_str}.")
                price = None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from CoinGecko: {e}")
            price = None
        return price

    def fetch_current_weeks_coin_price(
        self,
        coin_ids: dict,
        vs_currency='usd'
    ) -> dict:
        """
        Fetches the current week's price for a cryptocurrency from CoinGecko or CoinMarketCap.
        Args:
            coin_ids (dict): A dictionary containing the CoinGecko and CoinMarketCap IDs of the cryptocurrency.
                             Example: {"coin_gecko": "bitcoin", "coin_market_cap": "bitcoin"}
            vs_currency (str): The currency to get the price in (default is 'usd').
        Returns:
            dict: A dictionary containing the price, date, and error status.
                  Example: {
                      "price": 50000.0,
                      "date": "2023-10-01",
                      "is_error": False,
                      "error_message": None
                  }
        """
        result_dict = {
            "price": None,
            "date": None,
            "is_error": False,
            "error_message": None
        }

        coin_gecko_price = self.get_current_price_from_coin_gecko(
            coin_id=coin_ids["coin_gecko"],
            vs_currency=vs_currency
        )
        if coin_gecko_price is None:
            price = self.get_current_price_from_cmc(
                coin_id=coin_ids["coin_market_cap"],
                vs_currency=vs_currency
            )
        else:
            price = coin_gecko_price

        result_dict["date"] = datetime.today().strftime(
            app_config.get("mysql_column_format").get('date'))
        result_dict["price"] = price
        return result_dict

    def fetch_historical_data_for_currency(
        self,
        cc_abbreviation: str,
        days: int,
        vs_currency='usd'
    ):
        # TODO: needs to be overthought, bcs. at the moment I'm not able
        # to easily fetch historical data, bcs. CoinGecko costs money.
        # Solution would be to write a scraper
        coin_id = self.mapping_df[
                self.mapping_df["abbreviation"] == cc_abbreviation.lower()]["coin_id"].iloc[0]
        """Fetches daily data from CoinGecko and aggregates it to weekly OHLCV."""
        print(f"\nFetching daily data for {coin_id}...")
        # CoinGecko API endpoint for historical market data
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {
            'vs_currency': vs_currency,
            'days': days,
            'interval': 'daily' # Request daily granularity
        }
        headers = {'accept': 'application/json'}

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            if not data or 'prices' not in data or not data['prices']:
                print(f"Warning: No data returned from CoinGecko for {coin_id}.")
                return None

            prices_df = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
            volumes_df = pd.DataFrame(data['total_volumes'], columns=['timestamp', 'volume'])

            # Convert timestamp (milliseconds) to datetime objects (UTC)
            prices_df['date'] = pd.to_datetime(prices_df['timestamp'], unit='ms', utc=True)
            volumes_df['date'] = pd.to_datetime(volumes_df['timestamp'], unit='ms', utc=True)

            # Set date as index for resampling
            prices_df.set_index('date', inplace=True)
            volumes_df.set_index('date', inplace=True)

            return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {coin_id}: {e}")
            return None
