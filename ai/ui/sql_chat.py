import os
import json
import numpy as np
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from config import FORBIDDEN_WORDS, DATABRICKS_SYSTEM_PROMPT, EXAMPLE_QUESTIONS
from connections import get_model_connection, get_databricks_connection

load_dotenv('airflow/.env')

model = get_model_connection()
databricks_connection = get_databricks_connection()

def generate_sql(question):
    prompt = [
        {"role": "system", "content": DATABRICKS_SYSTEM_PROMPT},
        {"role": "user", "content": f"Question: {question}"},
    ]
    response = model.invoke(prompt).content
    sql = json.loads(response)['sql']
    return sql

def is_sql_safe(sql):
    sql_lower = sql.lower()
    if not sql_lower.startswith('select') and not sql_lower.startswith('with'):
        return False
    for word in FORBIDDEN_WORDS:
        if word in sql_lower:
            return False
    return True

def run_query(sql):
    curr = databricks_connection.cursor()
    curr.execute(sql)
    columns = [col[0] for col in curr.description]
    rows = curr.fetchall()
    curr.close()
    return pd.DataFrame(rows, columns=columns)


@st.cache_data
def convert_for_download(df):
    return df.to_csv(index=False).encode("utf-8")

st.title("Chat with your Zomato Data")
st.caption(f"Ask in English, {os.environ['GROQ_MODEL_NAME']} write the SQL, Databricks run it.")

question = st.text_input("Enter your question here",
                         placeholder="e.g. Top 10 restaurants by revenue in Bangalore",)
with st.expander('Example Questions'):
    for q in EXAMPLE_QUESTIONS:
        st.write(f" - {q}")

if question:
    sql = generate_sql(question)
    st.code(sql, language='sql')
    if not is_sql_safe(sql):
        st.error('Your generated SQL is not safe to run. Please modify your question.')
    else:
        try:
            res = run_query(sql)
            st.success(f'{len(res)} rows returned')
            st.table(res, hide_index=True)
            csv = convert_for_download(res)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"data.csv",
                mime="text/csv",
                icon=":material/download:",
            )
        except Exception as e:
            st.error(f"Error running query: {e}")
