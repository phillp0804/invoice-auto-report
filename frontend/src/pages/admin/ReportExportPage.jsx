import { useState } from "react";

import { downloadReportExcel } from "../../api/invoiceApi.js";

const GROUP_BY_OPTIONS = [
  { value: "department", label: "部門" },
  { value: "employee", label: "員工" },
  { value: "category", label: "類別" },
];

export default function ReportExportPage() {
  const now = new Date();
  const [year, setYear] = useState(String(now.getFullYear()));
  const [month, setMonth] = useState(String(now.getMonth() + 1));
  const [groupBy, setGroupBy] = useState("department");
  const [status, setStatus] = useState("idle"); // idle | downloading | error
  const [error, setError] = useState(null);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setStatus("downloading");
    setError(null);
    try {
      await downloadReportExcel({ year: Number(year), month: Number(month), groupBy });
      setStatus("idle");
    } catch (err) {
      setError(err.message);
      setStatus("error");
    }
  };

  return (
    <div style={{ maxWidth: 400 }}>
      <h2>匯出報表</h2>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: "0.75rem" }}>
          <label>
            年
            <br />
            <input
              type="number"
              value={year}
              onChange={(e) => setYear(e.target.value)}
              required
            />
          </label>
        </div>
        <div style={{ marginBottom: "0.75rem" }}>
          <label>
            月
            <br />
            <input
              type="number"
              min="1"
              max="12"
              value={month}
              onChange={(e) => setMonth(e.target.value)}
              required
            />
          </label>
        </div>
        <div style={{ marginBottom: "0.75rem" }}>
          <label>
            分組方式
            <br />
            <select value={groupBy} onChange={(e) => setGroupBy(e.target.value)}>
              {GROUP_BY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        {error && <p style={{ color: "#c02929" }}>{error}</p>}

        <button type="submit" disabled={status === "downloading"}>
          {status === "downloading" ? "匯出中..." : "匯出 Excel"}
        </button>
      </form>
    </div>
  );
}
