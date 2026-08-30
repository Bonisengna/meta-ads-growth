const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
const requestTimeoutMs = 20_000;

export type ApiErrorKind = "auth" | "network" | "rate-limit" | "server" | "request" | "invalid-response";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly kind: ApiErrorKind,
    readonly endpoint: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function isSessionExpired(cause: unknown): cause is ApiError {
  return cause instanceof ApiError && cause.kind === "auth";
}

function payloadDetail(payload: unknown): string | null {
  if (!payload || typeof payload !== "object" || !("detail" in payload)) return null;
  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (detail == null) return null;
  try { return JSON.stringify(detail); } catch { return null; }
}

function httpError(path: string, status: number, payload: unknown, retryAfter: string | null): ApiError {
  const detail = payloadDetail(payload);
  if (status === 401) return new ApiError("Sua sessão expirou. Entre novamente.", "auth", path, status);
  if (status === 429) {
    const wait = retryAfter && /^\d+$/.test(retryAfter) ? ` Aguarde ${retryAfter} segundos.` : " Aguarde alguns instantes.";
    return new ApiError(`Muitas atualizações foram solicitadas.${wait}`, "rate-limit", path, status);
  }
  if (status === 503) return new ApiError("Os dados estão temporariamente indisponíveis. Tente novamente em instantes.", "server", path, status);
  if (status >= 500) return new ApiError("O servidor encontrou um problema temporário. Tente novamente.", "server", path, status);
  return new ApiError(detail ?? `A solicitação não pôde ser concluída (${status}).`, "request", path, status);
}

async function fetchJson<T>(
  path: string,
  token: string,
  init: RequestInit = {},
  acceptHttpError = false,
): Promise<{ ok: boolean; data: T; status: number }> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), requestTimeoutMs);
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  headers.set("Authorization", `Bearer ${token}`);
  let response: Response;
  try {
    response = await fetch(`${apiUrl}${path}`, {
      ...init,
      headers,
      cache: init.cache ?? "no-store",
      signal: controller.signal,
    });
  } catch (cause) {
    const timedOut = cause instanceof DOMException && cause.name === "AbortError";
    throw new ApiError(
      timedOut
        ? "A resposta do servidor demorou demais. Tente novamente."
        : "Não foi possível conectar ao servidor. Verifique se a API está disponível e tente novamente.",
      "network",
      path,
    );
  } finally {
    window.clearTimeout(timeout);
  }

  const payload = await response.json().catch(() => null) as T | null;
  if (response.status === 401) throw httpError(path, response.status, payload, response.headers.get("Retry-After"));
  if (!response.ok && !acceptHttpError) throw httpError(path, response.status, payload, response.headers.get("Retry-After"));
  if (payload == null) throw new ApiError("O servidor retornou uma resposta inválida.", "invalid-response", path, response.status);
  return { ok: response.ok, data: payload, status: response.status };
}

export async function apiGet<T>(path: string, token: string): Promise<T> {
  return (await fetchJson<T>(path, token)).data;
}

export async function apiGetStatus<T>(path: string, token: string): Promise<{ ok: boolean; data: T }> {
  const result = await fetchJson<T>(path, token, {}, true);
  return { ok: result.ok, data: result.data };
}

export async function apiPost<T>(path: string, token: string, body: unknown): Promise<T> {
  return (await fetchJson<T>(path, token, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })).data;
}

export async function apiPatch<T>(path: string, token: string, body: unknown): Promise<T> {
  return (await fetchJson<T>(path, token, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })).data;
}

export function query(params: Record<string, string | number | undefined>) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => { if (value !== undefined && value !== "") search.set(key, String(value)); });
  return search.toString();
}
