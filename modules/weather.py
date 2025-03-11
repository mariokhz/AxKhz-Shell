import gi
import requests
import threading
import urllib.parse
from gi.repository import Gtk, GLib

from fabric.widgets.label import Label
from fabric.widgets.box import Box

gi.require_version("Gtk", "3.0")

import modules.icons as icons

class Weather(Box):
    def __init__(self, **kwargs) -> None:
        super().__init__(name="weather", orientation="h", spacing=8, **kwargs)
        self.label = Label(name="weather-label", markup=icons.loader)
        self.add(self.label)
        self.show_all()
        # Update every 10 mins
        GLib.timeout_add_seconds(600, self.fetch_weather)
        self.fetch_weather()

    def get_location(self):
        try:
            response = requests.get("https://ipinfo.io/json")
            if response.status_code == 200:
                data = response.json()
                return data.get("city", "")
            else:
                print("Error getting location from ipinfo.")
        except Exception as e:
            print(f"Error getting location: {e}")
        return ""

    def fetch_weather(self):
        threading.Thread(target=self._fetch_weather_thread, daemon=True).start()
        return True

    def _fetch_weather_thread(self):
        location = self.get_location()
        if location == "Madrid":
            location = "Valencia"
        if location:
            # URL encode the location to make it URL friendly.
            encoded_location = urllib.parse.quote(location)
            url = f"https://wttr.in/{encoded_location}?format=%c+%t"
        else:
            url = "https://wttr.in/?format=%c+%t"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                weather_data = response.text.strip()
                GLib.idle_add(self.label.set_label, weather_data.replace(" ", ""))
            else:
                GLib.idle_add(self.label.set_markup, f"{icons.cloud_off} Unavailable")
                self.set_visible(False)
        except Exception as e:
            print(f"Error fetching weather: {e}")
            GLib.idle_add(self.label.set_markup, f"{icons.cloud_off} Error")
            self.set_visible(False)
