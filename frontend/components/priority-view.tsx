"use client";

import { useEffect, useMemo, useState } from "react";
import { getPriorityQueue, PriorityQueue } from "@/lib/api";
import { useSession } from "@/lib/session";

export function PriorityView() {
  const { tokens } = useSession();
  const [queue, setQueue] = useState<PriorityQueue | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);

  async function loadQueue() {
    if (!tokens?.accessToken) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      setQueue(await getPriorityQueue(tokens.accessToken));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Oncelik kuyrugu alinamadi.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadQueue();
  }, [tokens?.accessToken]);

  const summary = useMemo(() => {
    const items = queue?.items ?? [];
    return {
      total: items.length,
      critical: items.filter((item) => item.score >= 80).length,
      high: items.filter((item) => item.priority === "high").length,
      generated: queue ? formatTime(queue.generated_at) : "--",
    };
  }, [queue]);

  return (
    <section className="moduleSurface">
      {error ? <p className="notice">{error}</p> : null}

      <div className="moduleGrid">
        <SummaryCard label="Toplam" value={summary.total} />
        <SummaryCard label="Kritik" value={summary.critical} />
        <SummaryCard label="Yuksek" value={summary.high} />
        <SummaryCard label="Uretim" value={summary.generated} />
      </div>

      <section className="panel">
        <div className="panelHeader">
          <h2>Oncelik kuyrugu</h2>
          <button disabled={isLoading} onClick={loadQueue} type="button">
            {isLoading ? "Yukleniyor" : "Yenile"}
          </button>
        </div>
        <div className="dataList">
          {isLoading ? <p className="emptyState">Oncelik kuyrugu yukleniyor.</p> : null}
          {!isLoading && !queue?.items.length ? (
            <p className="emptyState">Onceliklendirilecek is yok.</p>
          ) : null}
          {queue?.items.map((item) => (
            <article className="dataRow" key={`${item.item_type}-${item.item_id}`}>
              <div>
                <div className="rowTitle">
                  <h3>{item.title}</h3>
                  <span>{item.item_type}</span>
                </div>
                <p>{item.factors.map((factor) => factor.label).join(" | ") || "Faktor yok."}</p>
                <small>{item.due_at ? formatDateTime(item.due_at) : "Tarih yok"}</small>
              </div>
              <div className="rowActions">
                <span className={item.score >= 80 ? "scorePill hot" : "scorePill"}>{item.score}</span>
                <span className="statusPill">{item.priority}</span>
              </div>
            </article>
          ))}
        </div>
      </section>
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

function formatTime(value: string): string {
  return new Intl.DateTimeFormat("tr-TR", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
  }).format(new Date(value));
}
