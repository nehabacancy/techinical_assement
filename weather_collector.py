import requests
import time
import logging
import pandas as pd
from datetime import datetime
import psycopg2
import yaml

# Configure logging
logging.basicConfig(filename='weather_data.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

def load_config(config_name):

    """
    Load configuration settings from a YAML file.

    """
    try:
        with open(config_name) as file:
            config= yaml.safe_load(file)
    except Exception as e:
        logging.error("An error occurred while loading the configuration file '{}': {}".format(config_name, str(e)))
        config = {}
    return config


def get_weather_data(city, country,api_key,url):
    """
    Fetches weather data for a given city and country from OpenWeatherMap API.

    Args:
        city (str): Name of the city.
        country (str): Country code of the city.

    Returns:
        dict: The parsed JSON response containing weather data.

    Raises:
        requests.exceptions.RequestException: If the API request fails.
    """
    params = {
        "q": f"{city},{country}",
        "appid": api_key,
        "units": "metric"
    }

    logging.info(f"Sending API request for {city}, {country}")

    response = requests.get(url, params=params)
    response.raise_for_status()  # Raise an exception for non-2xx status codes

    logging.info(f"API request successful")
    return response.json()


def transform_weather_data(data):
    """
    Transforms raw weather data into a pandas DataFrame.

    Args:
        data (dict): The raw JSON response from the API.

    Returns:
        pd.DataFrame: A DataFrame containing weather data.
    """

    weather_dict = {
        "timestamp": datetime.fromtimestamp(data["dt"]),
        "city": data["name"],
        "country": data["sys"]["country"],
        "temperature": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "wind_speed": data["wind"]["speed"],
        "weather_description": data["weather"][0]["description"]
    }

    return pd.DataFrame([weather_dict])


def insert_data_to_database(data, sql_password):
    """
    Inserts weather data from a DataFrame into a PostgreSQL database table.

    Args:
        data (pd.DataFrame): The DataFrame containing weather data.
    """

    conn = None
    cursor = None

    try:

        conn = psycopg2.connect(
        host="localhost",
        user="postgres",
        password=sql_password,
        port= '5432'
        )

        cursor = conn.cursor()

        table_creation = """
        CREATE TABLE IF NOT EXISTS weather_data (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP NOT NULL,
        city VARCHAR(100) NOT NULL,
        country VARCHAR(100) NOT NULL,
        temperature FLOAT NOT NULL,
        humidity INTEGER NOT NULL,
        wind_speed FLOAT NOT NULL,
        weather_description VARCHAR(200) NOT NULL
        );
        """

        cursor.execute(table_creation)
        conn.commit()
        
        # Insert data from the DataFrame into the table
        for _, row in data.iterrows():
            query = """
                INSERT INTO weather_data (
                    timestamp, city, country, temperature, humidity, wind_speed, weather_description
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s
                );
            """
            values = (
                row["timestamp"],
                row["city"],
                row["country"],
                row["temperature"],
                row["humidity"],
                row["wind_speed"],
                row["weather_description"]
            )
            cursor.execute(query, values)
            conn.commit()


    except Exception as error:
        print(error)

    finally:
        if cursor is None:
            cursor.close()
        if conn is not None:
            conn.close()

            
def merge_dataframe(city_country_pairs):

    # Create an empty list to store dataframes
    all_dataframes = []

    # Iterate through the city-country pairs
    for city, country in city_country_pairs:
        try:
            data = get_weather_data(city, country, config['api_key'],config['url'])
            dataframe = transform_weather_data(data)
            all_dataframes.append(dataframe)
        except requests.exceptions.RequestException as e:
            print(f"API request failed for {city}, {country}: {e}")

    # Concatenate all dataframes into a single dataframe
    combined_dataframe = pd.concat(all_dataframes, ignore_index=True)

    # Print the combined dataframe
    return combined_dataframe

if __name__ == "__main__":
    try:
        # Load configuration settings from the "info.yaml" file
        config = load_config("info.yaml")
        #dataframe of all records
        dataframe = merge_dataframe(config['city_country_pairs'])
        #Insert data into database
        insert_data_to_database(dataframe,config['sql_password'])

    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {e}")
