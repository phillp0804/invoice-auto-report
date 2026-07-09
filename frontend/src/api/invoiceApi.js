/**
 * 封裝所有後端 API 呼叫，元件不直接使用 fetch。
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

let authToken = null;

/** 登入成功後由 AuthContext 呼叫，登出時傳 null 清除。 */
export function setAuthToken(token) {
  authToken = token;
}

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (authToken) {
    headers.Authorization = `Bearer ${authToken}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail || `API 請求失敗（${response.status}）`);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

// --- 認證 ---

export function login(firebaseToken) {
  return request("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ firebase_token: firebaseToken }),
  });
}

// --- 員工端 ---

export function uploadInvoice(file) {
  const formData = new FormData();
  formData.append("file", file);
  return request("/invoices/upload", { method: "POST", body: formData });
}

export function confirmInvoice(invoiceId, fields) {
  return request(`/invoices/${invoiceId}/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(fields),
  });
}

export function getMyInvoices() {
  return request("/invoices/my");
}

// --- 總務端 ---

export function getDashboard({ year, month } = {}) {
  const params = new URLSearchParams();
  if (year) params.set("year", year);
  if (month) params.set("month", month);
  const query = params.toString() ? `?${params.toString()}` : "";
  return request(`/admin/dashboard${query}`);
}

export function getPendingInvoices() {
  return request("/admin/invoices/pending");
}

export function approveInvoice(invoiceId) {
  return request(`/admin/invoices/${invoiceId}/approve`, { method: "POST" });
}

export function rejectInvoice(invoiceId, rejectReason) {
  const params = new URLSearchParams({ reject_reason: rejectReason });
  return request(`/admin/invoices/${invoiceId}/reject?${params.toString()}`, {
    method: "POST",
  });
}

/**
 * 匯出並下載 Excel 報表。
 *
 * 用 fetch 帶 Authorization header 取得檔案再手動觸發下載，
 * 不能用 <a href> 直接連到後端網址，因為瀏覽器導覽不會帶自訂
 * header，/admin/reports/export 會因為缺少總務權限驗證被擋下。
 */
export async function downloadReportExcel({ year, month, groupBy = "department" }) {
  const params = new URLSearchParams({
    year: String(year),
    month: String(month),
    group_by: groupBy,
  });
  const headers = {};
  if (authToken) {
    headers.Authorization = `Bearer ${authToken}`;
  }

  const response = await fetch(`${API_BASE_URL}/admin/reports/export?${params.toString()}`, {
    headers,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail || `匯出報表失敗（${response.status}）`);
  }

  const disposition = response.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  const filename = match ? match[1] : `invoice_report_${year}${String(month).padStart(2, "0")}.xlsx`;

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
