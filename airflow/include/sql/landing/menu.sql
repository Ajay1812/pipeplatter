COPY INTO zomato.landing.menu
FROM (
  SELECT menu_id, CAST(r_id AS STRING) AS r_id, f_id, cuisine, price
  FROM 's3://{{ var.value.s3_bucket }}/raw/menu/menu.csv'
)
FILEFORMAT = CSV
FORMAT_OPTIONS ('header' = 'true', 'inferSchema' = 'true');
