import os
import sys

# Streamlit only adds this script's own directory (ai/ui/) to sys.path, but the pages
# in this folder import shared code with flat imports (`from config import ...`,
# `from connections import ...`) that live one level up in ai/. Put ai/ on the path too.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

dashboard = st.Page("dashboard.py", title="Dashboard", icon=":material/bar_chart:", default=True)
reviews_chat = st.Page("reviews_chat.py", title="Reviews Chat", icon=":material/reviews:")
sql_chat = st.Page("sql_chat.py", title="SQL Chat", icon=":material/database:")

pg = st.navigation([dashboard, reviews_chat, sql_chat])
pg.run()
