import pandas as pd
import sqlite3
import os

# 1. Load the Yelp business dataset
df = pd.read_json("yelp_academic_dataset_business.json", lines=True)

# 2. Pick the city with the most restaurants (from cities known to be in Yelp dataset)
candidate_cities = ["Philadelphia", "Nashville", "Tampa", "Indianapolis", "Tucson",
                    "Reno", "New Orleans", "Pittsburgh", "Charlotte", "Phoenix", "Las Vegas"]

restaurants_all = df[df["categories"].str.contains("Restaurant|Food", na=False)]
city_counts = restaurants_all[restaurants_all["city"].isin(candidate_cities)]["city"].value_counts()
print("Restaurant counts by city:")
print(city_counts)

best_city = city_counts.index[0]
print(f"\nSelected city: {best_city}")

# 3. Filter to best city
filtered = restaurants_all[restaurants_all["city"] == best_city].copy()

# 4. Keep only useful columns (drop lat/lon)
cols = ["business_id", "name", "address", "city", "state",
        "stars", "review_count", "is_open", "categories", "hours", "attributes"]
filtered = filtered[[c for c in cols if c in filtered.columns]]

# 5. Flatten attributes into individual readable columns
import json
import ast

def parse_py_val(val):
    """Parse Python-literal strings like "u'average'" or "True"."""
    if not isinstance(val, str):
        return val
    val = val.strip()
    # Strip u'...' unicode prefix
    if val.startswith("u'") or val.startswith('u"'):
        val = val[1:]
    try:
        return ast.literal_eval(val)
    except Exception:
        return val

def extract_attrs(attrs):
    if not isinstance(attrs, dict):
        try:
            attrs = json.loads(attrs) if isinstance(attrs, str) else {}
        except Exception:
            attrs = {}

    def get(key):
        return parse_py_val(attrs.get(key, None))

    # Price range: 1=$, 2=$$, 3=$$$, 4=$$$$
    price_raw = get("RestaurantsPriceRange2")
    try:
        price_range = "$" * int(price_raw)
    except (TypeError, ValueError):
        price_range = None

    # Ambience: extract the True vibes as a comma-separated string
    ambience_raw = get("Ambience")
    if isinstance(ambience_raw, dict):
        ambience = ", ".join(k for k, v in ambience_raw.items() if v is True)
    else:
        ambience = None

    # Noise level
    noise = get("NoiseLevel")
    noise = str(noise).strip("'") if noise else None

    # Attire
    attire = get("RestaurantsAttire")
    attire = str(attire).strip("'") if attire else None

    # Alcohol
    alcohol = get("Alcohol")
    alcohol = str(alcohol).strip("'").replace("_", " ") if alcohol else None

    def bool_val(key):
        v = get(key)
        if v is True or v == "True":
            return True
        if v is False or v == "False":
            return False
        return None

    return {
        "price_range":    price_range,
        "ambience":       ambience or None,
        "noise_level":    noise,
        "attire":         attire,
        "alcohol":        alcohol,
        "wifi":           str(get("WiFi") or "").strip("'") or None,
        "outdoor_seating": bool_val("OutdoorSeating"),
        "good_for_groups": bool_val("RestaurantsGoodForGroups"),
        "good_for_kids":   bool_val("GoodForKids"),
        "delivery":        bool_val("RestaurantsDelivery"),
        "takeout":         bool_val("RestaurantsTakeOut"),
        "happy_hour":      bool_val("HappyHour"),
        "has_tv":          bool_val("HasTV"),
    }

attr_df = pd.DataFrame(filtered["attributes"].apply(extract_attrs).tolist())
filtered = pd.concat([filtered.drop(columns=["attributes"]), attr_df], axis=1)

# 6. Serialize hours (dict) to JSON string for SQLite
filtered["hours"] = filtered["hours"].apply(
    lambda x: json.dumps(x) if isinstance(x, dict) else x
)

# 6. Save to SQLite
db_path = "restaurants.db"
conn = sqlite3.connect(db_path)
filtered.to_sql("restaurants", conn, if_exists="replace", index=False)
conn.close()

size_mb = os.path.getsize(db_path) / (1024 * 1024)
print(f"Done! {len(filtered)} restaurants saved to {db_path} ({size_mb:.1f} MB)")
