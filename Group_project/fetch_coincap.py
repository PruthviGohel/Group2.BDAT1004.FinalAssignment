# fetch_coincap.py

import requests
import mysql.connector
from datetime import datetime
import time

# Database configuration
db_config = {
    'user': 'sanjay1007',
    'password': 'st2896239425',
    'host': 'sanjay1007.mysql.pythonanywhere-services.com',
    'database': 'sanjay1007$default'
}

# List of cryptocurrencies to track with their CoinCap IDs
cryptos = {
    'bitcoin': 'bitcoin',
    'ethereum': 'ethereum',
    'litecoin': 'litecoin'
}

# Base URL for CoinCap API
base_url = "https://api.coincap.io/v2"

def fetch_historical_data(asset_id, interval='d1'):
    """
    Fetch historical market data (price) for a cryptocurrency.
    :param asset_id: The CoinCap ID for the cryptocurrency.
    :param interval: Data interval (e.g., 'd1' for daily).
    :return: List of data points with timestamp and price.
    """
    # Define the time range (last 5 years)
    end = int(datetime.utcnow().timestamp() * 1000)  # Current time in ms
    start = end - (5 * 365 * 24 * 60 * 60 * 1000)  # 5 years ago in ms

    url = f"{base_url}/assets/{asset_id}/history"
    params = {
        'interval': interval,
        'start': start,
        'end': end
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('data', [])
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred for {asset_id}: {http_err}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred for {asset_id}: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred for {asset_id}: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"General error occurred for {asset_id}: {req_err}")
    return []

def store_historical_data(crypto_name, historical_data):
    """
    Store historical price data in the database.
    :param crypto_name: Name of the cryptocurrency.
    :param historical_data: List of data points with timestamp and price.
    """
    if not historical_data:
        print(f"No historical data to store for {crypto_name}.")
        return

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        for entry in historical_data:
            timestamp = datetime.strptime(entry['date'], '%Y-%m-%dT%H:%M:%S.%fZ')
            price = float(entry['priceUsd'])
            # Check if the entry already exists
            cursor.execute("""
                SELECT COUNT(*) FROM crypto_prices
                WHERE crypto_name = %s AND DATE(timestamp) = %s
            """, (crypto_name, timestamp.date()))
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.execute(
                    "INSERT INTO crypto_prices (crypto_name, price_usd, timestamp) VALUES (%s, %s, %s)",
                    (crypto_name, price, timestamp)
                )
        conn.commit()
        print(f"Historical data for {crypto_name} stored successfully.")
    except mysql.connector.Error as err:
        print(f"Database error while storing data for {crypto_name}: {err}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def main():
    for crypto_id, asset_id in cryptos.items():
        print(f"Fetching historical data for {crypto_id}...")
        historical_data = fetch_historical_data(asset_id)
        if historical_data:
            store_historical_data(crypto_id.capitalize(), historical_data)
        else:
            print(f"No data fetched for {crypto_id}.")
        # To respect API rate limits
        time.sleep(1)  # Adjust if necessary

if __name__ == '__main__':
    main()
