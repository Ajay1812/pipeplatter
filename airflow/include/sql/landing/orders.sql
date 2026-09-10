COPY INTO pipeplatter.landing.orders
FROM (
  SELECT CAST(order_id AS DECIMAL(10,0)) AS order_id,
         CAST(order_timestamp AS TIMESTAMP_NTZ) AS order_timestamp,
         order_date,
         CAST(user_id AS DECIMAL(10,0)) AS user_id,
         CAST(r_id AS DECIMAL(10,0)) AS r_id,
         restaurant_city, cuisine,
         CAST(items_count AS DECIMAL(10,0)) AS items_count,
         CAST(sales_qty AS DECIMAL(10,0)) AS sales_qty,
         CAST(subtotal AS DECIMAL(10,0)) AS subtotal,
         CAST(discount AS DECIMAL(10,0)) AS discount,
         CAST(delivery_fee AS DECIMAL(10,0)) AS delivery_fee,
         CAST(gst AS DECIMAL(10,0)) AS gst,
         CAST(sales_amount AS DECIMAL(10,0)) AS sales_amount,
         currency, payment_method, order_status,
         CAST(customer_rating AS DECIMAL(10,0)) AS customer_rating,
         CAST(delivery_time_min AS DECIMAL(10,0)) AS delivery_time_min
  FROM 's3://{{ var.value.s3_bucket }}/raw/orders/orders.csv'
)
FILEFORMAT = CSV
FORMAT_OPTIONS ('header' = 'true', 'inferSchema' = 'true');
