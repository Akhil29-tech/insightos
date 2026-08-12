# InsightOS

**An AI data analyst for retail teams — ask questions in plain English, get grounded SQL, charts, and insights back in seconds.**

Live demo: `https://insightos-app.netlify.app`
Backend API: `https://insightos-plcd.onrender.com`

## The problem

Analysts spend a large chunk of their week acting as a human query layer between stakeholders and the database — "can you pull me the numbers for X" requests that interrupt real analysis work. Static BI dashboards help, but they don't answer the follow-up question, and different teams often calculate the same metric ("revenue," "active customer") inconsistently, leading to conflicting numbers and eroded trust in the data.

InsightOS lets non-technical stakeholders ask business questions directly, in plain English, and get back a grounded, explainable answer — with the exact SQL and the "official" metric definition it relied on always visible. The goal isn't just convenience; it's trust. Every answer is traceable.

## How it works

1. A stakeholder asks a question ("which product categories drove the most revenue last quarter?")
2. The question is embedded and matched against a small knowledge base of **metric definitions and schema documentation** (RAG, via Chroma + local `sentence-transformers` embeddings — no embedding API cost)
3. Retrieved context + the question go to an LLM (Groq, Llama 3.3 70B) which writes a single read-only SQL query
4. The query is validated (SELECT-only, no destructive statements) and executed against Postgres using a dedicated **read-only database role**
5. Results come back as a chart, a plain-English insight sentence, and the SQL itself — fully visible and editable
6. Findings can be exported into a presentation deck with one click, for sharing in meetings

## Architecture

- **Database:** PostgreSQL (Supabase), seeded with the Olist Brazilian E-Commerce dataset (~99K orders, 9 relational tables)
- **Backend:** FastAPI, deployed on Render
- **Agent:** Groq (Llama 3.3 70B) for SQL generation and insight narration
- **RAG:** ChromaDB + local `sentence-transformers` embeddings (no external embedding API — zero cost, no rate limits)
- **Frontend:** React (Vite), deployed on Netlify
- **Presentation export:** python-pptx, generates a deck from the current session's findings

## Design decisions worth knowing about

**Read-only by design, at the database level, not just the app level.** The agent connects through a dedicated Postgres role (`insightos_agent`) with `SELECT`-only grants — no `INSERT`/`UPDATE`/`DELETE`/`DROP`. Even if a prompt injection or a bug caused the LLM to generate a destructive query, the database itself would refuse it. The app layer also independently validates that generated SQL is a single `SELECT` statement before execution — defense in depth.

**RAG grounding as a trust mechanism, not just a QA aid.** Early testing surfaced a recurring failure: the model would hallucinate a `quantity` column that doesn't exist in the Olist schema (a common assumption from general e-commerce training data), leading to silently wrong revenue calculations. Rather than patch each occurrence, the fix went into the knowledge base itself — and separately, a small set of "always apply" rules got added directly to every prompt (not just RAG-retrievable), for the handful of facts that are too important to depend on retrieval happening to surface them.

**Historical data needs an explicit "now."** The dataset covers Sept 2016–Aug 2018. Early on, a question like "how many active sellers are there" silently returned zero — because the agent computed "last 90 days" against the real current date, which is years past the data. The fix: any recency logic is computed relative to the dataset's own most recent order (`MAX(order_purchase_timestamp)`), not `CURRENT_DATE`. This is a subtle but realistic problem any team working with a periodically-refreshed warehouse will recognize.

**Integer division silently truncates.** A return-rate calculation (`COUNT(x) / COUNT(y)`) returned `0` for every category — Postgres performs integer division when both operands are whole numbers, silently flooring anything under 1. Fixed by explicitly casting to `numeric`. Worth knowing because it fails silently, not with an error — the kind of bug that produces confidently wrong numbers.

**RLS closes the public API surface, without touching the app's own access.** Supabase auto-generates a public REST API for every table. Since InsightOS never uses that API (the backend connects via `psycopg2` directly), enabling Row-Level Security with zero policies closes that public surface entirely — while granting the app's own database role `BYPASSRLS` keeps the actual application unaffected.

## What's next

- CSV/file upload as a second data source, for teams without direct database access
- Slack integration — ask InsightOS a question directly from the channel where the ad-hoc request would have been made in the first place
- Expanding the metric "rulebook" as more real questions surface edge cases

## Local setup

```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# add GROQ_API_KEY and DATABASE_URL to .env
python rag.py         # build the knowledge base index
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```
