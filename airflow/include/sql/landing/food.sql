COPY INTO pipeplatter.landing.food
FROM 's3://{{ var.value.s3_bucket }}/raw/food/food.csv'
FILEFORMAT = CSV
FORMAT_OPTIONS ('header' = 'true', 'inferSchema' = 'true')
COPY_OPTIONS ('mergeSchema' = 'true');
