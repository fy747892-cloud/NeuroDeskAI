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
      setError(loadError instanceof Error ? loadError.message : "Öncelik kuyruğu alınamadı.");
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
          <h2>Öncelik kuyruğu</h2>
          <button disabled={isLoading} onClick={loadQueue} type="button">
            {isLoading ? "Yükleniyor" : "Yenile"}
          </button>
        </div>
        <div className="taskCardList">
          {isLoading ? <p className="emptyState">Öncelik kuyruğu yükleniyor.</p> : null}
          {!isLoading && !queue?.items.length ? (
            <p className="emptyState">Önceliklendirilecek iş yok.</p>
          ) : null}
          {queue?.items.map((item) => {
            const cardClass = [
              "taskCard",
              item.score >= 80 ? "urgent" : item.priority === "high" ? "high" : "",
            ]
              .filter(Boolean)
              .join(" ");

            return (
              <article className={cardClass} key={`${item.item_type}-${item.item_id}`}>
                <span className={item.score >= 80 ? "scorePill hot" : "scorePill"}>{item.score}</span>
                <div className="taskCardBody">
                  <div className="taskCardHead">
                    <span className={`priorityTag ${item.priority}`}>
                      {item.item_type === "task" ? "Görev" : "Randevu"} · {item.priority}
                    </span>
                    <small>{item.due_at ? formatDateTime(item.due_at) : "Tarih yok"}</small>
                  </div>
                  <h4>{item.title}</h4>
                  {item.factors.length > 0 ? (
                    <div className="actionChips">
                      {item.factors.map((factor) => (
                        <span key={factor.key}>{factor.label}</span>
                      ))}
                    </div>
                  ) : null}
                </div>
              </article>
            );
          })}
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
