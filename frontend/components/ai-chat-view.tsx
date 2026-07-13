"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  ChatMessage,
  ChatSession,
  ChatSource,
  getChatSession,
  interpretVoiceCommand,
  listChatSessions,
  SearchResult,
  semanticSearch,
  sendChatMessage,
} from "@/lib/api";
import { useSession } from "@/lib/session";

type LocalMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  confidence: number | null;
  sources: ChatSource[] | null;
  created_at: string;
  isVoice?: boolean;
  voiceAction?: {
    intent: string;
    action_type: string;
    requiresApproval: boolean;
  } | null;
};

type ComposerMode = "chat" | "voice";

export function AIChatView() {
  const { tokens } = useSession();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [prompt, setPrompt] = useState("");
  const [mode, setMode] = useState<ComposerMode>("chat");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [isSending, setSending] = useState(false);
  const [isSearching, setSearching] = useState(false);

  async function loadSessions() {
    if (!tokens?.accessToken) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      setSessions(await listChatSessions(tokens.accessToken));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Chat oturumları alınamadı.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSessions();
  }, [tokens?.accessToken]);

  async function openSession(sessionId: string) {
    if (!tokens?.accessToken) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const detail = await getChatSession(tokens.accessToken, sessionId);
      setActiveSessionId(detail.id);
      setMessages(detail.messages.map(toLocalMessage));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Chat oturumu acilamadi.");
    } finally {
      setLoading(false);
    }
  }

  async function handleComposerSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !prompt.trim()) {
      return;
    }

    const text = prompt.trim();
    const userMessage: LocalMessage = {
      id: `local-${Date.now()}`,
      role: "user",
      content: text,
      confidence: null,
      sources: null,
      created_at: new Date().toISOString(),
      isVoice: mode === "voice",
    };

    setMessages((currentMessages) => [...currentMessages, userMessage]);
    setPrompt("");
    setSending(true);
    setError(null);

    try {
      if (mode === "chat") {
        const assistantMessage = await sendChatMessage(tokens.accessToken, {
          message: text,
          sessionId: activeSessionId,
        });
        setActiveSessionId(assistantMessage.session_id);
        setMessages((currentMessages) => [...currentMessages, toLocalMessage(assistantMessage)]);
        await loadSessions();
      } else {
        const result = await interpretVoiceCommand(tokens.accessToken, text);
        const assistantMessage: LocalMessage = {
          id: `local-${Date.now()}-voice`,
          role: "assistant",
          content: result.spoken_response,
          confidence: result.action.confidence,
          sources: null,
          created_at: new Date().toISOString(),
          voiceAction: {
            intent: result.action.intent,
            action_type: result.action.action_type,
            requiresApproval: result.action.requires_approval,
          },
        };
        setMessages((currentMessages) => [...currentMessages, assistantMessage]);
      }
    } catch (sendError) {
      setError(sendError instanceof Error ? sendError.message : "Mesaj gonderilemedi.");
    } finally {
      setSending(false);
    }
  }

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !searchQuery.trim()) {
      return;
    }

    setSearching(true);
    setError(null);
    try {
      setSearchResults(await semanticSearch(tokens.accessToken, searchQuery.trim()));
    } catch (searchError) {
      setError(searchError instanceof Error ? searchError.message : "Arama tamamlanamadi.");
    } finally {
      setSearching(false);
    }
  }

  const summary = useMemo(() => {
    return {
      sessions: sessions.length,
      messages: messages.length,
      sources: messages.reduce((count, message) => count + (message.sources?.length ?? 0), 0),
      results: searchResults.length,
    };
  }, [messages, searchResults.length, sessions.length]);

  return (
    <>
      {error ? <p className="notice">{error}</p> : null}

      <div className="moduleGrid" style={{ marginBottom: 16 }}>
        <SummaryCard label="Oturum" value={summary.sessions} />
        <SummaryCard label="Mesaj" value={summary.messages} />
        <SummaryCard label="Kaynak" value={summary.sources} />
        <SummaryCard label="Arama sonucu" value={summary.results} />
      </div>

      <div className="chatShell">
        <aside className="chatSessions">
          <div className="panelHeader">
            <h2>Oturumlar</h2>
            <button disabled={isLoading} onClick={loadSessions} type="button">
              Yenile
            </button>
          </div>
          <div className="sessionList">
            {sessions.length === 0 ? <p className="emptyState">Kayıtlı chat oturumu yok.</p> : null}
            {sessions.map((session) => (
              <button
                className={session.id === activeSessionId ? "sessionItem active" : "sessionItem"}
                key={session.id}
                onClick={() => openSession(session.id)}
                type="button"
              >
                <strong>{session.title ?? "Yeni sohbet"}</strong>
                <span>{formatDateTime(session.created_at)}</span>
              </button>
            ))}
          </div>
        </aside>

        <div className="chatColumn">
          <div className="chatScroll" aria-live="polite">
            {messages.length === 0 ? (
              <p className="emptyState">
                AI Chat hazır. İş akışınla ilgili bir soru sor ya da mikrofon simgesiyle sesli komut
                moduna geç.
              </p>
            ) : null}
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
          </div>

          <form className="composerBar" onSubmit={handleComposerSubmit}>
            {mode === "voice" ? (
              <p className="composerHint" style={{ marginTop: 0, marginBottom: 8 }}>
                <span>Sesli komut modu: yazdığın metin konuşma gibi yorumlanıp niyet çıkarımı yapılır.</span>
              </p>
            ) : null}
            <div className="composerRow">
              <textarea
                onChange={(event) => setPrompt(event.target.value)}
                placeholder={
                  mode === "chat"
                    ? "Bugün hangi görevlere odaklanmalıyım?"
                    : "Yarın Ahmet için takip görevi oluştur"
                }
                rows={1}
                value={prompt}
              />
              <div className="composerActions">
                <button
                  aria-label="Sesli komut modunu değiştir"
                  aria-pressed={mode === "voice"}
                  className={mode === "voice" ? "micToggle active" : "micToggle"}
                  onClick={() => setMode((current) => (current === "chat" ? "voice" : "chat"))}
                  type="button"
                >
                  <span className="material-symbols-outlined" aria-hidden="true">
                    mic
                  </span>
                </button>
                <button className="sendBtn" disabled={isSending || !prompt.trim()} type="submit">
                  <span className="material-symbols-outlined" aria-hidden="true">
                    {isSending ? "hourglass_empty" : "send"}
                  </span>
                </button>
              </div>
            </div>
            <div className="composerHint">
              <span>{mode === "voice" ? "Sesli komut modu aktif" : "NeuroModel sohbet modu"}</span>
              <span>tr-TR</span>
            </div>
          </form>
        </div>
      </div>

      <section className="panel searchPanel" style={{ marginTop: 20 }}>
        <div className="panelHeader">
          <h2>Semantic Search</h2>
          <form className="inlineSearch" onSubmit={handleSearch}>
            <input
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Ara"
              value={searchQuery}
            />
            <button disabled={isSearching || !searchQuery.trim()} type="submit">
              {isSearching ? "Aranıyor" : "Ara"}
            </button>
          </form>
        </div>
        <div className="dataList">
          {searchResults.length === 0 ? <p className="emptyState">Arama sonucu yok.</p> : null}
          {searchResults.map((result) => (
            <article className="dataRow" key={`${result.source_type}-${result.source_id}`}>
              <div>
                <div className="rowTitle">
                  <h3>{result.title}</h3>
                  <span>{result.source_type}</span>
                </div>
                <p>{result.snippet}</p>
                <small>Skor {Math.round(result.score * 100)}%</small>
              </div>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}

function MessageBubble({ message }: { message: LocalMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={`bubbleRow ${message.role}`}>
      {!isUser ? (
        <div className="bubbleAvatar">
          <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 16 }}>
            smart_toy
          </span>
        </div>
      ) : null}
      <div className="bubbleContent">
        {message.isVoice ? <span className="voiceChip">Sesli Komut</span> : null}
        <div className="bubbleCard">
          {!isUser && message.confidence !== null ? (
            <div className="bubbleConfidence">
              <span className="confidenceDot" aria-hidden="true" />
              <span className="confLabel">Güven Skoru</span>
              <span className="confValue">%{Math.round(message.confidence * 100)}</span>
            </div>
          ) : null}
          <p>{message.content}</p>

          {message.voiceAction ? (
            <div className="actionChips">
              <span>Niyet: {message.voiceAction.intent}</span>
              <span>Tip: {message.voiceAction.action_type}</span>
              <span>
                {message.voiceAction.requiresApproval ? "Onay gerekiyor" : "Onay gerekmiyor"}
              </span>
            </div>
          ) : null}

          {message.sources && message.sources.length > 0 ? (
            <>
              <div className="sourceGrid">
                {message.sources.slice(0, 4).map((source) => (
                  <div className="sourceCard" key={`${source.source_type}-${source.source_id}`}>
                    <strong>{source.title}</strong>
                    <p>{source.snippet}</p>
                  </div>
                ))}
              </div>
              {message.sources.length > 4 ? (
                <div className="citationPills">
                  {message.sources.slice(4).map((source) => (
                    <span key={`${source.source_type}-${source.source_id}`}>
                      <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 12 }}>
                        link
                      </span>
                      {source.title}
                    </span>
                  ))}
                </div>
              ) : null}
            </>
          ) : null}
        </div>
        <span className="bubbleMeta">{formatDateTime(message.created_at)}</span>
      </div>
      {isUser ? (
        <div className="bubbleAvatar user">
          <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 16 }}>
            person
          </span>
        </div>
      ) : null}
    </div>
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

function toLocalMessage(message: ChatMessage): LocalMessage {
  return {
    id: message.id,
    role: message.role === "user" ? "user" : "assistant",
    content: message.content,
    confidence: message.confidence,
    sources: message.sources,
    created_at: message.created_at,
  };
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
  }).format(new Date(value));
}
