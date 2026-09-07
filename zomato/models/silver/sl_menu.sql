SELECT
    menu_id,
    try_cast(r_id AS NUMERIC) AS restaurant_id,
    f_id AS food_id,
    cuisine,
    ROUND(try_cast(price AS DECIMAL(10,2)),2) AS price
FROM {{ref('br_menu')}}
WHERE try_cast(r_id AS NUMERIC) IS NOT NULL AND try_cast(price AS DECIMAL(10,2)) > 0