from agent import run_query

test_questions = [
    "What are the top 5 product categories by revenue?",
    "How many orders were delivered late?",
    "What is the average order value?",
    "Which state has the most customers?",
    "What is the most common payment type?",
    "How many active sellers are there?",
    "What is the average delivery time in days?",
    "Which product category has the lowest average review score?",
    "What percentage of orders were canceled?",
    "Show total revenue by month for 2018",
    "Which sellers have the highest total revenue?",
    "What is the return rate by product category?",
    "How many orders had more than one item?",
    "What is the average freight value by state?",
]

for i, q in enumerate(test_questions, 1):
    print(f"\n{'='*70}")
    print(f"Q{i}: {q}")
    print('='*70)
    result = run_query(q)
    if "error" in result:
        print(f"❌ ERROR: {result['error']}")
        print(f"SQL attempted:\n{result['sql']}")
    else:
        print(f"✅ SQL:\n{result['sql']}")
        print(f"\nResults (first 3 rows): {result['results'][:3]}")
