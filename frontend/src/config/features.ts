/// <reference types="vite/client" />

/**
 * Frontend feature flags for the additive "wow feature" layer (P1–P5).
 *
 * Every flag defaults to ON. To disable a feature, set the matching
 * VITE_ENABLE_* var to "false" (or "0") in Hackout/.env — the original app
 * behavior is preserved when a feature is off. See Hackout/.env.example.
 */

const flag = (v: string | undefined, dflt = true): boolean => {
  if (v === undefined || v === '') return dflt;
  const s = v.toLowerCase();
  return s !== 'false' && s !== '0' && s !== 'off' && s !== 'no';
};

export const features = {
  liveTwin: flag(import.meta.env.VITE_ENABLE_LIVE_TWIN),
  dualAi: flag(import.meta.env.VITE_ENABLE_DUAL_AI),
  certificates: flag(import.meta.env.VITE_ENABLE_CERTIFICATES),
  satellite: flag(import.meta.env.VITE_ENABLE_SATELLITE),
  fleet: flag(import.meta.env.VITE_ENABLE_FLEET),
  whatIf: flag(import.meta.env.VITE_ENABLE_WHATIF),
} as const;

/**
 * WebSocket origin for live telemetry, derived from the HTTP API base
 * (http→ws, https→wss) unless VITE_API_WS_URL explicitly overrides it.
 * Returns the base *without* the trailing /api and without a trailing slash,
 * e.g. "ws://127.0.0.1:8000".
 */
export function wsBase(): string {
  const explicit = import.meta.env.VITE_API_WS_URL;
  if (explicit) return explicit.replace(/\/+$/, '');
  const http = (import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api').replace(/\/+$/, '');
  // strip a trailing /api segment so callers can append their own WS path
  const origin = http.replace(/\/api$/, '');
  return origin.replace(/^http/, 'ws');
}
