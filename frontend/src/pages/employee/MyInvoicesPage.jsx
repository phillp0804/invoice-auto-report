import { useEffect, useState } from "react";

import InvoiceCard from "../../components/InvoiceCard.jsx";
import { getMyInvoices } from "../../api/invoiceApi.js";

export default function MyInvoicesPage() {
  const [invoices, setInvoices] = useState([]);
  const [status, setStatus] = useState("loading"); // loading | loaded | error

  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    setStatus("loading");
    getMyInvoices()
      .then((result) => {
        if (cancelled) return;
        setInvoices(result.invoices);
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
  }, []);

  return (
    <div style={{ maxWidth: 480 }}>
      <h2>我的上傳紀錄</h2>

      {status === "loading" && <p>載入中...</p>}

      {status === "error" && <p style={{ color: "#c02929" }}>載入失敗：{error}</p>}

      {status === "loaded" && invoices.length === 0 && <p>目前還沒有上傳紀錄。</p>}

      {status === "loaded" && invoices.length > 0 && (
        <div style={{ display: "grid", gap: "1rem" }}>
          {invoices.map((invoice) => (
            <InvoiceCard key={invoice.id} invoice={invoice} />
          ))}
        </div>
      )}
    </div>
  );
}
