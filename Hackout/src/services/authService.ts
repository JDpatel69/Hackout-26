import type { AuthSession, User, UserRole } from '../types/models';
import { api, tokenStore } from './http';

/**
 * Real authentication against the FastAPI backend.
 * Public method signatures are identical to the old mock, so AuthContext,
 * useAuth and every consumer keep working without any edits.
 *
 * Backend contract (see backend/app/routes/auth.py):
 *   POST /auth/signin  {email,password} -> {user, token, expiresAt}
 *   POST /auth/signout                  -> {message}   (stateless)
 *   GET  /auth/me                       -> User
 *   POST /auth/refresh                  -> {user, token, expiresAt}
 */

const SESSION_KEY = 'terra-ledger-session';

/** In-memory cache of the active session for the current tab. */
let current: AuthSession | null = null;

function cache(session: AuthSession) {
  current = session;
  tokenStore.set(session.token);
  localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

function clear() {
  current = null;
  tokenStore.set(null);
  localStorage.removeItem(SESSION_KEY);
}

export const authService = {
  async signIn(email: string, password: string): Promise<AuthSession> {
    const session = await api<AuthSession>('/auth/signin', {
      method: 'POST',
      auth: false,
      body: { email, password },
    });
    cache(session);
    return session;
  },

  async signOut(): Promise<void> {
    try {
      await api('/auth/signout', { method: 'POST' });
    } catch {
      /* server is stateless — ignore network/401 on signout */
    }
    clear();
  },

  async getCurrentUser(): Promise<User | null> {
    if (current) return current.user;
    if (!tokenStore.get()) return null;
    try {
      return await api<User>('/auth/me');
    } catch {
      return null;
    }
  },

  async getUserRole(): Promise<UserRole | null> {
    if (current) return current.user.role;
    if (!tokenStore.get()) return null;
    try {
      const user = await api<User>('/auth/me');
      return user.role;
    } catch {
      return null;
    }
  },

  async isAuthenticated(): Promise<boolean> {
    return Boolean(tokenStore.get());
  },

  async refreshSession(): Promise<AuthSession> {
    if (!tokenStore.get()) throw new Error('No active session');
    try {
      const session = await api<AuthSession>('/auth/refresh', { method: 'POST' });
      cache(session);
      return session;
    } catch (err) {
      clear();
      throw err;
    }
  },
};
