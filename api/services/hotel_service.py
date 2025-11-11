import requests
import json
from functools import lru_cache
from typing import List

from config import config

@lru_cache(maxsize=10)
def get_hotel_details(check_in_date: str, check_out_date: str, q: str):
    base_url: str = config.base_api_url
    hotel_params : dict = config.default_hotel_params.copy()
    headers = {
        "Authorization": f"Bearer {config.serp_key}"
    }

    hotel_params.update({
        "q": q,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date
    })
    # print(hotel_params)
    try:
        response = requests.get(url=base_url, headers=headers, params=hotel_params)
        if response.status_code == 200:
            hotel_data = response.json()
            with open('hotel_data.json','w') as f:
                json.dump(hotel_data,f,indent=2)
            # print(list(hotel_data.keys()))
            return hotel_data
    except Exception as e:
        print(e)
        return None
    
def parse_hotel_json(data: dict)->dict:
    parsed_dict: dict[List] = {'properties':[]}
    properties = data['properties']
    for p in properties:
        prop: dict = {
            "type": p.get("type", ""),
            "name": p.get("name", ""),
            "gps_coordinates": p.get("gps_coordinates", {}),
            "city": p.get("city", ""),
            "country": p.get("country", ""),
            "check_in_time": p.get("check_in_time", ""),
            "check_out_time": p.get("check_out_time", ""),
            "price_per_night": p.get("price_per_night", {}).get("extracted_price_before_taxes", ""),
            "total_price": p.get("total_price", {}).get("extracted_price_before_taxes", ""),
            "offers": p.get("offers", []),
            "rating": p.get("rating", 0.0),
            "reviews": p.get("reviews", 0),
            "location_rating": p.get("location_rating", 0.0),
            "proximity_to_transit_rating": p.get("proximity_to_transit_rating", 0.0),
            "airport_access_rating": p.get("airport_access_rating", 0.0),
            "amenities": p.get("amenities", []),
            "essential_info": p.get("essential_info", []),
            "images": p.get("images", [])
        }
        parsed_dict["properties"].append(prop)
    return parsed_dict

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
    data = get_hotel_details(
        check_in_date = "2025-11-11",
        check_out_date = "2025-11-13",
        q = "a beach side hotel room in puri"
    )
    # with open('hotel_data.json', 'r') as f:
    #     data = json.loads(f.read())

    print_parsed_info(parse_hotel_json(data))

    