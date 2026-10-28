import type {
  Case,
  CaseCreatePayload,
  CaseDocument,
  CaseUpdatePayload,
  TokenResponse,
  User,
} from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("cc_token");
}

export function setAuth(token: string, user: User) {
  localStorage.setItem("cc_token", token);
  localStorage.setItem("cc_user", JSON.stringify(user));
}

export function clearAuth() {
  localStorage.removeItem("cc_token");
  localStorage.removeItem("cc_user");
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("cc_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  auth = true,
): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (auth) {
    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
      if (Array.isArray(detail)) {
        detail = detail.map((d: { msg?: string }) => d.msg || String(d)).join(", ");
      }
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  register: (name: string, email: string, password: string) =>
    request<TokenResponse>(
      "/api/auth/register",
      { method: "POST", body: JSON.stringify({ name, email, password }) },
      false,
    ),

  login: (email: string, password: string) =>
    request<TokenResponse>(
      "/api/auth/login",
      { method: "POST", body: JSON.stringify({ email, password }) },
      false,
    ),

  me: () => request<User>("/api/auth/me"),

  listCases: () => request<Case[]>("/api/cases"),

  getCase: (id: string) => request<Case>(`/api/cases/${id}`),

  createCase: (payload: CaseCreatePayload) =>
    request<Case>("/api/cases", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  updateCase: (id: string, payload: CaseUpdatePayload) =>
    request<Case>(`/api/cases/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),

  deleteCase: (id: string) =>
    request<{ status: string }>(`/api/cases/${id}`, { method: "DELETE" }),

  listDocuments: (caseId: string) =>
    request<CaseDocument[]>(`/api/cases/${caseId}/documents`),

  uploadDocuments: (caseId: string, files: File[]) => {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    return request<CaseDocument[]>(`/api/cases/${caseId}/upload`, {
      method: "POST",
      body: form,
    });
  },

  deleteDocument: (caseId: string, docId: string) =>
    request<{ status: string }>(`/api/cases/${caseId}/documents/${docId}`, {
      method: "DELETE",
    }),
};
