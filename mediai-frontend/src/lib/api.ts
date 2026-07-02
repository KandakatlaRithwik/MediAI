import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

export const API_BASE_URL =
  (typeof window !== "undefined" && (window as any).__MEDIAI_API__) ||
  import.meta.env.VITE_API_URL ||
  "http://localhost:8000";

const ACCESS_KEY = "mediai_access_token";
const REFRESH_KEY = "mediai_refresh_token";

export const tokenStore = {
  get access() {
    return typeof window !== "undefined" ? window.localStorage.getItem(ACCESS_KEY) : null;
  },
  get refresh() {
    return typeof window !== "undefined" ? window.localStorage.getItem(REFRESH_KEY) : null;
  },
  set(access: string, refresh: string) {
    window.localStorage.setItem(ACCESS_KEY, access);
    window.localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear() {
    window.localStorage.removeItem(ACCESS_KEY);
    window.localStorage.removeItem(REFRESH_KEY);
    window.localStorage.removeItem("mediai_user");
  },
};

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = tokenStore.access;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Refresh-on-401 interceptor
let refreshPromise: Promise<string | null> | null = null;

async function performRefresh(): Promise<string | null> {
  const refresh = tokenStore.refresh;
  if (!refresh) return null;
  try {
    const { data } = await axios.post(
      `${API_BASE_URL}/auth/refresh`,
      { refresh_token: refresh },
      { headers: { "Content-Type": "application/json" } },
    );
    tokenStore.set(data.access_token, data.refresh_token);
    return data.access_token as string;
  } catch {
    tokenStore.clear();
    return null;
  }
}

api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    if (error.response?.status === 401 && original && !original._retry && !original.url?.includes("/auth/")) {
      original._retry = true;
      refreshPromise = refreshPromise ?? performRefresh();
      const newToken = await refreshPromise;
      refreshPromise = null;
      if (newToken) {
        original.headers = original.headers ?? {};
        (original.headers as any).Authorization = `Bearer ${newToken}`;
        return api.request(original);
      }
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

export function extractError(err: unknown, fallback = "Something went wrong"): string {
  const e = err as AxiosError<any>;
  const d = e?.response?.data;
  if (typeof d === "string") return d;
  if (d?.message) return d.message;
  if (d?.detail) {
    if (typeof d.detail === "string") return d.detail;
    if (Array.isArray(d.detail) && d.detail[0]?.msg) return d.detail[0].msg;
  }
  return e?.message || fallback;
}

export type UserRole = "PATIENT" | "DOCTOR" | "ADMIN";
export type User = {
  uuid: string;
  full_name: string;
  email: string;
  phone?: string | null;
  role: UserRole;
  is_active: boolean;
  created_at: string;
};

// Fallback list used if GET /auth/security-questions is unreachable —
// kept in sync with the server-side SECURITY_QUESTIONS constant.
export const DEFAULT_SECURITY_QUESTIONS: string[] = [
  "What was the name of your first school?",
  "What is your childhood nickname?",
  "Who was your favorite teacher?",
  "What is your favorite color?",
  "What was the name of your first pet?",
  "In what city were you born?",
];