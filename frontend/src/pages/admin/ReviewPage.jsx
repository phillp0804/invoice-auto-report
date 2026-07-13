import { useEffect, useRef, useState } from "react";

import InvoiceCard from "../../components/InvoiceCard.jsx";
import {
  approveInvoice,
  getInvoiceImageUrl,
  getPendingInvoices,
  rejectInvoice,
} from "../../api/invoiceApi.js";

export default function ReviewPage() {
  const [invoices, setInvoices] = useState([]);
  const [status, setStatus] = useState("loading"); // loading | loaded | error
  const [error, setError] = useState(null);

  const [rejectingId, setRejectingId] = useState(null);
  const [rejectReason, setRejectReason] = useState("");
  const [actionError, setActionError] = useState(null);
  const [processingId, setProcessingId] = useState(null);

  // key: invoiceId, value: blob 網址字串 | "loading" | Error 訊息字串
  const [imagePreviews, setImagePreviews] = useState({});
  // 讓 unmount 時的 cleanup 能讀到最新值，而不是 effect 掛載當下的舊值
  const imagePreviewsRef = useRef(imagePreviews);
  imagePreviewsRef.current = imagePreviews;

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

  useEffect(() => {
    // 離開頁面時釋放所有已載入的圖片 blob 網址，避免記憶體洩漏
    // 透過 ref 讀取，避免只抓到 mount 當下（空物件）的 stale closure
    return () => {
      Object.values(imagePreviewsRef.current).forEach((value) => {
        if (typeof value === "string" && value.startsWith("blob:")) {
          window.URL.revokeObjectURL(value);
        }
      });
    };
  }, []);

  const handleToggleImage = async (invoiceId) => {
    const current = imagePreviews[invoiceId];
    if (typeof current === "string" && current.startsWith("blob:")) {
      window.URL.revokeObjectURL(current);
      setImagePreviews((prev) => {
        const next = { ...prev };
        delete next[invoiceId];
        return next;
      });
      return;
    }

    setImagePreviews((prev) => ({ ...prev, [invoiceId]: "loading" }));
    try {
      const url = await getInvoiceImageUrl(invoiceId);
      setImagePreviews((prev) => ({ ...prev, [invoiceId]: url }));
    } catch (err) {
      setImagePreviews((prev) => ({ ...prev, [invoiceId]: err.message }));
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
                <button onClick={() => handleToggleImage(invoice.id)}>
                  {imagePreviews[invoice.id] ? "隱藏發票原圖" : "顯示發票原圖比對"}
                </button>
              </div>

              {imagePreviews[invoice.id] === "loading" && <p>圖片載入中...</p>}
              {imagePreviews[invoice.id] &&
                imagePreviews[invoice.id] !== "loading" &&
                (imagePreviews[invoice.id].startsWith("blob:") ? (
                  <img
                    src={imagePreviews[invoice.id]}
                    alt={`發票 ${invoice.invoice_number} 原圖`}
                    style={{ maxWidth: "100%", marginTop: "0.5rem", borderRadius: 8, border: "1px solid #ddd" }}
                  />
                ) : (
                  <p style={{ color: "#c02929" }}>{imagePreviews[invoice.id]}</p>
                ))}

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
