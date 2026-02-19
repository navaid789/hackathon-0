import { useState, useEffect } from "react";
import Login from "./Login";

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

const ROLE_BADGE = {
  admin:   { bg: "#4f46e5", label: "👑 Admin" },
  manager: { bg: "#0891b2", label: "📋 Manager" },
  viewer:  { bg: "#475569", label: "👁 Viewer" },
};

export default function App() {
  const [auth,    setAuth]    = useState(() => ({
    token:    localStorage.getItem("token"),
    role:     localStorage.getItem("role"),
    username: localStorage.getItem("username"),
  }));
  const [status,  setStatus]  = useState({});
  const [pending, setPending] = useState([]);
  const [report,  setReport]  = useState({});
  const [time,    setTime]    = useState(new Date().toLocaleTimeString());
  const [toast,   setToast]   = useState(null);

  const authHeaders = {
    "Authorization": `Bearer ${auth.token}`
  };

  const showToast = (msg, color = "#22c55e") => {
    setToast({ msg, color });
    setTimeout(() => setToast(null), 3000);
  };

  const fetchData = async () => {
    if (!auth.token) return;
    try {
      const [s, p, r] = await Promise.all([
        fetch(`${API}/api/status`,  { headers: authHeaders }).then(r => r.json()),
        fetch(`${API}/api/pending`, { headers: authHeaders }).then(r => r.json()),
        fetch(`${API}/api/report`,  { headers: authHeaders }).then(r => r.json()),
      ]);
      setStatus(s);
      setPending(p.pending || []);
      setReport(r);
      setTime(new Date().toLocaleTimeString());
    } catch {
      showToast("Server se connect nahi ho saka", "#ef4444");
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [auth.token]);

  const handleLogin = (data) => setAuth({ token: data.access_token, role: data.role, username: data.username });

  const handleLogout = () => {
    localStorage.clear();
    setAuth({ token: null, role: null, username: null });
  };

  const approve = async (filename) => {
    const res  = await fetch(`${API}/api/approve/${filename}`, { method: "POST", headers: authHeaders });
    const data = await res.json();
    if (res.ok) showToast(`✓ Approved: ${filename}`);
    else        showToast(data.detail, "#ef4444");
    fetchData();
  };

  const reject = async (filename) => {
    const res  = await fetch(`${API}/api/reject/${filename}`, { method: "POST", headers: authHeaders });
    const data = await res.json();
    if (res.ok) showToast(`✗ Rejected: ${filename}`, "#f59e0b");
    else        showToast(data.detail, "#ef4444");
    fetchData();
  };

  const canApprove = auth.role === "admin" || auth.role === "manager";

  if (!auth.token) return <Login onLogin={handleLogin} />;

  return (
    <div style={styles.app}>

      {/* Toast */}
      {toast && (
        <div style={{ ...styles.toast, background: toast.color }}>
          {toast.msg}
        </div>
      )}

      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>AutoOps AI</h1>
          <p style={styles.subtitle}>AI Email Operations Assistant</p>
        </div>
        <div style={styles.userInfo}>
          <span style={{ ...styles.roleBadge, background: ROLE_BADGE[auth.role]?.bg }}>
            {ROLE_BADGE[auth.role]?.label}
          </span>
          <span style={styles.username}>{auth.username}</span>
          <button style={styles.logoutBtn} onClick={handleLogout}>Logout</button>
        </div>
      </div>

      {/* Status Bar */}
      <div style={styles.statusBar}>
        <span style={styles.dot} /> Online · {time}
      </div>

      {/* CEO Report Cards */}
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

      {/* Priority Breakdown */}
      {report.priority_breakdown && (
        <div style={styles.priorityRow}>
          <span style={styles.priorityItem}>🔴 High: {report.priority_breakdown.high}</span>
          <span style={styles.priorityItem}>🟡 Medium: {report.priority_breakdown.medium}</span>
          <span style={styles.priorityItem}>🟢 Low: {report.priority_breakdown.low}</span>
        </div>
      )}

      {/* Workflow */}
      <h2 style={styles.sectionTitle}>Workflow Status</h2>
      <div style={styles.flow}>
        {["Inbox","Needs_Action","Plans","Pending_Approval","Approved","Done"].map((f, i, arr) => (
          <span key={f}>
            <span style={{ color: FOLDER_COLORS[f] }}>{f.replace("_"," ")}</span>
            {i < arr.length - 1 && <span style={{ color: "#334155" }}> → </span>}
          </span>
        ))}
      </div>

      {/* Folder Grid */}
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
                <div>
                  <span style={styles.pendingName}>📧 {item.name}</span>
                  <span style={{ marginLeft: 12, fontSize: "0.8rem" }}>{item.priority}</span>
                  <span style={{ marginLeft: 8, color: "#64748b", fontSize: "0.8rem" }}>👤 {item.client}</span>
                </div>
                <span style={styles.pendingTime}>{item.modified}</span>
              </div>
              <pre style={styles.pendingContent}>{item.content}</pre>
              {canApprove ? (
                <div style={styles.btnRow}>
                  <button style={styles.approveBtn} onClick={() => approve(item.name)}>✓ Approve</button>
                  <button style={styles.rejectBtn}  onClick={() => reject(item.name)}>✗ Reject</button>
                </div>
              ) : (
                <div style={styles.noPermission}>👁 Viewer — approve/reject ka permission nahi</div>
              )}
            </div>
          ))}
        </>
      )}

      <div style={styles.footer}>AutoOps AI · {auth.username} ({auth.role}) · Built with Python + React</div>
    </div>
  );
}

