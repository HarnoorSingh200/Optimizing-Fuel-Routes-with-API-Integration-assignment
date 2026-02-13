import time
import os
from api.services.routing_service import routing_service
from api.services.fuel_service import fuel_service
from api.services.optimization_service import optimization_service


START_LOCATION = "Key West, FL"
END_LOCATION = "Pensacola, FL"


def main():
    print("\nRunning FLORIDA pipeline test\n")

    # Get route
    t0 = time.perf_counter()
    route_data = routing_service.get_route(START_LOCATION, END_LOCATION)
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
    print("Stops:")
    for s in result["stops"]:
        print(f"  • {s['name']} — ${s['price']}")


if __name__ == "__main__":
    main()
