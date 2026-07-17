"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { listNotifications, markNotificationRead, type Notification } from "@/lib/api";
import { useSession } from "@/lib/session";
import { useLanguage } from "@/lib/i18n/context";
import { formatRelative } from "@/lib/format";

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
      // topbar affordance only — a failed fetch just leaves the bell without a badge
    }
  }, [tokens?.accessToken]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  async function handleOpen() {
    setOpen((prev) => !prev);
    await load();
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
      >
        <span className="material-symbols-outlined">notifications</span>
        {unreadCount > 0 ? (
          <span className="absolute top-0 right-0 w-2 h-2 bg-error rounded-full border-2 border-surface" />
        ) : null}
      </button>

      {isOpen ? (
        <div className="absolute right-0 mt-2 w-80 max-h-96 overflow-y-auto custom-scrollbar bg-surface-container-lowest border border-outline-variant/30 rounded-xl shadow-xl z-50">
          <div className="px-lg py-md border-b border-outline-variant/20 flex items-center justify-between">
            <h4 className="font-label-md text-label-md">{t("shell.notifications.title")}</h4>
            {unreadCount > 0 ? (
              <span className="text-[10px] font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-full">
                {t("shell.notifications.newCount", { count: unreadCount })}
              </span>
            ) : null}
          </div>
          {notifications.length === 0 ? (
            <p className="px-lg py-lg text-body-sm text-on-surface-variant">{t("shell.notifications.empty")}</p>
          ) : (
            <ul className="divide-y divide-outline-variant/10">
              {notifications.slice(0, 12).map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    onClick={() => handleRead(item.id)}
                    className={
                      "w-full text-left px-lg py-md hover:bg-primary-container/5 transition-colors " +
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
