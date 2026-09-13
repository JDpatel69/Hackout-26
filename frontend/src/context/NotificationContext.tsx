import { createContext, useCallback, useEffect, useMemo, useState } from 'react';
import type { AppNotification } from '../types/models';
import { notificationService } from '../services/notificationService';
import { useAuth } from '../hooks/useAuth';

export interface NotificationContextValue {
  notifications: AppNotification[];
  unreadCount: number;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  addNotification: (n: Omit<AppNotification, 'id' | 'createdAt' | 'isRead'>) => void;
  /** Re-fetch notifications from the server (call after approve/reject/invest actions). */
  refresh: () => void;
}

export const NotificationContext = createContext<NotificationContextValue | null>(null);

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState<AppNotification[]>([]);

  const refresh = useCallback(() => {
    if (!user) { setNotifications([]); return; }
    void notificationService.getNotifications(user.id).then(setNotifications);
  }, [user]);

  // Fetch on login / user change
  useEffect(() => { refresh(); }, [refresh]);

  const markAsRead = useCallback((id: string) => {
    setNotifications((all) => all.map((n) => (n.id === id ? { ...n, isRead: true } : n)));
    void notificationService.markAsRead(id);
  }, []);

  const markAllAsRead = useCallback(() => {
    if (!user) return;
    setNotifications((all) => all.map((n) => ({ ...n, isRead: true })));
    void notificationService.markAllAsRead(user.id);
  }, [user]);

  const addNotification = useCallback(
    (n: Omit<AppNotification, 'id' | 'createdAt' | 'isRead'>) => {
      setNotifications((all) => [notificationService.add(n), ...all]);
    },
    [],
  );

  const value = useMemo(
    () => ({
      notifications,
      unreadCount: notifications.filter((n) => !n.isRead).length,
      markAsRead,
      markAllAsRead,
      addNotification,
      refresh,
    }),
    [notifications, markAsRead, markAllAsRead, addNotification, refresh],
  );

  return <NotificationContext.Provider value={value}>{children}</NotificationContext.Provider>;
}
