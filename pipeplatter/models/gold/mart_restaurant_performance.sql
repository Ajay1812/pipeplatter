SELECT
    f.restaurant_id, r.restaurant_name, r.city, r.cuisine,
    COUNT(*) as orders,
    SUM(iff(f.is_delivered, f.sales_amount, 0)) as revenue,
    ROUND(avg(f.customer_rating),2) as avg_customer_rating,
    ROUND(avg(f.delivery_time_min),1) as avg_delivery_min
    FROM {{ ref('fct_orders') }} f
    LEFT JOIN {{ ref('dim_restaurants') }} r using (restaurant_id)
GROUP BY 1,2,3,4