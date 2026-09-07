select
    r.review_id,
    r.order_id,
    r.user_id::numeric as customer_id,
    r.restaurant_id::string as restaurant_id,
    r.rating::decimal(3,1) as rating,
    r.comment::string as comment,
    r.review_date::DATE as review_date,
    res.city as city
    from {{ ref('br_reviews') }} r
    left join {{ ref('sl_restaurants') }} res on try_cast(r.restaurant_id as decimal(10,0)) = res.restaurant_id
where r.comment is not null