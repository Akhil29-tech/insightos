import os
import re
from groq import Groq
from dotenv import load_dotenv
from db import get_connection
from rag import retrieve

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])

FULL_SCHEMA_HINT = """
Tables: customers, orders, order_items, order_payments, order_reviews,
products, sellers, geolocation, product_category_translation.
Key joins: orders.customer_id -> customers.customer_id,
order_items.order_id -> orders.order_id,
order_items.product_id -> products.product_id,
order_items.seller_id -> sellers.seller_id,
products.product_category_name -> product_category_translation.product_category_name.
geolocation joins via ZIP CODE PREFIX, not an id column:
customers.customer_zip_code_prefix -> geolocation.geolocation_zip_code_prefix,
sellers.seller_zip_code_prefix -> geolocation.geolocation_zip_code_prefix.
There is NO customers.geolocation_id or sellers.geolocation_id column.
geolocation columns are ALL prefixed with "geolocation_": geolocation_zip_code_prefix,
geolocation_lat, geolocation_lng, geolocation_city, geolocation_state.
There is NO plain "state" or "city" column on the geolocation table -
it is always geolocation_state / geolocation_city.
"""

ALWAYS_RULES = """
CRITICAL RULES (always apply, never violate):
1. order_items has NO quantity column. Never write oi.quantity - it
   does not exist. Each row is one unit. Revenue = SUM(price), never
   SUM(price * quantity).
2. ONLY when the question explicitly asks about recency, "active",
   "recent", or "last N days" style time windows: this dataset covers
   Sept 2016 to Aug 2018 ONLY, so never use CURRENT_DATE or
   CURRENT_TIMESTAMP. Instead compute relative to the dataset's own
   most recent order: (SELECT MAX(order_purchase_timestamp) FROM orders).
   Do NOT add any date/recency filter to questions that do not ask
   for one - most questions (revenue, ratings, return rate, etc.)
   should query the FULL dataset with no date restriction at all.
3. When computing a rate/ratio/percentage using COUNT(...)/COUNT(...),
   always cast to avoid integer division truncation, e.g.
   COUNT(x)::numeric / COUNT(y)::numeric, or multiply the numerator by 1.0.
4. geolocation joins via zip code prefix columns, never via a
   geolocation_id - see schema notes above.
5. review_score lives ONLY in the order_reviews table. It is never a
   column on orders. Any question involving reviews or ratings
   requires an explicit JOIN order_reviews ON order_reviews.order_id
   = orders.order_id - never assume it exists elsewhere.
"""

def is_safe_select(sql: str) -> bool:
    """Only allow single, read-only SELECT statements."""
    cleaned = sql.strip().rstrip(";")
    if ";" in cleaned:
        return False
    forbidden = r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE)\b"
    if re.search(forbidden, cleaned, re.IGNORECASE):
        return False
    return cleaned.strip().upper().startswith("SELECT")

def generate_sql(question: str) -> str:
    context_chunks = retrieve(question, n_results=4)
    context = "\n\n".join(context_chunks)

    prompt = f"""You are a PostgreSQL expert. Given the schema info and business
definitions below, write ONE safe, read-only SELECT query to answer the question.

{FULL_SCHEMA_HINT}

{ALWAYS_RULES}

Relevant definitions and schema notes:
{context}

Question: {question}

Rules:
- Output ONLY the raw SQL query, no explanation, no markdown code fences.
- Only use SELECT. Never modify data.
- Always include a LIMIT unless the question requires an aggregate/single row.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    sql = response.choices[0].message.content.strip()
    sql = re.sub(r"^```sql\s*|```$", "", sql, flags=re.MULTILINE).strip()
    return sql

def run_query(question: str):
    sql = generate_sql(question)

    if not is_safe_select(sql):
        return {"error": "Generated query failed safety check.", "sql": sql}

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        results = [dict(zip(columns, row)) for row in rows]
        narration = generate_narration(question, results)
        return {"sql": sql, "results": results, "narration": narration}
    except Exception as e:
        return {"error": str(e), "sql": sql}
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    test_question = "What are the top 5 product categories by revenue?"
    output = run_query(test_question)
    print("SQL generated:\n", output.get("sql"))
    print("\nResults:\n", output.get("results") or output.get("error"))


def generate_narration(question: str, results: list) -> str:
    if not results:
        return "No results found for this question."
    sample = str(results[:10])
    prompt = f"""Given this question and query results, write ONE short,
plain-English sentence (max 30 words) summarizing the key insight.
Be specific with numbers. No preamble, just the sentence.

Question: {question}
Results: {sample}
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()
