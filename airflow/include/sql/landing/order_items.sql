COPY INTO pipeplatter.landing.order_items
FROM (
  SELECT CAST(order_item_id AS DECIMAL(10,0)) AS order_item_id,
         CAST(order_id AS DECIMAL(10,0)) AS order_id,
         CAST(r_id AS DECIMAL(10,0)) AS r_id,
         f_id,
         CAST(price AS DECIMAL(10,0)) AS price,
         CAST(quantity AS DECIMAL(10,0)) AS quantity,
         CAST(line_amount AS DECIMAL(10,0)) AS line_amount
  FROM 's3://{{ var.value.s3_bucket }}/raw/order_items/order_items.csv'
)
FILEFORMAT = CSV
FORMAT_OPTIONS ('header' = 'true', 'inferSchema' = 'true');
