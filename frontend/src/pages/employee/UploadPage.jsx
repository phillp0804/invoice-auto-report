import { useState } from "react";

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

function buildQueueItem(file) {
  return {
    file,
    previewUrl: URL.createObjectURL(file),
    status: "pending", // pending | uploading | needsConfirm | confirming | done | error
    invoice: null,
    error: null,
  };
}

const STATUS_LABEL = {
  pending: "等待中",
  uploading: "上傳並辨識中...",
  needsConfirm: "需要確認",
  confirming: "送出確認中...",
  done: "完成",
  error: "失敗",
};

export default function UploadPage() {
  const [queue, setQueue] = useState([]);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [phase, setPhase] = useState("idle"); // idle | processing | finished
  const [confirmForm, setConfirmForm] = useState({
    invoice_number: "",
    tax_id: "",
    date: "",
    amount: "",
  });

  const updateItem = (index, patch) => {
    setQueue((prev) => prev.map((item, i) => (i === index ? { ...item, ...patch } : item)));
  };

  const handleFilesChange = (event) => {
    const files = Array.from(event.target.files ?? []);
    queue.forEach((item) => URL.revokeObjectURL(item.previewUrl));
    setQueue(files.map(buildQueueItem));
    setActiveIndex(-1);
    setPhase("idle");
  };

  // 依序（非同時）處理每一張，避免同時打多個 AI 辨識請求觸發額度限制
  const processFrom = async (index, items) => {
    if (index >= items.length) {
      setActiveIndex(-1);
      setPhase("finished");
      return;
    }

    setActiveIndex(index);
    updateItem(index, { status: "uploading" });

    try {
      const result = await uploadInvoice(items[index].file);
      updateItem(index, { invoice: result });

      if (needsConfirmation(result.field_confidence)) {
        setConfirmForm({
          invoice_number: result.invoice_number ?? "",
          tax_id: result.tax_id ?? "",
          date: "",
          amount: result.amount != null ? String(result.amount) : "",
        });
        updateItem(index, { status: "needsConfirm" });
        // 暫停在這一張，等使用者送出確認後才會繼續處理下一張
      } else {
        updateItem(index, { status: "done" });
        await processFrom(index + 1, items);
      }
    } catch (err) {
      updateItem(index, { status: "error", error: err.message });
      await processFrom(index + 1, items);
    }
  };

  const handleStartUpload = () => {
    if (queue.length === 0) {
      return;
    }
    setPhase("processing");
    processFrom(0, queue);
  };

  const handleConfirmSubmit = async (event) => {
    event.preventDefault();
    const index = activeIndex;
    const current = queue[index];
    updateItem(index, { status: "confirming" });

    // 只送出使用者實際修正過的欄位，維持後端「未提供 = 不變更」的部分更新語意
    const payload = {};
    if (confirmForm.invoice_number && confirmForm.invoice_number !== current.invoice.invoice_number) {
      payload.invoice_number = confirmForm.invoice_number;
    }
    if (confirmForm.tax_id && confirmForm.tax_id !== current.invoice.tax_id) {
      payload.tax_id = confirmForm.tax_id;
    }
    if (confirmForm.date) {
      payload.date = confirmForm.date;
    }
    if (confirmForm.amount && Number(confirmForm.amount) !== Number(current.invoice.amount)) {
      payload.amount = Number(confirmForm.amount);
    }

    try {
      const updated = await confirmInvoice(current.invoice.id, payload);
      updateItem(index, { invoice: updated, status: "done" });
      await processFrom(index + 1, queue);
    } catch (err) {
      updateItem(index, { status: "needsConfirm", error: err.message });
    }
  };

  const handleReset = () => {
    queue.forEach((item) => URL.revokeObjectURL(item.previewUrl));
    setQueue([]);
    setActiveIndex(-1);
    setPhase("idle");
    setConfirmForm({ invoice_number: "", tax_id: "", date: "", amount: "" });
  };

  const activeItem = activeIndex >= 0 ? queue[activeIndex] : null;
  const activeConfidence = activeItem?.invoice?.field_confidence;
  const doneCount = queue.filter((item) => item.status === "done").length;
  const errorCount = queue.filter((item) => item.status === "error").length;

  return (
    <div style={{ maxWidth: 480 }}>
      <h2>上傳發票</h2>

      {phase === "idle" && (
        <div>
          <input type="file" accept="image/*" capture="environment" multiple onChange={handleFilesChange} />

          {queue.length > 0 && (
            <div
              style={{
                marginTop: "1rem",
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(80px, 1fr))",
                gap: "0.5rem",
              }}
            >
              {queue.map((item, i) => (
                <img
                  key={i}
                  src={item.previewUrl}
                  alt={`發票預覽 ${i + 1}`}
                  style={{ width: "100%", height: 80, objectFit: "cover", borderRadius: 6 }}
                />
              ))}
            </div>
          )}

          <div style={{ marginTop: "1rem" }}>
            <button onClick={handleStartUpload} disabled={queue.length === 0}>
              上傳並辨識（共 {queue.length} 張）
            </button>
          </div>
        </div>
      )}

      {phase !== "idle" && (
        <div>
          <ul style={{ listStyle: "none", padding: 0, margin: "0 0 1rem" }}>
            {queue.map((item, i) => (
              <li
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.75rem",
                  padding: "0.5rem 0",
                  borderBottom: "1px solid #eee",
                  opacity: i === activeIndex ? 1 : 0.8,
                }}
              >
                <img
                  src={item.previewUrl}
                  alt={`發票預覽 ${i + 1}`}
                  style={{ width: 40, height: 40, objectFit: "cover", borderRadius: 4 }}
                />
                <span style={{ flex: 1 }}>{item.file.name}</span>
                <span
                  style={{
                    color:
                      item.status === "error"
                        ? "#c02929"
                        : item.status === "done"
                          ? "#2a7a2a"
                          : "#666",
                  }}
                >
                  {STATUS_LABEL[item.status]}
                </span>
              </li>
            ))}
          </ul>

          {activeItem?.status === "needsConfirm" && (
            <div>
              <p style={{ color: "#b26a00" }}>
                第 {activeIndex + 1} 張（{activeItem.file.name}）部分欄位辨識信心不足，請確認或修正下列資訊後送出。
              </p>
              <form onSubmit={handleConfirmSubmit}>
                <div style={{ marginBottom: "0.75rem" }}>
                  <label>
                    發票號碼{activeConfidence?.invoice_number === LOW_CONFIDENCE && "（信心不足）"}
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
                    統一編號{activeConfidence?.tax_id === LOW_CONFIDENCE && "（信心不足）"}
                    <br />
                    <input
                      value={confirmForm.tax_id}
                      onChange={(e) => setConfirmForm({ ...confirmForm, tax_id: e.target.value })}
                    />
                  </label>
                </div>
                <div style={{ marginBottom: "0.75rem" }}>
                  <label>
                    日期{activeConfidence?.date === LOW_CONFIDENCE && "（信心不足）"}
                    <br />
                    <input
                      placeholder={
                        activeItem.invoice.date
                          ? `目前：${activeItem.invoice.date}（如需修正請輸入民國年，例如 113/07/08）`
                          : "113/07/08"
                      }
                      value={confirmForm.date}
                      onChange={(e) => setConfirmForm({ ...confirmForm, date: e.target.value })}
                    />
                  </label>
                </div>
                <div style={{ marginBottom: "0.75rem" }}>
                  <label>
                    金額{activeConfidence?.amount === LOW_CONFIDENCE && "（信心不足）"}
                    <br />
                    <input
                      type="number"
                      step="1"
                      value={confirmForm.amount}
                      onChange={(e) => setConfirmForm({ ...confirmForm, amount: e.target.value })}
                    />
                  </label>
                </div>
                {activeItem.error && <p style={{ color: "#c02929" }}>{activeItem.error}</p>}
                <button type="submit">送出確認</button>
              </form>
            </div>
          )}

          {phase === "finished" && (
            <div>
              <p>
                全部處理完成：成功 {doneCount} 張
                {errorCount > 0 && <span style={{ color: "#c02929" }}>，失敗 {errorCount} 張</span>}
              </p>
              {queue
                .filter((item) => item.status === "done")
                .map((item, i) => (
                  <div key={i} style={{ marginBottom: "0.75rem" }}>
                    <InvoiceCard invoice={item.invoice} />
                  </div>
                ))}
              {queue
                .filter((item) => item.status === "error")
                .map((item, i) => (
                  <p key={i} style={{ color: "#c02929" }}>
                    {item.file.name}：{item.error}
                  </p>
                ))}
              <button style={{ marginTop: "1rem" }} onClick={handleReset}>
                上傳下一批
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
