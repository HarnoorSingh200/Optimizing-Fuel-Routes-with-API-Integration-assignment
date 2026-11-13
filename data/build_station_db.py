import json
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent

def build_station_database():
    fuel_path = DATA_DIR / "fuel_prices.csv"
    cities_path = DATA_DIR / "us_cities.csv"
    cache_path = DATA_DIR / "geocode_cache.json"
    fl_cache_path = DATA_DIR / "FL_city_coords.json"
    output_path = DATA_DIR / "stations_geocoded.json"

    print("Loading datasets...")
    df_fuel = pd.read_csv(fuel_path)
    df_fuel.columns = [c.strip().lower().replace(" ", "_") for c in df_fuel.columns]
    df_fuel = df_fuel.rename(
        columns={
            "opis_truckstop_id": "station_id",
            "truckstop_name": "name",
            "retail_price": "price",
        }
    )
    df_fuel = df_fuel.dropna(subset=["price"])
    df_fuel["price"] = df_fuel["price"].astype(float)
    # Deduplicate keeping cheapest price per station
    df_fuel = df_fuel.sort_values("price").groupby("station_id", as_index=False).first()

    # Load US cities lookup
    city_lookup = {}
    if cities_path.exists():
        df_cities = pd.read_csv(cities_path)
        for _, r in df_cities.iterrows():
            k = (str(r["CITY"]).strip().lower(), str(r["STATE_CODE"]).strip().upper())
            if k not in city_lookup:
                city_lookup[k] = (float(r["LATITUDE"]), float(r["LONGITUDE"]))

    # Load caches
    geocode_cache = {}
    if cache_path.exists():
        with open(cache_path, "r", encoding="utf-8") as f:
            geocode_cache = json.load(f)

    fl_cache = {}
    if fl_cache_path.exists():
        with open(fl_cache_path, "r", encoding="utf-8") as f:
            fl_cache = json.load(f)

    stations = []
    matched = 0

    for _, row in df_fuel.iterrows():
        sid = int(row["station_id"])
        name = str(row["name"]).strip()
        city = str(row["city"]).strip()
        state = str(row["state"]).strip().upper()
        price = float(row["price"])
        address = f"{row['address']}, {city}, {state}, USA"

        coord = None
        # 1. Address cache
        if address in geocode_cache and geocode_cache[address]:
            coord = geocode_cache[address]
        # 2. Florida cache
        elif f"{city}_{state}" in fl_cache and fl_cache[f"{city}_{state}"]:
            coord = fl_cache[f"{city}_{state}"]
        # 3. US cities DB
        elif (city.lower(), state) in city_lookup:
            coord = city_lookup[(city.lower(), state)]

        if coord:
            matched += 1
            stations.append({
                "station_id": sid,
                "name": name,
                "city": city,
                "state": state,
                "price": price,
                "latitude": float(coord[0]),
                "longitude": float(coord[1]),
            })

    print(f"Total unique stations: {len(df_fuel)}, Geocoded: {matched} ({matched/len(df_fuel)*100:.1f}%)")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(stations, f, indent=2)

    print(f"Saved {len(stations)} geocoded stations to {output_path}")

if __name__ == "__main__":
    build_station_database()
