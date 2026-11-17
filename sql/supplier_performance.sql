SELECT
    s.supplier_name,
    COUNT(*) AS orders,
    ROUND(100.0 * SUM(CASE WHEN d.delivered_date <= d.promised_date THEN 1 ELSE 0 END) / COUNT(*), 1) AS on_time_pct,
    ROUND(AVG(JULIANDAY(d.delivered_date) - JULIANDAY(d.promised_date)), 2) AS avg_delay_days,
    ROUND(AVG(JULIANDAY(d.delivered_date) - JULIANDAY(d.order_date)), 1) AS avg_lead_time_days
FROM deliveries d
JOIN suppliers s ON s.supplier_id = d.supplier_id
GROUP BY s.supplier_name
ORDER BY on_time_pct ASC;