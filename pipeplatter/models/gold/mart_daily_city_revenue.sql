SELECT
    order_date,
    city,
    COUNT(*) AS orders,
    count_if(is_delivered) AS delivered_orders,
    round(count_if(order_status='Cancelled') / nullif(count(*), 0), 4) AS cancel_rate,
    SUM(iff(is_delivered, sales_amount, 0)) AS gmv,
    ROUND(SUM(iff(is_delivered, sales_amount, 0)) / nullif(count_if(is_delivered), 0), 2) AS aov
FROM {{ ref('fct_orders') }}
GROUP BY 1,2