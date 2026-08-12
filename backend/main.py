from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import Response
from typing import List, Optional, Any
from presentation import build_presentation
from agent import is_safe_select
from db import get_connection
from agent import run_query

app = FastAPI(title="InsightOS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

class HistoryEntry(BaseModel):
    question: str
    narration: Optional[str] = ""
    sql: Optional[str] = ""
    results: Optional[List[dict]] = []

class ExportRequest(BaseModel):
    entries: List[HistoryEntry]

class SQLRequest(BaseModel):
    sql: str

@app.get("/")
def health_check():
    return {"status": "InsightOS API is running"}

@app.post("/query")
def query(request: QuestionRequest):
    result = run_query(request.question)
    return result

@app.get("/metrics")
def metrics():
    from db import get_connection
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT SUM(oi.price) FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        WHERE o.order_status = 'delivered';
    """)
    revenue = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM orders;")
    orders = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(DISTINCT oi.seller_id) FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        WHERE o.order_purchase_timestamp > (SELECT MAX(order_purchase_timestamp) FROM orders) - INTERVAL '90 days';
    """)
    active_sellers = cur.fetchone()[0]

    cur.close()
    conn.close()

    return {
        "revenue": float(revenue) if revenue else 0,
        "orders": orders,
        "active_sellers": active_sellers,
    }

@app.post("/export-presentation")
def export_presentation(request: ExportRequest):
    entries = [e.dict() for e in request.entries]
    pptx_bytes = build_presentation(entries)
    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": "attachment; filename=InsightOS_Findings.pptx"},
    )

@app.post("/run-sql")
def run_sql(request: SQLRequest):
    if not is_safe_select(request.sql):
        return {"error": "Query failed safety check. Only single SELECT statements are allowed."}

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(request.sql)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        results = [dict(zip(columns, row)) for row in rows]
        return {"sql": request.sql, "results": results}
    except Exception as e:
        return {"error": str(e), "sql": request.sql}
    finally:
        cur.close()
        conn.close()
