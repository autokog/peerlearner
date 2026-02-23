const BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  return fetch(BASE + path, { credentials: "include", ...init });
}
