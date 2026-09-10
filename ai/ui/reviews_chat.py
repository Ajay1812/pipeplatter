import os
import json
import numpy as np
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from connections import get_model_connection, get_databricks_connection
from config import RAG_SYSTEM_PROMPT, EMBEDDING_MODEL, QUERY_RAG_PREFIX
from sentence_transformers import SentenceTransformer

load_dotenv('airflow/.env')

NEW_REVIEWS = 70 # percent
TOP_K = 10
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
    df["concat_text"] = df.apply(
        lambda row: " | ".join([f"{col}: {row[col]}" for col in df.columns]), axis=1
    )
    databricks_conn.close()

    df.columns = [col.lower() for col in df.columns]
    return df

def embed(comments: list) -> pd.DataFrame:
    model = SentenceTransformer(EMBEDDING_MODEL)
    response = model.encode(comments)
    return  [item for item in response]


@st.cache_data()
def load_reviews():
    if os.path.exists(CACHE_FILE):
        return  pd.read_parquet(CACHE_FILE)
    df = read_reviews_from_databricks()
    df['embedding'] = embed(df['concat_text'].tolist())
    df.to_parquet(CACHE_FILE)
    return df

def cosine_similarity(vec_a, vec_b):
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))

def find_similar_reviews(question: str, df: pd.DataFrame) -> pd.DataFrame:
    question_vector = embed([QUERY_RAG_PREFIX + question])[0]
    scores = []
    for review_vector in df['embedding']:
        scores.append(cosine_similarity(review_vector, question_vector))

    df = df.copy()
    df['score'] = scores
    return df.nlargest(TOP_K, 'score')

def ask_llm(question: str, top_reviews: pd.DataFrame) -> str:
    context = ''
    for _, row in top_reviews.iterrows():
        context += f"{row['city']}, {row['rating']}, {row['comment']}, {row['review_date']}\n"

    model = get_model_connection()
    prompt = [
        {"role": "system", "content": RAG_SYSTEM_PROMPT},
        {"role": "user", "content": f"Reviews:\n{context}\nQuestion: {question}"},
    ]
    response = model.invoke(prompt)
    return response.content

st.title("Chat with your Pipeplatter Reviews")
st.caption(f"Searching {NEW_REVIEWS} review, answering with {os.environ['GROQ_MODEL_NAME']} model")

review_df = load_reviews()

question = st.text_input('Ask a question about your reviews',
                         placeholder='What are most common complaints about delivery?')
if question:
    top_reviews = find_similar_reviews(question, review_df)
    answer = ask_llm(question, top_reviews)
    st.write(answer)

    with st.expander('Review used to build this answer'):
        st.dataframe(top_reviews[['city', 'rating', 'comment', 'review_date']], hide_index=True)
