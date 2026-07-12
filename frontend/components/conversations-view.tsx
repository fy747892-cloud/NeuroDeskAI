"use client";

import { useEffect, useMemo, useState } from "react";
import { Call, deleteCall, Conversation, listCalls, listConversations } from "@/lib/api";
import { useSession } from "@/lib/session";

export function ConversationsView() {
  const { tokens } = useSession();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [calls, setCalls] = useState<Call[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [activeId, setActiveId] = useState<string | null>(null);

  async function loadConversations() {
    if (!tokens?.accessToken) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const [nextConversations, nextCalls] = await Promise.all([
        listConversations(tokens.accessToken),
        listCalls(tokens.accessToken),
      ]);
      setConversations(nextConversations);
      setCalls(nextCalls);
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
      calls: calls.length,
    };
  }, [calls.length, conversations]);

  async function handleDeleteCall(callId: string) {
    if (!tokens?.accessToken) {
      return;
    }

    setActiveId(callId);
    setError(null);
    try {
      await deleteCall(tokens.accessToken, callId);
      setCalls((currentCalls) => currentCalls.filter((call) => call.id !== callId));
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Cagri silinemedi.");
    } finally {
      setActiveId(null);
    }
  }

  return (
    <section className="moduleSurface">
      {error ? <p className="notice">{error}</p> : null}

      <div className="moduleGrid">
        <SummaryCard label="Toplam" value={summary.total} />
        <SummaryCard label="Aktif" value={summary.active} />
        <SummaryCard label="Cagri" value={summary.calls} />
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

      <div className="panel">
        <div className="panelHeader">
          <h2>Cagri listesi</h2>
          <span className="tag">{calls.length}</span>
        </div>
        <div className="dataList">
          {calls.length === 0 ? <p className="emptyState">Cagri kaydi yok.</p> : null}
          {calls.map((call) => (
            <article className="dataRow" key={call.id}>
              <div>
                <div className="rowTitle">
                  <h3>{call.phone_number ?? "Metin gorusmesi"}</h3>
                  <span>{call.call_direction ?? "manual"}</span>
                </div>
                <p>{call.transcriptions[0]?.transcript_text.slice(0, 160) ?? "Transkript yok."}</p>
                <small>{call.started_at ? formatDateTime(call.started_at) : formatDateTime(call.created_at)}</small>
              </div>
              <div className="rowActions horizontal">
                <span className="statusPill">{call.status}</span>
                <button disabled={activeId === call.id} onClick={() => handleDeleteCall(call.id)} type="button">
                  Sil
                </button>
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
