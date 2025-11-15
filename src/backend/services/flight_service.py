import httpx
import json
import logging
from functools import lru_cache

try:
    from .config import config
except ImportError:
    from config import config

# Configure logging
logger = logging.getLogger(__name__)

# Create a shared httpx client for connection pooling
_http_client = None


def get_http_client() -> httpx.AsyncClient:
    """Get or create the shared HTTP client"""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=30.0)
    return _http_client


async def close_http_client():
    """Close the shared HTTP client"""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


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
async def get_flight_details(
    departure: str,
    arrival: str,
    outbound_date: str,
    is_round_trip: bool = False,
    return_date: str | None = None,
):
    """Fetches flight data from SearchAPI.io and saves the result to data.json"""

    url = config.base_api_url

    logger.info("🌐 FLIGHT SERVICE: get_flight_details called")
    logger.info("   Input Parameters:")
    logger.info(f"      departure city: {departure}")
    logger.info(f"      arrival city: {arrival}")
    logger.info(f"      outbound_date: {outbound_date}")
    logger.info(f"      is_round_trip: {is_round_trip}")
    logger.info(f"      return_date: {return_date}")

    departure_iata = get_iata(departure)
    arrival_iata = get_iata(arrival)

    logger.info("   IATA Code Conversion:")
    logger.info(f"      {departure} → {departure_iata}")
    logger.info(f"      {arrival} → {arrival_iata}")

    if not departure_iata or not arrival_iata:
        logger.error("   ❌ Failed to convert city names to IATA codes")
        logger.error(f"      departure_iata: {departure_iata}, arrival_iata: {arrival_iata}")
        print("❌ Invalid city names provided.")
        return None

    # Start with base params from config
    params = config.default_flight_params.copy()
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
            logger.warning("⚠️ Round trip selected, but return_date not provided.")
            print("⚠️ Round trip selected, but return_date not provided.")

    headers = {
        "Authorization": f"Bearer {config.serp_key}"
    }

    logger.info("   📡 Making API Request:")
    logger.info(f"      URL: {url}")
    logger.info(f"      Full Params: {json.dumps(params, indent=2)}")
    logger.info(f"      Headers: Authorization: Bearer {config.serp_key[:20]}...")

    print(f"🔍 Fetching flights: {departure_iata} → {arrival_iata} ({params['flight_type']})...")

    try:
        client = get_http_client()
        response = await client.get(url, headers=headers, params=params)
        
        logger.info("   📥 API Response:")
        logger.info(f"      Status Code: {response.status_code}")
        logger.info(f"      Response Headers: {dict(response.headers)}")

        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as e:
        logger.error(f"   ❌ API Request failed: {e}", exc_info=True)
        print(f"❌ Request failed: {e}")
        return None

    logger.info("   ✅ Response received successfully")
    logger.info(f"      Response keys: {list(data.keys())}")
    logger.info(f"      Response preview: {json.dumps(data, indent=2)[:500]}...")

    # ✅ Save to JSON
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✅ Flight data saved to data.json")

    return data


# ---------- Parser: Read saved JSON ----------
def parse_flight_data_to_toon(flight_data: dict) -> tuple[str, dict]:
    """
    Returns (toon_string, full_data_dict)
    - toon_string: Lightweight format for LLM reasoning
    - full_data_dict: Complete flight data with all details for UI
    """
    flights_list = flight_data.get("other_flights", []) or flight_data.get("best_flights", [])
    if not flights_list:
        # Return empty results
        return "No flights found.", {"flights": []}
    
    toon_response = f"""flights [{len(flights_list)}] {{idx, price, duration, stops, departure, arrival, airline, flight_num}}
    """

    # Build full data structure for UI
    full_data = {
        "flights": [],
        "search_metadata": flight_data.get("search_metadata", {}),
        "search_parameters": flight_data.get("search_parameters", {}),
        "price_insights": flight_data.get("price_insights", {}),
        "airports": flight_data.get("airports", [])
    }

    for idx, flight in enumerate(flights_list, 1):
        price = flight.get("price", "N/A")
        duration = flight.get("total_duration", "N/A")
        segments = flight.get("flights", [])
        stops = len(segments) - 1  # Number of stops = segments - 1
        
        # Store full flight data
        full_data["flights"].append({
            "idx": idx,
            "price": price,
            "duration": duration,
            "stops": stops,
            "segments": segments,
            "carbon_emissions": flight.get("carbon_emissions", {}),
            "booking_token": flight.get("booking_token", ""),
            "raw_data": flight  # Keep original data
        })
        
        # Build TOON format (compact for LLM)
        for seg in segments:
            dep = seg.get("departure_airport", {}).get("id", "N/A")
            arr = seg.get("arrival_airport", {}).get("id", "N/A")
            airline = seg.get("airline", "Unknown")
            flight_num = seg.get("flight_number", "N/A")
            toon_response += f"\t\t{idx},{price},{duration},{stops},{dep},{arr},{airline},{flight_num}\n"

    return toon_response, full_data


# ---------- Entry point ----------
if __name__ == "__main__":
    import asyncio
    
    async def test():
        data = await get_flight_details(
            departure="Mumbai",
            arrival="Bhubaneswar",
            outbound_date="2025-12-10",
            is_round_trip=False
        )
        if data:
            toon, full_data = parse_flight_data_to_toon(data)
            print(toon)
            print(f"\nFull data contains {len(full_data.get('flights', []))} flights")
        await close_http_client()
    
    asyncio.run(test())
