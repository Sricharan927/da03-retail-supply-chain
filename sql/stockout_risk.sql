-- Days of cover per store/product, using the last 28 days of sales
WITH recent AS (
    SELECT store_id, product_id, AVG(units_sold) AS avg_daily_sales
    FROM sales
    WHERE date > (SELECT DATE(MAX(date), '-28 day') FROM sales)
    GROUP BY store_id, product_id
)
SELECT
    st.store_name,
    p.product_name,
    p.category,
    i.stock_on_hand,
    i.reorder_point,
    ROUND(r.avg_daily_sales, 1) AS avg_daily_sales,
    ROUND(i.stock_on_hand / r.avg_daily_sales, 1) AS days_of_cover,
    CASE
        WHEN i.stock_on_hand / r.avg_daily_sales < sup.avg_lead_time_days THEN 'Critical'
        WHEN i.stock_on_hand <= i.reorder_point THEN 'Reorder now'
        ELSE 'OK'
    END AS status
FROM inventory i
JOIN recent r   ON r.store_id = i.store_id AND r.product_id = i.product_id
JOIN stores st  ON st.store_id = i.store_id
JOIN products p ON p.product_id = i.product_id
JOIN suppliers sup ON sup.supplier_id = p.supplier_id
ORDER BY days_of_cover ASC;