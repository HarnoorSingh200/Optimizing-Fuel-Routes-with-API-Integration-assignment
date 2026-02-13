import pandas as pd
from collections import Counter

FILE_PATH = "fuel_prices.csv"


def main():
    print("\nFUEL DATASET ANALYSIS\n")

    df_raw = pd.read_csv(FILE_PATH)
    total_rows = len(df_raw)

    print("Total rows in original dataset:", total_rows)

    df = df_raw.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    df = df.rename(
        columns={
            "opis_truckstop_id": "station_id",
            "truckstop_name": "name",
            "retail_price": "price",
        }
    )

    # Null price rows
    null_rows = df["price"].isna().sum()
    print("🔹 Rows with NULL price:", null_rows)

    df = df.dropna(subset=["price"])
    after_null_drop = len(df)
    print("🔹 Rows after dropping NULL prices:", after_null_drop)

    # Convert price
    df["price"] = df["price"].astype(float)

    # Remove duplicate station_id entries
    before_dedup = len(df)
    df_dedup = df.drop_duplicates(subset=["station_id"])
    after_dedup = len(df_dedup)

    print("🔹 Rows before removing duplicate stations:", before_dedup)
    print("🔹 Rows after removing duplicate stations:", after_dedup)

    # Keep cheapest price per station
    df_cheapest_station = (
        df.sort_values("price")
        .groupby("station_id", as_index=False)
        .first()
    )

    print("🔹 Rows after selecting cheapest price per station:", len(df_cheapest_station))

    # Cheapest station per city
    df_cheapest_city = (
        df_cheapest_station.sort_values("price")
        .groupby("city", as_index=False)
        .first()
    )

    print("🔹 Cheapest stations per city:", len(df_cheapest_city))

    # State & city stats
    total_states = df_raw["State"].nunique()
    total_cities = df_raw["City"].nunique()

    print("\nGEOGRAPHIC STATS")
    print("🔹 Total states:", total_states)
    print("🔹 Total cities:", total_cities)

    # Stations per state
    state_counts = Counter(df_raw["State"])
    print("\nStations per state (top 10):")
    for state, count in state_counts.most_common(10):
        print(f"  {state}: {count}")

    # Cities per state
    cities_per_state = df_raw.groupby("State")["City"].nunique()

    print("\nCities per state (top 10):")
    for state, count in cities_per_state.sort_values(ascending=False).head(10).items():
        print(f"  {state}: {count}")

    # Price statistics
    print("\nPRICE STATS")
    print("🔹 Min price:", round(df["price"].min(), 2))
    print("🔹 Max price:", round(df["price"].max(), 2))
    print("🔹 Avg price:", round(df["price"].mean(), 2))

    print("\n---Analysis complete---\n")


if __name__ == "__main__":
    main()
