import requests
import time
import json

# -----------------------------
# CONFIG
# -----------------------------
API_URL = "http://127.0.0.1:8000/api/fuel-plan/"

PAYLOAD = {
    "start": "Key West, FL",
    "end": "Pensacola, FL"
}


def main():
    print("\n🚀 Sending request to Fuel Plan API\n")

    try:
        t0 = time.perf_counter()

        response = requests.post(API_URL, json=PAYLOAD)

        t1 = time.perf_counter()

        print("Status Code:", response.status_code)
        print("Response Time:", round(t1 - t0, 2), "sec\n")

        if response.status_code != 200:
            print("❌ Error Response:")
            print(response.text)
            return

        data = response.json()

        print("Status Code:", response.status_code)
        print("\nRaw Response:\n")
        print(response.text)

        print("---Beautified report---")

        print("🧭 Distance:", data.get("distance_miles"), "miles")
        print("💰 Total Cost:", data.get("total_cost"))
        print("⛽ Stops:", len(data.get("stops", [])))
        print()

        print("📍 Stops Detail:")
        for stop in data.get("stops", []):
            print(
                f"  • {stop['name']} — ${stop['price']} "
                f"({stop['latitude']}, {stop['longitude']})"
            )

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Is Django server running?")
    except Exception as e:
        print("❌ Error:", str(e))


if __name__ == "__main__":
    main()
