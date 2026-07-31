"use client";

import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ChatMessage,
  ChatSession,
  ChatSource,
  deleteChatSession,
  getChatSession,
  interpretVoiceCommand,
  listChatSessions,
  renameChatSession,
  sendChatMessage,
} from "@/lib/api";
import { useSession } from "@/lib/session";
import { useLanguage } from "@/lib/i18n/context";
import { useToast } from "@/lib/toast";
import { formatDateTime } from "@/lib/format";
import { deferredExecute, UNDO_WINDOW_MS } from "@/lib/undo";
import { Avatar } from "@/components/shell/avatar";
import { EmptyState } from "@/components/shell/empty-state";

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
  const { t, language } = useLanguage();
  const { showToast } = useToast();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [prompt, setPrompt] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSending, setSending] = useState(false);
  const [isVoiceOpen, setVoiceOpen] = useState(false);
  const [showSessions, setShowSessions] = useState(false);
  const [renamingSessionId, setRenamingSessionId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
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
      setError(loadError instanceof Error ? loadError.message : t("aiChat.errors.loadSessionsFailed"));
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
      setError(loadError instanceof Error ? loadError.message : t("aiChat.errors.openSessionFailed"));
    }
  }

  function startRenamingSession(session: ChatSession) {
    setRenamingSessionId(session.id);
    setRenameValue(session.title ?? "");
  }

  async function handleRenameSession(sessionId: string) {
    if (!tokens?.accessToken || !renameValue.trim()) {
      setRenamingSessionId(null);
      return;
    }
    try {
      const updated = await renameChatSession(tokens.accessToken, sessionId, renameValue.trim());
      setSessions((current) => current.map((s) => (s.id === updated.id ? updated : s)));
    } catch (renameError) {
      setError(renameError instanceof Error ? renameError.message : t("aiChat.errors.renameSessionFailed"));
    } finally {
      setRenamingSessionId(null);
    }
  }

  function handleDeleteSession(sessionId: string) {
    if (!tokens?.accessToken) return;
    const accessToken = tokens.accessToken;
    const previousSessions = sessions;
    const wasActive = activeSessionId === sessionId;
    const previousMessages = messages;
    const previousActiveSessionId = activeSessionId;

    setSessions((current) => current.filter((s) => s.id !== sessionId));
    if (wasActive) {
      setActiveSessionId(null);
      setMessages([]);
    }

    const pending = deferredExecute(async () => {
      try {
        await deleteChatSession(accessToken, sessionId);
      } catch (deleteError) {
        setSessions(previousSessions);
        if (wasActive) {
          setActiveSessionId(previousActiveSessionId);
          setMessages(previousMessages);
        }
        setError(deleteError instanceof Error ? deleteError.message : t("aiChat.errors.deleteSessionFailed"));
      }
    });

    showToast(t("aiChat.sessionDeletedToast"), "success", {
      duration: UNDO_WINDOW_MS,
      action: {
        label: t("common.undo"),
        onClick: () => {
          pending.cancel();
          setSessions(previousSessions);
          if (wasActive) {
            setActiveSessionId(previousActiveSessionId);
            setMessages(previousMessages);
          }
        },
      },
    });
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
      setError(sendError instanceof Error ? sendError.message : t("aiChat.errors.sendFailed"));
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

  const displayName = user?.profile?.full_name ?? user?.email ?? t("aiChat.defaultUserName");

  return (
    <div className="relative">
      <div className="p-xl relative flex flex-col min-h-[calc(100vh-64px)]">
        <div className="flex-1 max-w-4xl mx-auto w-full space-y-lg pb-40">
          {error ? <p className="text-error text-body-sm">{error}</p> : null}

          <div className="flex items-center justify-between">
            <h2 className="font-headline-md text-headline-md font-black text-on-surface">{t("aiChat.title")}</h2>
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowSessions((v) => !v)}
                className="text-on-surface-variant text-body-sm hover:text-primary flex items-center gap-1"
              >
                <span className="material-symbols-outlined text-[18px]">history</span>
                {t("aiChat.sessionsButton")}
              </button>
              {showSessions ? (
                <div className="absolute right-0 mt-2 w-64 bg-surface-container-lowest border border-outline-variant/30 rounded-xl shadow-xl z-30 max-h-80 overflow-y-auto custom-scrollbar">
                  {sessions.length === 0 ? (
                    <EmptyState icon="history" title={t("aiChat.noSavedSessions")} />
                  ) : (
                    sessions.map((s) =>
                      renamingSessionId === s.id ? (
                        <div key={s.id} className="flex items-center gap-1 px-md py-1.5">
                          <input
                            autoFocus
                            className="flex-1 min-w-0 bg-surface-container-low border border-outline-variant/30 rounded px-2 py-1 text-body-sm"
                            onChange={(e) => setRenameValue(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") handleRenameSession(s.id);
                              if (e.key === "Escape") setRenamingSessionId(null);
                            }}
                            value={renameValue}
                          />
                          <button
                            type="button"
                            onClick={() => handleRenameSession(s.id)}
                            aria-label={t("common.save")}
                            className="w-6 h-6 shrink-0 rounded flex items-center justify-center text-primary hover:bg-primary-container/10"
                          >
                            <span className="material-symbols-outlined text-[16px]">check</span>
                          </button>
                        </div>
                      ) : (
                        <div key={s.id} className="group/session flex items-center hover:bg-primary-container/5">
                          <button
                            type="button"
                            onClick={() => openSession(s.id)}
                            className={
                              "flex-1 min-w-0 text-left px-md py-2 text-body-sm truncate " +
                              (s.id === activeSessionId ? "text-primary font-bold" : "text-on-surface")
                            }
                          >
                            {s.title ?? t("aiChat.newChatFallback")}
                          </button>
                          <div className="hidden group-hover/session:flex items-center gap-0.5 pr-2 shrink-0">
                            <button
                              type="button"
                              onClick={() => startRenamingSession(s)}
                              aria-label={t("common.edit")}
                              className="w-6 h-6 rounded flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high"
                            >
                              <span className="material-symbols-outlined text-[14px]">edit</span>
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDeleteSession(s.id)}
                              aria-label={t("common.delete")}
                              className="w-6 h-6 rounded flex items-center justify-center text-error hover:bg-error-container/20"
                            >
                              <span className="material-symbols-outlined text-[14px]">delete</span>
                            </button>
                          </div>
                        </div>
                      ),
                    )
                  )}
                </div>
              ) : null}
            </div>
          </div>

          <div ref={scrollRef} className="space-y-lg overflow-y-auto">
            {messages.length === 0 ? (
              <EmptyState icon="smart_toy" size="lg" title={t("aiChat.emptyState")} />
            ) : null}
            {messages.map((message) =>
              message.role === "user" ? (
                <div key={message.id} className="flex justify-end items-start gap-md">
                  <div className="max-w-[80%] flex flex-col items-end">
                    <div className="bg-surface-container-highest p-4 rounded-2xl rounded-tr-none">
                      <p className="font-body-md text-body-md text-on-surface">{message.content}</p>
                    </div>
                    <span className="mt-xs text-[10px] text-on-surface-variant">
                      {formatDateTime(message.created_at, language)}
                    </span>
                  </div>
                  <Avatar
                    avatarUrl={user?.profile?.avatar_url}
                    name={displayName}
                    className="w-8 h-8 text-[11px] mt-1"
                  />
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
                            {t("aiChat.confidenceLabel")}
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
                      {formatDateTime(message.created_at, language)}
                    </span>
                  </div>
                </div>
              ),
            )}
          </div>
        </div>

        <form
          onSubmit={handleComposerSubmit}
          className="fixed bottom-md left-md right-md sm:bottom-xl sm:left-xl sm:right-xl lg:left-[300px] max-w-4xl mx-auto bg-surface-container-lowest/80 backdrop-blur-md rounded-2xl border border-outline-variant/30 shadow-xl p-4 z-40"
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
                placeholder={t("aiChat.composerPlaceholder")}
                rows={1}
                value={prompt}
              />
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                disabled={!prompt}
                onClick={() => setPrompt("")}
                className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-surface-container-high transition-colors text-on-surface-variant disabled:opacity-40"
                aria-label={t("common.clear")}
              >
                <span className="material-symbols-outlined">backspace</span>
              </button>
              <button
                type="button"
                onClick={() => setVoiceOpen(true)}
                className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-surface-container-high transition-colors text-on-surface-variant"
                aria-label={t("aiChat.voiceCommandAria")}
              >
                <span className="material-symbols-outlined">graphic_eq</span>
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

