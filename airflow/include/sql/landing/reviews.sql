COPY INTO pipeplatter.landing.reviews
FROM (
  SELECT CAST(review_id AS DECIMAL(10,0)) AS review_id,
         CAST(order_id AS DECIMAL(10,0)) AS order_id,
         CAST(user_id AS DECIMAL(10,0)) AS user_id,
         CAST(restaurant_id AS DECIMAL(10,0)) AS restaurant_id,
         CAST(rating AS DECIMAL(10,0)) AS rating,
         comment,
         review_date
  FROM 's3://{{ var.value.s3_bucket }}/raw/reviews/reviews.csv'
)
FILEFORMAT = CSV
FORMAT_OPTIONS ('header' = 'true', 'inferSchema' = 'true');
