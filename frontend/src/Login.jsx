import { useState } from "react";

const API = "http://localhost:8000";

export default function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error,    setError]    = useState("");
  const [loading,  setLoading]  = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch(`${API}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || "Login fail ho gaya");
      } else {
        localStorage.setItem("token",    data.access_token);
        localStorage.setItem("role",     data.role);
        localStorage.setItem("username", data.username);
        onLogin(data);
      }
    } catch {
      setError("Server se connect nahi ho saka");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <h1 style={styles.logo}>AutoOps AI</h1>
        <p style={styles.tagline}>AI Email Operations Assistant</p>

        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.field}>
            <label style={styles.label}>Username</label>
            <input
              style={styles.input}
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="admin / manager / viewer"
              required
              autoFocus
            />
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Password</label>
            <input
              style={styles.input}
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          {error && <div style={styles.error}>{error}</div>}

          <button style={styles.btn} type="submit" disabled={loading}>
            {loading ? "Logging in..." : "Login →"}
          </button>
        </form>

        <div style={styles.hint}>
          <p style={styles.hintTitle}>Demo Accounts:</p>
          <p>👑 admin / admin123</p>
          <p>📋 manager / manager123</p>
          <p>👁 viewer / viewer123</p>
        </div>
      </div>
    </div>
  );
}

const styles = {
  page:     { background: "#0f0f1a", minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'Segoe UI', sans-serif" },
  card:     { background: "#1e1e2e", border: "1px solid #2a2a4a", borderRadius: 16, padding: "40px 36px", width: "100%", maxWidth: 380 },
  logo:     { color: "#6366f1", fontSize: "1.8rem", textAlign: "center", margin: "0 0 6px", letterSpacing: 2 },
  tagline:  { color: "#64748b", textAlign: "center", fontSize: "0.85rem", marginBottom: 30 },
  form:     { display: "flex", flexDirection: "column", gap: 16 },
  field:    { display: "flex", flexDirection: "column", gap: 6 },
  label:    { color: "#94a3b8", fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: 1 },
  input:    { background: "#0f0f1a", border: "1px solid #2a2a4a", borderRadius: 8, padding: "10px 14px", color: "#e2e8f0", fontSize: "0.95rem", outline: "none" },
  error:    { background: "#450a0a", border: "1px solid #ef4444", borderRadius: 8, padding: "10px 14px", color: "#fca5a5", fontSize: "0.85rem" },
  btn:      { background: "#6366f1", color: "#fff", border: "none", borderRadius: 8, padding: "12px", fontSize: "1rem", fontWeight: "bold", cursor: "pointer", marginTop: 4 },
  hint:     { marginTop: 24, padding: "14px", background: "#0f0f1a", borderRadius: 8, fontSize: "0.8rem", color: "#475569", lineHeight: 1.8 },
  hintTitle:{ color: "#64748b", fontWeight: "bold", marginBottom: 4 },
};
