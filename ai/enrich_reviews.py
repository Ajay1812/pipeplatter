import os
import json
from dotenv import load_dotenv

from connections import get_databricks_connection, get_model_connection
from config import ENRICH_SYSTEM_PROMPT
load_dotenv('airflow/.env')

SAMPLE_N = 1000

def create_output_table(cursor):
    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {os.environ['DATABRICKS_CATALOG']}.AI")
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {os.environ['DATABRICKS_CATALOG']}.AI.REVIEW_ENRICHED (
            REVIEW_ID STRING,
            SENTIMENT_LABEL STRING,
            SENTIMENT_SCORE DECIMAL,
            TOPIC STRING,
            KEY_ISSUE STRING,
            MODEL STRING,
            ENRICHED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
        )
        TBLPROPERTIES ('delta.feature.allowColumnDefaults' = 'supported')
    """)

def get_reviews_to_enrich(cursor):
    cursor.execute(f"""
        SELECT REVIEW_ID, COMMENT
        FROM {os.environ['DATABRICKS_CATALOG']}.LANDING.REVIEWS
        WHERE REVIEW_ID NOT IN (SELECT REVIEW_ID FROM {os.environ['DATABRICKS_CATALOG']}.AI.REVIEW_ENRICHED)
        LIMIT {SAMPLE_N}
    """)
    return cursor.fetchall()

def classify_reviews(comment):
    model = get_model_connection()
    prompt = [
        {"role": "system", "content": ENRICH_SYSTEM_PROMPT},
        {"role": "user", "content": comment}
    ]
    response = model.invoke(prompt)
    answer = response.content
    return json.loads(answer)

def save_results(cursor, results):
    print(f"Saving {len(results)} enriched reviews to Databricks...")
    cursor.executemany(f"""
    INSERT INTO {os.environ['DATABRICKS_CATALOG']}.AI.REVIEW_ENRICHED (
    review_id, sentiment_label, sentiment_score, topic, key_issue, model)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        results
   )

def main():
    conn = get_databricks_connection()
    cursor = conn.cursor()
    create_output_table(cursor)
    reviews = get_reviews_to_enrich(cursor)

    if len(reviews) == 0:
        print("No enriched reviews found.")
        return
    print(f"Enriched reviews: {len(reviews)}")
    results = []
    for review_id, comment in reviews:
        # print(f"Classifying review {review_id}: {comment}")
        try:
            labels = classify_reviews(comment)
            # print(f"Labels for review {review_id}: {labels}")
            results.append((
                review_id,
                labels["sentiment_label"],
                labels["sentiment_score"],
                labels["topic"],
                labels["key_issue"],
                os.environ["GROQ_MODEL_NAME"],
            ))
        except Exception as e:
            print(f"Error while classifying review {review_id}: {e}")

    save_results(cursor, results)
    print(f"Saved {len(results)} enriched reviews to Databricks...")
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()