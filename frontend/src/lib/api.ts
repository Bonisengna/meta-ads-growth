const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export async function apiGet<T>(path: string, token: string): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, { headers: { Accept: "application/json", Authorization: `Bearer ${token}` }, cache: "no-store" });
  if (response.status === 401) throw new Error("SESSION_EXPIRED");
  if (!response.ok) {
    const payload = await response.json().catch(() => null) as { detail?: unknown } | null;
    const detail = typeof payload?.detail === "string"
      ? payload.detail
      : payload?.detail
        ? JSON.stringify(payload.detail)
        : "sem detalhes";
    throw new Error(`${path.split("?")[0]} respondeu ${response.status}: ${detail}`);
  }
  return response.json() as Promise<T>;
}

export async function apiGetStatus<T>(path: string, token: string): Promise<{ ok: boolean; data: T }> {
  const response = await fetch(`${apiUrl}${path}`, { headers: { Accept: "application/json", Authorization: `Bearer ${token}` }, cache: "no-store" });
  if (response.status === 401) throw new Error("SESSION_EXPIRED");
  const data = await response.json() as T;
  return { ok: response.ok, data };
}

export async function apiPost<T>(path: string, token: string, body: unknown): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  if (response.status === 401) throw new Error("SESSION_EXPIRED");
  if (!response.ok) {
    const payload = await response.json().catch(() => null) as { detail?: unknown } | null;
    throw new Error(typeof payload?.detail === "string" ? payload.detail : "Não foi possível registrar a decisão.");
  }
  return response.json() as Promise<T>;
}

export async function apiPatch<T>(path: string, token: string, body: unknown): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, {
    method: "PATCH",
    headers: { Accept: "application/json", "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  if (response.status === 401) throw new Error("SESSION_EXPIRED");
  if (!response.ok) {
    const payload = await response.json().catch(() => null) as { detail?: unknown } | null;
    const detail = typeof payload?.detail === "string" ? payload.detail : "Não foi possível atualizar o cliente.";
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export function query(params: Record<string, string | number | undefined>) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => { if (value !== undefined && value !== "") search.set(key, String(value)); });
  return search.toString();
}
