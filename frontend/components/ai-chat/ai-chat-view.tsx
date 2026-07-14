"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import {
  ChatMessage,
  ChatSession,
  ChatSource,
  getChatSession,
  interpretVoiceCommand,
  listChatSessions,
  sendChatMessage,
} from "@/lib/api";
import { useSession } from "@/lib/session";
import { formatDateTime, getInitials } from "@/lib/format";

type LocalMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  confidence: number | null;
  sources: ChatSource[] | null;
  created_at: string;
};

export function AIChatView() {
  const { tokens, user } = useSession();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [prompt, setPrompt] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSending, setSending] = useState(false);
  const [isVoiceOpen, setVoiceOpen] = useState(false);
  const [showSessions, setShowSessions] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const loadSessions = useCallback(async () => {
    if (!tokens?.accessToken) return;
    try {
      const list = await listChatSessions(tokens.accessToken);
      setSessions(list);
      if (!activeSessionId && list.length > 0) {
        const detail = await getChatSession(tokens.accessToken, list[0].id);
        setActiveSessionId(detail.id);
        setMessages(detail.messages.map(toLocalMessage));
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Chat oturumları alınamadı.");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tokens?.accessToken]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages]);

  async function openSession(sessionId: string) {
    if (!tokens?.accessToken) return;
    try {
      const detail = await getChatSession(tokens.accessToken, sessionId);
      setActiveSessionId(detail.id);
      setMessages(detail.messages.map(toLocalMessage));
      setShowSessions(false);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Chat oturumu açılamadı.");
    }
  }

  async function sendMessage(text: string) {
    if (!tokens?.accessToken || !text.trim()) return;
    const trimmed = text.trim();
    const userMessage: LocalMessage = {
      id: `local-${Date.now()}`,
      role: "user",
      content: trimmed,
      confidence: null,
      sources: null,
      created_at: new Date().toISOString(),
    };
    setMessages((current) => [...current, userMessage]);
    setSending(true);
    setError(null);
    try {
      const assistantMessage = await sendChatMessage(tokens.accessToken, {
        message: trimmed,
        sessionId: activeSessionId,
      });
      setActiveSessionId(assistantMessage.session_id);
      setMessages((current) => [...current, toLocalMessage(assistantMessage)]);
      await loadSessions();
    } catch (sendError) {
      setError(sendError instanceof Error ? sendError.message : "Mesaj gönderilemedi.");
    } finally {
      setSending(false);
    }
  }

  async function handleComposerSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = prompt;
    setPrompt("");
    await sendMessage(text);
  }

  const displayName = user?.profile?.full_name ?? user?.email ?? "Kullanıcı";

  return (
    <div className="relative">
      <div className="p-xl relative flex flex-col min-h-[calc(100vh-64px)]">
        <div className="flex-1 max-w-4xl mx-auto w-full space-y-lg pb-40">
          {error ? <p className="text-error text-body-sm">{error}</p> : null}

          <div className="flex items-center justify-between">
            <h2 className="font-headline-md text-headline-md font-black text-on-surface">AI Chat</h2>
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowSessions((v) => !v)}
                className="text-on-surface-variant text-body-sm hover:text-primary flex items-center gap-1"
              >
                <span className="material-symbols-outlined text-[18px]">history</span>
                Oturumlar
              </button>
              {showSessions ? (
                <div className="absolute right-0 mt-2 w-64 bg-surface-container-lowest border border-outline-variant/30 rounded-xl shadow-xl z-30 max-h-80 overflow-y-auto custom-scrollbar">
                  {sessions.length === 0 ? (
                    <p className="p-md text-body-sm text-on-surface-variant">Kayıtlı oturum yok.</p>
                  ) : (
                    sessions.map((s) => (
                      <button
                        key={s.id}
                        type="button"
                        onClick={() => openSession(s.id)}
                        className={
                          "w-full text-left px-md py-2 text-body-sm hover:bg-primary-container/5 " +
                          (s.id === activeSessionId ? "text-primary font-bold" : "text-on-surface")
                        }
                      >
                        {s.title ?? "Yeni sohbet"}
                      </button>
                    ))
                  )}
                </div>
              ) : null}
            </div>
          </div>

          <div ref={scrollRef} className="space-y-lg overflow-y-auto">
            {messages.length === 0 ? (
              <p className="text-body-md text-on-surface-variant">
                AI Chat hazır. İş akışınla ilgili bir soru sor ya da mikrofon simgesiyle sesli komut moduna geç.
              </p>
            ) : null}
            {messages.map((message) =>
              message.role === "user" ? (
                <div key={message.id} className="flex justify-end items-start gap-md">
                  <div className="max-w-[80%] flex flex-col items-end">
                    <div className="bg-surface-container-highest p-4 rounded-2xl rounded-tr-none">
                      <p className="font-body-md text-body-md text-on-surface">{message.content}</p>
                    </div>
                    <span className="mt-xs text-[10px] text-on-surface-variant">
                      {formatDateTime(message.created_at)}
                    </span>
                  </div>
                  <div className="w-8 h-8 rounded-full bg-primary-container/20 flex items-center justify-center text-primary text-[11px] font-bold shrink-0 mt-1">
                    {getInitials(displayName)}
                  </div>
                </div>
              ) : (
                <div key={message.id} className="flex justify-start items-start gap-md">
                  <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center shrink-0 mt-1">
                    <span className="material-symbols-outlined text-on-primary text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>
                      smart_toy
                    </span>
                  </div>
                  <div className="max-w-[90%] w-full flex flex-col items-start space-y-md">
                    <div className="bg-surface-container p-5 rounded-2xl rounded-tl-none ai-glow">
                      {message.confidence !== null ? (
                        <div className="flex items-center gap-2 mb-3 flex-wrap">
                          <span className="flex h-2 w-2 rounded-full bg-green-500" />
                          <span className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">
                            Confidence
                          </span>
                          <span className="font-label-sm text-label-sm font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-full">
                            {Math.round(message.confidence * 100)}%
                          </span>
                        </div>
                      ) : null}
                      <p className="font-body-lg text-body-lg text-on-surface leading-relaxed whitespace-pre-wrap">
                        {message.content}
                      </p>

                      {message.sources && message.sources.length > 0 ? (
                        <div className="mt-lg grid grid-cols-1 md:grid-cols-2 gap-md">
                          {message.sources.slice(0, 4).map((source) => (
                            <div
                              key={`${source.source_type}-${source.source_id}`}
                              className="p-3 bg-surface-container-lowest border border-outline-variant/30 rounded-xl hover:border-primary/40 hover:shadow-md transition-all"
                            >
                              <p className="font-label-md text-label-md text-on-surface leading-tight truncate">
                                {source.title}
                              </p>
                              <p className="text-[12px] text-on-surface-variant line-clamp-2 italic mt-1">
                                {source.snippet}
                              </p>
                            </div>
                          ))}
                        </div>
                      ) : null}
                    </div>
                    <span className="text-[10px] text-on-surface-variant">
                      {formatDateTime(message.created_at)}
                    </span>
                  </div>
                </div>
              ),
            )}
          </div>
        </div>

        <form
          onSubmit={handleComposerSubmit}
          className="fixed bottom-xl left-[300px] right-xl max-w-4xl mx-auto bg-surface-container-lowest/80 backdrop-blur-md rounded-2xl border border-outline-variant/30 shadow-xl p-4 z-40"
        >
          <div className="flex items-end gap-3">
            <div className="flex-1 bg-surface-container-low rounded-xl px-4 py-3 min-h-[48px] flex items-center">
              <textarea
                className="w-full bg-transparent border-none p-0 focus:ring-0 font-body-md text-body-md resize-none leading-relaxed"
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    e.currentTarget.form?.requestSubmit();
                  }
                }}
                placeholder="Ask NeuroDesk anything..."
                rows={1}
                value={prompt}
              />
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setVoiceOpen(true)}
                className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-surface-container-high transition-colors text-on-surface-variant"
                aria-label="Sesli komut"
              >
                <span className="material-symbols-outlined">mic</span>
              </button>
              <button
                type="submit"
                disabled={isSending || !prompt.trim()}
                className="w-10 h-10 flex items-center justify-center rounded-full bg-primary text-on-primary shadow-lg hover:scale-105 active:scale-95 transition-all disabled:opacity-60"
              >
                <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>
                  {isSending ? "hourglass_empty" : "send"}
                </span>
              </button>
            </div>
          </div>
        </form>
      </div>

      {isVoiceOpen ? (
        <VoiceOverlay onClose={() => setVoiceOpen(false)} onSubmitText={sendMessage} />
      ) : null}
    </div>
  );
}