const styles = {
  app:          { background: "#0f0f1a", minHeight: "100vh", color: "#e2e8f0", fontFamily: "'Segoe UI', sans-serif", padding: "24px 20px" },
  toast:        { position: "fixed", top: 20, right: 20, padding: "12px 20px", borderRadius: 10, color: "#fff", fontWeight: "bold", zIndex: 999, fontSize: "0.9rem" },
  header:       { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 },
  title:        { fontSize: "1.8rem", color: "#6366f1", letterSpacing: 2, margin: 0 },
  subtitle:     { color: "#64748b", marginTop: 4, fontSize: "0.85rem" },
  userInfo:     { display: "flex", alignItems: "center", gap: 10 },
  roleBadge:    { padding: "4px 12px", borderRadius: 20, fontSize: "0.75rem", color: "#fff", fontWeight: "bold" },
  username:     { color: "#94a3b8", fontSize: "0.85rem" },
  logoutBtn:    { background: "transparent", border: "1px solid #334155", color: "#94a3b8", borderRadius: 8, padding: "6px 14px", cursor: "pointer", fontSize: "0.8rem" },
  statusBar:    { display: "flex", alignItems: "center", gap: 8, color: "#64748b", fontSize: "0.8rem", marginBottom: 24 },
  dot:          { width: 8, height: 8, background: "#22c55e", borderRadius: "50%", display: "inline-block" },
  reportRow:    { display: "flex", gap: 16, marginBottom: 16, flexWrap: "wrap" },
  reportCard:   { flex: 1, minWidth: 140, background: "#1e1e2e", borderRadius: 12, padding: "18px 16px", textAlign: "center" },
  reportNum:    { fontSize: "2.2rem", fontWeight: "bold" },
  reportLabel:  { fontSize: "0.75rem", color: "#64748b", marginTop: 4 },
  priorityRow:  { display: "flex", gap: 20, marginBottom: 24, fontSize: "0.85rem", color: "#94a3b8" },
  priorityItem: { background: "#1e1e2e", padding: "6px 14px", borderRadius: 20 },
  sectionTitle: { color: "#94a3b8", fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: 2, marginBottom: 12 },
  flow:         { textAlign: "center", marginBottom: 20, fontSize: "0.85rem" },
  grid:         { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 16, marginBottom: 30 },
  card:         { background: "#1e1e2e", borderRadius: 12, padding: 16, border: "1px solid #1e293b" },
  cardTitle:    { fontSize: "0.7rem", textTransform: "uppercase", color: "#64748b", letterSpacing: 1, marginBottom: 8 },
  cardCount:    { fontSize: "2rem", fontWeight: "bold", marginBottom: 10 },
  fileList:     { fontSize: "0.75rem" },
  fileItem:     { padding: "4px 0", borderBottom: "1px solid #1e293b", display: "flex", justifyContent: "space-between" },
  fileTime:     { color: "#475569", fontSize: "0.65rem" },
  empty:        { color: "#334155", fontStyle: "italic" },
  pendingCard:  { background: "#1e1e2e", border: "1px solid #ef4444", borderRadius: 12, padding: 20, marginBottom: 16 },
  pendingHeader:{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 },
  pendingName:  { color: "#ef4444", fontWeight: "bold" },
  pendingTime:  { color: "#475569", fontSize: "0.8rem" },
  pendingContent:{ background: "#0f0f1a", padding: 12, borderRadius: 8, fontSize: "0.8rem", color: "#94a3b8", whiteSpace: "pre-wrap", marginBottom: 12 },
  btnRow:       { display: "flex", gap: 12 },
  approveBtn:   { flex: 1, padding: "10px", background: "#22c55e", color: "#fff", border: "none", borderRadius: 8, cursor: "pointer", fontWeight: "bold" },
  rejectBtn:    { flex: 1, padding: "10px", background: "#ef4444", color: "#fff", border: "none", borderRadius: 8, cursor: "pointer", fontWeight: "bold" },
  noPermission: { color: "#475569", fontSize: "0.85rem", textAlign: "center", padding: 10, background: "#0f0f1a", borderRadius: 8 },
  footer:       { textAlign: "center", color: "#334155", fontSize: "0.75rem", marginTop: 40 },
};
