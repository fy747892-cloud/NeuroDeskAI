"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  AIAnalysisJob,
  Call,
  ConversationDetail,
  createCallFromText,
  Conversation,
  deleteCall,
  getConversation,
  listAnalysisJobs,
  listConversations,
  requestConversationAnalysis,
} from "@/lib/api";
import { useSession } from "@/lib/session";

const EXTRACT_ICON: Record<string, string> = {
  task_extraction: "task_alt",
  appointment_extraction: "calendar_month",
  deal_extraction: "handshake",
};

export function ConversationsView() {
  const { tokens } = useSession();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [analysisJobs, setAnalysisJobs] = useState<AIAnalysisJob[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ConversationDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [isDetailLoading, setDetailLoading] = useState(false);
  const [isCreating, setCreating] = useState(false);
  const [isAnalyzing, setAnalyzing] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [activeCallId, setActiveCallId] = useState<string | null>(null);
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
      const [nextConversations, nextJobs] = await Promise.all([
        listConversations(tokens.accessToken),
        listAnalysisJobs(tokens.accessToken),
      ]);
      setConversations(nextConversations);
      setAnalysisJobs(nextJobs);
      if (nextConversations.length > 0 && !selectedId) {
        setSelectedId(nextConversations[0].id);
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Görüşmeler alınamadı.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadConversations();
  }, [tokens?.accessToken]);

  useEffect(() => {
    async function loadDetail() {
      if (!tokens?.accessToken || !selectedId) {
        setDetail(null);
        return;
      }
      setDetailLoading(true);
      try {
        setDetail(await getConversation(tokens.accessToken, selectedId));
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Görüşme detayı alınamadı.");
      } finally {
        setDetailLoading(false);
      }
    }
    loadDetail();
  }, [tokens?.accessToken, selectedId]);

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
      setConversations((current) => [result.conversation, ...current]);
      setSelectedId(result.conversation.id);
      setNewCall({ participants: "", phone: "", title: "", transcript: "" });
      setNotice("Metin görüşmesi oluşturuldu.");
      setShowCreateForm(false);
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Görüşme oluşturulamadı.");
    } finally {
      setCreating(false);
    }
  }

  async function handleDeleteCall(callId: string) {
    if (!tokens?.accessToken) {
      return;
    }

    setActiveCallId(callId);
    setError(null);
    try {
      await deleteCall(tokens.accessToken, callId);
      setDetail((current) =>
        current ? { ...current, calls: current.calls.filter((call) => call.id !== callId) } : current,
      );
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Çağrı silinemedi.");
    } finally {
      setActiveCallId(null);
    }
  }

  async function handleAnalyze() {
    if (!tokens?.accessToken || !selectedId) {
      return;
    }

    setAnalyzing(true);
    setError(null);
    try {
      const job = await requestConversationAnalysis(tokens.accessToken, selectedId);
      setAnalysisJobs((current) => [job, ...current.filter((item) => item.id !== job.id)]);
    } catch (analyzeError) {
      setError(analyzeError instanceof Error ? analyzeError.message : "AI analizi başlatılamadı.");
    } finally {
      setAnalyzing(false);
    }
  }

  const job = findLatestCompletedJob(analysisJobs, selectedId);
  const summaryText = job ? extractText(job, "conversation_summary", "summary_text") : null;
  const extractedItems = job ? extractItems(job) : [];

  return (
    <>
      {error ? <p className="notice">{error}</p> : null}
      {notice ? <p className="notice success">{notice}</p> : null}

      <div className="panelHeader" style={{ marginBottom: 14 }}>
        <h2>Görüşmeler</h2>
        <button onClick={() => setShowCreateForm((value) => !value)} type="button">
          {showCreateForm ? "Formu kapat" : "+ Yeni metin görüşmesi"}
        </button>
      </div>

      {showCreateForm ? (
        <div className="panel" style={{ marginBottom: 20 }}>
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
                placeholder={"Alex: Merhaba...\nJordan: Selam..."}
                rows={4}
                value={newCall.transcript}
              />
            </label>
            <button disabled={isCreating || !newCall.title.trim() || !newCall.transcript.trim()} type="submit">
              {isCreating ? "Oluşturuluyor" : "Oluştur"}
            </button>
          </form>
        </div>
      ) : null}

      <div className="convoLayout">
        <div className="convoRail">
          {isLoading ? <p className="emptyState">Görüşmeler yükleniyor.</p> : null}
          {!isLoading && conversations.length === 0 ? (
            <p className="emptyState">Henüz görüşme kaydı yok.</p>
          ) : null}
          {conversations.map((conversation) => (
            <button
              className={conversation.id === selectedId ? "convoItem active" : "convoItem"}
              key={conversation.id}
              onClick={() => setSelectedId(conversation.id)}
              type="button"
            >
              <div className="convoItemHead">
                <strong>{conversation.title}</strong>
                <span>{formatTime(conversation.created_at)}</span>
              </div>
              <p>
                {conversation.source_type} · {conversation.status}
              </p>
            </button>
          ))}
        </div>

        <div className="convoDetail">
          {isDetailLoading ? <p className="emptyState">Görüşme detayı yükleniyor.</p> : null}
          {!isDetailLoading && !detail ? (
            <p className="emptyState">Detayları görmek için soldan bir görüşme seç.</p>
          ) : null}
          {!isDetailLoading && detail ? (
            <>
              <div className="convoHeader">
                <div>
                  <h2>{detail.title}</h2>
                  <div className="convoMetaRow">
                    <span>
                      <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 16 }}>
                        calendar_today
                      </span>
                      {formatDateTime(detail.created_at)}
                    </span>
                    {detail.participants.length > 0 ? (
                      <span>
                        <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 16 }}>
                          person
                        </span>
                        {detail.participants.map((participant) => participant.display_name).join(", ")}
                      </span>
                    ) : null}
                    <span className="statusPill">{detail.status}</span>
                  </div>
                </div>
                <button disabled={isAnalyzing} onClick={handleAnalyze} type="button">
                  <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 18 }}>
                    auto_awesome
                  </span>{" "}
                  {isAnalyzing ? "Analiz ediliyor" : "AI ile Analiz Et"}
                </button>
              </div>

              {summaryText ? (
                <div className="aiSummaryBox">
                  <div className="summaryTag">
                    <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 16 }}>
                      smart_toy
                    </span>
                    AI Insight Summary
                  </div>
                  <p>{summaryText}</p>
                </div>
              ) : (
                <p className="emptyState">
                  Bu görüşme için henüz AI analizi yapılmadı. "AI ile Analiz Et" butonuna tıkla.
                </p>
              )}

              {extractedItems.length > 0 ? (
                <>
                  <p className="extractLabel">Çıkarılan Aksiyon Öğeleri</p>
                  <div className="extractChips">
                    {extractedItems.map((item, index) => (
                      <span className="extractChip" key={`${item.type}-${index}`}>
                        <span className="material-symbols-outlined" aria-hidden="true">
                          {EXTRACT_ICON[item.type] ?? "auto_awesome"}
                        </span>
                        {item.title}
                      </span>
                    ))}
                  </div>
                </>
              ) : null}

              <p className="extractLabel">Çağrılar &amp; Transkript</p>
              {detail.calls.length === 0 ? <p className="emptyState">Bu görüşmede çağrı yok.</p> : null}
              {detail.calls.map((call) => (
                <CallBlock
                  key={call.id}
                  call={call}
                  isBusy={activeCallId === call.id}
                  onDelete={() => handleDeleteCall(call.id)}
                />
              ))}
            </>
          ) : null}
        </div>
      </div>
    </>
  );
}

