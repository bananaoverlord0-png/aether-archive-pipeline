"use client";
import { useEffect, useState } from "react";

type Topic = {
  id: string;
  title: string;
  opportunity_score: number;
  status: string;
};

export default function Dashboard() {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch("http://localhost:8000/topics")
      .then((r) => r.json())
      .then(setTopics)
      .catch(() => setTopics([]));
  }, []);

  async function runPipeline(title?: string) {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/pipeline/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: title, mode: "demo" }),
      });
      setSummary(await res.json());
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ fontFamily: "system-ui", background: "#0b1215", color: "#d8e6ea", minHeight: "100vh", padding: 32 }}>
      <h1 style={{ letterSpacing: 2 }}>AETHER ARCHIVE</h1>
      <p style={{ opacity: 0.7 }}>Where evidence meets the unknown.</p>
      <section style={{ marginTop: 32 }}>
        <h2>Topic Candidates</h2>
        <ul>
          {topics.map((t) => (
            <li key={t.id} style={{ marginBottom: 12 }}>
              <strong>{t.opportunity_score.toFixed(3)}</strong> — {t.title}{" "}
              <button onClick={() => runPipeline(t.title)} disabled={loading} style={{ marginLeft: 8 }}>
                Produce
              </button>
            </li>
          ))}
        </ul>
        <button onClick={() => runPipeline()} disabled={loading}>
          {loading ? "Running…" : "Run best topic (demo)"}
        </button>
      </section>
      {summary && (
        <pre style={{ marginTop: 24, background: "#121a1e", padding: 16, overflow: "auto" }}>
          {JSON.stringify(summary, null, 2)}
        </pre>
      )}
    </main>
  );
}
