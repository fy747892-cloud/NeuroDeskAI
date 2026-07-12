"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { DashboardData, getDashboard } from "@/lib/api";
import { useSession } from "@/lib/session";

const fallbackQueue = [
  {
    title: "AI takip görevini onayla",
    detail: "Görüşme analizi hasta karşılama kontrol listesi önerdi.",
    status: "AI onayı",
    time: "09:20",
  },
  {
    title: "Randevu çakışmasını incele",
    detail: "Aynı organizasyon kişisi için iki geri arama çakışıyor.",
    status: "Takvim",
    time: "10:05",
  },
  {
    title: "E-posta hesabını senkronize et",
    detail: "Gmail sağlayıcısı sıradaki mesaj alma çalışması için hazır.",
    status: "E-posta",
    time: "11:10",
  },
];

const aiSignals = [
  { name: "Görüşme analizi", state: "Varsayılan mock", value: "Hazır" },
  { name: "OpenAI uyumlu LLM", state: "Env kontrollü", value: "Opsiyonel" },
  { name: "Tenant kapsamlı retrieval", state: "Context gated", value: "Aktif" },
];

export function DashboardView() {
  const { tokens, user } = useSession();
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);

  const loadDashboard = useCallback(async () => {
    if (!tokens?.accessToken) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      setDashboard(await getDashboard(tokens.accessToken));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Dashboard verisi alınamadı.");
    } finally {
      setLoading(false);
    }
  }, [tokens?.accessToken]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const metrics = useMemo(() => {
    const summary = dashboard?.summary;
    return [
      {
        label: "Açık görevler",
        value: String(summary?.open_tasks_count ?? 0),
        trend: `${summary?.overdue_tasks_count ?? 0} gecikmiş`,
      },
      {
        label: "AI onayları",
        value: String(summary?.pending_ai_approvals_count ?? 0),
        trend: "İnsan onayı bekliyor",
      },
      {
        label: "Yaklaşan randevular",
        value: String(summary?.upcoming_appointments_count ?? 0),
        trend: "7 günlük pencere",
      },
      {
        label: "Son güncelleme",
        value: dashboard ? formatTime(dashboard.generated_at) : "--",
        trend: isLoading ? "Yükleniyor" : "Canlı endpoint",
      },
    ];
  }, [dashboard, isLoading]);

  const queueItems = useMemo(() => {
    if (!dashboard) {
      return fallbackQueue;
    }

    const taskItems = [...dashboard.overdue_tasks, ...dashboard.open_tasks].slice(0, 4).map((task) => ({
      title: task.title,
      detail: task.description ?? `${task.priority} öncelikli ${task.status} görev`,
      status: task.priority,
      time: task.due_at ? formatTime(task.due_at) : formatTime(task.created_at),
    }));

    const approvalItems = dashboard.pending_ai_approvals.slice(0, 3).map((approval) => ({
      title: `${approval.action_type} onayı`,
      detail: `${approval.source_type} kaynağından üretilen AI aksiyonu.`,
      status: approval.status,
      time: formatTime(approval.created_at),
    }));

    const nextItems = [...approvalItems, ...taskItems];
    return nextItems.length > 0 ? nextItems : fallbackQueue;
  }, [dashboard]);

  const userName =
    user?.profile?.full_name?.trim() || user?.email?.split("@")[0] || "NeuroDesk";
  const todayLabel = useMemo(
    () =>
      new Intl.DateTimeFormat("tr-TR", {
        day: "2-digit",
        month: "long",
        weekday: "long",
        year: "numeric",
      }).format(new Date()),
    [],
  );

  return (
    <>
      {error ? <p className="notice">{error}</p> : null}

      <section className="dashboardHero">
        <div>
          <div className="heroMeta">
            <p className="eyebrow">Bugünün özeti</p>
            <span>{todayLabel}</span>
          </div>
          <h2>Günaydın, {userName}</h2>
          <p>
            Bugünün görevleri, randevuları ve AI onayları tek ekranda toplandı.
          </p>
        </div>
        <button disabled={isLoading} onClick={loadDashboard} type="button">
          {isLoading ? "Yükleniyor" : "Özeti yenile"}
        </button>
      </section>

      <section className="metrics" aria-label="Key metrics">
        {metrics.map((metric) => (
          <article className="metric" key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
            <small>{metric.trend}</small>
          </article>
        ))}
      </section>

      <section className="contentGrid">
        <div className="panel queuePanel">
          <div className="panelHeader">
            <h2>Akıllı Asistan Özeti</h2>
            <button disabled={isLoading} onClick={loadDashboard} type="button">
              {isLoading ? "Yükleniyor" : "Yenile"}
            </button>
          </div>
          <div className="queueList">
            {queueItems.map((item) => (
              <article className="queueItem" key={`${item.title}-${item.time}`}>
                <time>{item.time}</time>
                <div>
                  <h3>{item.title}</h3>
                  <p>{item.detail}</p>
                </div>
                <span>{item.status}</span>
              </article>
            ))}
          </div>
        </div>

        <div className="panel aiPanel">
          <div className="panelHeader">
            <h2>AI Katmanı</h2>
            <span className="tag">LLM hazır</span>
          </div>
          <div className="signalList">
            {aiSignals.map((signal) => (
              <div className="signal" key={signal.name}>
                <div>
                  <strong>{signal.name}</strong>
                  <span>{signal.state}</span>
                </div>
                <b>{signal.value}</b>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}

function formatTime(value: string): string {
  return new Intl.DateTimeFormat("tr-TR", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}
