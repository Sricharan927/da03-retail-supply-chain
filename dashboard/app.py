"""Retail and Supply Chain Control Tower - Streamlit dashboard."""
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Control Tower", layout="wide")


@st.cache_data
def load(query):
    conn = sqlite3.connect("data/processed/retail.db")
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


risk = pd.read_csv("reports/stockout_risk.csv")
supp = pd.read_csv("reports/supplier_performance.csv")
fc = load("SELECT * FROM forecast")
hist = load("""SELECT s.date, p.product_name, SUM(s.units_sold) AS units
               FROM sales s JOIN products p ON p.product_id = s.product_id
               WHERE s.date >= (SELECT DATE(MAX(date), '-60 day') FROM sales)
               GROUP BY s.date, p.product_name""")
acc = pd.read_csv("reports/forecast_accuracy.csv")

st.title("Retail and Supply Chain Control Tower")

# ---- Sidebar filters ----
stores = st.sidebar.multiselect("Store", sorted(risk.store_name.unique()),
                                default=sorted(risk.store_name.unique()))
cats = st.sidebar.multiselect("Category", sorted(risk.category.unique()),
                              default=sorted(risk.category.unique()))
view = risk[risk.store_name.isin(stores) & risk.category.isin(cats)]

# ---- KPI tiles ----
c1, c2, c3, c4 = st.columns(4)
c1.metric("Critical items", int((view.status == "Critical").sum()))
c2.metric("Reorder now", int((view.status == "Reorder now").sum()))
c3.metric("Avg supplier on-time", f"{supp.on_time_pct.mean():.1f}%")
c4.metric("Forecast error (MAPE)", f"{acc.mape_pct.mean():.1f}%")

# ---- Stock-out risk ----
st.subheader("Stock-out risk")
colors = {"Critical": "#e15759", "Reorder now": "#f28e2b", "OK": "#59a14f"}
status_counts = view.status.value_counts().reset_index()
status_counts.columns = ["status", "lines"]
left, right = st.columns([1, 2])
left.plotly_chart(px.pie(status_counts, names="status", values="lines", color="status",
                         color_discrete_map=colors, hole=0.5), use_container_width=True)
right.dataframe(
    view[view.status != "OK"].sort_values("days_of_cover")
        [["store_name", "product_name", "stock_on_hand", "days_of_cover", "status"]],
    use_container_width=True, hide_index=True, height=330)

# ---- Supplier performance ----
st.subheader("Supplier performance")
fig = px.bar(supp.sort_values("on_time_pct"), x="on_time_pct", y="supplier_name",
             orientation="h", text="on_time_pct",
             labels={"on_time_pct": "On-time %", "supplier_name": ""})
st.plotly_chart(fig, use_container_width=True)

# ---- Demand forecast ----
st.subheader("Demand forecast (next 14 days, all stores)")
product = st.selectbox("Product", sorted(fc.product_name.unique()))
h = hist[hist.product_name == product].rename(columns={"units": "value"})
h["type"] = "Actual (last 60 days)"
f = fc[fc.product_name == product].rename(columns={"forecast_units": "value"})
f["type"] = "Forecast"
line = pd.concat([h[["date", "value", "type"]], f[["date", "value", "type"]]])
st.plotly_chart(
    px.line(line, x="date", y="value", color="type",
            color_discrete_map={"Actual (last 60 days)": "#4e79a7", "Forecast": "#f28e2b"}),
    use_container_width=True)