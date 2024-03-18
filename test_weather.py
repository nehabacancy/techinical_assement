import pytest
import requests
import pandas as pd
from datetime import datetime
from unittest.mock import patch, Mock
from weather_collector import get_weather_data,transform_weather_data
# Mock the requests.get function
@patch('requests.get')
def test_get_weather_data(mock_get):
    # Set up mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "coord": {"lon": -0.1257, "lat": 51.5085},
        "weather": [{"id": 801, "main": "Clouds", "description": "few clouds", "icon": "02n"}],
        "base": "stations",
        "main": {"temp": 10.23, "feels_like": 8.41, "temp_min": 8.89, "temp_max": 11.67, "pressure": 1016, "humidity": 72},
        "visibility": 10000,
        "wind": {"speed": 2.06, "deg": 160},
        "clouds": {"all": 20},
        "dt": 1679133600,
        "sys": {"type": 2, "id": 2075535, "country": "GB", "sunrise": 1679089744, "sunset": 1679134305},
        "timezone": 3600,
        "id": 2643743,
        "name": "London",
        "cod": 200
    }
    mock_get.return_value = mock_response

    # Call the function
    data = get_weather_data("London", "UK")

    # Assert the expected output
    assert data == mock_response.json()

# Test the transform_weather_data function
def test_transform_weather_data():
    sample_data = {
        "coord": {"lon": -0.1257, "lat": 51.5085},
        "weather": [{"id": 801, "main": "Clouds", "description": "few clouds", "icon": "02n"}],
        "base": "stations",
        "main": {"temp": 10.23, "feels_like": 8.41, "temp_min": 8.89, "temp_max": 11.67, "pressure": 1016, "humidity": 72},
        "visibility": 10000,
        "wind": {"speed": 2.06, "deg": 160},
        "clouds": {"all": 20},
        "dt": 1679133600,
        "sys": {"type": 2, "id": 2075535, "country": "GB", "sunrise": 1679089744, "sunset": 1679134305},
        "timezone": 3600,
        "id": 2643743,
        "name": "London",
        "cod": 200
    }

    expected_data = [{
        "timestamp": datetime.fromtimestamp(1679133600),
        "city": "London",
        "country": "GB",
        "temperature": 10.23,
        "humidity": 72,
        "wind_speed": 2.06,
        "weather_description": "few clouds"
    }]

    dataframe = transform_weather_data(sample_data)
    assert dataframe.to_dict('records') == expected_data