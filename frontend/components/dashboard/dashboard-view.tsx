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
  sendWhatsAppFromApproval,
} from "@/lib/api";
import { useSession } from "@/lib/session";
import { useLanguage } from "@/lib/i18n/context";
import { useToast } from "@/lib/toast";
import { formatTime } from "@/lib/format";
import { Skeleton, SkeletonRow } from "@/components/shell/skeleton";
import { EmptyState } from "@/components/shell/empty-state";

export function DashboardView() {
  const { tokens, user } = useSession();
  const { t, language } = useLanguage();
  const { showToast } = useToast();
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
      setError(loadError instanceof Error ? loadError.message : t("dashboard.loadError"));
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
      setError(actionError instanceof Error ? actionError.message : t("dashboard.taskCompleteError"));
    } finally {
      setBusyId(null);
    }
  }

  async function handleApprove(approvalId: string) {
    if (!tokens?.accessToken) return;
    setBusyId(approvalId);
    try {
      const approval = dashboard?.pending_ai_approvals.find((item) => item.id === approvalId);
      await approveAction(tokens.accessToken, approvalId);
      if (approval?.action_type === "whatsapp_message") {
        const message = await sendWhatsAppFromApproval(tokens.accessToken, approvalId);
        showToast(t("dashboard.whatsappReadyToast"), "success", {
          action: {
            label: t("approvals.whatsappToast.action"),
            onClick: () => window.open(message.deep_link_url, "_blank", "noopener,noreferrer"),
          },
        });
      }
      await loadDashboard();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : t("dashboard.approveError"));
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
      setError(actionError instanceof Error ? actionError.message : t("dashboard.rejectError"));
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

  const isWorkspaceEmpty = Boolean(
    dashboard &&
      dashboard.summary.open_tasks_count === 0 &&
      dashboard.summary.overdue_tasks_count === 0 &&
      dashboard.summary.upcoming_appointments_count === 0 &&
      dashboard.summary.pending_ai_approvals_count === 0 &&
      dashboard.recent_conversations.length === 0,
  );

  return (
    <div className="p-xl space-y-xl">
      {error ? <p className="text-error text-body-sm">{error}</p> : null}

      {isWorkspaceEmpty ? (
        <section className="rounded-3xl p-xl glass-card border border-primary/10">
          <div className="flex items-center gap-2 mb-md">
            <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>
              rocket_launch
            </span>
            <span className="font-label-sm text-label-sm text-primary uppercase tracking-widest">
              {t("dashboard.onboarding.eyebrow")}
            </span>
          </div>
          <h3 className="font-headline-md text-headline-md text-on-surface mb-1">{t("dashboard.onboarding.title")}</h3>
          <p className="text-body-md text-on-surface-variant mb-lg max-w-2xl">{t("dashboard.onboarding.subtitle")}</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-md">
            <Link
              href="/gorusmeler"
              className="flex items-start gap-3 p-md rounded-xl border border-outline-variant/30 bg-surface-container-lowest hover:border-primary/40 hover:shadow-md active:scale-[0.98] transition-all"
            >
              <span className="material-symbols-outlined text-primary shrink-0">mic</span>
              <span>
                <span className="block font-label-md text-on-surface">{t("dashboard.onboarding.step1Title")}</span>
                <span className="block text-body-sm text-on-surface-variant mt-0.5">
                  {t("dashboard.onboarding.step1Body")}
                </span>
              </span>
            </Link>
            <Link
              href="/gorevler"
              className="flex items-start gap-3 p-md rounded-xl border border-outline-variant/30 bg-surface-container-lowest hover:border-primary/40 hover:shadow-md active:scale-[0.98] transition-all"
            >
              <span className="material-symbols-outlined text-primary shrink-0">task_alt</span>
              <span>
                <span className="block font-label-md text-on-surface">{t("dashboard.onboarding.step2Title")}</span>
                <span className="block text-body-sm text-on-surface-variant mt-0.5">
                  {t("dashboard.onboarding.step2Body")}
                </span>
              </span>
            </Link>
            <Link
              href="/kisiler"
              className="flex items-start gap-3 p-md rounded-xl border border-outline-variant/30 bg-surface-container-lowest hover:border-primary/40 hover:shadow-md active:scale-[0.98] transition-all"
            >
              <span className="material-symbols-outlined text-primary shrink-0">person_add</span>
              <span>
                <span className="block font-label-md text-on-surface">{t("dashboard.onboarding.step3Title")}</span>
                <span className="block text-body-sm text-on-surface-variant mt-0.5">
                  {t("dashboard.onboarding.step3Body")}
                </span>
              </span>
            </Link>
          </div>
        </section>
      ) : null}

      <section className="relative overflow-hidden rounded-3xl p-xl glass-card ai-banner-shimmer shadow-lg">
        <div className="relative z-10 max-w-3xl">
          <div className="flex items-center gap-2 mb-md">
            <span className="material-symbols-outlined text-secondary" style={{ fontVariationSettings: "'FILL' 1" }}>
              auto_awesome
            </span>
            <span className="font-label-sm text-label-sm text-secondary uppercase tracking-widest">
              {t("dashboard.intelligentOverview")}
            </span>
          </div>
          <h2 className="font-headline-lg text-headline-lg text-on-background leading-tight">
            {t("dashboard.greetingPrefix", { name: firstName })}{" "}
            <span className="text-primary font-bold">
              {t("dashboard.appointmentsCount", { count: appointments.length })}
            </span>
            ,{" "}
            <span className="text-primary font-bold">
              {t("dashboard.pendingApprovalsCount", {
                count: dashboard?.summary.pending_ai_approvals_count ?? 0,
              })}
            </span>{" "}
            {t("common.and")}{" "}
            <span className="text-primary font-bold">
              {t("dashboard.openTasksCount", { count: dashboard?.summary.open_tasks_count ?? 0 })}
            </span>{" "}
            {t("dashboard.greetingSuffix")}
          </h2>
          <div className="mt-xl flex gap-md">
            <button
              type="button"
              disabled={isLoading}
              onClick={loadDashboard}
              className="bg-primary text-on-primary px-lg py-sm rounded-full font-label-md flex items-center gap-2 hover:shadow-lg hover:-translate-y-0.5 transition-all disabled:opacity-60"
            >
              <span className="material-symbols-outlined text-[18px]">bolt</span>
              {isLoading ? t("dashboard.refreshing") : t("dashboard.refreshSummary")}
            </button>
            <Link
              href="/gorevler"
              className="bg-surface-container-lowest/50 border border-outline-variant text-on-surface px-lg py-sm rounded-full font-label-md hover:bg-surface-container-lowest transition-colors"
            >
              {t("dashboard.viewFullCalendar")}
            </Link>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-xl">
        <div className="flex flex-col gap-lg">
          <div className="flex items-center justify-between">
            <h3 className="font-headline-md text-headline-md flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">calendar_today</span>
              {t("dashboard.todaysAppointments")}
            </h3>
            <Link href="/gorevler" className="text-primary font-label-sm text-label-sm hover:underline">
              {t("common.viewAll")}
            </Link>
          </div>
          <div className="space-y-md">
            {isLoading && !dashboard ? (
              <>
                <Skeleton className="h-16 w-full rounded-xl" />
                <Skeleton className="h-16 w-full rounded-xl" />
              </>
            ) : appointments.length === 0 ? (
              <EmptyState icon="event_available" title={t("dashboard.noUpcomingAppointments")} />
            ) : (
              appointments.map((appt) => (
                <Link
                  key={appt.id}
                  href="/gorevler"
                  className="block p-md rounded-xl bg-surface-container-lowest border border-outline-variant/30 hover:shadow-md hover:border-primary/30 active:scale-[0.98] transition-all group"
                >
                  <div className="flex gap-md">
                    <div className="flex flex-col items-center justify-center w-14 py-2 bg-primary-container/10 rounded-lg shrink-0">
                      <span className="font-label-sm text-label-sm text-primary">
                        {formatTime(appt.start_at, language)}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-label-md text-label-md group-hover:text-primary transition-colors truncate">
                        {appt.title}
                      </p>
                      <p className="font-body-sm text-body-sm text-on-surface-variant truncate">
                        {appt.location ?? appt.description ?? t("common.noDetail")}
                      </p>
                    </div>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>

        <div className="flex flex-col gap-lg">
          <div className="flex items-center justify-between">
            <h3 className="font-headline-md text-headline-md flex items-center gap-2">
              <span className="material-symbols-outlined text-error">warning</span>
              {t("dashboard.criticalTasks")}
            </h3>
            {overdueCount > 0 ? (
              <div className="bg-error-container text-on-error-container text-[10px] px-2 py-0.5 rounded font-bold">
                {overdueCount} {t("dashboard.overdueBadge")}
              </div>
            ) : null}
          </div>
          <div className="bg-surface-container-lowest rounded-2xl border border-outline-variant/30 overflow-hidden">
            {isLoading && !dashboard ? (
              <div className="divide-y divide-outline-variant/20">
                <SkeletonRow />
                <SkeletonRow />
              </div>
            ) : criticalTasks.length === 0 ? (
              <EmptyState icon="check_circle" title={t("dashboard.noCriticalTasks")} />
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
                {t("dashboard.createNewTask")}
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
              {t("dashboard.aiSuggestions")}
            </h3>
          </div>
          <div className="space-y-md">
            {isLoading && !dashboard ? (
              <>
                <Skeleton className="h-24 w-full rounded-2xl" />
                <Skeleton className="h-24 w-full rounded-2xl" />
              </>
            ) : approvals.length === 0 ? (
              <EmptyState icon="auto_awesome" title={t("dashboard.noApprovals")} />
            ) : (
              approvals.map((approval) => (
                <div
                  key={approval.id}
                  className="bg-surface-container-lowest rounded-2xl border border-secondary/20 shadow-sm overflow-hidden relative"
                >
                  <div className="absolute left-0 top-0 w-1 h-full bg-secondary" />
                  <div className="p-md">
                    <div className="flex items-center gap-2 mb-sm">
                      <span className="material-symbols-outlined text-secondary text-[18px]">
                        {actionTypeIcon(approval.action_type)}
                      </span>
                      <span className="font-label-sm text-label-sm text-on-surface-variant capitalize">
                        {actionTypeLabel(approval.action_type, t)}
                      </span>
                    </div>
                    <p className="font-label-md text-label-md mb-sm text-on-surface">
                      {t("dashboard.generatedFrom", { source: approval.source_type })}
                    </p>
                    {approval.confidence_score !== null ? (
                      <p className="text-[11px] text-primary font-bold mb-md">
                        {t("dashboard.confidenceScore", {
                          percent: Math.round(approval.confidence_score * 100),
                        })}
                      </p>
                    ) : null}
                    <div className="flex gap-2">
                      <button
                        type="button"
                        disabled={busyId === approval.id}
                        onClick={() => handleApprove(approval.id)}
                        className="flex-1 py-1.5 bg-primary text-on-primary rounded-lg text-[12px] font-bold active:scale-95 transition-transform disabled:opacity-60"
                      >
                        {t("common.confirm")}
                      </button>
                      <button
                        type="button"
                        disabled={busyId === approval.id}
                        onClick={() => handleReject(approval.id)}
                        className="flex-1 py-1.5 bg-surface-container-lowest border border-outline-variant rounded-lg text-[12px] font-bold text-on-surface active:scale-95 transition-transform disabled:opacity-60"
                      >
                        {t("common.reject")}
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
  const { t } = useLanguage();
  return (
    <div className="p-md flex gap-md items-start hover:bg-surface-container-low transition-colors group">
      <button
        type="button"
        disabled={isBusy}
        onClick={onComplete}
        aria-label={t("dashboard.completeTaskAria")}
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
            {t("dashboard.overdueLabel")}
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
    case "whatsapp_message":
      return "chat";
    default:
      return "auto_awesome";
  }
}

function actionTypeLabel(actionType: string, t: (key: string) => string): string {
  if (actionType === "whatsapp_message") return t("dashboard.actionType.whatsapp");
  return actionType;
}