function VoiceOverlay({
  onClose,
  onSubmitText,
}: {
  onClose: () => void;
  onSubmitText: (text: string) => Promise<void>;
}) {
  const { tokens } = useSession();
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState<string | null>(null);
  const [actionMeta, setActionMeta] = useState<{ intent: string; actionType: string; requiresApproval: boolean } | null>(
    null,
  );
  const [isBusy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleVoiceSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !transcript.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const result = await interpretVoiceCommand(tokens.accessToken, transcript.trim());
      setResponse(result.spoken_response);
      setActionMeta({
        intent: result.action.intent,
        actionType: result.action.action_type,
        requiresApproval: result.action.requires_approval,
      });
    } catch (voiceError) {
      setError(voiceError instanceof Error ? voiceError.message : "Sesli komut yorumlanamadı.");
    } finally {
      setBusy(false);
    }
  }

  async function handleSendToChat() {
    if (!transcript.trim()) return;
    await onSubmitText(transcript.trim());
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 ml-[260px] glass-overlay flex flex-col items-center justify-center">
      <button
        type="button"
        onClick={onClose}
        className="absolute top-xl right-xl p-3 text-on-surface-variant hover:text-primary transition-colors active:scale-90"
        aria-label="Kapat"
      >
        <span className="material-symbols-outlined text-[32px]">close</span>
      </button>

      <div className="max-w-3xl w-full px-xl mb-auto mt-24 text-center">
        <span className="px-3 py-1 rounded-full bg-primary-container/10 text-primary font-label-sm text-label-sm uppercase tracking-wider mb-4 inline-block">
          Real-time Transcript
        </span>
        <form id="voice-form" onSubmit={handleVoiceSubmit}>
          <input
            autoFocus
            className="w-full bg-transparent border-b-2 border-primary/20 focus:border-primary text-center font-headline-lg text-headline-lg text-on-surface font-medium leading-relaxed outline-none pb-2"
            onChange={(e) => setTranscript(e.target.value)}
            placeholder="Söylemek istediğini yaz..."
            value={transcript}
          />
        </form>
      </div>

      <div className="flex flex-col items-center gap-12 py-xl">
        <div className="relative">
          <div className="absolute inset-0 bg-primary/20 rounded-full blur-3xl scale-150 animate-pulse" />
          <button
            type="submit"
            form="voice-form"
            disabled={isBusy || !transcript.trim()}
            className="relative w-32 h-32 bg-primary text-on-primary rounded-full flex items-center justify-center mic-glow transition-transform active:scale-95 shadow-2xl z-10 disabled:opacity-60"
          >
            <span className="material-symbols-outlined text-[48px]" style={{ fontVariationSettings: "'FILL' 1" }}>
              mic
            </span>
          </button>
        </div>
        <div className="flex items-center gap-1.5 h-12">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="wave-bar" style={{ animationDelay: `${(i % 5) * 0.1}s` }} />
          ))}
        </div>
      </div>

      <div className="max-w-2xl w-full px-xl mt-auto mb-24">
        {error ? <p className="text-error text-body-sm mb-4 text-center">{error}</p> : null}
        {response ? (
          <div className="bg-surface-container-lowest p-xl rounded-2xl border border-primary/20 shadow-xl relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full bg-primary" />
            <div className="flex items-start gap-4">
              <div className="p-2 bg-primary-container/10 rounded-lg shrink-0">
                <span className="material-symbols-outlined text-primary">smart_toy</span>
              </div>
              <div className="flex-1">
                <h4 className="font-label-sm text-label-sm text-primary mb-2 uppercase tracking-tight">
                  NeuroDesk Response
                </h4>
                <p className="text-on-surface-variant font-body-lg text-body-lg leading-snug">{response}</p>
                {actionMeta ? (
                  <p className="text-[11px] text-outline mt-3">
                    Niyet: {actionMeta.intent} · Tip: {actionMeta.actionType} ·{" "}
                    {actionMeta.requiresApproval ? "Onay gerekiyor" : "Onay gerekmiyor"}
                  </p>
                ) : null}
                <div className="flex gap-2 mt-6">
                  <button
                    type="button"
                    onClick={handleSendToChat}
                    className="px-4 py-2 bg-primary text-on-primary rounded-lg text-sm font-medium hover:brightness-110 active:scale-95 transition-all"
                  >
                    Sohbete Ekle
                  </button>
                  {actionMeta?.requiresApproval ? (
                    <a
                      href="/onay-merkezi"
                      className="px-4 py-2 bg-surface-container-high text-on-surface rounded-lg text-sm font-medium hover:bg-surface-container-highest active:scale-95 transition-all"
                    >
                      Onay Merkezine Git
                    </a>
                  ) : null}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <p className="text-center text-body-sm text-on-surface-variant">
            Komutunu yazıp mikrofon düğmesine bas.
          </p>
        )}
      </div>
    </div>
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
