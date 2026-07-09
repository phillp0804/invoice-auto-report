import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getDashboard } from "../../api/invoiceApi.js";

const cellStyle = { border: "1px solid #ddd", padding: "0.5rem", textAlign: "left" };

function SummaryTable({ title, rows, getLabel, getKey }) {
  return (
    <div style={{ marginBottom: "1.5rem" }}>
      <h3>{title}</h3>
      {rows.length === 0 ? (
        <p>無資料</p>
      ) : (
        <table style={{ borderCollapse: "collapse", width: "100%" }}>
          <thead>
            <tr>
              <th style={cellStyle}>項目</th>
              <th style={cellStyle}>金額</th>
              <th style={cellStyle}>件數</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={getKey(row)}>
                <td style={cellStyle}>{getLabel(row)}</td>
                <td style={cellStyle}>NT$ {row.total_amount}</td>
                <td style={cellStyle}>{row.count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default function DashboardPage() {
  const now = new Date();
  const [year, setYear] = useState(String(now.getFullYear()));
  const [month, setMonth] = useState(String(now.getMonth() + 1));
  // 預設顯示本月彙整，清除篩選後才會改成顯示全部已確認發票
  const [filter, setFilter] = useState({ year: now.getFullYear(), month: now.getMonth() + 1 });
  const [dashboard, setDashboard] = useState(null);
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    setStatus("loading");
    getDashboard(filter)
      .then((result) => {
        if (cancelled) return;
        setDashboard(result);
        setStatus("loaded");
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err.message);
        setStatus("error");
      });

    return () => {
      cancelled = true;
    };
  }, [filter]);

  const handleApplyFilter = (event) => {
    event.preventDefault();
    setFilter({
      year: year ? Number(year) : undefined,
      month: month ? Number(month) : undefined,
    });
  };

  const handleClearFilter = () => {
    setYear("");
    setMonth("");
    setFilter({});
  };

  return (
    <div style={{ maxWidth: 720 }}>
      <h2>總務儀表板</h2>

      <form
        onSubmit={handleApplyFilter}
        style={{ display: "flex", gap: "0.5rem", alignItems: "flex-end", marginBottom: "1.5rem" }}
      >
        <label>
          年
          <br />
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(e.target.value)}
            placeholder="例如 2024"
            style={{ width: 100 }}
          />
        </label>
        <label>
          月
          <br />
          <input
            type="number"
            min="1"
            max="12"
            value={month}
            onChange={(e) => setMonth(e.target.value)}
            placeholder="1-12"
            style={{ width: 80 }}
          />
        </label>
        <button type="submit">套用篩選</button>
        <button type="button" onClick={handleClearFilter}>
          清除（顯示全部）
        </button>
      </form>

      {status === "loading" && <p>載入中...</p>}
      {status === "error" && <p style={{ color: "#c02929" }}>載入失敗：{error}</p>}

      {status === "loaded" && dashboard && (
        <div>
          <div style={{ display: "flex", gap: "2rem", marginBottom: "1.5rem" }}>
            <div>
              <div style={{ fontSize: "0.85rem", color: "#666" }}>已確認總金額</div>
              <div style={{ fontSize: "1.5rem", fontWeight: 700 }}>
                NT$ {dashboard.total_amount}
              </div>
            </div>
            <div>
              <div style={{ fontSize: "0.85rem", color: "#666" }}>已確認件數</div>
              <div style={{ fontSize: "1.5rem", fontWeight: 700 }}>{dashboard.total_count}</div>
            </div>
            <div>
              <div style={{ fontSize: "0.85rem", color: "#666" }}>待審核件數（不受篩選影響）</div>
              <Link
                to="/admin/review"
                style={{
                  fontSize: "1.5rem",
                  fontWeight: 700,
                  color: dashboard.pending_count > 0 ? "#b26a00" : "inherit",
                }}
              >
                {dashboard.pending_count}
              </Link>
            </div>
          </div>

          <SummaryTable
            title="依類別"
            rows={dashboard.by_category}
            getLabel={(row) => row.category}
            getKey={(row) => row.category}
          />
          <SummaryTable
            title="依員工"
            rows={dashboard.by_employee}
            getLabel={(row) => row.user_name}
            getKey={(row) => row.user_id}
          />
          <SummaryTable
            title="依部門"
            rows={dashboard.by_department}
            getLabel={(row) => row.department_name}
            getKey={(row) => row.department_id}
          />
        </div>
      )}
    </div>
  );
}
