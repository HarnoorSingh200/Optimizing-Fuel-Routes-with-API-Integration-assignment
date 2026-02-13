import requests
from django.conf import settings

ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"


class RoutingService:
    def __init__(self):
        self.api_key = settings.ORS_API_KEY

    def geocode(self, location):
        url = "https://api.openrouteservice.org/geocode/search"

        params = {
            "api_key": self.api_key,
            "text": location,
            "size": 1
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()

        if not data["features"]:
            raise ValueError(f"Could not geocode location: {location}")

        coords = data["features"][0]["geometry"]["coordinates"]
        # ORS returns [lng, lat]
        return coords[1], coords[0]

    def get_route(self, start, end):
        """Returns route info between start and end """
        start_lat, start_lng = self.geocode(start)
        end_lat, end_lng = self.geocode(end)

        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }

        body = {
            "coordinates": [
                [start_lng, start_lat],
                [end_lng, end_lat]
            ]
        }

        response = requests.post(ORS_URL, json=body, headers=headers)
        response.raise_for_status()

        data = response.json()

        route = data["routes"][0]

        distance_meters = route["summary"]["distance"]
        distance_miles = distance_meters * 0.000621371

        geometry = route["geometry"]

        return {
            "distance_miles": round(distance_miles, 2),
            "geometry": geometry,
            "start_coords": (start_lat, start_lng),
            "end_coords": (end_lat, end_lng),
        }

routing_service = RoutingService()
