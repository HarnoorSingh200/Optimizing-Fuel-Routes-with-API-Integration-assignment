import requests
import time

API_URL = "http://127.0.0.1:8000/api/fuel-plan/"

TEST_ROUTES = [
    ("Key West, FL", "Pensacola, FL"),    # longest route
    ("Key West, FL", "Tallahassee, FL"),  # long
    ("Miami, FL", "Pensacola, FL")        # medium
]


def run_test(start, end):
    payload = {"start": start, "end": end}

    print(f"\nTesting: {start} → {end}\n")

    try:
        t0 = time.perf_counter()
        response = requests.post(API_URL, json=payload)
        t1 = time.perf_counter()

        print("Status Code:", response.status_code)
        print("Response Time:", round(t1 - t0, 2), "sec")

        if response.status_code != 200:
            print("Error:", response.text)
            return

        data = response.json()

        print("\nDistance:", data.get("distance_miles"), "miles")
        print("Total Cost:", data.get("total_cost"))
        print("Stops:", len(data.get("stops", [])))

        print("\nStops:")
        for stop in data.get("stops", []):
            print(
                f"  • {stop['name']} — ${stop['price']} "
                f"({stop['latitude']}, {stop['longitude']})"
            )

        print("\n" + "-" * 50)

    except requests.exceptions.ConnectionError:
        print("Server not running")
    except Exception as e:
        print("Error:", str(e))


def main():
    print("\nRunning Florida Route Test Suite\n")

    for start, end in TEST_ROUTES:
        run_test(start, end)


if __name__ == "__main__":
    main()
