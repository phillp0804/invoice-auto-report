import { useEffect, useState } from "react";

import InvoiceCard from "../../components/InvoiceCard.jsx";
import { confirmInvoice, uploadInvoice } from "../../api/invoiceApi.js";

const LOW_CONFIDENCE = "low";

/**
 * 判斷是否需要跳出員工確認/修正畫面。
 *
 * core rule 12：QR 解碼 field_confidence 為 null（100% 可信，不觸發確認）；
 * AI 辨識只有在任一欄位信心為 "low" 時才視為信心不足，"medium" 仍自動接受
 * （信心分數門檻文件本身列為待調整項目，這是目前的判斷基準）。
 */
function needsConfirmation(fieldConfidence) {
  if (!fieldConfidence) {
    return false;
  }
  return Object.values(fieldConfidence).some((level) => level === LOW_CONFIDENCE);
}

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | uploading | needsConfirm | confirming | done
  const [invoice, setInvoice] = useState(null);
  const [error, setError] = useState(null);
  const [confirmForm, setConfirmForm] = useState({
    invoice_number: "",
    tax_id: "",
    date: "",
    amount: "",
  });

  useEffect(() => {
    if (!file) {
      setPreviewUrl(null);
      return undefined;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const handleFileChange = (event) => {
    setFile(event.target.files?.[0] ?? null);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) {
      return;
    }
    setStatus("uploading");
    setError(null);
    try {
      const result = await uploadInvoice(file);
      setInvoice(result);
      if (needsConfirmation(result.field_confidence)) {
        setConfirmForm({
          invoice_number: result.invoice_number ?? "",
          tax_id: result.tax_id ?? "",
          date: "",
          amount: result.amount != null ? String(result.amount) : "",
        });
        setStatus("needsConfirm");
      } else {
        setStatus("done");
      }
    } catch (err) {
      setError(err.message);
      setStatus("idle");
    }
  };

  const handleConfirmSubmit = async (event) => {
    event.preventDefault();
    setStatus("confirming");
    setError(null);

    // 只送出使用者實際修正過的欄位，維持後端「未提供 = 不變更」的部分更新語意
    const payload = {};
    if (confirmForm.invoice_number && confirmForm.invoice_number !== invoice.invoice_number) {
      payload.invoice_number = confirmForm.invoice_number;
    }
    if (confirmForm.tax_id && confirmForm.tax_id !== invoice.tax_id) {
      payload.tax_id = confirmForm.tax_id;
    }
    if (confirmForm.date) {
      payload.date = confirmForm.date;
    }
    if (confirmForm.amount && Number(confirmForm.amount) !== Number(invoice.amount)) {
      payload.amount = Number(confirmForm.amount);
    }

    try {
      const updated = await confirmInvoice(invoice.id, payload);
      setInvoice(updated);
      setStatus("done");
    } catch (err) {
      setError(err.message);
      setStatus("needsConfirm");
    }
  };

  const handleReset = () => {
    setFile(null);
    setInvoice(null);
    setError(null);
    setConfirmForm({ invoice_number: "", tax_id: "", date: "", amount: "" });
    setStatus("idle");
  };

  const confidence = invoice?.field_confidence;

  return (
    <div style={{ maxWidth: 480 }}>
      <h2>上傳發票</h2>

      {status === "idle" && (
        <div>
          <input type="file" accept="image/*" capture="environment" onChange={handleFileChange} />
          {previewUrl && (
            <div style={{ marginTop: "1rem" }}>
              <img src={previewUrl} alt="發票預覽" style={{ maxWidth: "100%", borderRadius: 8 }} />
            </div>
          )}
          <div style={{ marginTop: "1rem" }}>
            <button onClick={handleUpload} disabled={!file}>
              上傳並辨識
            </button>
          </div>
          {error && <p style={{ color: "#c02929" }}>{error}</p>}
        </div>
      )}

      {status === "uploading" && <p>上傳並辨識中...</p>}

      {status === "needsConfirm" && invoice && (
        <div>
          <p style={{ color: "#b26a00" }}>部分欄位辨識信心不足，請確認或修正下列資訊後送出。</p>
          <form onSubmit={handleConfirmSubmit}>
            <div style={{ marginBottom: "0.75rem" }}>
              <label>
                發票號碼{confidence?.invoice_number === LOW_CONFIDENCE && "（信心不足）"}
                <br />
                <input
                  value={confirmForm.invoice_number}
                  onChange={(e) =>
                    setConfirmForm({ ...confirmForm, invoice_number: e.target.value })
                  }
                />
              </label>
            </div>
            <div style={{ marginBottom: "0.75rem" }}>
              <label>
                統一編號{confidence?.tax_id === LOW_CONFIDENCE && "（信心不足）"}
                <br />
                <input
                  value={confirmForm.tax_id}
                  onChange={(e) => setConfirmForm({ ...confirmForm, tax_id: e.target.value })}
                />
              </label>
            </div>
            <div style={{ marginBottom: "0.75rem" }}>
              <label>
                日期{confidence?.date === LOW_CONFIDENCE && "（信心不足）"}
                <br />
                <input
                  placeholder={
                    invoice.date ? `目前：${invoice.date}（如需修正請輸入民國年，例如 113/07/08）` : "113/07/08"
                  }
                  value={confirmForm.date}
                  onChange={(e) => setConfirmForm({ ...confirmForm, date: e.target.value })}
                />
              </label>
            </div>
            <div style={{ marginBottom: "0.75rem" }}>
              <label>
                金額{confidence?.amount === LOW_CONFIDENCE && "（信心不足）"}
                <br />
                <input
                  type="number"
                  step="1"
                  value={confirmForm.amount}
                  onChange={(e) => setConfirmForm({ ...confirmForm, amount: e.target.value })}
                />
              </label>
            </div>
            {error && <p style={{ color: "#c02929" }}>{error}</p>}
            <button type="submit">送出確認</button>
          </form>
        </div>
      )}

      {status === "confirming" && <p>送出確認中...</p>}

      {status === "done" && invoice && (
        <div>
          <p>上傳成功！</p>
          <InvoiceCard invoice={invoice} />
          <button style={{ marginTop: "1rem" }} onClick={handleReset}>
            上傳下一張
          </button>
        </div>
      )}
    </div>
  );
}
