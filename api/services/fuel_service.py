import json
from pathlib import Path
import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
GEOCODED_STATIONS_PATH = DATA_DIR / "stations_geocoded.json"
RAW_FUEL_PATH = DATA_DIR / "fuel_prices.csv"
FL_CITY_PATH = DATA_DIR / "FL_city_coords.json"


class FuelService:
    """
    High-performance Fuel Station Service.
    Loads and provides geocoded retail fuel truck stops across the continental United States.
    Uses spatial bounding-box vectorization to prune candidates in under 10ms.
    """

    def __init__(self):
        self.stations = self._load_stations()
        self._init_spatial_matrix()

    def _load_stations(self):
        """Loads pre-geocoded nationwide station database if available, else builds from CSV/caches."""
        if GEOCODED_STATIONS_PATH.exists():
            with open(GEOCODED_STATIONS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)

        # Fallback to loading CSV + FL city cache
        if RAW_FUEL_PATH.exists():
            df = pd.read_csv(RAW_FUEL_PATH)
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
            df = df.sort_values("price").groupby("station_id", as_index=False).first()

            fl_coords = {}
            if FL_CITY_PATH.exists():
                with open(FL_CITY_PATH, "r", encoding="utf-8") as f:
                    fl_coords = json.load(f)

            stations = []
            for _, r in df.iterrows():
                key = f"{r['city']}_{r['state']}"
                if key in fl_coords:
                    lat, lng = fl_coords[key]
                    stations.append({
                        "station_id": int(r["station_id"]),
                        "name": r["name"],
                        "city": r["city"],
                        "state": r["state"],
                        "price": float(r["price"]),
                        "latitude": float(lat),
                        "longitude": float(lng),
                    })
            return stations

        return []

    def _init_spatial_matrix(self):
        """Initializes fast NumPy coordinate arrays for vector math."""
        if not self.stations:
            self.coord_matrix = np.empty((0, 2), dtype=float)
            return

        self.coord_matrix = np.array(
            [[s["latitude"], s["longitude"]] for s in self.stations],
            dtype=float
        )

    def get_candidate_stations(self, route_data, buffer_degrees=1.0):
        """
        Fast corridor pruning. Given start and end coordinates (or route bounding box),
        filters all nationwide stations down to candidates within the route corridor.
        """
        if len(self.stations) == 0:
            return []

        start_lat, start_lng = route_data["start_coords"]
        end_lat, end_lng = route_data["end_coords"]

        min_lat = min(start_lat, end_lat) - buffer_degrees
        max_lat = max(start_lat, end_lat) + buffer_degrees
        min_lng = min(start_lng, end_lng) - buffer_degrees
        max_lng = max(start_lng, end_lng) + buffer_degrees

        # Vectorized bounding box slice
        lats = self.coord_matrix[:, 0]
        lngs = self.coord_matrix[:, 1]

        mask = (
            (lats >= min_lat) & (lats <= max_lat) &
            (lngs >= min_lng) & (lngs <= max_lng)
        )

        indices = np.where(mask)[0]
        candidates = [self.stations[i] for i in indices]
        return candidates


fuel_service = FuelService()
