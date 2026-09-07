SELECT
    f_id AS food_id,
    item AS food_name,
    LOWER(veg_or_non_veg) AS veg_or_non_veg
FROM {{ ref('br_food') }}
