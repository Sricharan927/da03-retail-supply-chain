"""Forecast the next 14 days of demand per product (all stores combined) with Prophet."""
import logging
import sqlite3
import pandas as pd
from prophet import Prophet

logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
logging.getLogger("prophet").setLevel(logging.WARNING)

HORIZON = 14
conn = sqlite3.connect("data/processed/retail.db")
sales = pd.read_sql_query(
    """SELECT s.date, s.product_id, p.product_name, SUM(s.units_sold) AS y
       FROM sales s JOIN products p ON p.product_id = s.product_id
       GROUP BY s.date, s.product_id""", conn, parse_dates=["date"])

# Hold out the last 14 days to measure accuracy honestly
cutoff = sales.date.max() - pd.Timedelta(days=HORIZON)
results, errors = [], []
for pid, g in sales.groupby("product_id"):
    name = g.product_name.iloc[0]
    df = g.rename(columns={"date": "ds"})[["ds", "y"]]
    train, test = df[df.ds <= cutoff], df[df.ds > cutoff]

    m = Prophet(weekly_seasonality=True, yearly_seasonality=True, daily_seasonality=False)
    m.fit(train)
    pred = m.predict(m.make_future_dataframe(periods=HORIZON))
    merged = test.merge(pred[["ds", "yhat"]], on="ds")
    mape = (abs(merged.y - merged.yhat) / merged.y).mean() * 100
    errors.append({"product_id": pid, "product_name": name, "mape_pct": round(mape, 1)})

    # Refit on all data and forecast the real future
    m = Prophet(weekly_seasonality=True, yearly_seasonality=True, daily_seasonality=False)
    m.fit(df)
    fut = m.predict(m.make_future_dataframe(periods=HORIZON)).tail(HORIZON)
    for _, r in fut.iterrows():
        results.append({"product_id": pid, "product_name": name, "date": r.ds.date(),
                        "forecast_units": max(0, round(r.yhat))})
    print(f"forecast done: {name} (MAPE {mape:.1f}%)")

forecast = pd.DataFrame(results)
forecast.to_sql("forecast", conn, if_exists="replace", index=False)
forecast.to_csv("reports/forecast.csv", index=False)
pd.DataFrame(errors).to_csv("reports/forecast_accuracy.csv", index=False)
print(f"\nAverage MAPE across products: {pd.DataFrame(errors).mape_pct.mean():.1f}%")
conn.close()