SELECT
    try_cast(id AS NUMERIC) AS restaurant_id,
    name AS restaurant_name,
    trim(COALESCE(regexp_substr(city, '[^,]+$'), city)) AS city,
    CAST(ROUND(NULLIF(rating, '--'), 1) AS DECIMAL(3,1)) AS rating,
    CAST(regexp_substr(rating_count, '[0-9]+') AS NUMERIC) AS rating_count,
    CAST(regexp_substr(cost, '[0-9]+') AS NUMERIC) AS cost_for_two,
    cuisine,
    lic_no AS license_no
FROM {{ ref('br_restaurants') }}
WHERE try_cast(id AS NUMERIC) IS NOT NULL