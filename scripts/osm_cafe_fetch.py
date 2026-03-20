import requests
import json

from plot_cafes_on_map import plot_map

OVERPASS_URL = "http://overpass-api.de/api/interpreter"

query = """
[out:json][timeout:60];
(
    node["amenity"="cafe"](55.594,12.450,55.760,12.700);
    way["amenity"="cafe"](55.594,12.450,55.760,12.700);
    rel["amenity"="cafe"](55.594,12.450,55.760,12.700);

    node["amenity"="coffee_shop"](55.594,12.450,55.760,12.700);
    way["amenity"="coffee_shop"](55.594,12.450,55.760,12.700);

    node["shop"="coffee"](55.594,12.450,55.760,12.700);
    way["shop"="coffee"](55.594,12.450,55.760,12.700);
);
out center;
"""


def run_overpass_query(query: str, retries:int=3):


    print("Sending Overpass query...")
    try:
        response = requests.get(OVERPASS_URL, params={'data': query})
        response.raise_for_status()
        print("Request successful!")
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"Request error: {e}")
        return None
    
def extract_relevant_fields(osm_json: dict):
    elements = osm_json.get("elements", [])
    cafes = []
    
    for el in elements:
        tags = el.get("tags", {})

        lat = el.get("lat")
        lon = el.get("lon")

        if lat is None or lon is None:
            center = el.get("center", {})
            lat = center.get("lat")
            lon = center.get("lon")
    
        cafe = {
            "OSM_ID" : el.get('id'),
            "OSM_TYPE" : el.get("type"),
            "LAT" : lat,
            "LON" : lon,
            "TAGS" : tags
            }
        cafes.append(cafe)
    return cafes
    
def main():
    response = run_overpass_query(query)
    cafes = extract_relevant_fields(response)
    with open("data/cafes_raw.json", "w", encoding="utf-8") as f:
        json.dump(cafes, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(cafes)} cafés")

    plot_map(cafes)

if __name__ == "__main__":
    main()