COPY INTO pipeplatter.landing.users
FROM (
  SELECT CAST(user_id AS STRING) AS user_id, name, email, password,
         CAST(`Age` AS STRING) AS age, `Gender` AS gender, `Marital Status` AS marital_status,
         `Occupation` AS occupation, `Monthly Income` AS monthly_income,
         `Educational Qualifications` AS education, CAST(`Family size` AS STRING) AS family_size
  FROM 's3://{{ var.value.s3_bucket }}/raw/users/users.csv'
)
FILEFORMAT = CSV
FORMAT_OPTIONS ('header' = 'true', 'inferSchema' = 'true');
