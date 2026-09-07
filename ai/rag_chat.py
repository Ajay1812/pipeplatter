import os
import json
import numpy as np
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from connections import get_model_connection, get_databricks_connection
from sentence_transformers import SentenceTransformer

load_dotenv('airflow/.env')

EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
# NEW_REVIEWS = 0.1 # percent
NEW_REVIEWS = 0.002
TOP_K = 5
CACHE_FILE = 'review_embeddings.parquet'

def read_reviews_from_databricks() -> pd.DataFrame:
    databricks_conn = get_databricks_connection()
    curr = databricks_conn.cursor()
    query = f"""
        SELECT REVIEW_ID, CITY, RATING, COMMENT, REVIEW_DATE
        FROM {os.environ['DATABRICKS_CATALOG']}.silver.sl_reviews
        TABLESAMPLE ({NEW_REVIEWS} PERCENT);
    """

    df = pd.DataFrame(curr.execute(query).fetchall(), columns=['REVIEW_ID', 'CITY', 'RATING', 'COMMENT', 'REVIEW_DATE'])
    databricks_conn.close()

    df.columns = [col.lower() for col in df.columns]
    return df

def embed(comments: list) -> pd.DataFrame:
    model = SentenceTransformer(EMBEDDING_MODEL)
    response = model.encode(comments)
    print(response)


@st.cache_data()
def load_reviews():
    if os.path.exists(CACHE_FILE):
        return  pd.read_parquet(CACHE_FILE)
    df = read_reviews_from_databricks()
    df['embedding'] = embed(df['comment'].to_list())
    return  df.to_parquet(CACHE_FILE)


reviews = load_reviews()

st.title("Chat with your Zomato Reviews")
st.caption(f"Searching {NEW_REVIEWS} review, answering with {os.environ['GROQ_MODEL_NAME']} model")