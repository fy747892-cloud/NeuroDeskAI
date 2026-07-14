"use client";

import Link from "next/link";
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
import { formatTime } from "@/lib/format";

export function DashboardView() {
  const { tokens, user } = useSession();
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    if (!tokens?.accessToken) return;
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

  const firstName =
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
  const overdueCount = dashboard?.summary.overdue_tasks_count ?? 0;

  return (
    <div className="p-xl space-y-xl">
      {error ? <p className="text-error text-body-sm">{error}</p> : null}

      <section className="relative overflow-hidden rounded-3xl p-xl glass-card ai-banner-shimmer shadow-lg">
        <div className="relative z-10 max-w-3xl">
          <div className="flex items-center gap-2 mb-md">
            <span className="material-symbols-outlined text-secondary" style={{ fontVariationSettings: "'FILL' 1" }}>
              auto_awesome
            </span>
            <span className="font-label-sm text-label-sm text-secondary uppercase tracking-widest">
              Intelligent Overview
            </span>
          </div>
          <h2 className="font-headline-lg text-headline-lg text-on-background leading-tight">
            Günaydın, {firstName}! Bugün{" "}
            <span className="text-primary font-bold">{appointments.length} randevun</span>,{" "}
            <span className="text-primary font-bold">
              {dashboard?.summary.pending_ai_approvals_count ?? 0} bekleyen AI önerin
            </span>{" "}
            ve{" "}
            <span className="text-primary font-bold">
              {dashboard?.summary.open_tasks_count ?? 0} açık görevin
            </span>{" "}
            var.
          </h2>
          <div className="mt-xl flex gap-md">
            <button
              type="button"
              disabled={isLoading}
              onClick={loadDashboard}
              className="bg-primary text-on-primary px-lg py-sm rounded-full font-label-md flex items-center gap-2 hover:shadow-lg hover:-translate-y-0.5 transition-all disabled:opacity-60"
            >
              <span className="material-symbols-outlined text-[18px]">bolt</span>
              {isLoading ? "Yükleniyor..." : "Özeti Yenile"}
            </button>
            <Link
              href="/gorevler"
              className="bg-white/50 border border-outline-variant text-on-surface px-lg py-sm rounded-full font-label-md hover:bg-white transition-colors"
            >
              Tüm Takvimi Gör
            </Link>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-xl">
        <div className="flex flex-col gap-lg">
          <div className="flex items-center justify-between">
            <h3 className="font-headline-md text-headline-md flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">calendar_today</span>
              Bugünün Randevuları
            </h3>
            <Link href="/gorevler" className="text-primary font-label-sm text-label-sm hover:underline">
              Tümünü Gör
            </Link>
          </div>
          <div className="space-y-md">
            {appointments.length === 0 ? (
              <p className="text-body-sm text-on-surface-variant">Yaklaşan randevu bulunmuyor.</p>
            ) : (
              appointments.map((appt) => (
                <article
                  key={appt.id}
                  className="p-md rounded-xl bg-white border border-outline-variant/30 hover:shadow-md transition-shadow cursor-pointer group"
                >
                  <div className="flex gap-md">
                    <div className="flex flex-col items-center justify-center w-14 py-2 bg-primary-container/10 rounded-lg shrink-0">
                      <span className="font-label-sm text-label-sm text-primary">
                        {formatTime(appt.start_at)}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-label-md text-label-md group-hover:text-primary transition-colors truncate">
                        {appt.title}
                      </p>
                      <p className="font-body-sm text-body-sm text-on-surface-variant truncate">
                        {appt.location ?? appt.description ?? "Detay yok"}
                      </p>
                    </div>
                  </div>
                </article>
              ))
            )}
          </div>
        </div>

        <div className="flex flex-col gap-lg">
          <div className="flex items-center justify-between">
            <h3 className="font-headline-md text-headline-md flex items-center gap-2">
              <span className="material-symbols-outlined text-error">warning</span>
              Kritik Görevler
            </h3>
            {overdueCount > 0 ? (
              <div className="bg-error-container text-on-error-container text-[10px] px-2 py-0.5 rounded font-bold">
                {overdueCount} OVERDUE
              </div>
            ) : null}
          </div>
          <div className="bg-white rounded-2xl border border-outline-variant/30 overflow-hidden">
            {criticalTasks.length === 0 ? (
              <p className="p-md text-body-sm text-on-surface-variant">Bekleyen kritik görev yok.</p>
            ) : (
              <div className="divide-y divide-outline-variant/20">
                {criticalTasks.map((task) => (
                  <TaskRow
                    key={task.id}
                    task={task}
                    isBusy={busyId === task.id}
                    onComplete={() => handleCompleteTask(task.id)}
                  />
                ))}
              </div>
            )}
            <div className="p-md bg-surface-container-low border-t border-outline-variant/30 text-center">
              <Link
                href="/gorevler"
                className="text-primary font-label-sm text-label-sm flex items-center justify-center w-full gap-2"
              >
                <span className="material-symbols-outlined text-[18px]">add</span>
                Yeni Görev Oluştur
              </Link>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-lg">
          <div className="flex items-center justify-between">
            <h3 className="font-headline-md text-headline-md flex items-center gap-2">
              <span className="material-symbols-outlined text-secondary" style={{ fontVariationSettings: "'FILL' 1" }}>
                smart_toy
              </span>
              AI Suggestions
            </h3>
            <Link href="/onay-merkezi" className="text-on-surface-variant text-[11px] hover:text-primary">
              Tümünü Gör
            </Link>
          </div>
          <div className="space-y-md">
            {approvals.length === 0 ? (
              <p className="text-body-sm text-on-surface-variant">Onay bekleyen AI önerisi yok.</p>
            ) : (
              approvals.map((approval) => (
                <div
                  key={approval.id}
                  className="bg-white rounded-2xl border border-secondary/20 shadow-sm overflow-hidden relative"
                >
                  <div className="absolute left-0 top-0 w-1 h-full bg-secondary" />
                  <div className="p-md">
                    <div className="flex items-center gap-2 mb-sm">
                      <span className="material-symbols-outlined text-secondary text-[18px]">
                        {actionTypeIcon(approval.action_type)}
                      </span>
                      <span className="font-label-sm text-label-sm text-on-surface-variant capitalize">
                        {approval.action_type}
                      </span>
                    </div>
                    <p className="font-label-md text-label-md mb-sm text-on-surface">
                      {approval.source_type} kaynağından üretildi
                    </p>
                    {approval.confidence_score !== null ? (
                      <p className="text-[11px] text-primary font-bold mb-md">
                        %{Math.round(approval.confidence_score * 100)} güven skoru
                      </p>
                    ) : null}
                    <div className="flex gap-2">
                      <button
                        type="button"
                        disabled={busyId === approval.id}
                        onClick={() => handleApprove(approval.id)}
                        className="flex-1 py-1.5 bg-primary text-on-primary rounded-lg text-[12px] font-bold active:scale-95 transition-transform disabled:opacity-60"
                      >
                        Onayla
                      </button>
                      <button
                        type="button"
                        disabled={busyId === approval.id}
                        onClick={() => handleReject(approval.id)}
                        className="flex-1 py-1.5 bg-white border border-outline-variant rounded-lg text-[12px] font-bold text-on-surface active:scale-95 transition-transform disabled:opacity-60"
                      >
                        Reddet
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
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
    <div className="p-md flex gap-md items-start hover:bg-surface-container-low transition-colors group">
      <button
        type="button"
        disabled={isBusy}
        onClick={onComplete}
        aria-label="Görevi tamamla"
        className="mt-1 w-5 h-5 rounded border-2 border-outline-variant flex items-center justify-center group-hover:border-primary transition-colors shrink-0 disabled:opacity-60"
      >
        <span className="material-symbols-outlined text-[16px] text-transparent">check</span>
      </button>
      <div className="flex-1 min-w-0">
        <div className="flex justify-between items-start gap-2">
          <p className="font-label-md text-label-md text-on-surface truncate">{task.title}</p>
          <span className="text-[10px] px-2 py-0.5 bg-primary/10 text-primary rounded font-bold uppercase tracking-tighter shrink-0">
            {task.priority}
          </span>
        </div>
        {task.overdue ? (
          <p className="font-body-sm text-body-sm text-error mt-xs flex items-center gap-1">
            <span className="material-symbols-outlined text-[14px]">schedule</span>
            Süresi geçti
          </p>
        ) : (
          <p className="font-body-sm text-body-sm text-on-surface-variant mt-xs truncate">
            {task.description ?? task.status}
          </p>
        )}
      </div>
    </div>
  );
}

function actionTypeIcon(actionType: string): string {
  switch (actionType) {
    case "appointment":
      return "calendar_today";
    case "deal":
      return "payments";
    case "task":
      return "checklist";
    default:
      return "auto_awesome";
  }
}
