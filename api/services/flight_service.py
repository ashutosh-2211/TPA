import requests
import json
from functools import lru_cache
from config import config


# ---------- Utility: Load IATA data ----------
@lru_cache(maxsize=10)
def get_data_json():
    file_path = "IATA.json"
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------- Utility: Get IATA/ICAO code from city ----------
@lru_cache(maxsize=50)
def get_iata(city_name: str) -> str | None:
    data = get_data_json()
    for value in data.values():
        if value.get("city", "").lower() == city_name.lower():
            return value["iata"] or value["icao"]
    return None


# ---------- Main: Fetch flight data ----------
def get_flight_details(
    departure: str,
    arrival: str,
    outbound_date: str,
    is_round_trip: bool = False,
    return_date: str | None = None,
):
    """Fetches flight data from SearchAPI.io and saves the result to data.json"""

    url = config.flight_api_url
    departure_iata = get_iata(departure)
    arrival_iata = get_iata(arrival)

    if not departure_iata or not arrival_iata:
        print("❌ Invalid city names provided.")
        return

    # Start with base params from config
    params = config.default_params.copy()
    params.update({
        "departure_id": departure_iata,
        "arrival_id": arrival_iata,
        "outbound_date": outbound_date,
    })

    # Handle round trip logic cleanly
    if is_round_trip:
        params["flight_type"] = "round_trip"
        if return_date:
            params["return_date"] = return_date
        else:
            print("⚠️ Round trip selected, but return_date not provided.")

    headers = {
        "Authorization": f"Bearer {config.serp_key}"
    }

    print(f"🔍 Fetching flights: {departure_iata} → {arrival_iata} ({params['flight_type']})...")

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return

    data = response.json()

    # ✅ Save to JSON
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✅ Flight data saved to data.json")

    # Print short summary
    for flight in data.get("best_flights", []):
        print("-", flight.get("price"), "INR")


# ---------- Parser: Read saved JSON ----------
def parse_flight_data(file_path="data.json"):
    """Reads flight data from a JSON file and prints a readable summary."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("❌ Unable to read valid JSON file.")
        return

    flights_list = data.get("other_flights", []) or data.get("best_flights", [])
    if not flights_list:
        print("⚠️ No flight data found in JSON.")
        return

    print("\n✈️ Flights Found:\n")
    for idx, flight in enumerate(flights_list, 1):
        price = flight.get("price", "N/A")
        duration = flight.get("total_duration", "N/A")
        segments = flight.get("flights", [])
        print(f"🟦 Option {idx}: ₹{price} | Duration: {duration} min")

        for seg in segments:
            dep = seg.get("departure_airport", {}).get("id")
            arr = seg.get("arrival_airport", {}).get("id")
            airline = seg.get("airline", "Unknown")
            flight_num = seg.get("flight_number", "N/A")
            print(f"   🛫 {dep} → {arr} | {airline} {flight_num}")

        print()

    print("✅ Done parsing flight data.")


# ---------- Entry point ----------
if __name__ == "__main__":
    get_flight_details(
        departure="Mumbai",
        arrival="Bhubaneswar",
        outbound_date="2025-12-10",
        return_date="2026-02-10",
        is_round_trip=True
    )
    parse_flight_data()
