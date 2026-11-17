import numpy as np
import pandas as pd
from faker import Faker
from pathlib import Path

SEED = 7
rng = np.random.default_rng(SEED)
fake = Faker("en_IN")
Faker.seed(SEED)

OUT = Path("data/raw")
OUT.mkdir(parents=True, exist_ok=True)

# End the history at yesterday's date so "today" is realistic
END = pd.Timestamp.today().normalize() - pd.Timedelta(days=1)
START = END - pd.Timedelta(days=729)
days = pd.date_range(START, END, freq="D")

# ---------- Master data ----------
cities = ["Hyderabad", "Bengaluru", "Chennai", "Mumbai", "Delhi", "Pune"]
stores = pd.DataFrame({
    "store_id": range(1, 7),
    "store_name": [f"{c} Store" for c in cities],
    "city": cities,
})

suppliers = pd.DataFrame({
    "supplier_id": range(1, 6),
    "supplier_name": [fake.company() for _ in range(5)],
    "avg_lead_time_days": [4, 6, 8, 5, 10],
    "reliability": [0.95, 0.88, 0.80, 0.92, 0.70],   # share of on-time deliveries
})

categories = ["Grocery", "Beverages", "Personal Care", "Household", "Snacks"]
n_products = 20
products = pd.DataFrame({
    "product_id": range(1, n_products + 1),
    "product_name": [f"{categories[i % 5]} Item {i + 1}" for i in range(n_products)],
    "category": [categories[i % 5] for i in range(n_products)],
    "unit_cost": rng.integers(20, 400, n_products),
    "supplier_id": [(i % 5) + 1 for i in range(n_products)],
})

# ---------- Daily sales ----------
rows = []
for _, p in products.iterrows():
    base = rng.uniform(8, 40)                      # base daily demand per store
    for _, s in stores.iterrows():
        store_factor = rng.uniform(0.7, 1.4)
        trend = np.linspace(1.0, 1.15, len(days))                     # slow growth
        weekly = 1 + 0.18 * np.isin(days.dayofweek, [5, 6])           # weekend lift
        yearly = 1 + 0.15 * np.sin(2 * np.pi * (days.dayofyear - 80) / 365)
        mean = base * store_factor * trend * weekly * yearly
        units = rng.poisson(mean)
        rows.append(pd.DataFrame({"date": days, "store_id": s.store_id,
                                  "product_id": p.product_id, "units_sold": units}))
sales = pd.concat(rows, ignore_index=True)

# ---------- Current inventory ----------
recent = sales[sales.date > END - pd.Timedelta(days=28)]
avg_daily = recent.groupby(["store_id", "product_id"]).units_sold.mean().reset_index()
inventory = avg_daily.copy()
# stock = between 1 and 25 days of cover, so some items are at risk of stock-out
inventory["stock_on_hand"] = (inventory.units_sold * rng.uniform(1, 25, len(inventory))).round().astype(int)
inventory["reorder_point"] = (inventory.units_sold * 7).round().astype(int)
inventory = inventory.drop(columns="units_sold")

# ---------- Deliveries ----------
orders = []
for i in range(600):
    prod = products.sample(1, random_state=int(rng.integers(1e9))).iloc[0]
    sup = suppliers[suppliers.supplier_id == prod.supplier_id].iloc[0]
    order_date = START + pd.Timedelta(days=int(rng.integers(0, 700)))
    promised = order_date + pd.Timedelta(days=int(sup.avg_lead_time_days))
    on_time = rng.random() < sup.reliability
    delay = 0 if on_time else int(rng.integers(1, 8))
    orders.append({
        "order_id": i + 1,
        "supplier_id": int(sup.supplier_id),
        "product_id": int(prod.product_id),
        "store_id": int(rng.integers(1, 7)),
        "order_date": order_date,
        "promised_date": promised,
        "delivered_date": promised + pd.Timedelta(days=delay),
        "quantity": int(rng.integers(100, 1000)),
    })
deliveries = pd.DataFrame(orders)

# ---------- Save ----------
for name, df in [("stores", stores), ("products", products), ("suppliers", suppliers),
                 ("sales", sales), ("inventory", inventory), ("deliveries", deliveries)]:
    df.to_csv(OUT / f"{name}.csv", index=False)

print("Done. Files written to", OUT.resolve())
print(f"Sales rows: {len(sales):,} | Inventory rows: {len(inventory)} | "
      f"Deliveries: {len(deliveries)} | Date range: {START:%Y-%m-%d} to {END:%Y-%m-%d}")