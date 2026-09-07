import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from databricks import sql
load_dotenv('airflow/.env')

@lru_cache(maxsize=2)
def get_databricks_connection():
    return  sql.connect(
        server_hostname=os.environ['DATABRICKS_HOST'],
        http_path=os.environ['DATABRICKS_HTTP_PATH'],
        access_token=os.environ['DATABRICKS_TOKEN']
    )

@lru_cache(maxsize=2)
def get_model_connection():
    model = ChatGroq(
        model=os.environ['GROQ_MODEL_NAME'],
        api_key=os.environ['GROQ_API_KEY'],
        temperature=0.0,
    )
    return model