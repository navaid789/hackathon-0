import { useState, useEffect } from "react";

const API = "http://localhost:8000";

const FOLDER_COLORS = {
  Inbox:            "#6366f1",
  Needs_Action:     "#f59e0b",
  Plans:            "#8b5cf6",
  Pending_Approval: "#ef4444",
  Approved:         "#10b981",
  Done:             "#22c55e",
  Logs:             "#64748b",
};

export default function App() {
  const [status,  setStatus]  = useState({});
  const [pending, setPending] = useState([]);
  const [report,  setReport]  = useState({});
  const [time,    setTime]    = useState(new Date().toLocaleTimeString());

  const fetchData = async () => {
    const [s, p, r] = await Promise.all([
      fetch(`${API}/api/status`).then(r => r.json()),
      fetch(`${API}/api/pending`).then(r => r.json()),
      fetch(`${API}/api/report`).then(r => r.json()),
    ]);
    setStatus(s);
    setPending(p.pending || []);
    setReport(r);
    setTime(new Date().toLocaleTimeString());
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const approve = async (filename) => {
    await fetch(`${API}/api/approve/${filename}`, { method: "POST" });
    fetchData();
  };

  const reject = async (filename) => {
    await fetch(`${API}/api/reject/${filename}`, { method: "POST" });
    fetchData();
  };

  return (
    <div style={styles.app}>
      {/* Header */}
      <div style={styles.header}>
        <h1 style={styles.title}>AutoOps AI</h1>
        <p style={styles.subtitle}>AI Email Operations Assistant</p>
        <div style={styles.statusBadge}>
          <span style={styles.dot} /> Online · Last updated: {time}
        </div>
      </div>

      {/* CEO Report */}
      <div style={styles.reportRow}>
        {[
          { label: "Total Processed",  value: report.total_processed  ?? 0, color: "#6366f1" },
          { label: "Needs Action",     value: report.needs_action     ?? 0, color: "#f59e0b" },
          { label: "Pending Approval", value: report.pending_approval ?? 0, color: "#ef4444" },
          { label: "Completed",        value: report.tasks_completed  ?? 0, color: "#22c55e" },
        ].map(({ label, value, color }) => (
          <div key={label} style={{ ...styles.reportCard, borderTop: `3px solid ${color}` }}>
            <div style={{ ...styles.reportNum, color }}>{value}</div>
            <div style={styles.reportLabel}>{label}</div>
          </div>
        ))}
      </div>

      {/* Folder Grid */}
      <h2 style={styles.sectionTitle}>Workflow Status</h2>
      <div style={styles.flow}>
        {["Inbox","Needs_Action","Plans","Pending_Approval","Approved","Done"].map((f, i, arr) => (
          <span key={f}>
            <span style={{ color: FOLDER_COLORS[f] }}>{f.replace("_"," ")}</span>
            {i < arr.length - 1 && <span style={{ color: "#334155" }}> → </span>}
          </span>
        ))}
      </div>

      <div style={styles.grid}>
        {Object.entries(status).map(([folder, data]) => (
          <div key={folder} style={{ ...styles.card, borderTop: `3px solid ${FOLDER_COLORS[folder] || "#475569"}` }}>
            <div style={styles.cardTitle}>{folder.replace("_", " ")}</div>
            <div style={{ ...styles.cardCount, color: FOLDER_COLORS[folder] || "#94a3b8" }}>
              {data?.count ?? 0}
            </div>
            <div style={styles.fileList}>
              {data?.files?.length > 0
                ? data.files.map(f => (
                    <div key={f.name} style={styles.fileItem}>
                      <span>📄 {f.name}</span>
                      <span style={styles.fileTime}>{f.modified}</span>
                    </div>
                  ))
                : <div style={styles.empty}>Khali hai</div>
              }
            </div>
          </div>
        ))}
      </div>

      {/* Pending Approval */}
      {pending.length > 0 && (
        <>
          <h2 style={styles.sectionTitle}>⏳ Pending Approval</h2>
          {pending.map(item => (
            <div key={item.name} style={styles.pendingCard}>
              <div style={styles.pendingHeader}>
                <span style={styles.pendingName}>📧 {item.name}</span>
                <span style={styles.pendingTime}>{item.modified}</span>
              </div>
              <pre style={styles.pendingContent}>{item.content}</pre>
              <div style={styles.btnRow}>
                <button style={styles.approveBtn} onClick={() => approve(item.name)}>✓ Approve</button>
                <button style={styles.rejectBtn}  onClick={() => reject(item.name)}>✗ Reject</button>
              </div>
            </div>
          ))}
        </>
      )}

      <div style={styles.footer}>AutoOps AI · Built with Python + React</div>
    </div>
  );
}

const styles = {
  app:           { background: "#0f0f1a", minHeight: "100vh", color: "#e2e8f0", fontFamily: "'Segoe UI', sans-serif", padding: "30px 20px" },
  header:        { textAlign: "center", marginBottom: 30 },
  title:         { fontSize: "2.2rem", color: "#6366f1", letterSpacing: 3, margin: 0 },
  subtitle:      { color: "#64748b", marginTop: 6, fontSize: "0.9rem" },
  statusBadge:   { display: "inline-flex", alignItems: "center", gap: 8, background: "#1e1e2e", padding: "6px 16px", borderRadius: 20, marginTop: 12, fontSize: "0.8rem", color: "#94a3b8" },
  dot:           { width: 8, height: 8, background: "#22c55e", borderRadius: "50%", display: "inline-block" },
  reportRow:     { display: "flex", gap: 16, marginBottom: 30, flexWrap: "wrap" },
  reportCard:    { flex: 1, minWidth: 140, background: "#1e1e2e", borderRadius: 12, padding: "20px 16px", textAlign: "center" },
  reportNum:     { fontSize: "2.4rem", fontWeight: "bold" },
  reportLabel:   { fontSize: "0.75rem", color: "#64748b", marginTop: 4 },
  sectionTitle:  { color: "#94a3b8", fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: 2, marginBottom: 16 },
  flow:          { textAlign: "center", marginBottom: 20, fontSize: "0.85rem" },
  grid:          { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 16, marginBottom: 30 },
  card:          { background: "#1e1e2e", borderRadius: 12, padding: 16, border: "1px solid #1e293b" },
  cardTitle:     { fontSize: "0.7rem", textTransform: "uppercase", color: "#64748b", letterSpacing: 1, marginBottom: 8 },
  cardCount:     { fontSize: "2rem", fontWeight: "bold", marginBottom: 10 },
  fileList:      { fontSize: "0.75rem" },
  fileItem:      { padding: "4px 0", borderBottom: "1px solid #1e293b", display: "flex", justifyContent: "space-between" },
  fileTime:      { color: "#475569", fontSize: "0.65rem" },
  empty:         { color: "#334155", fontStyle: "italic" },
  pendingCard:   { background: "#1e1e2e", border: "1px solid #ef4444", borderRadius: 12, padding: 20, marginBottom: 16 },
  pendingHeader: { display: "flex", justifyContent: "space-between", marginBottom: 12 },
  pendingName:   { color: "#ef4444", fontWeight: "bold" },
  pendingTime:   { color: "#475569", fontSize: "0.8rem" },
  pendingContent:{ background: "#0f0f1a", padding: 12, borderRadius: 8, fontSize: "0.8rem", color: "#94a3b8", whiteSpace: "pre-wrap", marginBottom: 12 },
  btnRow:        { display: "flex", gap: 12 },
  approveBtn:    { flex: 1, padding: "10px", background: "#22c55e", color: "#fff", border: "none", borderRadius: 8, cursor: "pointer", fontWeight: "bold", fontSize: "0.9rem" },
  rejectBtn:     { flex: 1, padding: "10px", background: "#ef4444", color: "#fff", border: "none", borderRadius: 8, cursor: "pointer", fontWeight: "bold", fontSize: "0.9rem" },
  footer:        { textAlign: "center", color: "#334155", fontSize: "0.75rem", marginTop: 40 },
};
