import os
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from connections import get_databricks_connection

load_dotenv('airflow/.env')

st.set_page_config(layout="wide")


@st.cache_data(ttl=600)
def run_query(sql: str) -> pd.DataFrame:
    conn = get_databricks_connection()
    curr = conn.cursor()
    curr.execute(sql)
    columns = [col[0] for col in curr.description]
    rows = curr.fetchall()
    curr.close()
    df = pd.DataFrame(rows, columns=columns)

    # Databricks DECIMAL columns come back as python Decimal -> pandas dtype=object,
    # which breaks nlargest/nsmallest and other numeric ops. Coerce what can be numeric.
    for col in df.columns:
        if df[col].dtype == object:
            try:
                df[col] = pd.to_numeric(df[col])
            except (ValueError, TypeError):
                pass
    return df


CATALOG = os.environ['DATABRICKS_CATALOG']

st.title("Zomato Dashboard")

tab_revenue, tab_restaurants, tab_sla, tab_cuisine = st.tabs(
    ["Revenue & Orders", "Top Restaurants", "Delivery SLA", "Cuisine Trends"]
)

with tab_revenue:
    df = run_query(f"SELECT * FROM {CATALOG}.gold.mart_daily_city_revenue")

    cities = sorted(df['city'].unique())
    selected_cities = st.multiselect("City", cities, default=cities, key="revenue_city")
    filtered = df[df['city'].isin(selected_cities)]

    if filtered.empty:
        st.info("No data for the selected cities.")
    else:
        daily = filtered.groupby('order_date', as_index=False).agg(
            orders=('orders', 'sum'),
            gmv=('gmv', 'sum'),
            weighted_cancels=('orders', lambda s: (s * filtered.loc[s.index, 'cancel_rate']).sum()),
        )
        daily['cancel_rate'] = daily['weighted_cancels'] / daily['orders']
        daily['aov'] = daily['gmv'] / daily['orders']

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total GMV", f"₹{daily['gmv'].sum():,.0f}")
        col2.metric("Total Orders", f"{daily['orders'].sum():,.0f}")
        col3.metric("Avg AOV", f"₹{daily['gmv'].sum() / daily['orders'].sum():,.2f}")
        col4.metric("Avg Cancel Rate", f"{daily['cancel_rate'].mean() * 100:.1f}%")

        st.plotly_chart(px.line(daily, x='order_date', y='gmv', title='GMV over time'), width="stretch")
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(px.bar(daily, x='order_date', y='orders', title='Orders over time'), width="stretch")
        col_b.plotly_chart(px.line(daily, x='order_date', y='cancel_rate', title='Cancel rate over time'), width="stretch")

with tab_restaurants:
    df = run_query(f"SELECT * FROM {CATALOG}.gold.mart_restaurant_performance")

    cities = sorted(df['city'].unique())
    selected_city = st.selectbox("City", ["All"] + cities, key="restaurant_city")
    top_n = st.slider("Show top N restaurants", 5, 50, 10, key="restaurant_top_n")

    filtered = df if selected_city == "All" else df[df['city'] == selected_city]
    top = filtered.nlargest(top_n, 'revenue')

    if top.empty:
        st.info("No restaurants for the selected city.")
    else:
        st.plotly_chart(
            px.bar(top.sort_values('revenue'), x='revenue', y='restaurant_name', orientation='h',
                   title=f'Top {top_n} restaurants by revenue', color='cuisine'),
            width="stretch",
        )
        st.dataframe(
            top[['restaurant_name', 'city', 'cuisine', 'orders', 'revenue', 'avg_customer_rating', 'avg_delivery_min']],
            hide_index=True,
        )

with tab_sla:
    df = run_query(f"SELECT * FROM {CATALOG}.gold.mart_delivery_sla")

    cities = sorted(df['city'].unique())
    selected_cities = st.multiselect("City", cities, default=cities[:3], key="sla_city")
    filtered = df[df['city'].isin(selected_cities)].sort_values('order_hour')

    if filtered.empty:
        st.info("Select at least one city.")
    else:
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(
            px.line(filtered, x='order_hour', y='p50', color='city', title='p50 delivery time by hour (min)'),
            width="stretch",
        )
        col_b.plotly_chart(
            px.line(filtered, x='order_hour', y='p90', color='city', title='p90 delivery time by hour (min)'),
            width="stretch",
        )

with tab_cuisine:
    df = run_query(f"SELECT * FROM {CATALOG}.gold.mart_cuisine_trends")

    top_cuisines = df.groupby('cuisine')['revenue'].sum().nlargest(8).index.tolist()
    selected_cuisines = st.multiselect("Cuisine", sorted(df['cuisine'].unique()), default=top_cuisines, key="cuisine_filter")
    filtered = df[df['cuisine'].isin(selected_cuisines)].sort_values('month')

    if filtered.empty:
        st.info("Select at least one cuisine.")
    else:
        st.plotly_chart(
            px.line(filtered, x='month', y='revenue', color='cuisine', title='Revenue by cuisine over time'),
            width="stretch",
        )
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(
            px.bar(filtered.groupby('cuisine', as_index=False)['orders'].sum().sort_values('orders'),
                   x='orders', y='cuisine', orientation='h', title='Total orders by cuisine'),
            width="stretch",
        )
        col_b.plotly_chart(
            px.bar(filtered.groupby('cuisine', as_index=False)['unique_customers'].sum().sort_values('unique_customers'),
                   x='unique_customers', y='cuisine', orientation='h', title='Unique customers by cuisine'),
            width="stretch",
        )
