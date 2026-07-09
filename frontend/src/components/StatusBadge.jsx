const STATUS_STYLES = {
  待審核: { background: "#fff4e5", color: "#b26a00" },
  已確認: { background: "#e7f6e7", color: "#1e7d1e" },
  已退回: { background: "#fde8e8", color: "#c02929" },
};

/** 顯示發票狀態的色塊標籤（待審核 / 已確認 / 已退回）。 */
export default function StatusBadge({ status }) {
  const style = STATUS_STYLES[status] || { background: "#eee", color: "#333" };

  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 10px",
        borderRadius: "999px",
        fontSize: "0.85rem",
        fontWeight: 600,
        ...style,
      }}
    >
      {status}
    </span>
  );
}
