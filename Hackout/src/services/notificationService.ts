import type { AppNotification } from '../types/models';
import { api } from './http';

/**
 * Notifications — backed by /api/notifications (current user is derived from
 * the JWT, so the userId args are accepted for signature-compatibility but the
 * server scopes results to the authenticated user).
 */
export const notificationService = {
  async getNotifications(_userId: string): Promise<AppNotification[]> {
    return api<AppNotification[]>('/notifications');
  },
  async markAsRead(id: string): Promise<void> {
    await api(`/notifications/${id}/read`, { method: 'POST' });
  },
  async markAllAsRead(_userId: string): Promise<void> {
    await api('/notifications/read-all', { method: 'POST' });
  },
  /** Local-only optimistic helper — the server creates real notifications as
   *  side effects of actions (approve/invest/etc.); this just mints a temp one. */
  add(n: Omit<AppNotification, 'id' | 'createdAt' | 'isRead'>): AppNotification {
    return { ...n, id: `local-${Date.now()}`, createdAt: new Date().toISOString(), isRead: false };
  },
};
