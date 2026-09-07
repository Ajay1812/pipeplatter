SELECT
    try_cast(user_id AS NUMERIC) AS customer_id,
    name AS customer_name,
    lower(email) AS email,
    CAST(age AS NUMERIC) AS age,
    gender,
    marital_status,
    occupation,
    monthly_income AS income_band,
    education,
    CAST(family_size AS NUMERIC) AS family_size
FROM {{ ref('br_users') }}
WHERE try_cast(user_id AS NUMERIC) IS NOT NULL