"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  approveAction,
  completeTask,
  DashboardData,
  DashboardTask,
  getDashboard,
  rejectAction,
} from "@/lib/api";
import { useSession } from "@/lib/session";

export function DashboardView() {
  const { tokens, user } = useSession();
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);

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

  async function handleCompleteTask(taskId: string) {
    if (!tokens?.accessToken) return;
    setBusyId(taskId);
    try {
      await completeTask(tokens.accessToken, taskId);
      await loadDashboard();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Görev tamamlanamadı.");
    } finally {
      setBusyId(null);
    }
  }

  async function handleApprove(approvalId: string) {
    if (!tokens?.accessToken) return;
    setBusyId(approvalId);
    try {
      await approveAction(tokens.accessToken, approvalId);
      await loadDashboard();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Öneri onaylanamadı.");
    } finally {
      setBusyId(null);
    }
  }

  async function handleReject(approvalId: string) {
    if (!tokens?.accessToken) return;
    setBusyId(approvalId);
    try {
      await rejectAction(tokens.accessToken, approvalId);
      await loadDashboard();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Öneri reddedilemedi.");
    } finally {
      setBusyId(null);
    }
  }

  const userName =
    user?.profile?.full_name?.trim().split(" ")[0] || user?.email?.split("@")[0] || "NeuroDesk";

  const criticalTasks = useMemo(() => {
    if (!dashboard) return [];
    const overdue = dashboard.overdue_tasks.map((task) => ({ ...task, overdue: true }));
    const open = dashboard.open_tasks
      .filter((task) => !overdue.some((item) => item.id === task.id))
      .map((task) => ({ ...task, overdue: false }));
    return [...overdue, ...open].slice(0, 4);
  }, [dashboard]);

  const appointments = dashboard?.upcoming_appointments.slice(0, 4) ?? [];
  const approvals = dashboard?.pending_ai_approvals.slice(0, 3) ?? [];

  return (
    <>
      {error ? <p className="notice">{error}</p> : null}

      <section className="heroBanner">
        <div className="heroTag">
          <span className="material-symbols-outlined" aria-hidden="true">
            auto_awesome
          </span>
          Akıllı Özet
        </div>
        <h2>
          Günaydın, {userName}! Bugün <strong>{appointments.length} randevun</strong>,{" "}
          <strong>{dashboard?.summary.pending_ai_approvals_count ?? 0} bekleyen AI önerin</strong>{" "}
          ve <strong>{dashboard?.summary.open_tasks_count ?? 0} açık görevin</strong> var.
        </h2>
        <div className="heroActions">
          <button className="primaryBtn" disabled={isLoading} onClick={loadDashboard} type="button">
            <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 18 }}>
              bolt
            </span>
            {isLoading ? "Yükleniyor" : "Özeti Yenile"}
          </button>
          <a className="ghostBtn" href="/takvim">
            Tüm Takvimi Gör
          </a>
        </div>
      </section>

      <div className="dashboardColumns">
        <div>
          <div className="columnHead">
            <h3>
              <span className="material-symbols-outlined" aria-hidden="true" style={{ color: "var(--primary)" }}>
                calendar_today
              </span>
              Bugünün Randevuları
            </h3>
            <a href="/takvim">Tümünü Gör</a>
          </div>
          <div className="apptList">
            {appointments.length === 0 ? (
              <p className="emptyState">Yaklaşan randevu bulunmuyor.</p>
            ) : (
              appointments.map((appt) => (
                <article className="apptCard" key={appt.id}>
                  <div className="apptTime">
                    <span>{formatTime(appt.start_at)}</span>
                  </div>
                  <div>
                    <h4>{appt.title}</h4>
                    <p>{appt.location ?? appt.description ?? "Detay yok"}</p>
                  </div>
                </article>
              ))
            )}
          </div>
        </div>

        <div>
          <div className="columnHead">
            <h3>
              <span className="material-symbols-outlined" aria-hidden="true" style={{ color: "var(--coral)" }}>
                warning
              </span>
              Kritik Görevler
            </h3>
            <a href="/gorevler">Tümünü Gör</a>
          </div>
          <div className="taskBoard">
            {criticalTasks.length === 0 ? (
              <p className="emptyState">Bekleyen kritik görev yok.</p>
            ) : (
              criticalTasks.map((task) => (
                <TaskRow
                  key={task.id}
                  task={task}
                  isBusy={busyId === task.id}
                  onComplete={() => handleCompleteTask(task.id)}
                />
              ))
            )}
            <div className="taskBoardFooter">
              <a href="/gorevler">
                <button type="button">+ Yeni Görev Oluştur</button>
              </a>
            </div>
          </div>
        </div>

        <div>
          <div className="columnHead">
            <h3>
              <span className="material-symbols-outlined" aria-hidden="true" style={{ color: "var(--purple)" }}>
                smart_toy
              </span>
              AI Önerileri
            </h3>
            <a href="/onay-merkezi">Tümünü Gör</a>
          </div>
          <div className="suggestionList">
            {approvals.length === 0 ? (
              <p className="emptyState">Onay bekleyen AI önerisi yok.</p>
            ) : (
              approvals.map((approval, index) => (
                <article className={`suggestionCard${index === 0 ? " primary" : ""}`} key={approval.id}>
                  <div className="suggestionEyebrow">
                    <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 16 }}>
                      auto_awesome
                    </span>
                    {approval.action_type}
                  </div>
                  <h4>{approval.source_type} kaynağından üretildi</h4>
                  {approval.confidence_score !== null ? (
                    <p className="confidenceTag">
                      %{Math.round(approval.confidence_score * 100)} güven skoru
                    </p>
                  ) : null}
                  <div className="suggestionActions">
                    <button
                      className="approveBtn"
                      disabled={busyId === approval.id}
                      onClick={() => handleApprove(approval.id)}
                      type="button"
                    >
                      Onayla
                    </button>
                    <button
                      className="rejectBtn"
                      disabled={busyId === approval.id}
                      onClick={() => handleReject(approval.id)}
                      type="button"
                    >
                      Reddet
                    </button>
                  </div>
                </article>
              ))
            )}
          </div>
        </div>
      </div>
    </>
  );
}

function TaskRow({
  task,
  isBusy,
  onComplete,
}: {
  task: DashboardTask & { overdue: boolean };
  isBusy: boolean;
  onComplete: () => void;
}) {
  return (
    <div className="taskRow">
      <button
        className="taskCheck"
        disabled={isBusy}
        onClick={onComplete}
        type="button"
        aria-label="Görevi tamamla"
      >
        <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 14 }}>
          check
        </span>
      </button>
      <div className="taskBody">
        <div className="taskTitleRow">
          <p style={{ margin: 0, fontWeight: 500 }}>{task.title}</p>
          <span className="taskPill">{task.priority}</span>
        </div>
        {task.overdue ? (
          <p className="dueMeta">
            <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 14 }}>
              schedule
            </span>
            Süresi geçti
          </p>
        ) : (
          <p className="plainMeta">{task.description ?? task.status}</p>
        )}
      </div>
    </div>
  );
}

function formatTime(value: string): string {
  return new Intl.DateTimeFormat("tr-TR", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}
