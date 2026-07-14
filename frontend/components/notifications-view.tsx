"use client";

import { useEffect, useMemo, useState } from "react";
import {
  listNotifications,
  markNotificationRead,
  Notification,
  processDueNotifications,
  ProcessDueSummary,
} from "@/lib/api";
import { useSession } from "@/lib/session";

export function NotificationsView() {
  const { tokens } = useSession();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [lastProcess, setLastProcess] = useState<ProcessDueSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [activeId, setActiveId] = useState<string | null>(null);

  async function loadNotifications() {
    if (!tokens?.accessToken) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      setNotifications(await listNotifications(tokens.accessToken));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Bildirimler alınamadı.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadNotifications();
  }, [tokens?.accessToken]);

  const summary = useMemo(() => {
    return {
      total: notifications.length,
      unread: notifications.filter((notification) => !notification.read_at).length,
      failed: notifications.filter((notification) => notification.status === "failed").length,
      due: notifications.filter((notification) => new Date(notification.scheduled_at) <= new Date()).length,
    };
  }, [notifications]);

  async function handleRead(notificationId: string) {
    if (!tokens?.accessToken) {
      return;
    }

    setActiveId(notificationId);
    setError(null);
    try {
      const updatedNotification = await markNotificationRead(tokens.accessToken, notificationId);
      setNotifications((currentNotifications) =>
        currentNotifications.map((notification) =>
          notification.id === updatedNotification.id ? updatedNotification : notification,
        ),
      );
    } catch (readError) {
      setError(readError instanceof Error ? readError.message : "Bildirim okundu isaretlenemedi.");
    } finally {
      setActiveId(null);
    }
  }

  async function handleProcessDue() {
    if (!tokens?.accessToken) {
      return;
    }

    setActiveId("process-due");
    setError(null);
    try {
      const summary = await processDueNotifications(tokens.accessToken);
      setLastProcess(summary);
      await loadNotifications();
    } catch (processError) {
      setError(processError instanceof Error ? processError.message : "Due bildirimler islenemedi.");
    } finally {
      setActiveId(null);
    }
  }

  return (
    <section className="moduleSurface">
      {error ? <p className="notice">{error}</p> : null}
      {lastProcess ? (
        <p className="notice success">
          Islem: {lastProcess.processed}, gonderilen: {lastProcess.sent}, hata: {lastProcess.failed}
        </p>
      ) : null}

      <div className="statTileRow">
        <StatTile icon="notifications" label="Toplam" value={summary.total} />
        <StatTile icon="mark_email_unread" label="Okunmamış" value={summary.unread} />
        <StatTile icon="schedule" label="Zamanı gelen" value={summary.due} />
        <StatTile icon="error" label="Hatalı" value={summary.failed} />
      </div>

      <section className="panel">
        <div className="panelHeader">
          <h2>Bildirim merkezi</h2>
          <div className="rowActions horizontal">
            <button disabled={isLoading} onClick={loadNotifications} type="button">
              {isLoading ? "Yükleniyor" : "Yenile"}
            </button>
            <button disabled={activeId === "process-due"} onClick={handleProcessDue} type="button">
              Zamanı geleni işle
            </button>
          </div>
        </div>
        <div className="dataList">
          {isLoading ? <p className="emptyState">Bildirimler yukleniyor.</p> : null}
          {!isLoading && notifications.length === 0 ? (
            <p className="emptyState">Bildirim bulunmuyor.</p>
          ) : null}
          {notifications.map((notification) => (
            <article className="dataRow" key={notification.id}>
              <div>
                <div className="rowTitle">
                  <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 16 }}>
                    {notification.channel === "email" ? "mail" : "notifications"}
                  </span>
                  <h3>{notification.title}</h3>
                  {!notification.read_at ? <span className="priorityTag ai">Yeni</span> : null}
                </div>
                <p>{notification.body}</p>
                <small>{formatDateTime(notification.scheduled_at)} · {notification.channel}</small>
              </div>
              <div className="rowActions horizontal">
                <span className={notification.status === "failed" ? "statusPill danger" : notification.read_at ? "statusPill done" : "statusPill"}>
                  {notification.status}
                </span>
                <button
                  disabled={Boolean(notification.read_at) || activeId === notification.id}
                  onClick={() => handleRead(notification.id)}
                  type="button"
                >
                  Okundu
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}

function StatTile({ icon, label, value }: { icon: string; label: string; value: number }) {
  return (
    <div className="statTile">
      <div className="statTileHead">
        <div className="statTileIcon">
          <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 18 }}>
            {icon}
          </span>
        </div>
      </div>
      <p>{label}</p>
      <strong>{value}</strong>
    </div>
  );
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
  }).format(new Date(value));
}
