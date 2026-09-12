/// <reference types="vite/client" />

/**
 * Shared HTTP client for the TerraLedger backend (FastAPI, mounted at /api).
 * - Reads the base URL from VITE_API_URL (falls back to localhost:8000/api).
 * - Attaches the JWT bearer token (stored by authService) to every call.
 * - Normalises FastAPI error payloads ({detail}) into a thrown ApiError.
 * - Supports JSON bodies, multipart (FormData) uploads, and query params.
 *
 * This is the single seam between the app and the server: every *Service.ts
 * calls `api(...)` instead of mutating the in-memory mock store.
 */

const BASE_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api').replace(/\/+$/, '');

const TOKEN_KEY = 'terra-ledger-token';

/** Small persistence helper so the JWT survives reloads. */
export const tokenStore = {
  get: (): string | null => localStorage.getItem(TOKEN_KEY),
  set: (token: string | null) => {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  },
};

/** Absolute API base — for direct fetch()/download calls that bypass api(). */
export const API_BASE = BASE_URL;

/** Authorization header for direct fetch() calls (e.g. Blob downloads). */
export function authHeaders(): Record<string, string> {
  const token = tokenStore.get();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

type Query = Record<string, string | number | boolean | undefined | null>;

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE';
  body?: unknown; // serialised as JSON
  form?: FormData; // multipart upload (takes precedence over body)
  query?: Query; // appended as ?a=b
  auth?: boolean; // attach bearer token (default: true)
}

function buildUrl(path: string, query?: Query): string {
  let url = `${BASE_URL}${path}`;
  if (query) {
    const pairs = Object.entries(query)
      .filter(([, v]) => v !== undefined && v !== null && v !== '')
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`);
    if (pairs.length) url += `${url.includes('?') ? '&' : '?'}${pairs.join('&')}`;
  }
  return url;
}

function readError(data: unknown, res: Response): string {
  const holder = (data ?? {}) as { detail?: unknown; message?: unknown };
  const detail = holder.detail ?? holder.message;
  if (Array.isArray(detail)) {
    // FastAPI 422 validation errors: [{ loc, msg, type }, ...]
    return detail
      .map((e) => (e && typeof e === 'object' && 'msg' in e ? String((e as { msg: unknown }).msg) : String(e)))
      .join('; ');
  }
  if (typeof detail === 'string') return detail;
  return res.statusText || `Request failed (${res.status})`;
}

export async function api<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, form, query, auth = true } = opts;
  const headers: Record<string, string> = {};

  if (auth) {
    const token = tokenStore.get();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  let payload: BodyInit | undefined;
  if (form) {
    payload = form; // let the browser set the multipart boundary itself
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
    payload = JSON.stringify(body);
  }

  let res: Response;
  try {
    res = await fetch(buildUrl(path, query), { method, headers, body: payload });
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Make sure the backend is running on port 8000.');
  }

  if (res.status === 204) return undefined as T;

  const text = await res.text();
  const data = text ? JSON.parse(text) : null;

  if (!res.ok) {
    if (res.status === 401) tokenStore.set(null); // stale / expired token — drop it
    throw new ApiError(res.status, readError(data, res));
  }

  return data as T;
}
