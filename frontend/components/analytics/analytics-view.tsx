"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AIActionApproval,
  AIMetric,
  AnalyticsOverview,
  AuditLog,
  CallMetric,
  getAiAnalytics,
  getAnalyticsOverview,
  getCallAnalytics,
  getTaskAnalytics,
  listApprovals,
  listAuditLogs,
  runAnalyticsAggregate,
  TaskMetric,
} from "@/lib/api";
import { useSession } from "@/lib/session";
import { Language, useLanguage } from "@/lib/i18n/context";
import { formatDateTime, formatMoney } from "@/lib/format";
import { EmptyState } from "@/components/shell/empty-state";

const RANGE_DAYS = 7;

export function AnalyticsView() {
  const { tokens } = useSession();
  const { t, language } = useLanguage();
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [previousOverview, setPreviousOverview] = useState<AnalyticsOverview | null>(null);
  const [taskMetrics, setTaskMetrics] = useState<TaskMetric[]>([]);
  const [callMetrics, setCallMetrics] = useState<CallMetric[]>([]);
  const [aiMetrics, setAiMetrics] = useState<AIMetric[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [approvals, setApprovals] = useState<AIActionApproval[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [isAggregating, setAggregating] = useState(false);

  const loadAnalytics = useCallback(async () => {
    if (!tokens?.accessToken) return;
    setLoading(true);
    setError(null);
    try {
      const today = new Date();
      const currentFrom = new Date(today);
      currentFrom.setDate(today.getDate() - (RANGE_DAYS - 1));
      const previousTo = new Date(currentFrom);
      previousTo.setDate(currentFrom.getDate() - 1);
      const previousFrom = new Date(previousTo);
      previousFrom.setDate(previousTo.getDate() - (RANGE_DAYS - 1));

      const [current, prior, nextTaskMetrics, nextCallMetrics, nextAiMetrics, nextAuditLogs, nextApprovals] =
        await Promise.all([
          getAnalyticsOverview(tokens.accessToken, { dateFrom: toDateKey(currentFrom), dateTo: toDateKey(today) }),
          getAnalyticsOverview(tokens.accessToken, {
            dateFrom: toDateKey(previousFrom),
            dateTo: toDateKey(previousTo),
          }),
          getTaskAnalytics(tokens.accessToken),
          getCallAnalytics(tokens.accessToken),
          getAiAnalytics(tokens.accessToken),
          listAuditLogs(tokens.accessToken, 8),
          listApprovals(tokens.accessToken),
        ]);
      setOverview(current);
      setPreviousOverview(prior);
      setTaskMetrics(nextTaskMetrics);
      setCallMetrics(nextCallMetrics);
      setAiMetrics(nextAiMetrics);
      setAuditLogs(nextAuditLogs);
      setApprovals(nextApprovals);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : t("analytics.errors.loadFailed"));
    } finally {
      setLoading(false);
    }
  }, [tokens?.accessToken]);

  useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  async function handleAggregate() {
    if (!tokens?.accessToken) return;
    setAggregating(true);
    setError(null);
    try {
      await runAnalyticsAggregate(tokens.accessToken);
      await loadAnalytics();
    } catch (aggregateError) {
      setError(aggregateError instanceof Error ? aggregateError.message : t("analytics.errors.aggregateFailed"));
    } finally {
      setAggregating(false);
    }
  }

  const avgLatency = useMemo(() => {
    if (aiMetrics.length === 0) return null;
    const total = aiMetrics.reduce((sum, item) => sum + item.avg_latency_ms, 0);
    return Math.round(total / aiMetrics.length);
  }, [aiMetrics]);

  const acceptance = useMemo(() => {
    const decided = approvals.filter((a) => a.status === "approved" || a.status === "rejected");
    const approvedCount = decided.filter((a) => a.status === "approved").length;
    return decided.length > 0 ? Math.round((approvedCount / decided.length) * 100) : null;
  }, [approvals]);

  const callDelta = computeDelta(overview?.calls_total, previousOverview?.calls_total);
  const taskDelta = computeDelta(overview?.tasks_completed, previousOverview?.tasks_completed);

  return (
    <div className="px-xl py-lg space-y-lg max-w-7xl mx-auto w-full">
      {error ? <p className="text-error text-body-sm">{error}</p> : null}

      <div className="flex justify-between items-end flex-wrap gap-md">
        <div>
          <h2 className="font-headline-lg text-headline-lg text-on-surface tracking-tight">
            {t("analytics.title")}
          </h2>
          <p className="text-on-surface-variant font-body-md mt-1">
            {t("analytics.subtitle", {
              range: overview ? `${overview.date_from} — ${overview.date_to}` : t("analytics.defaultRange"),
            })}
          </p>
        </div>
        <button
          type="button"
          disabled={isAggregating}
          onClick={handleAggregate}
          className="px-4 py-2 bg-primary text-on-primary rounded-lg text-label-sm flex items-center gap-2 shadow-sm active:scale-95 transition-transform disabled:opacity-60"
        >
          <span className="material-symbols-outlined text-[18px]">bolt</span>
          {isAggregating ? t("analytics.aggregating") : t("analytics.aggregateButton")}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-lg">
        <div className="glass-card p-xl rounded-xl relative overflow-hidden">
          <div className="flex justify-between items-start mb-base">
            <span className="material-symbols-outlined text-primary bg-primary-container/10 p-2 rounded-lg">call</span>
            {callDelta !== null ? <DeltaBadge value={callDelta} /> : null}
          </div>
          <p className="text-on-surface-variant font-label-md text-label-md">{t("analytics.weeklyCallVolume")}</p>
          <h3 className="text-headline-lg font-bold mt-2">
            {(overview?.calls_total ?? 0).toLocaleString(localeFor(language))}
          </h3>
          <div className="mt-4 h-12 flex items-end gap-1">
            {sparklineBars(callMetrics.map((m) => m.call_count), t)}
          </div>
        </div>

        <div className="glass-card p-xl rounded-xl">
          <div className="flex justify-between items-start mb-base">
            <span className="material-symbols-outlined text-secondary bg-secondary-fixed p-2 rounded-lg">task_alt</span>
            {taskDelta !== null ? <DeltaBadge value={taskDelta} /> : null}
          </div>
          <p className="text-on-surface-variant font-label-md text-label-md">{t("analytics.tasksCompleted")}</p>
          <h3 className="text-headline-lg font-bold mt-2">
            {(overview?.tasks_completed ?? 0).toLocaleString(localeFor(language))}
          </h3>
          <p className="text-[11px] text-outline mt-4">
            {t("analytics.overdueTasks", { count: overview?.tasks_overdue ?? 0 })}
          </p>
        </div>

        <div className="glass-card p-xl rounded-xl border-primary/20 ai-glow bg-gradient-to-br from-white to-primary/5">
          <div className="flex justify-between items-start mb-base">
            <span className="material-symbols-outlined text-primary bg-primary-fixed p-2 rounded-lg" style={{ fontVariationSettings: "'FILL' 1" }}>
              auto_awesome
            </span>
            <span className="text-body-sm font-semibold text-primary-fixed-variant bg-primary-fixed rounded px-2 py-0.5 animate-pulse-subtle">
              {t("analytics.live")}
            </span>
          </div>
          <p className="text-on-surface-variant font-label-md text-label-md">{t("analytics.aiSuggestionsApproved")}</p>
          <h3 className="text-headline-lg font-bold mt-2 text-primary">
            {acceptance !== null ? `${acceptance}%` : "--"}
          </h3>
          <p className="text-[11px] text-outline mt-4">
            {t("analytics.totalSuggestions", { count: approvals.length })}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-lg">
        <div className="glass-card p-xl rounded-xl flex flex-col h-[380px]">
          <div className="flex justify-between items-center mb-xl">
            <h4 className="font-headline-md text-headline-md">{t("analytics.productivityTrends")}</h4>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-primary" />
                <span className="text-body-sm text-outline">{t("analytics.completedLegend")}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-outline-variant" />
                <span className="text-body-sm text-outline">{t("analytics.createdLegend")}</span>
              </div>
            </div>
          </div>
          <TrendChart metrics={taskMetrics} t={t} language={language} />
        </div>

        <div className="glass-card p-xl rounded-xl flex flex-col h-[380px]">
          <div className="flex justify-between items-center mb-xl">
            <h4 className="font-headline-md text-headline-md">{t("analytics.callVolume")}</h4>
          </div>
          <CallBarChart metrics={callMetrics} t={t} language={language} />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-lg">
        <div className="md:col-span-3 glass-card p-xl rounded-xl">
          <div className="flex justify-between items-center mb-md flex-wrap gap-2">
            <div>
              <h4 className="font-headline-md text-headline-md">{t("analytics.aiComputeUsage")}</h4>
              <p className="text-body-sm text-outline">{t("analytics.estimatedCostSubtitle")}</p>
            </div>
            <div className="text-right">
              <span className="text-headline-md font-bold text-primary">
                {formatMoney(overview?.ai_cost_amount ?? 0, "USD", language)}
              </span>
              <p className="text-[10px] text-outline uppercase font-bold">{t("analytics.estimatedTotal")}</p>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-surface-container-low p-3 rounded-lg border border-outline-variant/20">
              <p className="text-[10px] text-outline uppercase font-bold">{t("analytics.aiRequests")}</p>
              <p className="text-body-md font-bold">
                {(overview?.ai_requests ?? 0).toLocaleString(localeFor(language))}
              </p>
            </div>
            <div className="bg-surface-container-low p-3 rounded-lg border border-outline-variant/20">
              <p className="text-[10px] text-outline uppercase font-bold">{t("analytics.avgLatency")}</p>
              <p className="text-body-md font-bold">{avgLatency !== null ? `${avgLatency} ms` : "--"}</p>
            </div>
            <div className="bg-surface-container-low p-3 rounded-lg border border-outline-variant/20">
              <p className="text-[10px] text-outline uppercase font-bold">{t("analytics.analyzedConversations")}</p>
              <p className="text-body-md font-bold">{overview?.calls_analyzed ?? 0}</p>
            </div>
          </div>
        </div>
        <div className="glass-card p-xl rounded-xl bg-inverse-surface text-inverse-on-surface flex flex-col justify-between overflow-hidden relative">
          <div className="relative z-10">
            <span className="material-symbols-outlined text-primary-fixed-dim mb-md">workspace_premium</span>
            <h4 className="font-headline-md text-headline-md mb-2">{t("analytics.upgradeTitle")}</h4>
            <p className="text-body-sm text-outline-variant">{t("analytics.upgradeSubtitle")}</p>
          </div>
          <a
            href="/ayarlar"
            className="w-full py-3 bg-primary text-on-primary rounded-lg font-label-md mt-lg hover:brightness-110 active:scale-95 transition-all relative z-10 text-center"
          >
            {t("analytics.viewPlans")}
          </a>
        </div>
      </div>

      <div className="glass-card rounded-xl overflow-hidden">
        <div className="px-xl py-md border-b border-outline-variant/30 flex justify-between items-center">
          <h4 className="font-headline-md text-headline-md">{t("analytics.auditLogs")}</h4>
        </div>
        {isLoading ? <p className="p-xl text-body-sm text-on-surface-variant">{t("common.loading")}</p> : null}
        {!isLoading && auditLogs.length === 0 ? (
          <EmptyState icon="history" title={t("analytics.noAuditLogs")} />
        ) : null}
        {auditLogs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-surface-container text-outline font-label-sm uppercase tracking-wider">
                  <th className="px-xl py-4">{t("analytics.table.action")}</th>
                  <th className="px-xl py-4">{t("analytics.table.entity")}</th>
                  <th className="px-xl py-4 text-right">{t("analytics.table.time")}</th>
                </tr>
              </thead>
              <tbody className="text-body-sm text-on-surface">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-surface-container-low transition-colors border-b border-outline-variant/10">
                    <td className="px-xl py-4">{log.action}</td>
                    <td className="px-xl py-4">{log.entity_type}</td>
                    <td className="px-xl py-4 text-right text-outline">
                      {formatDateTime(log.created_at, language)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function localeFor(language: Language): string {
  return language === "tr" ? "tr-TR" : "en-US";
}

function DeltaBadge({ value }: { value: number }) {
  return (
    <span className={"text-body-sm font-semibold flex items-center " + (value >= 0 ? "text-success" : "text-error")}>
      <span className="material-symbols-outlined text-[16px]">{value >= 0 ? "trending_up" : "trending_down"}</span>
      {value >= 0 ? "+" : ""}
      {value}%
    </span>
  );
}

function sparklineBars(values: number[], t: (path: string) => string) {
  if (values.length === 0) {
    return <p className="text-[11px] text-on-surface-variant">{t("analytics.noData")}</p>;
  }
  const max = Math.max(1, ...values);
  return values.map((value, index) => (
    <div
      key={index}
      className="flex-1 bg-primary/20 rounded-t-sm"
      style={{ height: `${Math.max(8, (value / max) * 100)}%` }}
    />
  ));
}

function TrendChart({
  metrics,
  t,
  language,
}: {
  metrics: TaskMetric[];
  t: (path: string, vars?: Record<string, string | number>) => string;
  language: Language;
}) {
  if (metrics.length === 0) {
    return (
      <p className="flex-1 flex items-center justify-center text-body-sm text-on-surface-variant">
        {t("analytics.noDataInRange")}
      </p>
    );
  }

  const width = 500;
  const height = 200;
  const maxValue = Math.max(1, ...metrics.map((item) => Math.max(item.created_count, item.completed_count)));
  const stepX = metrics.length > 1 ? width / (metrics.length - 1) : 0;

  function pointsFor(key: "created_count" | "completed_count") {
    return metrics
      .map((item, index) => {
        const x = index * stepX;
        const y = height - (item[key] / maxValue) * height;
        return `${x},${y}`;
      })
      .join(" ");
  }

  return (
    <div className="flex-1 relative">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full overflow-visible">
        {[0, 0.25, 0.5, 0.75, 1].map((fraction) => (
          <line
            key={fraction}
            x1={0}
            x2={width}
            y1={height * fraction}
            y2={height * fraction}
            style={{ stroke: "rgb(var(--color-outline-variant) / 0.4)" }}
            strokeDasharray="4"
            strokeWidth={1}
          />
        ))}
        <polyline
          points={pointsFor("created_count")}
          fill="none"
          style={{ stroke: "rgb(var(--color-outline-variant))" }}
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        <polyline
          points={pointsFor("completed_count")}
          fill="none"
          style={{ stroke: "rgb(var(--color-primary))" }}
          strokeWidth={3}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        {metrics.map((item, index) => (
          <circle
            key={item.date}
            cx={index * stepX}
            cy={height - (item.completed_count / maxValue) * height}
            r={4}
            style={{ fill: "rgb(var(--color-primary))", stroke: "rgb(var(--color-surface))" }}
            strokeWidth={2}
          >
            <title>
              {t("analytics.chartTooltip", {
                date: item.date,
                completed: item.completed_count,
                created: item.created_count,
              })}
            </title>
          </circle>
        ))}
      </svg>
      <div className="flex justify-between mt-4 text-[10px] text-outline uppercase tracking-widest font-bold">
        {metrics.map((item) => (
          <span key={item.date}>{formatShortDate(item.date, language)}</span>
        ))}
      </div>
    </div>
  );
}

function CallBarChart({
  metrics,
  t,
  language,
}: {
  metrics: CallMetric[];
  t: (path: string, vars?: Record<string, string | number>) => string;
  language: Language;
}) {
  if (metrics.length === 0) {
    return (
      <p className="flex-1 flex items-center justify-center text-body-sm text-on-surface-variant">
        {t("analytics.noDataInRange")}
      </p>
    );
  }

  const maxValue = Math.max(1, ...metrics.map((item) => item.call_count));

  return (
    <div className="flex-1 flex flex-col">
      <div className="flex-1 flex items-end justify-between gap-3 px-2">
        {metrics.map((item) => (
          <div key={item.date} className="flex flex-col items-center gap-2 w-full group">
            <div className="w-full bg-surface-container-high rounded-t-lg relative flex flex-col justify-end overflow-hidden h-full">
              <div
                className="w-full bg-primary group-hover:brightness-110 transition-all duration-300"
                style={{ height: `${Math.max(4, (item.call_count / maxValue) * 100)}%` }}
                title={t("analytics.callChartTooltip", {
                  date: item.date,
                  count: item.call_count,
                  analyzed: item.analyzed_count,
                })}
              />
            </div>
          </div>
        ))}
      </div>
      <div className="flex justify-between mt-2 text-[10px] text-outline uppercase tracking-widest font-bold">
        {metrics.map((item) => (
          <span key={item.date}>{formatShortDate(item.date, language)}</span>
        ))}
      </div>
    </div>
  );
}

function computeDelta(current?: number, previous?: number): number | null {
  if (current === undefined || previous === undefined) return null;
  if (previous === 0) return current === 0 ? 0 : null;
  return Math.round(((current - previous) / previous) * 100);
}

function toDateKey(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function formatShortDate(value: string, language: Language): string {
  return new Intl.DateTimeFormat(localeFor(language), { day: "2-digit", month: "2-digit" }).format(new Date(value));
}
