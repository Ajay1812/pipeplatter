with spine as (
    select explode(sequence(to_date('2024-01-01'), to_date('2027-04-14'), interval 1 day)) as date_day
)
select date_day, year(date_day) as year, month(date_day) as month, date_format(date_day, 'MMMM') as month_name,
       date_format(date_day, 'EEEE') as day_name, (dayofweek(date_day) in (1, 7)) as is_weekend
from spine where date_day <= '2026-12-31'
