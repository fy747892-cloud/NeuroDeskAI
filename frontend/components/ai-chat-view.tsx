"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  ChatMessage,
  ChatSession,
  getChatSession,
  interpretVoiceCommand,
  listChatSessions,
  SearchResult,
  semanticSearch,
  sendChatMessage,
} from "@/lib/api";
import { useSession } from "@/lib/session";

type LocalMessage = Pick<ChatMessage, "role" | "content" | "confidence" | "sources" | "created_at"> & {
  id: string;
};

export function AIChatView() {
  const { tokens } = useSession();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [prompt, setPrompt] = useState("");
  const [voiceText, setVoiceText] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [voiceResult, setVoiceResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [isSending, setSending] = useState(false);
  const [isSearching, setSearching] = useState(false);
  const [isInterpreting, setInterpreting] = useState(false);

  async function loadSessions() {
    if (!tokens?.accessToken) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      setSessions(await listChatSessions(tokens.accessToken));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Chat oturumlari alinamadi.");
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
      setMessages(detail.messages);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Chat oturumu acilamadi.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !prompt.trim()) {
      return;
    }

    const userMessage: LocalMessage = {
      id: `local-${Date.now()}`,
      role: "user",
      content: prompt.trim(),
      confidence: null,
      sources: null,
      created_at: new Date().toISOString(),
    };

    setMessages((currentMessages) => [...currentMessages, userMessage]);
    setPrompt("");
    setSending(true);
    setError(null);

    try {
      const assistantMessage = await sendChatMessage(tokens.accessToken, {
        message: userMessage.content,
        sessionId: activeSessionId,
      });
      setActiveSessionId(assistantMessage.session_id);
      setMessages((currentMessages) => [...currentMessages, assistantMessage]);
      await loadSessions();
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

  async function handleVoiceCommand(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !voiceText.trim()) {
      return;
    }

    setInterpreting(true);
    setError(null);
    setVoiceResult(null);
    try {
      const result = await interpretVoiceCommand(tokens.accessToken, voiceText.trim());
      setVoiceResult(
        `${result.action.intent} -> ${result.action.action_type} (${Math.round(result.action.confidence * 100)}%)`,
      );
    } catch (voiceError) {
      setError(voiceError instanceof Error ? voiceError.message : "Ses komutu yorumlanamadi.");
    } finally {
      setInterpreting(false);
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
    <section className="chatWorkspace">
      {error ? <p className="notice">{error}</p> : null}

      <aside className="chatRail panel">
        <div className="panelHeader">
          <h2>Oturumlar</h2>
          <button disabled={isLoading} onClick={loadSessions} type="button">
            Yenile
          </button>
        </div>
        <div className="sessionList">
          {sessions.length === 0 ? <p className="emptyState">Kayitli chat oturumu yok.</p> : null}
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

      <div className="chatMain">
        <div className="moduleGrid">
          <SummaryCard label="Oturum" value={summary.sessions} />
          <SummaryCard label="Mesaj" value={summary.messages} />
          <SummaryCard label="Kaynak" value={summary.sources} />
          <SummaryCard label="Arama sonucu" value={summary.results} />
        </div>

        <section className="panel chatPanel">
          <div className="messageList" aria-live="polite">
            {messages.length === 0 ? (
              <p className="emptyState">AI Chat hazir. Is akisinla ilgili bir soru sorabilirsin.</p>
            ) : null}
            {messages.map((message) => (
              <article className={`messageBubble ${message.role}`} key={message.id}>
                <div>
                  <span>{message.role === "assistant" ? "NeuroDesk AI" : "Sen"}</span>
                  <small>{formatConfidence(message.confidence)}</small>
                </div>
                <p>{message.content}</p>
                {message.sources && message.sources.length > 0 ? (
                  <div className="sourceList">
                    {message.sources.map((source) => (
                      <span key={`${source.source_type}-${source.source_id}`}>
                        {source.source_type}: {source.title}
                      </span>
                    ))}
                  </div>
                ) : null}
              </article>
            ))}
          </div>

          <form className="chatComposer" onSubmit={handleSend}>
            <textarea
              onChange={(event) => setPrompt(event.target.value)}
              placeholder="Bugun hangi gorevlere odaklanmaliyim?"
              rows={3}
              value={prompt}
            />
            <button disabled={isSending || !prompt.trim()} type="submit">
              {isSending ? "Dusunuyor" : "Gonder"}
            </button>
          </form>
        </section>

        <section className="panel searchPanel">
          <div className="panelHeader">
            <h2>Semantic Search</h2>
            <form className="inlineSearch" onSubmit={handleSearch}>
              <input
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Ara"
                value={searchQuery}
              />
              <button disabled={isSearching || !searchQuery.trim()} type="submit">
                {isSearching ? "Araniyor" : "Ara"}
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

        <section className="panel">
          <div className="panelHeader">
            <h2>Voice Command</h2>
            <span className="tag">tr-TR</span>
          </div>
          <form className="chatComposer" onSubmit={handleVoiceCommand}>
            <textarea
              onChange={(event) => setVoiceText(event.target.value)}
              placeholder="Yarin Ahmet icin takip gorevi olustur"
              rows={2}
              value={voiceText}
            />
            <button disabled={isInterpreting || !voiceText.trim()} type="submit">
              {isInterpreting ? "Yorumlaniyor" : "Yorumla"}
            </button>
          </form>
          {voiceResult ? <p className="notice success">{voiceResult}</p> : null}
        </section>
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

function formatConfidence(value: number | null): string {
  if (value === null) {
    return "";
  }
  return `${Math.round(value * 100)}%`;
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
  }).format(new Date(value));
}
