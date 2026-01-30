import axios from "axios";

const baseURL = process.env.REACT_APP_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL,
  timeout: 20000,
});

// Centralized auth + tenant headers
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("lexecon_token");
  const tenantId =
    localStorage.getItem("lexecon_tenant_id") ||
    process.env.REACT_APP_DEFAULT_TENANT_ID ||
    "default";

  config.headers = config.headers || {};
  config.headers["X-Tenant-ID"] = tenantId;

  if (token) {
    config.headers["Authorization"] = `Bearer ${token}`;
  }

  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err?.response?.status;
    const message =
      err?.response?.data?.detail ||
      err?.response?.data?.message ||
      err?.message ||
      "Request failed";

    // Auto-logout on auth failures
    if (status === 401) {
      localStorage.removeItem("lexecon_token");
      // Only redirect if not already on login page
      if (!window.location.pathname.includes("/login")) {
        window.location.href = "/login";
      }
    }

    return Promise.reject({ status, message, raw: err });
  }
);