type SpeechRecognitionLike = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((event: any) => void) | null;
  onerror: ((event: any) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

function getSpeechRecognitionCtor(): (new () => SpeechRecognitionLike) | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as Record<string, unknown>;
  return (w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null) as (new () => SpeechRecognitionLike) | null;
}

function VoiceOverlay({
  onClose,
  onSubmitText,
}: {
  onClose: () => void;
  onSubmitText: (text: string) => Promise<void>;
}) {
  const { tokens } = useSession();
  const { t, language } = useLanguage();
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState<string | null>(null);
  const [actionMeta, setActionMeta] = useState<{ intent: string; actionType: string; requiresApproval: boolean } | null>(
    null,
  );
  const [isBusy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isListening, setListening] = useState(false);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const isSpeechSupported = useMemo(() => getSpeechRecognitionCtor() !== null, []);

  const submitTranscript = useCallback(
    async (text: string) => {
      if (!tokens?.accessToken || !text.trim()) return;
      setBusy(true);
      setError(null);
      try {
        const result = await interpretVoiceCommand(tokens.accessToken, text.trim());
        setResponse(result.spoken_response);
        setActionMeta({
          intent: result.action.intent,
          actionType: result.action.action_type,
          requiresApproval: result.action.requires_approval,
        });
      } catch (voiceError) {
        setError(voiceError instanceof Error ? voiceError.message : t("aiChat.errors.voiceInterpretFailed"));
      } finally {
        setBusy(false);
      }
    },
    [t, tokens?.accessToken],
  );

  async function handleVoiceSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await submitTranscript(transcript);
  }

  function stopListening() {
    recognitionRef.current?.stop();
  }

  function startListening() {
    const Ctor = getSpeechRecognitionCtor();
    if (!Ctor) {
      setError(t("aiChat.errors.voiceNotSupported"));
      return;
    }
    setError(null);
    setResponse(null);
    setActionMeta(null);
    setTranscript("");

    const recognition = new Ctor();
    recognition.lang = language === "tr" ? "tr-TR" : "en-US";
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.onresult = (event: any) => {
      let combined = "";
      for (let i = 0; i < event.results.length; i += 1) {
        combined += event.results[i][0].transcript;
      }
      setTranscript(combined);
    };
    recognition.onerror = () => {
      setError(t("aiChat.errors.voiceRecognitionFailed"));
      setListening(false);
    };
    recognition.onend = () => {
      setListening(false);
      recognitionRef.current = null;
      setTranscript((current) => {
        if (current.trim()) {
          void submitTranscript(current);
        }
        return current;
      });
    };

    recognitionRef.current = recognition;
    setListening(true);
    recognition.start();
  }

  function handleMicButtonClick() {
    if (isListening) {
      stopListening();
      return;
    }
    if (isSpeechSupported) {
      startListening();
      return;
    }
    if (transcript.trim()) {
      void submitTranscript(transcript);
    }
  }

  useEffect(() => {
    return () => {
      recognitionRef.current?.stop();
    };
  }, []);

  async function handleSendToChat() {
    if (!transcript.trim()) return;
    await onSubmitText(transcript.trim());
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 lg:ml-[260px] glass-overlay flex flex-col items-center justify-center">
      <button
        type="button"
        onClick={onClose}
        className="absolute top-xl right-xl p-3 text-on-surface-variant hover:text-primary transition-colors active:scale-90"
        aria-label={t("common.close")}
      >
        <span className="material-symbols-outlined text-[32px]">close</span>
      </button>

      <div className="max-w-3xl w-full px-xl mb-auto mt-24 text-center">
        <span className="px-3 py-1 rounded-full bg-primary-container/10 text-primary font-label-sm text-label-sm uppercase tracking-wider mb-4 inline-flex items-center gap-2">
          {isListening ? (
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
          ) : null}
          {isSpeechSupported ? t("aiChat.realTimeTranscript") : t("aiChat.typeInstead")}
        </span>
        <form id="voice-form" onSubmit={handleVoiceSubmit} className="relative">
          <input
            autoFocus
            className="w-full bg-transparent border-b-2 border-primary/20 focus:border-primary text-center font-headline-lg text-headline-lg text-on-surface font-medium leading-relaxed outline-none pb-2 pr-12"
            onChange={(e) => setTranscript(e.target.value)}
            placeholder={t("aiChat.voiceInputPlaceholder")}
            value={transcript}
          />
          <button
            type="button"
            disabled={!transcript}
            onClick={() => {
              setTranscript("");
              setResponse(null);
              setActionMeta(null);
            }}
            className="absolute right-0 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full text-on-surface-variant hover:bg-surface-container-high disabled:opacity-40"
            aria-label={t("common.clear")}
          >
            <span className="material-symbols-outlined">backspace</span>
          </button>
        </form>
      </div>

      <div className="flex flex-col items-center gap-12 py-xl">
        <div className="relative">
          {isListening ? (
            <div className="absolute inset-0 bg-primary/20 rounded-full blur-3xl scale-150 animate-pulse" />
          ) : null}
          <button
            type="button"
            onClick={handleMicButtonClick}
            disabled={isBusy}
            aria-label={isListening ? t("aiChat.stopListeningAria") : t("aiChat.voiceCommandAria")}
            className={
              "relative w-32 h-32 rounded-full flex items-center justify-center transition-transform active:scale-95 shadow-2xl z-10 disabled:opacity-60 " +
              (isListening ? "bg-primary text-on-primary mic-glow" : "bg-surface-container-high text-primary")
            }
          >
            <span className="material-symbols-outlined text-[48px]" style={{ fontVariationSettings: "'FILL' 1" }}>
              {isListening ? "stop" : "mic"}
            </span>
          </button>
        </div>
        <div className="flex items-center gap-1.5 h-12">
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              className="wave-bar"
              style={{
                animationDelay: `${(i % 5) * 0.1}s`,
                animationPlayState: isListening ? "running" : "paused",
                opacity: isListening ? 1 : 0.25,
              }}
            />
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
                  {t("aiChat.neuroDeskResponse")}
                </h4>
                <p className="text-on-surface-variant font-body-lg text-body-lg leading-snug">{response}</p>
                {actionMeta ? (
                  <p className="text-[11px] text-outline mt-3">
                    {t("aiChat.voiceMeta", { intent: actionMeta.intent, actionType: actionMeta.actionType })}{" "}
                    {actionMeta.requiresApproval ? t("aiChat.requiresApproval") : t("aiChat.noApprovalNeeded")}
                  </p>
                ) : null}
                <div className="flex gap-2 mt-6">
                  <button
                    type="button"
                    onClick={handleSendToChat}
                    className="px-4 py-2 bg-primary text-on-primary rounded-lg text-sm font-medium hover:brightness-110 active:scale-95 transition-all"
                  >
                    {t("aiChat.addToChat")}
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <p className="text-center text-body-sm text-on-surface-variant">{t("aiChat.voicePrompt")}</p>
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
