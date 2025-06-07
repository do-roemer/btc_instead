import requests
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()
import requests
import pandas as pd
import os
from dotenv import load_dotenv # To load the API key from .env file

def get_cmc_map_from_api():
    """
    Fetches the cryptocurrency map from the CoinMarketCap API.
    Requires a CMC_API_KEY environment variable or set in a .env file.

    Returns:
        pandas.DataFrame: DataFrame with CMC ID, name, symbol, slug, etc.,
                          or None if the request fails.
    """
    # Load environment variables from .env file (if it exists)
    load_dotenv()

    # Get API key from environment variable
    api_key = os.getenv('COINMARKETCAP_API_KEY')

    if not api_key:
        print("Error: CoinMarketCap API Key not found.")
        print("Please set the CMC_API_KEY environment variable or add it to a .env file.")
        return None

    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/map'
    headers = {
      'Accepts': 'application/json',
      'X-CMC_PRO_API_KEY': api_key,
    }

    # Parameters (optional, e.g., to list inactive coins too)
    # params = {'listing_status': 'inactive'} # Example
    params = {} # Use defaults (active coins)

    print("Fetching data from CoinMarketCap API (/v1/cryptocurrency/map)...")

    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        data = response.json()

        # Check if the request was successful according to CMC's status object
        if data.get('status') and data['status']['error_code'] == 0:
            print(f"Successfully fetched {len(data.get('data', []))} entries.")
            # Convert the list of coin dictionaries into a DataFrame
            df = pd.DataFrame(data.get('data', []))
            return df
        else:
            error_message = data.get('status', {}).get('error_message', 'Unknown error')
            print(f"API Error: {error_message}")
            return None

    except requests.exceptions.Timeout:
        print("Error: Request timed out.")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error fetching data: {e.response.status_code} {e.response.reason}")
        try:
            # Try to print the error message from CMC if available
            error_data = e.response.json()
            print(f"API Response Error: {error_data.get('status', {}).get('error_message', 'No details provided')}")
        except Exception:
            pass # Ignore if response isn't JSON
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request Exception fetching data: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# --- Main Execution ---
if __name__ == "__main__":
    cmc_map_df = get_cmc_map_from_api()

    if cmc_map_df is not None:
        print("\n--- Sample Data (First 5 Rows) ---")
        # Select and rename columns to be similar to the previous example if desired
        # Available columns usually include: id, name, symbol, slug, is_active, first_historical_data, last_historical_data, platform
        print(cmc_map_df.head())

        # Example: Select only relevant columns
        output_df = cmc_map_df[['symbol', 'id', 'name', 'slug']].copy()
        output_df.rename(columns={'symbol': 'abbreviation'}, inplace=True)

        # Save to CSV
        output_csv_file = 'coinmarketcap_coin_map.csv'
        try:
            output_df.to_csv(output_csv_file, index=False, encoding='utf-8')
            print(f"\nSuccessfully saved data for {len(output_df)} coins to {output_csv_file}")
        except Exception as e:
            print(f"\nError saving data to CSV: {e}")
    else:
        print("\nFailed to retrieve data from CoinMarketCap API.")