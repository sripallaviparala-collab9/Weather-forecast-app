"""
utils.py
--------
Utility/helper functions shared across the application:
    - Unit conversions (Kelvin <-> Celsius <-> Fahrenheit)
    - Timestamp formatting
    - Input validation
    - Custom exception classes
    - Simple JSON-backed persistence helpers for "recent searches"

Keeping these small, pure functions separate from the GUI and API code
makes them easy to test and reuse.
"""

import json
import os
import re
from datetime import datetime


# ---------------------------------------------------------------------------
# CUSTOM EXCEPTIONS
# ---------------------------------------------------------------------------

class WeatherAppError(Exception):
    """Base exception for all predictable, user-facing app errors."""
    pass


class CityNotFoundError(WeatherAppError):
    """Raised when the API cannot find the requested city."""
    pass


class InvalidAPIKeyError(WeatherAppError):
    """Raised when the OpenWeatherMap API key is missing or invalid."""
    pass


class NetworkError(WeatherAppError):
    """Raised when a network/connection problem prevents an API call."""
    pass


# ---------------------------------------------------------------------------
# TEMPERATURE CONVERSIONS
# ---------------------------------------------------------------------------

def kelvin_to_celsius(kelvin: float) -> float:
    """Convert a Kelvin temperature to Celsius, rounded to 1 decimal place."""
    return round(kelvin - 273.15, 1)


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert a Celsius temperature to Fahrenheit, rounded to 1 decimal."""
    return round((celsius * 9 / 5) + 32, 1)


def kelvin_to_fahrenheit(kelvin: float) -> float:
    """Convert a Kelvin temperature directly to Fahrenheit."""
    return celsius_to_fahrenheit(kelvin_to_celsius(kelvin))


# ---------------------------------------------------------------------------
# TIME / DATE FORMATTING
# ---------------------------------------------------------------------------

def format_unix_time(timestamp: int, tz_offset_seconds: int = 0, fmt: str = "%I:%M %p") -> str:
    """
    Convert a UNIX timestamp (as returned by OpenWeatherMap) into a
    human-readable local time string, adjusted for the city's UTC offset.
    """
    try:
        local_time = datetime.utcfromtimestamp(timestamp + tz_offset_seconds)
        return local_time.strftime(fmt)
    except (OSError, OverflowError, ValueError):
        return "N/A"


def current_datetime_string() -> str:
    """Return the current local date/time formatted for display in the UI."""
    return datetime.now().strftime("%A, %d %B %Y | %I:%M %p")


# ---------------------------------------------------------------------------
# INPUT VALIDATION
# ---------------------------------------------------------------------------

def validate_city_name(city: str) -> str:
    """
    Validate and normalize a user-entered city name.

    Returns the cleaned city string if valid.
    Raises ValueError with a friendly message if invalid.
    """
    if city is None:
        raise ValueError("Please enter a city name.")

    cleaned = city.strip()

    if not cleaned:
        raise ValueError("City name cannot be empty.")

    if len(cleaned) < 2:
        raise ValueError("City name is too short.")

    # Allow letters (incl. accented), spaces, hyphens, apostrophes, and commas
    # (commas let users type "London,GB" style queries).
    if not re.match(r"^[A-Za-z\u00C0-\u024F\s\-',.]+$", cleaned):
        raise ValueError("City name contains invalid characters.")

    return cleaned


# ---------------------------------------------------------------------------
# RECENT SEARCHES PERSISTENCE
# ---------------------------------------------------------------------------

def load_recent_searches(filepath: str) -> list:
    """Load the list of recent city searches from a JSON file on disk."""
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, OSError):
        # Corrupt or unreadable file -- fail gracefully with an empty list
        return []


def save_recent_search(filepath: str, city: str, max_items: int) -> list:
    """
    Add a city to the recent searches list (most recent first), removing
    duplicates and trimming to `max_items`. Returns the updated list.
    """
    searches = load_recent_searches(filepath)

    # Remove existing occurrence (case-insensitive) so it moves to the top
    searches = [c for c in searches if c.lower() != city.lower()]
    searches.insert(0, city)
    searches = searches[:max_items]

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(searches, f, indent=2)
    except OSError:
        # If we can't write to disk, silently continue -- this feature
        # is a "nice to have" and shouldn't crash the app.
        pass

    return searches