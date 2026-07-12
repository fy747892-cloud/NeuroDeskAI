"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  Call,
  createCallFromText,
  deleteCall,
  Conversation,
  listCalls,
  listConversations,
} from "@/lib/api";
import { useSession } from "@/lib/session";

export function ConversationsView() {
  const { tokens } = useSession();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [calls, setCalls] = useState<Call[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [isCreating, setCreating] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [newCall, setNewCall] = useState({
    participants: "",
    phone: "",
    title: "",
    transcript: "",
  });

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
      setError(loadError instanceof Error ? loadError.message : "Görüşmeler alınamadı.");
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
      setError(deleteError instanceof Error ? deleteError.message : "Çağrı silinemedi.");
    } finally {
      setActiveId(null);
    }
  }

  async function handleCreateCall(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !newCall.title.trim() || !newCall.transcript.trim()) {
      return;
    }

    setCreating(true);
    setError(null);
    setNotice(null);
    try {
      const result = await createCallFromText(tokens.accessToken, {
        title: newCall.title.trim(),
        transcript_text: newCall.transcript.trim(),
        phone_number: newCall.phone.trim() || null,
        participant_names: newCall.participants
          .split(",")
          .map((participant) => participant.trim())
          .filter(Boolean),
      });
      setConversations((currentConversations) => [result.conversation, ...currentConversations]);
      setCalls((currentCalls) => [result.call, ...currentCalls]);
      setNewCall({ participants: "", phone: "", title: "", transcript: "" });
      setNotice("Metin görüşmesi oluşturuldu.");
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Görüşme oluşturulamadı.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <section className="moduleSurface">
      {error ? <p className="notice">{error}</p> : null}
      {notice ? <p className="notice success">{notice}</p> : null}

      <div className="moduleGrid">
        <SummaryCard label="Toplam" value={summary.total} />
        <SummaryCard label="Aktif" value={summary.active} />
        <SummaryCard label="Çağrı" value={summary.calls} />
        <SummaryCard label="Kapali" value={summary.closed} />
      </div>

      <div className="panel">
        <div className="panelHeader">
          <h2>Yeni metin görüşmesi</h2>
          <span className="tag">Call text</span>
        </div>
        <form className="createForm createFormWide" onSubmit={handleCreateCall}>
          <label>
            Başlık
            <input
              onChange={(event) => setNewCall((call) => ({ ...call, title: event.target.value }))}
              placeholder="Hasta görüşmesi"
              value={newCall.title}
            />
          </label>
          <label>
            Katilimcilar
            <input
              onChange={(event) =>
                setNewCall((call) => ({ ...call, participants: event.target.value }))
              }
              placeholder="Ayse, Mehmet"
              value={newCall.participants}
            />
          </label>
          <label>
            Telefon
            <input
              onChange={(event) => setNewCall((call) => ({ ...call, phone: event.target.value }))}
              placeholder="+90..."
              value={newCall.phone}
            />
          </label>
          <label className="wideField">
            Transkript
            <textarea
              onChange={(event) =>
                setNewCall((call) => ({ ...call, transcript: event.target.value }))
              }
              placeholder="Görüşme metnini buraya yapıştır"
              rows={4}
              value={newCall.transcript}
            />
          </label>
          <button disabled={isCreating || !newCall.title.trim() || !newCall.transcript.trim()} type="submit">
            {isCreating ? "Oluşturuluyor" : "Oluştur"}
          </button>
        </form>
      </div>

      <div className="panel">
        <div className="panelHeader">
          <h2>Görüşme listesi</h2>
          <button disabled={isLoading} onClick={loadConversations} type="button">
            {isLoading ? "Yükleniyor" : "Yenile"}
          </button>
        </div>

        <div className="dataList">
          {isLoading ? <p className="emptyState">Görüşmeler yükleniyor.</p> : null}
          {!isLoading && conversations.length === 0 ? (
            <p className="emptyState">Henüz görüşme kaydı yok.</p>
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
          <h2>Çağrı listesi</h2>
          <span className="tag">{calls.length}</span>
        </div>
        <div className="dataList">
          {calls.length === 0 ? <p className="emptyState">Çağrı kaydı yok.</p> : null}
          {calls.map((call) => (
            <article className="dataRow" key={call.id}>
              <div>
                <div className="rowTitle">
                  <h3>{call.phone_number ?? "Metin görüşmesi"}</h3>
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
