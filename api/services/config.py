# config.py
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv(override=True)

class Config(BaseSettings):
    serp_key: str = os.getenv("SEARCH_API_KEY")
    flight_api_url: str = "https://www.searchapi.io/api/v1/search"

    # Default parameters for Google Flights API
    default_params: dict = {
        "engine": "google_flights",     # Required
        "travel_class": "economy",      # economy | premium_economy | business | first_class
        "flight_type": "one_way",       # default, overridden for round_trip
        "gl": "IN",                     # Country code
        "hl": "en",                     # Language
        "currency": "INR",              # Currency code
        "stops": "any",                 # any | nonstop | one_stop_or_fewer | two_stops_or_fewer
        "sort_by": "price",             # price | duration | top_flights
        "adults": 1,
        "children": 0,
        "infants_on_lap": 0,
        "infants_in_seat": 0,
    }

config = Config()
