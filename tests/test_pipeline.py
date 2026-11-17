"""Validation tests for DA-03. Run: python -m pytest tests -v"""
import sqlite3
import pandas as pd
import pytest

DB = "data/processed/retail.db"


@pytest.fixture(scope="module")
def conn():
    c = sqlite3.connect(DB)
    yield c
    c.close()


def test_row_counts(conn):
    counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ["stores", "products", "suppliers", "sales", "inventory", "deliveries"]}
    assert counts == {"stores": 6, "products": 20, "suppliers": 5,
                      "sales": 87600, "inventory": 120, "deliveries": 600}


def test_every_supplier_has_products(conn):
    n = conn.execute("SELECT COUNT(DISTINCT supplier_id) FROM products").fetchone()[0]
    assert n == 5


def test_no_negative_sales_or_stock(conn):
    assert conn.execute("SELECT COUNT(*) FROM sales WHERE units_sold < 0").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM inventory WHERE stock_on_hand < 0").fetchone()[0] == 0


def test_deliveries_not_before_order(conn):
    bad = conn.execute("SELECT COUNT(*) FROM deliveries WHERE delivered_date < order_date").fetchone()[0]
    assert bad == 0


def test_status_values_valid():
    risk = pd.read_csv("reports/stockout_risk.csv")
    assert set(risk.status) <= {"Critical", "Reorder now", "OK"}
    assert len(risk) == 120


def test_critical_means_cover_below_lead_time(conn):
    risk = pd.read_csv("reports/stockout_risk.csv")
    max_lead = conn.execute("SELECT MAX(avg_lead_time_days) FROM suppliers").fetchone()[0]
    assert (risk[risk.status == "Critical"].days_of_cover < max_lead).all()


def test_forecast_complete(conn):
    fc = pd.read_sql_query("SELECT * FROM forecast", conn)
    assert fc.product_id.nunique() == 20
    assert len(fc) == 20 * 14
    assert (fc.forecast_units >= 0).all()


def test_forecast_accuracy_reasonable():
    acc = pd.read_csv("reports/forecast_accuracy.csv")
    assert acc.mape_pct.mean() < 15