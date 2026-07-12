"use client";

import { useEffect, useMemo, useState } from "react";
import { AnalyticsOverview, getAnalyticsOverview } from "@/lib/api";
import { useSession } from "@/lib/session";

export function AnalyticsView() {
  const { tokens } = useSession();
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);

  async function loadAnalytics() {
    if (!tokens?.accessToken) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      setOverview(await getAnalyticsOverview(tokens.accessToken));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Analitik verisi alınamadı.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAnalytics();
  }, [tokens?.accessToken]);

  const completionRate = useMemo(() => {
    if (!overview || overview.tasks_created === 0) {
      return 0;
    }
    return Math.round((overview.tasks_completed / overview.tasks_created) * 100);
  }, [overview]);

  return (
    <section className="moduleSurface">
      {error ? <p className="notice">{error}</p> : null}

      <div className="moduleGrid">
        <SummaryCard label="Oluşturulan görev" value={overview?.tasks_created ?? 0} />
        <SummaryCard label="Tamamlanan görev" value={overview?.tasks_completed ?? 0} />
        <SummaryCard label="AI istekleri" value={overview?.ai_requests ?? 0} />
        <SummaryCard label="Tamamlama" value={`${completionRate}%`} />
      </div>

      <div className="contentGrid">
        <section className="panel">
          <div className="panelHeader">
            <h2>Operasyon ozeti</h2>
            <button disabled={isLoading} onClick={loadAnalytics} type="button">
              {isLoading ? "Yükleniyor" : "Yenile"}
            </button>
          </div>
          <div className="metricList">
            <MetricLine label="Gecikmiş görev" value={overview?.tasks_overdue ?? 0} />
            <MetricLine label="Toplam görüşme" value={overview?.calls_total ?? 0} />
            <MetricLine label="Analiz edilen görüşme" value={overview?.calls_analyzed ?? 0} />
            <MetricLine label="Tamamlanan randevu" value={overview?.appointments_completed ?? 0} />
            <MetricLine label="Yaklasan randevu" value={overview?.appointments_upcoming ?? 0} />
          </div>
        </section>

        <section className="panel">
          <div className="panelHeader">
            <h2>AI maliyeti</h2>
            <span className="tag">7 gun</span>
          </div>
          <div className="costBlock">
            <strong>{formatCurrency(overview?.ai_cost_amount ?? 0)}</strong>
            <span>{overview ? `${overview.date_from} - ${overview.date_to}` : "Veri bekleniyor"}</span>
          </div>
        </section>
      </div>
    </section>
  );
}

function SummaryCard({ label, value }: { label: string; value: number | string }) {
  return (
    <article className="moduleCard compact">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function MetricLine({ label, value }: { label: string; value: number }) {
  return (
    <div className="metricLine">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("tr-TR", {
    currency: "USD",
    maximumFractionDigits: 4,
    style: "currency",
  }).format(value);
}
