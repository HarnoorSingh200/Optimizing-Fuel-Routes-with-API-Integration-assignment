import math
import polyline
from geopy.distance import geodesic


MAX_RANGE_MILES = 400
MPG = 10
SEARCH_RADIUS_MILES = 20


class OptimizationService:

    def decode_route(self, geometry):
        return polyline.decode(geometry)

    def distance(self, p1, p2):
        """haversine approximation: Fast haversine distance in miles"""

        lat1, lon1 = p1
        lat2, lon2 = p2

        R = 3958.8  # Earth radius in miles

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (
                math.sin(dlat / 2) ** 2
                + math.cos(math.radians(lat1))
                * math.cos(math.radians(lat2))
                * math.sin(dlon / 2) ** 2
        )

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def cumulative_distances(self, route_points):
        distances = [0]
        for i in range(1, len(route_points)):
            d = self.distance(route_points[i - 1], route_points[i])
            distances.append(distances[-1] + d)
        return distances

    def stations_near_route(self, route_points, stations):
        near = []
        for station in stations:
            sp = (station["latitude"], station["longitude"])
            for rp in route_points:
                if self.distance(sp, rp) <= SEARCH_RADIUS_MILES:
                    near.append(station)
                    break
        return near

    def find_optimal_stops(self, route_points, cumulative_dist, stations):
        stops = []
        last_stop_distance = 0
        current_range_end = MAX_RANGE_MILES
        total_route_distance = cumulative_dist[-1]

        while current_range_end < total_route_distance:
            candidates = []

            for station in stations:
                sp = (station["latitude"], station["longitude"])

                for i, rp in enumerate(route_points):
                    if self.distance(sp, rp) <= SEARCH_RADIUS_MILES:
                        station_distance = cumulative_dist[i]

                        if last_stop_distance < station_distance <= current_range_end:
                            candidates.append((station_distance, station))
                        break

            if not candidates:
                break

            best_distance, best_station = min(
                candidates, key=lambda x: x[1]["price"]
            )

            stops.append(best_station)
            last_stop_distance = best_distance
            current_range_end = last_stop_distance + MAX_RANGE_MILES

        return stops

    def calculate_total_cost(self, total_distance, stops):
        fuel_needed = total_distance / MPG
        avg_price = (
            sum(s["price"] for s in stops) / len(stops)
            if stops else 3.5
        )
        return round(fuel_needed * avg_price, 2)

    def optimize(self, route_data, stations):
        route_points = self.decode_route(route_data["geometry"])
        cumulative_dist = self.cumulative_distances(route_points)

        near_stations = self.stations_near_route(route_points, stations)
        stops = self.find_optimal_stops(route_points, cumulative_dist, near_stations)

        total_cost = self.calculate_total_cost(route_data["distance_miles"], stops)

        return {
            "distance_miles": route_data["distance_miles"],
            "stops": stops,
            "total_cost": total_cost,
        }


optimization_service = OptimizationService()
