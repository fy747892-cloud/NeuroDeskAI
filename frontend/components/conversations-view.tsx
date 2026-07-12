"use client";

import { useEffect, useMemo, useState } from "react";
import { Conversation, listConversations } from "@/lib/api";
import { useSession } from "@/lib/session";

export function ConversationsView() {
  const { tokens } = useSession();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);

  async function loadConversations() {
    if (!tokens?.accessToken) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      setConversations(await listConversations(tokens.accessToken));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Gorusmeler alinamadi.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadConversations();
  }, [tokens?.accessToken]);

  const summary = useMemo(() => {
    return {
      total: conversations.length,
      manual: conversations.filter((conversation) => conversation.source_type === "manual").length,
      active: conversations.filter((conversation) => conversation.status !== "closed").length,
      closed: conversations.filter((conversation) => conversation.status === "closed").length,
    };
  }, [conversations]);

  return (
    <section className="moduleSurface">
      {error ? <p className="notice">{error}</p> : null}

      <div className="moduleGrid">
        <SummaryCard label="Toplam" value={summary.total} />
        <SummaryCard label="Aktif" value={summary.active} />
        <SummaryCard label="Manuel" value={summary.manual} />
        <SummaryCard label="Kapali" value={summary.closed} />
      </div>

      <div className="panel">
        <div className="panelHeader">
          <h2>Gorusme listesi</h2>
          <button disabled={isLoading} onClick={loadConversations} type="button">
            {isLoading ? "Yukleniyor" : "Yenile"}
          </button>
        </div>

        <div className="dataList">
          {isLoading ? <p className="emptyState">Gorusmeler yukleniyor.</p> : null}
          {!isLoading && conversations.length === 0 ? (
            <p className="emptyState">Henuz gorusme kaydi yok.</p>
          ) : null}
          {conversations.map((conversation) => (
            <article className="dataRow" key={conversation.id}>
              <div>
                <div className="rowTitle">
                  <h3>{conversation.title}</h3>
                  <span>{conversation.source_type}</span>
                </div>
                <p>AI analiz ve transkript detaylari sonraki derin ekranlarda baglanacak.</p>
                <small>{formatDateTime(conversation.created_at)}</small>
              </div>
              <div className="rowActions">
                <span className="statusPill">{conversation.status}</span>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function SummaryCard({ label, value }: { label: string; value: number }) {
  return (
    <article className="moduleCard compact">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
  }).format(new Date(value));
}
