import pandas as pd
from collections import Counter

STATE = "FL"  # change if needed

df = pd.read_csv("fuel_prices.csv")
df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

df_state = df[df["state"] == STATE]

cities = df_state["city"].dropna().unique()

print(f"Total stations in {STATE}:", len(df_state))
print(f"Unique cities in {STATE}:", len(cities))

pd.DataFrame({"city": cities}).to_csv(f"{STATE}_cities.csv", index=False)

print("Saved city list")
