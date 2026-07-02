"""
config.py
---------
Central configuration for the Weather Forecast App.

This module stores API settings, application constants, and the color /
font palettes used for the light and dark themes. Keeping all of this in
one place makes the rest of the codebase easier to read and maintain.

API KEY SETUP:
    1. Create a free account at https://openweathermap.org/api
    2. Generate an API key from your account dashboard.
    3. Either:
        a) Set it as an environment variable named OPENWEATHER_API_KEY, OR
        b) Paste it directly into the DEFAULT_API_KEY variable below.
    Option (a) is strongly recommended so you never commit a real key
    to GitHub.
"""

import os

# ---------------------------------------------------------------------------
# API CONFIGURATION
# ---------------------------------------------------------------------------

# The app first looks for the key in the environment. If it isn't found,
# it falls back to DEFAULT_API_KEY (left blank on purpose for safety).
DEFAULT_API_KEY = "d3e6dd0cd5628a3dd7b4af162f309005"
API_KEY = os.getenv("OPENWEATHER_API_KEY", DEFAULT_API_KEY)

# OpenWeatherMap endpoints
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
ICON_URL_TEMPLATE = "https://openweathermap.org/img/wn/{icon_code}@2x.png"

# Network settings
REQUEST_TIMEOUT = 10  # seconds

# ---------------------------------------------------------------------------
# APPLICATION CONSTANTS
# ---------------------------------------------------------------------------

APP_NAME = "Weather Forecast App"
APP_VERSION = "1.0.0"
WINDOW_MIN_WIDTH = 480
WINDOW_MIN_HEIGHT = 640

RECENT_SEARCHES_FILE = "recent_searches.json"
MAX_RECENT_SEARCHES = 5

# ---------------------------------------------------------------------------
# THEME / COLOR PALETTES
# ---------------------------------------------------------------------------

LIGHT_THEME = {
    "bg": "#f0f4f8",
    "card_bg": "#ffffff",
    "primary": "#2563eb",
    "primary_hover": "#1d4ed8",
    "text": "#1e293b",
    "subtext": "#64748b",
    "error": "#dc2626",
    "border": "#e2e8f0",
    "entry_bg": "#ffffff",
}

DARK_THEME = {
    "bg": "#0f172a",
    "card_bg": "#1e293b",
    "primary": "#3b82f6",
    "primary_hover": "#60a5fa",
    "text": "#f1f5f9",
    "subtext": "#94a3b8",
    "error": "#f87171",
    "border": "#334155",
    "entry_bg": "#334155",
}

# ---------------------------------------------------------------------------
# FONTS
# ---------------------------------------------------------------------------

FONT_FAMILY = "Segoe UI"

FONTS = {
    "title": (FONT_FAMILY, 20, "bold"),
    "temperature": (FONT_FAMILY, 42, "bold"),
    "heading": (FONT_FAMILY, 14, "bold"),
    "body": (FONT_FAMILY, 11, "normal"),
    "small": (FONT_FAMILY, 9, "normal"),
    "button": (FONT_FAMILY, 11, "bold"),
}