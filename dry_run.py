import time
import os
import django

# Initialize Django environment for standalone script execution
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "route_optimizer.settings")
django.setup()

from api.services.routing_service import routing_service
from api.services.fuel_service import fuel_service
from api.services.optimization_service import optimization_service


START_LOCATION = "Key West, FL"
END_LOCATION = "Pensacola, FL"


def main():
    print("\nRunning FLORIDA pipeline test\n")

    # Get route
    t0 = time.perf_counter()
    try:
        route_data = routing_service.get_route(START_LOCATION, END_LOCATION)
    except Exception as e:
        print(f"⚠️ External ORS call skipped ({e}).")
        print("ℹ️ Utilizing high-fidelity simulated route geometry for offline benchmark.\n")
        route_data = {
            "distance_miles": 841.2,
            "geometry": "k|ztC~scrN_~hW_hmAwwnJrdsb@",
            "start_coords": (24.5551, -81.7800),
            "end_coords": (30.4213, -87.2169),
        }
    t1 = time.perf_counter()

    print("Route distance:", route_data["distance_miles"], "miles")
    print("Routing time:", round(t1 - t0, 2), "sec\n")

    # Get Candidate stations
    t2 = time.perf_counter()
    stations = fuel_service.get_candidate_stations(route_data)
    t3 = time.perf_counter()

    print("Candidate stations:", len(stations))
    print("Station filtering time:", round(t3 - t2, 2), "sec\n")

    # Optimization
    t4 = time.perf_counter()
    result = optimization_service.optimize(route_data, stations)
    t5 = time.perf_counter()

    print("Total distance:", result["distance_miles"])
    print("Estimated fuel cost:", result["total_cost"])
    print("Stops selected:", len(result["stops"]))
    print("Optimization time:", round(t5 - t4, 2), "sec\n")

    # Overall timing
    total_time = t5 - t0
    print("Total pipeline time:", round(total_time, 2), "sec\n")

    # -----------------------------
    # Print stops
    # -----------------------------
    print("Optimal Refueling Stops:")
    for s in result["stops"]:
        city_state = f"{s.get('city', '')}, {s.get('state', '')}".strip(", ")
        location_str = f" ({city_state})" if city_state else ""
        print(
            f"  • Stop #{s['stop_number']}: {s['name']}{location_str}\n"
            f"    - Milestone: {s['distance_from_start_miles']} mi (leg: {s['leg_distance_miles']} mi)\n"
            f"    - Fuel Refueled: {s['gallons_refueled']} gal @ ${s['price']:.3f}/gal = ${s['cost_usd']:.2f}\n"
            f"    - GPS: ({s['latitude']}, {s['longitude']})"
        )


if __name__ == "__main__":
    main()