function CallBlock({
  call,
  isBusy,
  onDelete,
}: {
  call: Call;
  isBusy: boolean;
  onDelete: () => void;
}) {
  const transcriptText = call.transcriptions[0]?.transcript_text ?? null;
  const turns = transcriptText ? parseTranscript(transcriptText) : [];

  return (
    <div style={{ marginBottom: 16 }}>
      <div className="rowActions horizontal" style={{ justifyContent: "space-between", marginBottom: 8 }}>
        <span className="statusPill">
          {call.phone_number ?? "Metin görüşmesi"} · {call.status}
        </span>
        <button disabled={isBusy} onClick={onDelete} type="button">
          {isBusy ? "Siliniyor" : "Çağrıyı Sil"}
        </button>
      </div>
      {turns.length > 0 ? (
        <div className="transcriptList">
          {turns.map((turn, index) => (
            <div className="transcriptTurn" key={index}>
              <div className="transcriptTime">{String(index).padStart(2, "0")}:00</div>
              <div className="transcriptBody">
                {turn.speaker ? <span className="transcriptSpeaker">{turn.speaker}</span> : null}
                <p>{turn.text}</p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="emptyState">Transkript yok.</p>
      )}
    </div>
  );
}

function parseTranscript(text: string): { speaker: string | null; text: string }[] {
  const lines = text.split("\n").map((line) => line.trim()).filter(Boolean);
  const speakerLine = /^([^:]{1,40}):\s*(.+)$/;
  const matches = lines.filter((line) => speakerLine.test(line));

  if (matches.length >= Math.max(1, lines.length - 1)) {
    return lines.map((line) => {
      const match = line.match(speakerLine);
      if (match) {
        return { speaker: match[1], text: match[2] };
      }
      return { speaker: null, text: line };
    });
  }

  return [{ speaker: null, text }];
}

function findLatestCompletedJob(jobs: AIAnalysisJob[], conversationId: string | null): AIAnalysisJob | null {
  if (!conversationId) {
    return null;
  }
  const matches = jobs.filter(
    (candidate) =>
      candidate.source_type === "conversation" &&
      candidate.source_id === conversationId &&
      candidate.status === "completed",
  );
  if (matches.length === 0) {
    return null;
  }
  return matches.sort((a, b) => {
    const aTime = new Date(a.completed_at ?? a.queued_at).getTime();
    const bTime = new Date(b.completed_at ?? b.queued_at).getTime();
    return bTime - aTime;
  })[0];
}

function extractText(job: AIAnalysisJob, resultType: string, field: string): string | null {
  const result = job.results.find((item) => item.result_type === resultType);
  const value = result?.result_payload[field];
  return typeof value === "string" && value.trim() ? value : null;
}

function extractItems(job: AIAnalysisJob): { type: string; title: string }[] {
  const items: { type: string; title: string }[] = [];
  for (const resultType of ["task_extraction", "appointment_extraction", "deal_extraction"]) {
    const result = job.results.find((item) => item.result_type === resultType);
    const rawItems = result?.result_payload.items;
    if (Array.isArray(rawItems)) {
      for (const rawItem of rawItems) {
        if (rawItem && typeof rawItem === "object" && typeof (rawItem as { title?: unknown }).title === "string") {
          items.push({ type: resultType, title: (rawItem as { title: string }).title });
        }
      }
    }
  }
  return items;
}

function formatTime(value: string): string {
  return new Intl.DateTimeFormat("tr-TR", { hour: "2-digit", minute: "2-digit" }).format(new Date(value));
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
  }).format(new Date(value));
}
