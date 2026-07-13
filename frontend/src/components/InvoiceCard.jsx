import StatusBadge from "./StatusBadge.jsx";

/** 顯示單筆發票摘要的卡片，供上傳結果、我的紀錄、總務審核頁共用。 */
export default function InvoiceCard({ invoice }) {
  return (
    <div
      style={{
        border: "1px solid #ddd",
        borderRadius: 8,
        padding: "1rem",
        background: "#fff",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <strong>{invoice.invoice_number}</strong>
        <StatusBadge status={invoice.status} />
      </div>

      <dl
        style={{
          margin: "0.5rem 0 0",
          display: "grid",
          gridTemplateColumns: "auto 1fr",
          gap: "0.25rem 1rem",
        }}
      >
        <dt>日期</dt>
        <dd>{invoice.date ?? "—"}</dd>
        <dt>金額</dt>
        <dd>{invoice.amount != null ? `NT$ ${invoice.amount}` : "—"}</dd>
        <dt>類別</dt>
        <dd>{invoice.category ?? "—"}</dd>
        <dt>賣方統編</dt>
        <dd>
          {invoice.tax_id ?? "—"}
          {invoice.tax_id_valid === false && (
            <span style={{ color: "#c02929" }}>（檢查碼未通過）</span>
          )}
        </dd>
        <dt>買方統編</dt>
        <dd>
          {invoice.buyer_tax_id && invoice.buyer_tax_id !== "00000000"
            ? invoice.buyer_tax_id
            : "—"}
        </dd>
      </dl>

      {invoice.is_duplicate && (
        <p style={{ color: "#c02929", margin: "0.5rem 0 0" }}>⚠ 疑似重複發票，待總務確認</p>
      )}
      {invoice.buyer_tax_id_status === "missing" && (
        <p style={{ color: "#c02929", margin: "0.5rem 0 0" }}>⚠ 未打統編</p>
      )}
      {invoice.buyer_tax_id_status === "mismatch" && (
        <p style={{ color: "#c02929", margin: "0.5rem 0 0" }}>⚠ 買方統編非本公司</p>
      )}
      {invoice.status === "已退回" && invoice.reject_reason && (
        <p style={{ color: "#c02929", margin: "0.5rem 0 0" }}>退回原因：{invoice.reject_reason}</p>
      )}
    </div>
  );
}
