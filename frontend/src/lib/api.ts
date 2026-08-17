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

export function query(params: Record<string, string | number | undefined>) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => { if (value !== undefined && value !== "") search.set(key, String(value)); });
  return search.toString();
}
