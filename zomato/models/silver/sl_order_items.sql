SELECT
    order_item_id,
    order_id,
    r_id as restaurant_id,
    f_id,
    CAST(price AS decimal(10,2)) AS price,
    CAST(quantity AS NUMERIC) AS quantity,
    CAST(line_amount AS decimal(10,2)) AS  line_amount
FROM {{ ref('br_order_items') }}