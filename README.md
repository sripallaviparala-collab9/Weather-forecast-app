# Weather-forecast-app
A Python Weather Forecast App built with Tkinter and the OpenWeatherMap API to display real-time weather data with a modern, user-friendly interface.
📖 Project Overview

Weather Forecast App is a clean, well-structured Python project that
demonstrates practical skills in API integration, GUI development, and
object-oriented software design. Users can search for any city and instantly
view current conditions — temperature, humidity, wind, pressure, visibility,
sunrise/sunset — along with a 5-day outlook, all inside a responsive,
themeable interface.

The codebase is split into focused modules (config, utils, weather,
main) rather than one large script, following the same separation-of-concerns
principles used in production applications.


✨ Features

Core


🔍 Search weather for any city worldwide
🌡️ Current temperature with °C / °F toggle
🤔 "Feels like" temperature
💧 Humidity, 💨 wind speed, 📊 pressure, 👁️ visibility
🌅 Sunrise and 🌇 sunset times (localized to the city's timezone)
🖼️ Live weather condition icons
⏳ Non-blocking loading indicator (network calls run on a background thread)
⚠️ Graceful error handling for invalid cities, bad API keys, and network issues
📱 Responsive, resizable, card-based UI


Bonus


📅 5-day forecast strip
🌙 Dark mode / ☀️ light mode toggle
🕘 Recent searches (persisted locally to JSON, accessible from a dropdown)
🔁 One-click refresh of the current city
🖼️ Screenshots


Add your own screenshots after running the app locally and place them in
the screenshots/ folder, then reference them here, e.g.:

markdown![Light mode](screenshots/light-mode.png)
![Dark mode](screenshots/dark-mode.png)




🛠️ Installation Instructions

Prerequisites


Python 3.12 or newer
pip (Python package manager)
tkinter (included with most standard Python installations; on Linux you
may need sudo apt install python3-tk)


Steps


Clone the repository


bash   git clone https://github.com/<your-username>/weather-app.git
   cd weather-app


Create and activate a virtual environment (recommended)


bash   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS / Linux
   source venv/bin/activate


Install dependencies


bash   pip install -r requirements.txt


🔑 API Key Setup

This app uses the free OpenWeatherMap API.


Create a free account at https://home.openweathermap.org/users/sign_up
Navigate to API keys in your account dashboard and generate a key.

New keys can take a few minutes to a couple of hours to activate.




Provide the key to the app using one of these methods:
Option A — Environment variable (recommended, keeps your key out of git)


bash   # Windows (PowerShell)
   $env:OPENWEATHER_API_KEY="your_api_key_here"

   # macOS / Linux
   export OPENWEATHER_API_KEY="your_api_key_here"

Option B — Directly in code
Open config.py and set:

python   DEFAULT_API_KEY = "your_api_key_here"

⚠️ If you use Option B, make sure not to commit your real key to a public
repository.


▶️ Usage

Run the application from the project root:

bashpython main.py


Type a city name into the search box (e.g. London, Tokyo, New York).
Press Enter or click Search.
View current conditions, the 5-day forecast, and use the toolbar to:

Toggle °C / °F
Toggle Dark Mode
Refresh the current city
Reopen a Recent search from the dropdown
README


🚀 Future Improvements


 Hourly forecast graph (matplotlib or a custom Canvas chart)
 Favorite / pinned cities with a dedicated panel
 Auto-refresh weather on a timer
 Geolocation-based "weather near me"
 Unit tests with pytest and CI via GitHub Actions
 Packaged executable (PyInstaller) for easy distribution
 Multi-language support



📄 License

This project is licensed under the MIT License — see below.

MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.


👤 Author
**Sri Pallavi**
Built as a portfolio project to demonstrate Python, GUI development, REST
API integration, and clean software architecture.


