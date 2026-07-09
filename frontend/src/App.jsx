import { Link, Navigate, Route, Routes } from "react-router-dom";

import "./App.css";
import { AuthProvider, useAuth } from "./auth/AuthContext.jsx";
import DashboardPage from "./pages/admin/DashboardPage.jsx";
import ReportExportPage from "./pages/admin/ReportExportPage.jsx";
import ReviewPage from "./pages/admin/ReviewPage.jsx";
import MyInvoicesPage from "./pages/employee/MyInvoicesPage.jsx";
import UploadPage from "./pages/employee/UploadPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";

/** 依角色決定畫面是否可存取；後端 API 一樣會驗證 role，這裡只是隱藏畫面用。 */
function ProtectedRoute({ children, requiredRole }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <p>載入中...</p>;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (requiredRole && user.role !== requiredRole && user.role !== "admin") {
    return <Navigate to="/" replace />;
  }

  return children;
}

function Nav() {
  const { user, logout } = useAuth();

  if (!user) {
    return null;
  }

  return (
    <nav style={{ display: "flex", gap: "1rem", padding: "1rem", background: "#fff" }}>
      {user.role === "admin" ? (
        <>
          <Link to="/admin/dashboard">儀表板</Link>
          <Link to="/admin/review">待審核</Link>
          <Link to="/admin/reports">匯出報表</Link>
        </>
      ) : (
        <>
          <Link to="/employee/upload">上傳發票</Link>
          <Link to="/employee/my-invoices">我的紀錄</Link>
        </>
      )}
      <span style={{ marginLeft: "auto" }}>
        {user.name}（{user.role === "admin" ? "總務" : "員工"}）
      </span>
      <button onClick={logout}>登出</button>
    </nav>
  );
}

function HomeRedirect() {
  const { user } = useAuth();
  const target = user?.role === "admin" ? "/admin/dashboard" : "/employee/upload";
  return <Navigate to={target} replace />;
}

function AppRoutes() {
  return (
    <>
      <Nav />
      <main style={{ padding: "1.5rem" }}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<HomeRedirect />} />
          <Route
            path="/employee/upload"
            element={
              <ProtectedRoute requiredRole="employee">
                <UploadPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/employee/my-invoices"
            element={
              <ProtectedRoute requiredRole="employee">
                <MyInvoicesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/dashboard"
            element={
              <ProtectedRoute requiredRole="admin">
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/review"
            element={
              <ProtectedRoute requiredRole="admin">
                <ReviewPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/reports"
            element={
              <ProtectedRoute requiredRole="admin">
                <ReportExportPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>
    </>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}
