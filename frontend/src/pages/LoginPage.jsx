import { Navigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext.jsx";

export default function LoginPage() {
  const { user, loading, error, login } = useAuth();

  if (loading) {
    return <p>載入中...</p>;
  }

  if (user) {
    return <Navigate to="/" replace />;
  }

  return (
    <div style={{ display: "grid", placeItems: "center", height: "100vh" }}>
      <div style={{ textAlign: "center" }}>
        <h1>發票自動報帳系統</h1>
        <p>請用公司 Google 帳號登入</p>
        {error && <p style={{ color: "#c02929" }}>{error}</p>}
        <button onClick={login} style={{ padding: "10px 24px", fontSize: "1rem" }}>
          使用 Google 登入
        </button>
      </div>
    </div>
  );
}
