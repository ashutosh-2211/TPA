import httpx
import json
import logging

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


async def get_hotel_details(check_in_date: str, check_out_date: str, q: str):
    """Fetches hotel data from SearchAPI.io"""
    base_url: str = config.base_api_url
    hotel_params: dict = config.default_hotel_params.copy()
    headers = {
        "Authorization": f"Bearer {config.serp_key}"
    }

    hotel_params.update({
        "q": q,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date
    })
    
    logger.info("🏨 HOTEL SERVICE: get_hotel_details called")
    logger.info(f"   Location: {q}")
    logger.info(f"   Check-in: {check_in_date}, Check-out: {check_out_date}")
    
    try:
        client = get_http_client()
        response = await client.get(url=base_url, headers=headers, params=hotel_params)
        
        if response.status_code == 200:
            hotel_data = response.json()
            with open('hotel_data.json', 'w') as f:
                json.dump(hotel_data, f, indent=2)
            logger.info(f"   ✅ Found {len(hotel_data.get('properties', []))} hotels")
            return hotel_data
        else:
            logger.error(f"   ❌ API returned status code: {response.status_code}")
            return None
    except httpx.HTTPError as e:
        logger.error(f"   ❌ Request failed: {e}", exc_info=True)
        print(e)
        return None
    
def parse_hotel_json(data: dict) -> tuple[str, dict]:
    """
    Returns (toon_string, full_data_dict)
    - toon_string: Lightweight format for LLM reasoning
    - full_data_dict: Complete hotel data with images, GPS, offers for UI
    """
    properties = data.get('properties', [])

    # TOON: Compact format for agent to analyze and filter
    property_toon = f"""properties [{len(properties)}] {{idx, name, city, country, price_per_night, total_price, rating, reviews, location_rating, amenities_summary}}\n"""

    # Full data: Everything the UI will need
    full_data = {'properties': []}

    for idx, p in enumerate(properties, 1):
        # Extract amenities summary for TOON
        amenities = p.get("amenities", [])
        if len(amenities) == 0:
            amenities_summary = "None"
        elif len(amenities) <= 3:
            amenities_summary = ", ".join(amenities)
        else:
            amenities_summary = f"{', '.join(amenities[:2])}, +{len(amenities)-2} more"

        # Extract prices
        price_per_night = p.get("price_per_night", {}).get("extracted_price_before_taxes", "N/A")
        total_price = p.get("total_price", {}).get("extracted_price_before_taxes", "N/A")

        # TOON line: Only essentials for comparison
        property_toon += f"\t\t{idx},{p.get('name', 'N/A')},{p.get('city', 'N/A')},{p.get('country', 'N/A')},{price_per_night},{total_price},{p.get('rating', 0.0)},{p.get('reviews', 0)},{p.get('location_rating', 0.0)},{amenities_summary}\n"

        # Full data: Complete information including images, GPS, offers
        full_data['properties'].append({
            "idx": idx,  # For agent to reference this hotel
            "type": p.get("type", ""),
            "name": p.get("name", ""),
            "gps_coordinates": p.get("gps_coordinates", {}),
            "city": p.get("city", ""),
            "country": p.get("country", ""),
            "check_in_time": p.get("check_in_time", ""),
            "check_out_time": p.get("check_out_time", ""),
            "price_per_night": p.get("price_per_night", {}),
            "total_price": p.get("total_price", {}),
            "offers": p.get("offers", []),
            "rating": p.get("rating", 0.0),
            "reviews": p.get("reviews", 0),
            "location_rating": p.get("location_rating", 0.0),
            "proximity_to_transit_rating": p.get("proximity_to_transit_rating", 0.0),
            "airport_access_rating": p.get("airport_access_rating", 0.0),
            "amenities": amenities,
            "essential_info": p.get("essential_info", []),
            "images": p.get("images", [])
        })

    return property_toon, full_data

def print_parsed_info(parsed_data: dict):
    print("=="*5,"PROPERTIES","=="*5)
    print(f"Found properties: {len(parsed_data['properties'])}")
    for p in parsed_data["properties"]:
        print(f"Property: {p['name']},{p['city']} Rating: {p['rating']}/({p['reviews']})")
        print(f"Check in time: {p['check_in_time']}")
        print(f"Check out time: {p['check_out_time']}")
        print(f"Per night cost: {p['price_per_night']}, Total Price: {p['total_price']}")
        print("\n","--"*5,"\n")

    

if __name__ == "__main__":
    import asyncio
    
    async def test():
        data = await get_hotel_details(
            check_in_date="2025-12-13",
            check_out_date="2025-12-15",
            q="a beach side hotel room in bali"
        )
        
        if data:
            toon, full_data = parse_hotel_json(data)
            print("\n=== TOON FORMAT (for Agent) ===")
            print(toon)
            print("\n=== FULL DATA (for UI) ===")
            print_parsed_info(full_data)
        
        await close_http_client()
    
    asyncio.run(test())

    