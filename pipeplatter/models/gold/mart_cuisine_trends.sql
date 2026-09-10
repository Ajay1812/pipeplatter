SELECT
    date_trunc('month', order_date) AS month,
    cuisine,
    COUNT(*) AS orders,
    SUM(iff(is_delivered, sales_amount, 0)) AS revenue,
    COUNT(DISTINCT customer_id) AS unique_customers
FROM {{ ref('fct_orders') }}
GROUP BY 1, 2
