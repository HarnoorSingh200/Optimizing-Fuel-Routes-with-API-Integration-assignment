from pathlib import Path
import pandas as pd
from collections import Counter

STATE = "FL"  # change if needed
DATA_DIR = Path(__file__).resolve().parent

df = pd.read_csv(DATA_DIR / "fuel_prices.csv")
df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

df_state = df[df["state"] == STATE]

cities = df_state["city"].dropna().unique()

print(f"Total stations in {STATE}:", len(df_state))
print(f"Unique cities in {STATE}:", len(cities))

pd.DataFrame({"city": cities}).to_csv(DATA_DIR / f"{STATE}_cities.csv", index=False)

print("Saved city list")
