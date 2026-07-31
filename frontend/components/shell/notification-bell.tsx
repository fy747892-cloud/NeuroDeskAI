"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { listNotifications, markAllNotificationsRead, markNotificationRead, type Notification } from "@/lib/api";
import { useSession } from "@/lib/session";
import { useLanguage } from "@/lib/i18n/context";
import { formatRelative } from "@/lib/format";
import { EmptyState } from "@/components/shell/empty-state";

export function NotificationBell() {
  const { tokens } = useSession();
  const { t, language } = useLanguage();
  const [isOpen, setOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const unreadCount = notifications.filter((item) => !item.read_at).length;

  const load = useCallback(async () => {
    if (!tokens?.accessToken) return;
    try {
      setNotifications(await listNotifications(tokens.accessToken));
    } catch {
      // Topbar affordance only; a failed fetch just leaves the bell without a badge.
    }
  }, [tokens?.accessToken]);

  useEffect(() => {
    load();
    const timer = window.setInterval(load, 20000);
    return () => window.clearInterval(timer);
  }, [load]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, []);

  async function handleOpen() {
    setOpen((prev) => !prev);
    await load();
  }

  async function handleMarkAllRead() {
    if (!tokens?.accessToken) return;
    const now = new Date().toISOString();
    setNotifications((prev) => prev.map((item) => (item.read_at ? item : { ...item, read_at: now })));
    try {
      await markAllNotificationsRead(tokens.accessToken);
    } catch {
      await load();
    }
  }

  async function handleRead(id: string) {
    if (!tokens?.accessToken) return;
    setNotifications((prev) =>
      prev.map((item) => (item.id === id ? { ...item, read_at: new Date().toISOString() } : item)),
    );
    try {
      await markNotificationRead(tokens.accessToken, id);
    } catch {
      await load();
    }
  }

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        onClick={handleOpen}
        className="relative text-on-surface-variant hover:text-primary transition-colors"
        aria-label={t("shell.notifications.aria")}
        aria-haspopup="true"
        aria-expanded={isOpen}
      >
        <span className="material-symbols-outlined">notifications</span>
        {unreadCount > 0 ? (
          <span className="absolute top-0 right-0 w-2 h-2 bg-error rounded-full border-2 border-surface" />
        ) : null}
      </button>

      {isOpen ? (
        <div className="absolute right-0 mt-2 w-[calc(100vw-2rem)] max-w-80 max-h-[70vh] overflow-y-auto custom-scrollbar bg-surface-container-lowest border border-outline-variant/30 rounded-xl shadow-xl z-50">
          <div className="px-lg py-md border-b border-outline-variant/20 flex items-center justify-between gap-2">
            <h4 className="font-label-md text-label-md">{t("shell.notifications.title")}</h4>
            <div className="flex items-center gap-2 shrink-0">
              {unreadCount > 0 ? (
                <span className="text-[10px] font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-full">
                  {t("shell.notifications.newCount", { count: unreadCount })}
                </span>
              ) : null}
              {unreadCount > 0 ? (
                <button
                  type="button"
                  onClick={handleMarkAllRead}
                  className="text-[11px] font-bold text-on-surface-variant hover:text-primary hover:underline"
                >
                  {t("shell.notifications.markAllRead")}
                </button>
              ) : null}
            </div>
          </div>
          {notifications.length === 0 ? (
            <EmptyState icon="notifications_off" title={t("shell.notifications.empty")} />
          ) : (
            <ul className="divide-y divide-outline-variant/10">
              {notifications.slice(0, 12).map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    onClick={() => handleRead(item.id)}
                    className={
                      "w-full text-left px-lg py-md hover:bg-primary-container/5 active:bg-primary-container/10 transition-colors " +
                      (item.read_at ? "opacity-60" : "")
                    }
                  >
                    <p className="font-label-md text-label-md text-on-surface">{item.title}</p>
                    <p className="text-body-sm text-on-surface-variant line-clamp-2 mt-0.5">{item.body}</p>
                    <p className="text-[10px] text-outline mt-1">{formatRelative(item.created_at, language)}</p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}
    </div>
  );
}
