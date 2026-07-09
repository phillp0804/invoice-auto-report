import { useEffect, useState } from "react";

import InvoiceCard from "../../components/InvoiceCard.jsx";
import { approveInvoice, getPendingInvoices, rejectInvoice } from "../../api/invoiceApi.js";

export default function ReviewPage() {
  const [invoices, setInvoices] = useState([]);
  const [status, setStatus] = useState("loading"); // loading | loaded | error
  const [error, setError] = useState(null);

  const [rejectingId, setRejectingId] = useState(null);
  const [rejectReason, setRejectReason] = useState("");
  const [actionError, setActionError] = useState(null);
  const [processingId, setProcessingId] = useState(null);

  useEffect(() => {
    let cancelled = false;

    setStatus("loading");
    getPendingInvoices()
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

  const handleApprove = async (invoiceId) => {
    setActionError(null);
    setProcessingId(invoiceId);
    try {
      await approveInvoice(invoiceId);
      setInvoices((prev) => prev.filter((invoice) => invoice.id !== invoiceId));
    } catch (err) {
      setActionError(err.message);
    } finally {
      setProcessingId(null);
    }
  };

  const handleStartReject = (invoiceId) => {
    setRejectingId(invoiceId);
    setRejectReason("");
    setActionError(null);
  };

  const handleCancelReject = () => {
    setRejectingId(null);
    setRejectReason("");
  };

  const handleSubmitReject = async (event, invoiceId) => {
    event.preventDefault();
    if (!rejectReason.trim()) {
      setActionError("請填寫退回原因");
      return;
    }
    setActionError(null);
    setProcessingId(invoiceId);
    try {
      await rejectInvoice(invoiceId, rejectReason);
      setInvoices((prev) => prev.filter((invoice) => invoice.id !== invoiceId));
      setRejectingId(null);
      setRejectReason("");
    } catch (err) {
      setActionError(err.message);
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div style={{ maxWidth: 560 }}>
      <h2>待審核例外項目</h2>

      {status === "loading" && <p>載入中...</p>}
      {status === "error" && <p style={{ color: "#c02929" }}>載入失敗：{error}</p>}
      {status === "loaded" && invoices.length === 0 && <p>目前沒有待審核的發票。</p>}
      {actionError && <p style={{ color: "#c02929" }}>{actionError}</p>}

      {status === "loaded" && invoices.length > 0 && (
        <div style={{ display: "grid", gap: "1rem" }}>
          {invoices.map((invoice) => (
            <div key={invoice.id}>
              <InvoiceCard invoice={invoice} />

              <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem" }}>
                <button onClick={() => handleApprove(invoice.id)} disabled={processingId === invoice.id}>
                  核准
                </button>
                <button
                  onClick={() => handleStartReject(invoice.id)}
                  disabled={processingId === invoice.id}
                >
                  退回
                </button>
              </div>

              {rejectingId === invoice.id && (
                <form
                  onSubmit={(event) => handleSubmitReject(event, invoice.id)}
                  style={{ marginTop: "0.5rem" }}
                >
                  <textarea
                    value={rejectReason}
                    onChange={(e) => setRejectReason(e.target.value)}
                    placeholder="請填寫退回原因（員工會收到這則原因）"
                    rows={2}
                    style={{ width: "100%" }}
                  />
                  <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.25rem" }}>
                    <button type="submit" disabled={processingId === invoice.id}>
                      確認退回
                    </button>
                    <button type="button" onClick={handleCancelReject}>
                      取消
                    </button>
                  </div>
                </form>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
