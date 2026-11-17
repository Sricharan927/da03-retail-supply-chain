"""Run the SQL files and save results as CSV."""
import sqlite3
from pathlib import Path
import pandas as pd

conn = sqlite3.connect("data/processed/retail.db")
Path("reports").mkdir(exist_ok=True)
for name in ["stockout_risk", "supplier_performance"]:
    sql = Path(f"sql/{name}.sql").read_text(encoding="utf-8-sig")
    df = pd.read_sql_query(sql, conn)
    df.to_csv(f"reports/{name}.csv", index=False)
    print(f"\n=== {name} ({len(df)} rows) ===")
    print(df.head(8).to_string(index=False))
conn.close()