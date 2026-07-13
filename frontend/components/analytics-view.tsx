"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AIMetric,
  AnalyticsOverview,
  AuditLog,
  CallMetric,
  getAiAnalytics,
  getAnalyticsOverview,
  getCallAnalytics,
  getTaskAnalytics,
  listAuditLogs,
  runAnalyticsAggregate,
  TaskMetric,
} from "@/lib/api";
import { useSession } from "@/lib/session";

const RANGE_DAYS = 7;

export function AnalyticsView() {
  const { tokens } = useSession();
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [previousOverview, setPreviousOverview] = useState<AnalyticsOverview | null>(null);
  const [taskMetrics, setTaskMetrics] = useState<TaskMetric[]>([]);
  const [callMetrics, setCallMetrics] = useState<CallMetric[]>([]);
  const [aiMetrics, setAiMetrics] = useState<AIMetric[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [isAggregating, setAggregating] = useState(false);

  async function loadAnalytics() {
    if (!tokens?.accessToken) {
      return;
    }

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

      const [
        currentOverview,
        priorOverview,
        nextTaskMetrics,
        nextCallMetrics,
        nextAiMetrics,
        nextAuditLogs,
      ] = await Promise.all([
        getAnalyticsOverview(tokens.accessToken, {
          dateFrom: toDateKey(currentFrom),
          dateTo: toDateKey(today),
        }),
        getAnalyticsOverview(tokens.accessToken, {
          dateFrom: toDateKey(previousFrom),
          dateTo: toDateKey(previousTo),
        }),
        getTaskAnalytics(tokens.accessToken),
        getCallAnalytics(tokens.accessToken),
        getAiAnalytics(tokens.accessToken),
        listAuditLogs(tokens.accessToken, 8),
      ]);
      setOverview(currentOverview);
      setPreviousOverview(priorOverview);
      setTaskMetrics(nextTaskMetrics);
      setCallMetrics(nextCallMetrics);
      setAiMetrics(nextAiMetrics);
      setAuditLogs(nextAuditLogs);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Analitik verisi alınamadı.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAnalytics();
  }, [tokens?.accessToken]);

  async function handleAggregate() {
    if (!tokens?.accessToken) {
      return;
    }
    setAggregating(true);
    setError(null);
    try {
      await runAnalyticsAggregate(tokens.accessToken);
      await loadAnalytics();
    } catch (aggregateError) {
      setError(aggregateError instanceof Error ? aggregateError.message : "Hesaplama tetiklenemedi.");
    } finally {
      setAggregating(false);
    }
  }

  const avgLatency = useMemo(() => {
    if (aiMetrics.length === 0) return null;
    const total = aiMetrics.reduce((sum, item) => sum + item.avg_latency_ms, 0);
    return Math.round(total / aiMetrics.length);
  }, [aiMetrics]);

  return (
    <>
      {error ? <p className="notice">{error}</p> : null}

      <div className="analyticsHead">
        <div>
          <h2 style={{ margin: 0 }}>Performans İstihbaratı</h2>
          <p className="moduleLead">
            {overview ? `${overview.date_from} — ${overview.date_to}` : "Son 7 gün"} gerçek zamanlı
            operasyon ve AI verimlilik metrikleri.
          </p>
        </div>
        <button disabled={isAggregating} onClick={handleAggregate} type="button">
          {isAggregating ? "Hesaplanıyor" : "Bugünü Hesapla"}
        </button>
      </div>

      <div className="statTileRow">
        <StatTile
          icon="task_alt"
          label="Tamamlanan görev"
          value={overview?.tasks_completed ?? 0}
          delta={computeDelta(overview?.tasks_completed, previousOverview?.tasks_completed)}
        />
        <StatTile
          icon="call"
          label="Toplam görüşme"
          value={overview?.calls_total ?? 0}
          delta={computeDelta(overview?.calls_total, previousOverview?.calls_total)}
        />
        <StatTile
          icon="auto_awesome"
          label="AI istekleri"
          value={overview?.ai_requests ?? 0}
          delta={computeDelta(overview?.ai_requests, previousOverview?.ai_requests)}
        />
        <StatTile
          icon="warning"
          label="Gecikmiş görev"
          value={overview?.tasks_overdue ?? 0}
        />
      </div>

      <div className="chartsGrid">
        <div className="chartCard">
          <div className="chartCardHead">
            <h4 style={{ margin: 0 }}>Görev Trendi</h4>
            <div className="chartLegend">
              <span>
                <span className="swatch" style={{ background: "var(--chart-accent)" }} />
                Tamamlanan
              </span>
              <span>
                <span className="swatch" style={{ background: "var(--muted)" }} />
                Oluşturulan
              </span>
            </div>
          </div>
          <TrendChart metrics={taskMetrics} />
        </div>

        <div className="chartCard">
          <div className="chartCardHead">
            <h4 style={{ margin: 0 }}>Çağrı Hacmi</h4>
          </div>
          <CallBarChart metrics={callMetrics} />
        </div>
      </div>

      <div className="aiUsagePanel">
        <div className="aiUsageHero">
          <h4>AI Maliyeti</h4>
          <strong>{formatCurrency(overview?.ai_cost_amount ?? 0)}</strong>
          <span style={{ fontSize: 12, opacity: 0.85 }}>
            {overview ? `${overview.date_from} - ${overview.date_to}` : "Veri bekleniyor"}
          </span>
        </div>
        <div className="statTile">
          <p>Ortalama gecikme</p>
          <strong>{avgLatency !== null ? `${avgLatency} ms` : "--"}</strong>
        </div>
        <div className="statTile">
          <p>Analiz edilen görüşme</p>
          <strong>{overview?.calls_analyzed ?? 0}</strong>
        </div>
      </div>

      <div className="panel">
        <div className="panelHeader">
          <h2>Son Aktiviteler</h2>
          <span className="tag">Denetim Kaydı</span>
        </div>
        {isLoading ? <p className="emptyState">Yükleniyor.</p> : null}
        {!isLoading && auditLogs.length === 0 ? (
          <p className="emptyState">Henüz denetim kaydı yok.</p>
        ) : null}
        {auditLogs.length > 0 ? (
          <table className="auditTable">
            <thead>
              <tr>
                <th>Aksiyon</th>
                <th>Varlık</th>
                <th>Zaman</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.map((log) => (
                <tr key={log.id}>
                  <td>{log.action}</td>
                  <td>{log.entity_type}</td>
                  <td>{formatDateTime(log.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
      </div>
    </>
  );
}

function StatTile({
  icon,
  label,
  value,
  delta,
}: {
  icon: string;
  label: string;
  value: number;
  delta?: number | null;
}) {
  return (
    <div className="statTile">
      <div className="statTileHead">
        <div className="statTileIcon">
          <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 18 }}>
            {icon}
          </span>
        </div>
        {delta !== null && delta !== undefined ? (
          <span className={`statDelta ${delta >= 0 ? "up" : "down"}`}>
            <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 14 }}>
              {delta >= 0 ? "trending_up" : "trending_down"}
            </span>
            {delta >= 0 ? "+" : ""}
            {delta}%
          </span>
        ) : null}
      </div>
      <p>{label}</p>
      <strong>{value.toLocaleString("tr-TR")}</strong>
    </div>
  );
}

function TrendChart({ metrics }: { metrics: TaskMetric[] }) {
  if (metrics.length === 0) {
    return <p className="emptyState">Bu aralıkta veri yok. "Bugünü Hesapla" ile üretebilirsin.</p>;
  }

  const width = 500;
  const height = 160;
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
    <>
      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", height: 160 }}>
        {[0, 0.25, 0.5, 0.75, 1].map((fraction) => (
          <line
            key={fraction}
            x1={0}
            x2={width}
            y1={height * fraction}
            y2={height * fraction}
            stroke="var(--line)"
            strokeWidth={1}
          />
        ))}
        <polyline
          points={pointsFor("created_count")}
          fill="none"
          stroke="var(--muted)"
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        <polyline
          points={pointsFor("completed_count")}
          fill="none"
          stroke="var(--chart-accent)"
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        {metrics.map((item, index) => (
          <circle
            key={item.date}
            cx={index * stepX}
            cy={height - (item.completed_count / maxValue) * height}
            r={4}
            fill="var(--chart-accent)"
            stroke="var(--surface)"
            strokeWidth={2}
          >
            <title>
              {item.date}: {item.completed_count} tamamlanan / {item.created_count} oluşturulan
            </title>
          </circle>
        ))}
      </svg>
      <div className="chartAxisLabels">
        {metrics.map((item) => (
          <span key={item.date}>{formatShortDate(item.date)}</span>
        ))}
      </div>
    </>
  );
}

function CallBarChart({ metrics }: { metrics: CallMetric[] }) {
  if (metrics.length === 0) {
    return <p className="emptyState">Bu aralıkta veri yok. "Bugünü Hesapla" ile üretebilirsin.</p>;
  }

  const maxValue = Math.max(1, ...metrics.map((item) => item.call_count));

  return (
    <>
      <div className="barChart">
        {metrics.map((item) => (
          <div className="barCol" key={item.date}>
            <div
              className="bar"
              style={{ height: `${Math.max(2, (item.call_count / maxValue) * 100)}%` }}
              title={`${item.date}: ${item.call_count} çağrı, ${item.analyzed_count} analiz edildi`}
            />
          </div>
        ))}
      </div>
      <div className="chartAxisLabels">
        {metrics.map((item) => (
          <span key={item.date}>{formatShortDate(item.date)}</span>
        ))}
      </div>
    </>
  );
}

function computeDelta(current?: number, previous?: number): number | null {
  if (current === undefined || previous === undefined) {
    return null;
  }
  if (previous === 0) {
    return current === 0 ? 0 : null;
  }
  return Math.round(((current - previous) / previous) * 100);
}

function toDateKey(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function formatShortDate(value: string): string {
  return new Intl.DateTimeFormat("tr-TR", { day: "2-digit", month: "2-digit" }).format(new Date(value));
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
  }).format(new Date(value));
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("tr-TR", {
    currency: "USD",
    maximumFractionDigits: 4,
    style: "currency",
  }).format(value);
}
