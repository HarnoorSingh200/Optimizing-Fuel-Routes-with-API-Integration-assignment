import pandas as pd
import json
from pathlib import Path
from api.services.routing_service import routing_service

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "fuel_prices.csv"
CACHE_PATH = Path(__file__).resolve().parents[2] / "data" / "geocode_cache.json"
CITY_CACHE_PATH = Path(__file__).resolve().parents[2] / "data" / "FL_city_coords.json"

TARGET_STATE = "FL"
USE_STATE_CACHE = True  # demo mode


class FuelService:
    def __init__(self):
        self.df = self._load_data()
        self.cache = self._load_cache()
        self.city_cache = self._load_city_cache()

    # Load dataset
    def _load_data(self):
        df = pd.read_csv(DATA_PATH)

        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        df = df.rename(
            columns={
                "opis_truckstop_id": "station_id",
                "truckstop_name": "name",
                "retail_price": "price",
            }
        )

        df = df.dropna(subset=["price"])
        df["price"] = df["price"].astype(float)

        df = (
            df.sort_values("price")
            .groupby("station_id", as_index=False)
            .first()
        )

        return df

    # Load station geocode cache
    def _load_cache(self):
        if CACHE_PATH.exists():
            with open(CACHE_PATH, "r") as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        with open(CACHE_PATH, "w") as f:
            json.dump(self.cache, f)

    # Load Florida city cache (only for demo)
    def _load_city_cache(self):
        if CITY_CACHE_PATH.exists():
            with open(CITY_CACHE_PATH, "r") as f:
                return json.load(f)
        return {}

    # get geocode
    def _get_coords(self, address):
        if address in self.cache:
            cached = self.cache[address]
            if cached is None:
                return None, None
            return tuple(cached)

        try:
            lat, lng = routing_service.geocode(address)
            self.cache[address] = (lat, lng)
            self._save_cache()
            return lat, lng
        except Exception:
            self.cache[address] = None
            self._save_cache()
            return None, None

    # Fetch station
    def get_candidate_stations(self, route_data):
        stations = []

        # DEMO MODE — Florida only
        if USE_STATE_CACHE:
            df_state = self.df[self.df["state"] == TARGET_STATE]

            for _, row in df_state.iterrows():
                key = f"{row['city']}_{row['state']}"
                coords = self.city_cache.get(key)

                if not coords:
                    continue

                lat, lng = coords

                stations.append({
                    "station_id": row["station_id"],
                    "name": row["name"],
                    "price": row["price"],
                    "latitude": lat,
                    "longitude": lng,
                })

            return stations

        # FULL PIPELINE — nationwide, use bounding box to filter out relevant stations only
        start_lat, start_lng = route_data["start_coords"]
        end_lat, end_lng = route_data["end_coords"]

        buffer = 3

        min_lat = min(start_lat, end_lat) - buffer
        max_lat = max(start_lat, end_lat) + buffer
        min_lng = min(start_lng, end_lng) - buffer
        max_lng = max(start_lng, end_lng) + buffer

        for _, row in self.df.iterrows():
            address = f"{row['address']}, {row['city']}, {row['state']}, USA"

            lat, lng = self._get_coords(address)

            if lat is None or lng is None:
                continue

            if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
                stations.append({
                    "station_id": row["station_id"],
                    "name": row["name"],
                    "price": row["price"],
                    "latitude": lat,
                    "longitude": lng,
                })

        return stations


fuel_service = FuelService()
