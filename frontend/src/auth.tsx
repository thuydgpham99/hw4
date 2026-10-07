/** Session state for the whole app.
 *
 * The token is an opaque signed string from the backend; the frontend only
 * stores it and attaches it to requests. It carries no password material.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'
import type { ReactNode } from 'react'
import type { User } from './types'

const TOKEN_KEY = 'campus_customs_token'

interface AuthState {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (input: {
    first_name: string
    last_name: string
    email: string
    password: string
  }) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthState | null>(null)

/** Reads the API's error detail so the form can show the real reason. */
async function errorFrom(response: Response, fallback: string): Promise<string> {
  try {
    const body = await response.json()
    if (typeof body.detail === 'string') return body.detail
    // FastAPI validation errors arrive as a list of per-field objects.
    if (Array.isArray(body.detail) && body.detail[0]?.msg) {
      return body.detail[0].msg
    }
  } catch {
    /* fall through */
  }
  return fallback
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // On load, ask the backend whether the saved token is still valid rather than
  // trusting whatever is in storage.
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (!token) {
      setLoading(false)
      return
    }
    fetch('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then((data) => setUser(data.user))
      .catch(() => localStorage.removeItem(TOKEN_KEY))
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) throw new Error(await errorFrom(res, 'Could not sign you in.'))
    const data = await res.json()
    localStorage.setItem(TOKEN_KEY, data.token)
    setUser(data.user)
  }, [])

  const register = useCallback(
    async (input: {
      first_name: string
      last_name: string
      email: string
      password: string
    }) => {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(input),
      })
      if (!res.ok) throw new Error(await errorFrom(res, 'Could not create your account.'))
      const data = await res.json()
      localStorage.setItem(TOKEN_KEY, data.token)
      setUser(data.user)
    },
    [],
  )

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({ user, loading, login, register, logout }),
    [user, loading, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside an AuthProvider')
  return context
}

/** The saved token, for callers that need to authenticate a request. */
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}
