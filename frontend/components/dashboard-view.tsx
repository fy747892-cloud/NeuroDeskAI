"use client";

import { useEffect, useMemo, useState } from "react";
import { DashboardData, getDashboard, HealthStatus } from "@/lib/api";
import { useSession } from "@/lib/session";
import { UserMenu } from "@/components/user-menu";

const navItems = [
  "Dashboard",
  "AI Chat",
  "Gorusmeler",
  "Gorevler",
  "Takvim",
  "Kisiler",
  "Mailler",
  "Onay Merkezi",
  "Analitik",
  "Ayarlar",
];

const fallbackQueue = [
  {
    title: "AI takip gorevini onayla",
    detail: "Gorusme analizi hasta karsilama kontrol listesi onerdi.",
    status: "AI onayi",
    time: "09:20",
  },
  {
    title: "Randevu cakismasini incele",
    detail: "Ayni organizasyon kisisi icin iki geri arama cakisiyor.",
    status: "Takvim",
    time: "10:05",
  },
  {
    title: "Email hesabini senkronize et",
    detail: "Gmail saglayicisi siradaki mesaj alma calismasi icin hazir.",
    status: "Email",
    time: "11:10",
  },
];

const aiSignals = [
  { name: "Gorusme analizi", state: "Varsayilan mock", value: "Hazir" },
  { name: "OpenAI uyumlu LLM", state: "Env kontrollu", value: "Opsiyonel" },
  { name: "Tenant kapsamli retrieval", state: "Context gated", value: "Aktif" },
];

type DashboardViewProps = {
  health: HealthStatus;
};

export function DashboardView({ health }: DashboardViewProps) {
  const { tokens } = useSession();
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);

  useEffect(() => {
    let isActive = true;

    async function loadDashboard() {
      if (!tokens?.accessToken) {
        return;
      }

      setLoading(true);
      setError(null);
      try {
        const data = await getDashboard(tokens.accessToken);
        if (isActive) {
          setDashboard(data);
        }
      } catch (loadError) {
        if (isActive) {
          setError(loadError instanceof Error ? loadError.message : "Dashboard verisi alinamadi.");
        }
      } finally {
        if (isActive) {
          setLoading(false);
        }
      }
    }

    loadDashboard();

    return () => {
      isActive = false;
    };
  }, [tokens?.accessToken]);

  const metrics = useMemo(() => {
    const summary = dashboard?.summary;
    return [
      {
        label: "Acik gorevler",
        value: String(summary?.open_tasks_count ?? 0),
        trend: `${summary?.overdue_tasks_count ?? 0} gecikmis`,
      },
      {
        label: "AI onaylari",
        value: String(summary?.pending_ai_approvals_count ?? 0),
        trend: "Insan onayi bekliyor",
      },
      {
        label: "Yaklasan randevular",
        value: String(summary?.upcoming_appointments_count ?? 0),
        trend: "7 gunluk pencere",
      },
      {
        label: "Son guncelleme",
        value: dashboard ? formatTime(dashboard.generated_at) : "--",
        trend: isLoading ? "Yukleniyor" : "Canli endpoint",
      },
    ];
  }, [dashboard, isLoading]);

  const queueItems = useMemo(() => {
    if (!dashboard) {
      return fallbackQueue;
    }

    const taskItems = [...dashboard.overdue_tasks, ...dashboard.open_tasks].slice(0, 4).map((task) => ({
      title: task.title,
      detail: task.description ?? `${task.priority} oncelikli ${task.status} gorev`,
      status: task.priority,
      time: task.due_at ? formatTime(task.due_at) : formatTime(task.created_at),
    }));

    const approvalItems = dashboard.pending_ai_approvals.slice(0, 3).map((approval) => ({
      title: `${approval.action_type} onayi`,
      detail: `${approval.source_type} kaynagindan uretilen AI aksiyonu.`,
      status: approval.status,
      time: formatTime(approval.created_at),
    }));

    const nextItems = [...approvalItems, ...taskItems];
    return nextItems.length > 0 ? nextItems : fallbackQueue;
  }, [dashboard]);

  return (
    <main className="shell">
      <aside className="sidebar" aria-label="Primary navigation">
        <div className="brand">
          <div className="brandMark">N</div>
          <div>
            <strong>NeuroDeskAI</strong>
            <span>Operations</span>
          </div>
        </div>

        <nav>
          {navItems.map((item) => (
            <a href="#" className={item === "Dashboard" ? "active" : ""} key={item}>
              {item}
            </a>
          ))}
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Workspace overview</p>
            <h1>Dashboard</h1>
          </div>
          <div className="topbarActions">
            <div className={`status ${health.ok ? "online" : "offline"}`}>
              <span aria-hidden="true" />
              {health.label}
            </div>
            <UserMenu />
          </div>
        </header>

        {error ? <p className="notice">{error}</p> : null}

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
              <h2>Priority Queue</h2>
              <button disabled={isLoading} onClick={() => window.location.reload()} type="button">
                {isLoading ? "Loading" : "Refresh"}
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
              <h2>AI Layer</h2>
              <span className="tag">LLM ready</span>
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
      </section>
    </main>
  );
}

function formatTime(value: string): string {
  return new Intl.DateTimeFormat("tr-TR", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}
