import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])

if __name__ == "__main__":
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM orders;")
    result = cur.fetchone()
    print(f"Connected! Orders count: {result[0]}")
    cur.close()
    conn.close()
