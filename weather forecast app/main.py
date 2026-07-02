"""
main.py
-------
Entry point and GUI layer for the Weather Forecast App.

This module defines the WeatherApp class (a tk.Tk subclass) that builds
the entire interface, wires up user interactions, and talks to the
WeatherService (weather.py) for data. All network calls run on a
background thread so the GUI never freezes while waiting on the API.

Run with:
    python main.py
"""

import io
import os
import threading
import tkinter as tk
from tkinter import font as tkfont

import requests
from PIL import Image, ImageTk

import config
import utils
from weather import WeatherService


class WeatherApp(tk.Tk):
    """Main application window for the Weather Forecast App."""

    def __init__(self):
        super().__init__()

        # -- window setup -----------------------------------------------
        self.title(config.APP_NAME)
        self.minsize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)
        self.geometry(f"{config.WINDOW_MIN_WIDTH}x{config.WINDOW_MIN_HEIGHT}")

        # -- state --------------------------------------------------------
        self.weather_service = WeatherService()
        self.is_dark_mode = False
        self.unit = "C"  # "C" or "F"
        self.current_weather = None       # last successful CurrentWeather
        self.current_forecast = []        # last successful forecast list
        self._icon_cache = {}             # icon_code -> ImageTk.PhotoImage
        self.recent_searches_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), config.RECENT_SEARCHES_FILE
        )

        self.theme = config.LIGHT_THEME
        self.configure(bg=self.theme["bg"])

        self._build_ui()
        self._refresh_recent_searches_menu()

    # =========================================================================
    # UI CONSTRUCTION
    # =========================================================================

    def _build_ui(self):
        """Build and lay out every widget in the application."""
        self._build_header()
        self._build_search_bar()
        self._build_status_label()
        self._build_weather_card()
        self._build_details_grid()
        self._build_forecast_row()
        self._build_footer()

    def _build_header(self):
        bar = tk.Frame(self, bg=self.theme["bg"])
        bar.pack(fill="x", padx=16, pady=(16, 4))

        self.title_label = tk.Label(
            bar, text="\u2600  Weather Forecast", font=config.FONTS["title"],
            bg=self.theme["bg"], fg=self.theme["text"],
        )
        self.title_label.pack(side="left")

        self.theme_button = tk.Button(
            bar, text="\U0001F319 Dark Mode", command=self.toggle_theme,
            font=config.FONTS["small"], relief="flat", cursor="hand2",
            bg=self.theme["bg"], fg=self.theme["primary"], activeforeground=self.theme["primary_hover"],
        )
        self.theme_button.pack(side="right")

        self.unit_button = tk.Button(
            bar, text="\u00b0F", command=self.toggle_unit,
            font=config.FONTS["small"], relief="flat", cursor="hand2", width=4,
            bg=self.theme["bg"], fg=self.theme["primary"], activeforeground=self.theme["primary_hover"],
        )
        self.unit_button.pack(side="right", padx=(0, 12))

    def _build_search_bar(self):
        frame = tk.Frame(self, bg=self.theme["bg"])
        frame.pack(fill="x", padx=16, pady=8)

        self.city_entry = tk.Entry(
            frame, font=config.FONTS["body"], relief="flat",
            bg=self.theme["entry_bg"], fg=self.theme["text"], insertbackground=self.theme["text"],
        )
        self.city_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self.city_entry.insert(0, "Enter city name...")
        self.city_entry.bind("<FocusIn>", self._clear_placeholder)
        self.city_entry.bind("<Return>", lambda event: self.search_weather())

        self.search_button = tk.Button(
            frame, text="Search", command=self.search_weather,
            font=config.FONTS["button"], relief="flat", cursor="hand2",
            bg=self.theme["primary"], fg="white", activebackground=self.theme["primary_hover"],
            padx=16,
        )
        self.search_button.pack(side="left")

        self.refresh_button = tk.Button(
            frame, text="\u21bb", command=self.refresh_weather,
            font=config.FONTS["button"], relief="flat", cursor="hand2",
            bg=self.theme["bg"], fg=self.theme["primary"], width=3,
        )
        self.refresh_button.pack(side="left", padx=(8, 0))

        # Recent searches dropdown
        self.recent_var = tk.StringVar(value="Recent")
        self.recent_menu = tk.OptionMenu(frame, self.recent_var, "Recent", command=self._on_recent_selected)
        self.recent_menu.config(
            font=config.FONTS["small"], relief="flat", bg=self.theme["bg"], fg=self.theme["subtext"],
        )
        self.recent_menu.pack(side="left", padx=(8, 0))

    def _build_status_label(self):
        self.status_label = tk.Label(
            self, text="", font=config.FONTS["small"],
            bg=self.theme["bg"], fg=self.theme["error"], wraplength=config.WINDOW_MIN_WIDTH - 32,
        )
        self.status_label.pack(fill="x", padx=16)

    def _build_weather_card(self):
        self.card = tk.Frame(self, bg=self.theme["card_bg"], padx=20, pady=20)
        self.card.pack(fill="x", padx=16, pady=8)

        self.city_label = tk.Label(
            self.card, text="Search for a city to begin", font=config.FONTS["heading"],
            bg=self.theme["card_bg"], fg=self.theme["text"],
        )
        self.city_label.pack()

        self.datetime_label = tk.Label(
            self.card, text="", font=config.FONTS["small"],
            bg=self.theme["card_bg"], fg=self.theme["subtext"],
        )
        self.datetime_label.pack(pady=(2, 8))

        self.icon_label = tk.Label(self.card, bg=self.theme["card_bg"])
        self.icon_label.pack()

        self.temp_label = tk.Label(
            self.card, text="--\u00b0", font=config.FONTS["temperature"],
            bg=self.theme["card_bg"], fg=self.theme["primary"],
        )
        self.temp_label.pack()

        self.condition_label = tk.Label(
            self.card, text="", font=config.FONTS["body"],
            bg=self.theme["card_bg"], fg=self.theme["subtext"],
        )
        self.condition_label.pack()

        self.feels_like_label = tk.Label(
            self.card, text="", font=config.FONTS["small"],
            bg=self.theme["card_bg"], fg=self.theme["subtext"],
        )
        self.feels_like_label.pack(pady=(2, 0))

    def _build_details_grid(self):
        self.details_frame = tk.Frame(self, bg=self.theme["bg"])
        self.details_frame.pack(fill="x", padx=16, pady=8)

        # Each entry: (key, display label, icon)
        self._detail_specs = [
            ("humidity", "Humidity", "\U0001F4A7"),
            ("wind", "Wind", "\U0001F4A8"),
            ("pressure", "Pressure", "\U0001F4CA"),
            ("visibility", "Visibility", "\U0001F441"),
            ("sunrise", "Sunrise", "\U0001F305"),
            ("sunset", "Sunset", "\U0001F307"),
        ]
        self._detail_value_labels = {}

        for index, (key, label_text, icon) in enumerate(self._detail_specs):
            row, col = divmod(index, 2)
            cell = tk.Frame(self.details_frame, bg=self.theme["card_bg"], padx=12, pady=10)
            cell.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
            self.details_frame.grid_columnconfigure(col, weight=1)

            header = tk.Label(
                cell, text=f"{icon}  {label_text}", font=config.FONTS["small"],
                bg=self.theme["card_bg"], fg=self.theme["subtext"], anchor="w",
            )
            header.pack(fill="x")

            value = tk.Label(
                cell, text="--", font=config.FONTS["heading"],
                bg=self.theme["card_bg"], fg=self.theme["text"], anchor="w",
            )
            value.pack(fill="x")

            self._detail_value_labels[key] = (cell, header, value)

    def _build_forecast_row(self):
        tk.Label(
            self, text="5-Day Forecast", font=config.FONTS["heading"],
            bg=self.theme["bg"], fg=self.theme["text"], anchor="w",
        ).pack(fill="x", padx=16, pady=(8, 4))

        self.forecast_frame = tk.Frame(self, bg=self.theme["bg"])
        self.forecast_frame.pack(fill="x", padx=16, pady=(0, 8))
        self.forecast_cells = []

    def _build_footer(self):
        self.footer_label = tk.Label(
            self, text=f"{config.APP_NAME} v{config.APP_VERSION} | Data: OpenWeatherMap",
            font=config.FONTS["small"], bg=self.theme["bg"], fg=self.theme["subtext"],
        )
        self.footer_label.pack(side="bottom", pady=8)

    # =========================================================================
    # EVENT HANDLERS
    # =========================================================================

    def _clear_placeholder(self, _event):
        if self.city_entry.get() == "Enter city name...":
            self.city_entry.delete(0, tk.END)

    def _on_recent_selected(self, city):
        if city and city != "Recent":
            self.city_entry.delete(0, tk.END)
            self.city_entry.insert(0, city)
            self.search_weather()

    def search_weather(self):
        """Validate input and kick off a background fetch for the city."""
        raw_city = self.city_entry.get()
        try:
            city = utils.validate_city_name(raw_city)
        except ValueError as exc:
            self._show_error(str(exc))
            return

        self._set_loading_state(True)
        thread = threading.Thread(target=self._fetch_weather_worker, args=(city,), daemon=True)
        thread.start()

    def refresh_weather(self):
        """Re-fetch weather for the currently displayed city, if any."""
        if self.current_weather:
            self.city_entry.delete(0, tk.END)
            self.city_entry.insert(0, self.current_weather.city)
            self.search_weather()
        else:
            self._show_error("No city loaded yet. Search for one first.")

    def toggle_unit(self):
        """Switch the displayed temperature unit between Celsius and Fahrenheit."""
        self.unit = "F" if self.unit == "C" else "C"
        self.unit_button.config(text="\u00b0C" if self.unit == "F" else "\u00b0F")
        if self.current_weather:
            self._render_current_weather(self.current_weather)
            self._render_forecast(self.current_forecast)

    def toggle_theme(self):
        """Switch between light and dark color themes."""
        self.is_dark_mode = not self.is_dark_mode
        self.theme = config.DARK_THEME if self.is_dark_mode else config.LIGHT_THEME
        self.theme_button.config(text="\u2600 Light Mode" if self.is_dark_mode else "\U0001F319 Dark Mode")
        self._apply_theme()

    # =========================================================================
    # BACKGROUND WORK (runs off the main thread)
    # =========================================================================

    def _fetch_weather_worker(self, city: str):
        """
        Runs on a background thread: performs the (possibly slow) network
        calls, then schedules the UI update back on the main thread via
        `self.after(...)`, since Tkinter is not thread-safe.
        """
        try:
            current = self.weather_service.get_current_weather(city)
            forecast = self.weather_service.get_forecast(city)
            icon_image = self._download_icon(current.icon_code)
            self.after(0, self._on_fetch_success, current, forecast, icon_image)
        except utils.WeatherAppError as exc:
            self.after(0, self._on_fetch_failure, str(exc))
        except Exception as exc:  # noqa: BLE001 - final safety net for unexpected errors
            self.after(0, self._on_fetch_failure, f"An unexpected error occurred: {exc}")

    def _download_icon(self, icon_code: str):
        """Download (or reuse a cached copy of) a weather icon image."""
        if icon_code in self._icon_cache:
            return self._icon_cache[icon_code]
        try:
            url = self.weather_service.get_icon_url(icon_code)
            response = requests.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            image = Image.open(io.BytesIO(response.content)).resize((100, 100))
            photo = ImageTk.PhotoImage(image)
            self._icon_cache[icon_code] = photo
            return photo
        except Exception:
            # Icon download failing shouldn't break the whole weather display
            return None

    # =========================================================================
    # MAIN-THREAD UI UPDATES
    # =========================================================================

    def _set_loading_state(self, is_loading: bool):
        if is_loading:
            self.status_label.config(text="Loading weather data...", fg=self.theme["subtext"])
            self.search_button.config(state="disabled", text="Searching...")
        else:
            self.search_button.config(state="normal", text="Search")

    def _on_fetch_success(self, current, forecast, icon_image):
        self._set_loading_state(False)
        self.status_label.config(text="")
        self.current_weather = current
        self.current_forecast = forecast
        self._current_icon_image = icon_image  # keep a reference alive

        self._render_current_weather(current)
        self._render_forecast(forecast)

        updated = utils.save_recent_search(
            self.recent_searches_path, f"{current.city}", config.MAX_RECENT_SEARCHES
        )
        self._refresh_recent_searches_menu(updated)

    def _on_fetch_failure(self, message: str):
        self._set_loading_state(False)
        self._show_error(message)

    def _show_error(self, message: str):
        self.status_label.config(text=f"\u26a0 {message}", fg=self.theme["error"])

    def _render_current_weather(self, weather):
        self.city_label.config(text=f"{weather.city}, {weather.country}")
        self.datetime_label.config(text=utils.current_datetime_string())

        if getattr(self, "_current_icon_image", None):
            self.icon_label.config(image=self._current_icon_image)

        temp = weather.temp_c if self.unit == "C" else weather.temp_f
        feels = weather.feels_like_c if self.unit == "C" else weather.feels_like_f
        self.temp_label.config(text=f"{temp:.1f}\u00b0{self.unit}")
        self.condition_label.config(text=f"{weather.condition} \u2014 {weather.description}")
        self.feels_like_label.config(text=f"Feels like {feels:.1f}\u00b0{self.unit}")

        wind_display = f"{weather.wind_speed:.1f} m/s"
        sunrise = utils.format_unix_time(weather.sunrise_unix, weather.timezone_offset)
        sunset = utils.format_unix_time(weather.sunset_unix, weather.timezone_offset)

        values = {
            "humidity": f"{weather.humidity}%",
            "wind": wind_display,
            "pressure": f"{weather.pressure} hPa",
            "visibility": f"{weather.visibility_km} km",
            "sunrise": sunrise,
            "sunset": sunset,
        }
        for key, (_cell, _header, value_label) in self._detail_value_labels.items():
            value_label.config(text=values.get(key, "--"))

    def _render_forecast(self, forecast_days):
        # Clear any previously rendered forecast cells
        for cell in self.forecast_cells:
            cell.destroy()
        self.forecast_cells = []

        for index, day in enumerate(forecast_days):
            cell = tk.Frame(self.forecast_frame, bg=self.theme["card_bg"], padx=8, pady=8)
            cell.grid(row=0, column=index, sticky="nsew", padx=3)
            self.forecast_frame.grid_columnconfigure(index, weight=1)

            tk.Label(
                cell, text=day.date_label[5:], font=config.FONTS["small"],
                bg=self.theme["card_bg"], fg=self.theme["subtext"],
            ).pack()

            max_t = day.max_temp_c if self.unit == "C" else day.max_temp_f
            min_t = day.min_temp_c if self.unit == "C" else day.min_temp_f
            tk.Label(
                cell, text=f"{max_t:.0f}\u00b0/{min_t:.0f}\u00b0", font=config.FONTS["body"],
                bg=self.theme["card_bg"], fg=self.theme["text"],
            ).pack()

            tk.Label(
                cell, text=day.condition, font=config.FONTS["small"],
                bg=self.theme["card_bg"], fg=self.theme["subtext"],
            ).pack()

            self.forecast_cells.append(cell)

    def _refresh_recent_searches_menu(self, searches=None):
        if searches is None:
            searches = utils.load_recent_searches(self.recent_searches_path)

        menu = self.recent_menu["menu"]
        menu.delete(0, "end")
        menu.add_command(label="Recent", command=lambda: self.recent_var.set("Recent"))
        for city in searches:
            menu.add_command(label=city, command=lambda c=city: self._on_recent_selected(c))

    # =========================================================================
    # THEME APPLICATION
    # =========================================================================

    def _apply_theme(self):
        """Re-color every widget after a theme switch."""
        t = self.theme
        self.configure(bg=t["bg"])
        self.title_label.config(bg=t["bg"], fg=t["text"])
        self.theme_button.config(bg=t["bg"], fg=t["primary"])
        self.unit_button.config(bg=t["bg"], fg=t["primary"])
        self.status_label.config(bg=t["bg"])
        self.footer_label.config(bg=t["bg"], fg=t["subtext"])

        for widget in (self.card, self.icon_label):
            widget.config(bg=t["card_bg"])
        self.city_label.config(bg=t["card_bg"], fg=t["text"])
        self.datetime_label.config(bg=t["card_bg"], fg=t["subtext"])
        self.temp_label.config(bg=t["card_bg"], fg=t["primary"])
        self.condition_label.config(bg=t["card_bg"], fg=t["subtext"])
        self.feels_like_label.config(bg=t["card_bg"], fg=t["subtext"])

        self.details_frame.config(bg=t["bg"])
        for _key, (cell, header, value_label) in self._detail_value_labels.items():
            cell.config(bg=t["card_bg"])
            header.config(bg=t["card_bg"], fg=t["subtext"])
            value_label.config(bg=t["card_bg"], fg=t["text"])

        self.forecast_frame.config(bg=t["bg"])
        for cell in self.forecast_cells:
            cell.config(bg=t["card_bg"])
            for child in cell.winfo_children():
                child.config(bg=t["card_bg"])

        self.city_entry.config(bg=t["entry_bg"], fg=t["text"], insertbackground=t["text"])
        self.search_button.config(bg=t["primary"], activebackground=t["primary_hover"])
        self.refresh_button.config(bg=t["bg"], fg=t["primary"])
        self.recent_menu.config(bg=t["bg"], fg=t["subtext"])


def main():
    """Application entry point."""
    app = WeatherApp()
    app.mainloop()


if __name__ == "__main__":
    main()