import { useState, useEffect } from "react";
import axios from "axios";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [current, setCurrent] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [sqlDraft, setSqlDraft] = useState("");
  const [sqlResult, setSqlResult] = useState(null);
  const [sqlRunning, setSqlRunning] = useState(false);
  const [sqlHistory, setSqlHistory] = useState([]);

  useEffect(() => {
    const saved = localStorage.getItem("insightos_sql_history");
    if (saved) {
      try {
        setSqlHistory(JSON.parse(saved));
      } catch (e) {}
    }
  }, []);

  const runSql = async () => {
    setSqlRunning(true);
    try {
      const res = await axios.post(`${API_URL}/run-sql`, { sql: sqlDraft });
      setSqlResult(res.data);
      if (!res.data.error) {
        const updated = [{ sql: sqlDraft, timestamp: Date.now() }, ...sqlHistory].slice(0, 20);
        setSqlHistory(updated);
        localStorage.setItem("insightos_sql_history", JSON.stringify(updated));
      }
    } catch (err) {
      setSqlResult({ error: "Request failed. Is the backend running?" });
    }
    setSqlRunning(false);
  };

  useEffect(() => {
    const saved = localStorage.getItem("insightos_history");
    if (saved) {
      try {
        setHistory(JSON.parse(saved));
      } catch (e) {}
    }
  }, []);

  useEffect(() => {
    axios.get(`${API_URL}/metrics`).then((res) => setMetrics(res.data)).catch(() => {});
  }, []);

  const createPresentation = async () => {
    if (history.length === 0) return;
    try {
      const res = await axios.post(
        `${API_URL}/export-presentation`,
        { entries: history },
        { responseType: "blob" }
      );
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "InsightOS_Findings.pptx");
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert("Failed to generate presentation.");
    }
  };

  const askQuestion = async () => {
    if (!question.trim()) return;
    setLoading(true);
    try {
      const res = await axios.post(`${API_URL}/query`, { question });
      const entry = { question, ...res.data };
      setCurrent(entry);
      setSqlDraft(entry.sql || "");
      setSqlResult(null);
      const updatedHistory = [entry, ...history];
      setHistory(updatedHistory);
      localStorage.setItem("insightos_history", JSON.stringify(updatedHistory));
      setQuestion("");
    } catch (err) {
      setCurrent({ question, error: "Request failed. Is the backend running?" });
    }
    setLoading(false);
  };

  const chartData =
    current?.results && current.results.length > 0 && !current.error
      ? current.results.map((row) => {
          const keys = Object.keys(row);
          const labelKey = keys.find((k) => typeof row[k] === "string") || keys[0];
          const valueKey = keys.find((k) => typeof row[k] !== "string") || keys[1];
          return { label: String(row[labelKey]), value: Number(row[valueKey]) };
        })
      : [];

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="tabs">
          <div
            className={`tab ${activeTab === "data" ? "active" : ""}`}
            onClick={() => setActiveTab("data")}
          >
            Data source
          </div>
          <div
            className={`tab ${activeTab === "sql" ? "active" : ""}`}
            onClick={() => setActiveTab("sql")}
          >
            SQL query
          </div>
          <div
            className={`tab ${activeTab === "dashboard" ? "active" : ""}`}
            onClick={() => setActiveTab("dashboard")}
          >
            Dashboard
          </div>
        </div>
        <div className="history">
          <div className="history-label">HISTORY</div>
          {history.map((h, i) => (
            <div
              key={i}
              className="history-item"
              onClick={() => setCurrent(h)}
            >
              {h.question}
            </div>
          ))}
        </div>
      </aside>

      <main className="main">
        {activeTab === "dashboard" && (
          <>
            <div className="metrics-header-row">
              {metrics && (
                <div className="metrics-row">
                <div className="metric-card">
                  <div className="metric-label">Revenue</div>
                  <div className="metric-value">
                    R$ {(metrics.revenue / 1000000).toFixed(1)}M
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Orders</div>
                  <div className="metric-value">{metrics.orders.toLocaleString()}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Active sellers</div>
                  <div className="metric-value">{metrics.active_sellers}</div>
                </div>
                </div>
              )}
              <button className="presentation-btn" onClick={createPresentation} disabled={history.length === 0}>
                Create presentation
              </button>
            </div>
            {current?.error && <div className="error-box">{current.error}</div>}

            {current && !current.error && (
              <div className="card">
                <div className="question-text">{current.question}</div>
                {current.narration && (
                  <div className="narration-text">{current.narration}</div>
                )}
                {chartData.length > 0 && (
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={chartData}>
                      <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Bar dataKey="value" fill="#1D9E75" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
                <pre className="raw-results">
                  {JSON.stringify(current.results, null, 2)}
                </pre>
              </div>
            )}

            {!current && (
              <div className="empty-state">
                Ask a question below to get started.
              </div>
            )}

            <div className="input-row">
              <input
                type="text"
                placeholder="Ask a question about your retail data"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && askQuestion()}
              />
              <button onClick={askQuestion} disabled={loading}>
                {loading ? "..." : "→"}
              </button>
            </div>
          </>
        )}

        {activeTab === "sql" && (
          <div className="card">
            <div className="sql-editor-header">
              <div className="sql-label">SQL EDITOR</div>
              <button className="run-btn" onClick={runSql} disabled={sqlRunning || !sqlDraft.trim()}>
                {sqlRunning ? "Running..." : "Run"}
              </button>
            </div>
            <textarea
              className="sql-textarea"
              value={sqlDraft}
              onChange={(e) => setSqlDraft(e.target.value)}
              placeholder="Ask a question in Dashboard first, or write your own SELECT query here"
              rows={6}
            />
            {sqlResult?.error && <div className="error-box">{sqlResult.error}</div>}
            {sqlResult?.results && (
              <pre className="raw-results">{JSON.stringify(sqlResult.results, null, 2)}</pre>
            )}

            {sqlHistory.length > 0 && (
              <div className="sql-history">
                <div className="sql-history-label">PREVIOUS QUERIES</div>
                {sqlHistory.map((h, i) => (
                  <div
                    key={i}
                    className="sql-history-item"
                    onClick={() => { setSqlDraft(h.sql); setSqlResult(null); }}
                  >
                    {h.sql.length > 80 ? h.sql.slice(0, 80) + "..." : h.sql}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "data" && (
          <div className="card">Data source config coming soon.</div>
        )}
      </main>
    </div>
  );
}

export default App;
