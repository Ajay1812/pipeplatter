COPY INTO zomato.landing.restaurants
FROM 's3://{{ var.value.s3_bucket }}/raw/restaurants/restaurant.csv'
FILEFORMAT = CSV
FORMAT_OPTIONS ('header' = 'true', 'inferSchema' = 'true')
COPY_OPTIONS ('mergeSchema' = 'true');
