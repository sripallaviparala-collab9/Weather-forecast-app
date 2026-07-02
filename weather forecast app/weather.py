"""
weather.py
----------
Handles all communication with the OpenWeatherMap API.

The WeatherService class encapsulates:
    - Fetching current weather data for a city.
    - Fetching a 5-day / 3-hour forecast for a city.
    - Translating raw API responses into simple Python objects
      (CurrentWeather / ForecastDay) that the GUI layer can consume
      without needing to know anything about the OpenWeatherMap JSON shape.
    - Raising clear, custom exceptions for predictable failure cases
      (invalid city, bad API key, network problems) so the GUI can
      display friendly messages instead of raw stack traces.
"""

from dataclasses import dataclass, field
from typing import List

import requests

import config
from utils import (
    CityNotFoundError,
    InvalidAPIKeyError,
    NetworkError,
    kelvin_to_celsius,
    kelvin_to_fahrenheit,
)


# ---------------------------------------------------------------------------
# DATA MODELS
# ---------------------------------------------------------------------------

@dataclass
class CurrentWeather:
    """A simple container for the current-weather fields the UI needs."""
    city: str
    country: str
    temp_c: float
    temp_f: float
    feels_like_c: float
    feels_like_f: float
    condition: str
    description: str
    icon_code: str
    humidity: int
    wind_speed: float          # meters/second
    pressure: int               # hPa
    visibility_km: float
    sunrise_unix: int
    sunset_unix: int
    timezone_offset: int        # seconds from UTC


@dataclass
class ForecastEntry:
    """One 3-hour forecast slot."""
    dt_unix: int
    temp_c: float
    temp_f: float
    condition: str
    icon_code: str


@dataclass
class DailyForecast:
    """Aggregated forecast for a single day (used for the 5-day summary)."""
    date_label: str
    min_temp_c: float
    max_temp_c: float
    min_temp_f: float
    max_temp_f: float
    condition: str
    icon_code: str
    entries: List[ForecastEntry] = field(default_factory=list)


# ---------------------------------------------------------------------------
# WEATHER SERVICE
# ---------------------------------------------------------------------------

class WeatherService:
    """
    Thin wrapper around the OpenWeatherMap REST API.

    All network I/O lives here so the GUI code never touches `requests`
    directly. This separation makes the API layer easy to unit test or
    swap out later (e.g. to support a different weather provider).
    """

    def __init__(self, api_key: str = config.API_KEY):
        self.api_key = api_key

    # -- public API ---------------------------------------------------------

    def get_current_weather(self, city: str) -> CurrentWeather:
        """Fetch and parse current weather data for the given city."""
        data = self._request(config.BASE_URL, city)
        return self._parse_current_weather(data)

    def get_forecast(self, city: str) -> List[DailyForecast]:
        """Fetch and parse a 5-day forecast, grouped into daily buckets."""
        data = self._request(config.FORECAST_URL, city)
        return self._parse_forecast(data)

    @staticmethod
    def get_icon_url(icon_code: str) -> str:
        """Build the full URL for a weather icon image."""
        return config.ICON_URL_TEMPLATE.format(icon_code=icon_code)

    # -- internal helpers -----------------------------------------------------

    def _request(self, url: str, city: str) -> dict:
        """
        Perform the actual HTTP GET request and translate common failure
        modes into our custom exception types.
        """
        if not self.api_key:
            raise InvalidAPIKeyError(
                "No API key configured. Set the OPENWEATHER_API_KEY "
                "environment variable or edit config.py."
            )

        params = {
            "q": city,
            "appid": self.api_key,
            # We request Kelvin from the API and convert locally so we
            # always have both Celsius and Fahrenheit available.
        }

        try:
            response = requests.get(url, params=params, timeout=config.REQUEST_TIMEOUT)
        except requests.exceptions.ConnectionError as exc:
            raise NetworkError(
                "Could not connect to the weather service. "
                "Please check your internet connection."
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise NetworkError("The request timed out. Please try again.") from exc
        except requests.exceptions.RequestException as exc:
            raise NetworkError(f"A network error occurred: {exc}") from exc

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise CityNotFoundError(f'City "{city}" was not found. Please check the spelling.')
        elif response.status_code == 401:
            raise InvalidAPIKeyError("Invalid API key. Please check your OpenWeatherMap key.")
        else:
            raise NetworkError(f"Weather service returned an error (HTTP {response.status_code}).")

    def _parse_current_weather(self, data: dict) -> CurrentWeather:
        """Convert a raw /weather JSON payload into a CurrentWeather object."""
        try:
            main = data["main"]
            weather = data["weather"][0]
            wind = data.get("wind", {})
            sys_info = data.get("sys", {})

            temp_c = kelvin_to_celsius(main["temp"])
            feels_like_c = kelvin_to_celsius(main["feels_like"])

            return CurrentWeather(
                city=data.get("name", "Unknown"),
                country=sys_info.get("country", ""),
                temp_c=temp_c,
                temp_f=kelvin_to_fahrenheit(main["temp"]),
                feels_like_c=feels_like_c,
                feels_like_f=kelvin_to_fahrenheit(main["feels_like"]),
                condition=weather.get("main", "N/A"),
                description=weather.get("description", "N/A").title(),
                icon_code=weather.get("icon", "01d"),
                humidity=main.get("humidity", 0),
                wind_speed=wind.get("speed", 0.0),
                pressure=main.get("pressure", 0),
                visibility_km=round(data.get("visibility", 0) / 1000, 1),
                sunrise_unix=sys_info.get("sunrise", 0),
                sunset_unix=sys_info.get("sunset", 0),
                timezone_offset=data.get("timezone", 0),
            )
        except (KeyError, IndexError, TypeError) as exc:
            raise Exception(
                "Unexpected response format from the weather service."
            ) from exc

    def _parse_forecast(self, data: dict) -> List[DailyForecast]:
        """
        Convert a raw /forecast JSON payload (3-hour steps over 5 days)
        into a list of aggregated DailyForecast objects, one per day.
        """
        try:
            buckets = {}  # date_label -> list of raw entries

            for item in data.get("list", []):
                date_label = item["dt_txt"].split(" ")[0]  # 'YYYY-MM-DD'
                buckets.setdefault(date_label, []).append(item)

            daily_forecasts = []
            for date_label, items in list(buckets.items())[:5]:
                temps_k = [i["main"]["temp"] for i in items]
                min_k, max_k = min(temps_k), max(temps_k)

                # Use the mid-day entry's icon/condition as representative
                mid_item = items[len(items) // 2]
                condition = mid_item["weather"][0]["main"]
                icon_code = mid_item["weather"][0]["icon"]

                entries = [
                    ForecastEntry(
                        dt_unix=i["dt"],
                        temp_c=kelvin_to_celsius(i["main"]["temp"]),
                        temp_f=kelvin_to_fahrenheit(i["main"]["temp"]),
                        condition=i["weather"][0]["main"],
                        icon_code=i["weather"][0]["icon"],
                    )
                    for i in items
                ]

                daily_forecasts.append(
                    DailyForecast(
                        date_label=date_label,
                        min_temp_c=kelvin_to_celsius(min_k),
                        max_temp_c=kelvin_to_celsius(max_k),
                        min_temp_f=kelvin_to_fahrenheit(min_k),
                        max_temp_f=kelvin_to_fahrenheit(max_k),
                        condition=condition,
                        icon_code=icon_code,
                        entries=entries,
                    )
                )

            return daily_forecasts
        except (KeyError, IndexError, TypeError) as exc:
            raise Exception(
                "Unexpected forecast response format from the weather service."
            ) from exc