SELECT city,
    HOUR(order_timestamp) as order_hour,
    count_if(is_delivered) as delivered_orders,
    ROUND(median(delivery_time_min),1) as p50,
    ROUND(percentile_cont(0.9) within group (order by delivery_time_min),1) as p90
FROM {{ ref('fct_orders') }}
WHERE is_delivered
GROUP BY 1,2