/**
 * Runtime backend configuration & authenticated API fetch helper (`Step 5.3-C`).
 *
 * - Inside Tauri 2 (detected via the injected Tauri API global), resolves
 *   `{ baseUrl, token }` from the `get_backend_config` Rust command and attaches
 *   `Authorization: Bearer <token>` on every API request.
 * - Outside Tauri (browser / Vite `/api` proxy), uses relative `/api/v1/...`
 *   paths without hardcoding any loopback host literal.
 */

export interface BackendConfig {
  baseUrl: string
  token: string | null
}

type TauriInvokeFn = <T>(cmd: string, args?: Record<string, unknown>) => Promise<T>

interface TauriWindowGlobals {
  __TAURI__?: {
    core?: {
      invoke?: TauriInvokeFn
    }
  }
  __TAURI_INTERNALS__?: {
    invoke?: TauriInvokeFn
  }
}

function getTauriInvoke(): TauriInvokeFn | null {
  if (typeof window === 'undefined') {
    return null
  }
  const win = window as unknown as TauriWindowGlobals
  if (typeof win.__TAURI__?.core?.invoke === 'function') {
    return win.__TAURI__.core.invoke.bind(win.__TAURI__.core)
  }
  if (typeof win.__TAURI_INTERNALS__?.invoke === 'function') {
    return win.__TAURI_INTERNALS__.invoke.bind(win.__TAURI_INTERNALS__)
  }
  return null
}

export function isTauriRuntime(): boolean {
  return getTauriInvoke() !== null
}

let cachedConfigPromise: Promise<BackendConfig> | null = null

export function resolveBackendConfig(): Promise<BackendConfig> {
  if (cachedConfigPromise !== null) {
    return cachedConfigPromise
  }

  const invoke = getTauriInvoke()
  if (invoke === null) {
    cachedConfigPromise = Promise.resolve({ baseUrl: '', token: null })
    return cachedConfigPromise
  }

  cachedConfigPromise = invoke<{ baseUrl: string; token: string }>('get_backend_config').then(
    raw => ({
      baseUrl: raw.baseUrl.replace(/\/+$/, ''),
      token: raw.token || null,
    })
  )
  return cachedConfigPromise
}

export async function apiFetch(
  path: `/api/${string}`,
  init?: RequestInit
): Promise<Response> {
  const { baseUrl, token } = await resolveBackendConfig()
  const targetUrl = baseUrl ? `${baseUrl}${path}` : path

  const headers = new Headers(init?.headers)
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  return fetch(targetUrl, {
    ...init,
    headers,
  })
}
