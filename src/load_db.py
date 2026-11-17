import sqlite3
from pathlib import Path
import pandas as pd

RAW = Path("data/raw")
DB = Path("data/processed/retail.db")
DB.parent.mkdir(parents=True, exist_ok=True)

tables = ["stores", "products", "suppliers", "sales", "inventory", "deliveries"]
conn = sqlite3.connect(DB)
for name in tables:
    df = pd.read_csv(RAW / f"{name}.csv")
    df.to_sql(name, conn, if_exists="replace", index=False)
    print(f"{name}: {len(df):,} rows")
conn.execute("CREATE INDEX IF NOT EXISTS ix_sales ON sales(store_id, product_id, date)")
conn.commit()
conn.close()
print("Database created at", DB.resolve())