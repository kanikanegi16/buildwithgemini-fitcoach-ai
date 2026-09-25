# app/maps_tools.py
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path


def _get_api_key() -> str:
    """Reads the GOOGLE_MAPS_API_KEY from environment or .env file."""
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        env_path = Path(__file__).resolve().parent.parent / ".env"
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GOOGLE_MAPS_API_KEY="):
                        api_key = line.split("=", 1)[1].strip()
                        os.environ["GOOGLE_MAPS_API_KEY"] = api_key
                        break
    if not api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY is missing from environment or .env file.")
    return api_key


def geocode_address(address: str) -> dict:
    """Converts a street address, city, or landmark into geographical coordinates (latitude and longitude).

    Args:
        address: The address or location name to geocode (e.g. 'Golden Gate Park, San Francisco').

    Returns:
        A dictionary containing formatted address and location coordinates (latitude and longitude).
    """
    try:
        api_key = _get_api_key()
        encoded_address = urllib.parse.quote(address)
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if data.get("status") == "OK" and data.get("results"):
            top_result = data["results"][0]
            loc = top_result["geometry"]["location"]
            return {
                "address": address,
                "formatted_address": top_result.get("formatted_address"),
                "location": {
                    "latitude": loc["lat"],
                    "longitude": loc["lng"],
                },
            }
        return {"error": f"Geocoding failed for address '{address}': {data.get('status')}"}
    except Exception as e:
        return {"error": f"Geocoding API error: {str(e)}"}


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "fitness_center",
    radius_meters: float = 2000.0,
) -> list[dict]:
    """Finds nearby places of interest (e.g. gyms, parks, fitness centers, sports complexes) using Google Places API (New).

    Args:
        latitude: Latitude of center location.
        longitude: Longitude of center location.
        place_type: Type of place to search for (e.g. 'fitness_center', 'gym', 'park', 'sports_complex').
        radius_meters: Search radius in meters (default is 2000m).

    Returns:
        A list of nearby places containing name, address, location coordinates, and primary type.
    """
    try:
        api_key = _get_api_key()
        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.primaryType",
        }

        # Normalize place_type into list
        included_types = [place_type]
        if place_type == "gym" and "fitness_center" not in included_types:
            included_types.append("fitness_center")

        body = {
            "includedTypes": included_types,
            "maxResultCount": 10,
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": latitude,
                        "longitude": longitude,
                    },
                    "radius": float(radius_meters),
                }
            },
        }

        req = urllib.request.Request(
            url, data=json.dumps(body).encode("utf-8"), headers=headers
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        places_result = []
        for p in data.get("places", []):
            name = p.get("displayName", {}).get("text", "Unknown Place")
            addr = p.get("formattedAddress", "N/A")
            loc = p.get("location", {})
            places_result.append(
                {
                    "name": name,
                    "address": addr,
                    "location": {
                        "latitude": loc.get("latitude"),
                        "longitude": loc.get("longitude"),
                    },
                    "primary_type": p.get("primaryType", place_type),
                }
            )

        return places_result
    except Exception as e:
        return [{"error": f"Places API (New) error: {str(e)}"}]
