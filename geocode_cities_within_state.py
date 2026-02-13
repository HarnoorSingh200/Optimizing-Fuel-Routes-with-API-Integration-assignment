import pandas as pd
import json
from api.services.routing_service import routing_service

STATE = "FL"

df = pd.read_csv(f"data/{STATE}_cities.csv")

city_cache = {}

for _, row in df.iterrows():
    city = row["city"]
    key = f"{city}_{STATE}"
    location = f"{city}, {STATE}, USA"

    try:
        lat, lng = routing_service.geocode(location)
        city_cache[key] = [lat, lng]
        print("Geocoded:", key)
    except Exception:
        print("Failed:", key)

with open(f"data/{STATE}_city_coords.json", "w") as f:
    json.dump(city_cache, f)

print("Saved city coordinates")
