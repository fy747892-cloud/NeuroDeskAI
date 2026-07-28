"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import {
  AIAnalysisJob,
  Call,
  ConversationDetail,
  createCallFromAudio,
  createCallFromText,
  Conversation,
  deleteCall,
  getConversation,
  listAnalysisJobs,
  listConversations,
  requestConversationAnalysis,
  updateConversation,
} from "@/lib/api";
import { useSession } from "@/lib/session";
import { useLanguage } from "@/lib/i18n/context";
import { formatDateTime, formatTime } from "@/lib/format";

const EXTRACT_ICON: Record<string, string> = {
  task_extraction: "task_alt",
  appointment_extraction: "calendar_month",
  deal_extraction: "handshake",
};

export function ConversationsView() {
  const { tokens } = useSession();
  const { t, language } = useLanguage();
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
  const [showAudioForm, setShowAudioForm] = useState(false);
  const [activeCallId, setActiveCallId] = useState<string | null>(null);
  const [isRenaming, setRenaming] = useState(false);
  const [isEditingTitle, setEditingTitle] = useState(false);
  const [editingTitle, setEditingTitleValue] = useState("");
  const [newCall, setNewCall] = useState({ participants: "", phone: "", title: "", transcript: "" });
  const [audioCall, setAudioCall] = useState({ participants: "", phone: "", title: "" });
  const [recordingState, setRecordingState] = useState<"idle" | "recording" | "uploading" | "analyzing">("idle");
  const [recordingStartedAt, setRecordingStartedAt] = useState<number | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const loadConversations = useCallback(async () => {
    if (!tokens?.accessToken) return;
    setLoading(true);
    setError(null);
    try {
      const [nextConversations, nextJobs] = await Promise.all([
        listConversations(tokens.accessToken),
        listAnalysisJobs(tokens.accessToken),
      ]);
      setConversations(nextConversations);
      setAnalysisJobs(nextJobs);
      setSelectedId((current) => current ?? nextConversations[0]?.id ?? null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : t("conversations.errors.loadFailed"));
    } finally {
      setLoading(false);
    }
  }, [t, tokens?.accessToken]);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  useEffect(() => {
    return () => {
      cleanupRecorder();
    };
  }, []);

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
        setError(loadError instanceof Error ? loadError.message : t("conversations.errors.loadDetailFailed"));
      } finally {
        setDetailLoading(false);
      }
    }
    loadDetail();
  }, [t, tokens?.accessToken, selectedId]);

  async function handleCreateCall(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !newCall.title.trim() || !newCall.transcript.trim()) return;

    setCreating(true);
    setError(null);
    setNotice(null);
    try {
      const result = await createCallFromText(tokens.accessToken, {
        title: newCall.title.trim(),
        transcript_text: newCall.transcript.trim(),
        phone_number: newCall.phone.trim() || null,
        participant_names: newCall.participants.split(",").map((p) => p.trim()).filter(Boolean),
      });
      setConversations((current) => [result.conversation, ...current]);
      setSelectedId(result.conversation.id);
      setNewCall({ participants: "", phone: "", title: "", transcript: "" });
      setNotice(t("conversations.notices.callCreated"));
      setShowCreateForm(false);
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : t("conversations.errors.createFailed"));
    } finally {
      setCreating(false);
    }
  }

  async function handleStartRecording() {
    if (!tokens?.accessToken || recordingState !== "idle") return;
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setError(t("conversations.audio.unsupported"));
      return;
    }

    setError(null);
    setNotice(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      streamRef.current = stream;
      recorderRef.current = recorder;
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };
      recorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop());
      };
      recorder.start();
      setRecordingStartedAt(Date.now());
      setRecordingState("recording");
    } catch {
      cleanupRecorder();
      setRecordingState("idle");
      setError(t("conversations.audio.permissionDenied"));
    }
  }

  function cleanupRecorder() {
    recorderRef.current = null;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }

  async function handleStopRecording() {
    if (!tokens?.accessToken || recordingState !== "recording") return;

    const recorder = recorderRef.current;
    if (!recorder) return;

    const audioBlob = await stopRecorder(recorder, chunksRef.current);
    const durationSeconds = recordingStartedAt ? Math.max(1, Math.round((Date.now() - recordingStartedAt) / 1000)) : null;
    cleanupRecorder();

    if (audioBlob.size === 0) {
      setRecordingState("idle");
      setError(t("conversations.audio.empty"));
      return;
    }

    setRecordingState("uploading");
    setError(null);
    setNotice(null);
    try {
      const result = await createCallFromAudio(tokens.accessToken, {
        title: audioCall.title.trim() || "Webden kaydedilen görüşme",
        audio: audioBlob,
        phone_number: audioCall.phone.trim() || null,
        participant_names: audioCall.participants.split(",").map((p) => p.trim()).filter(Boolean),
        duration_seconds: durationSeconds,
      });
      setRecordingState("analyzing");
      const job = await requestConversationAnalysis(tokens.accessToken, result.conversation.id);
      setConversations((current) => [result.conversation, ...current.filter((item) => item.id !== result.conversation.id)]);
      setAnalysisJobs((current) => [job, ...current.filter((item) => item.id !== job.id)]);
      setSelectedId(result.conversation.id);
      setDetail(await getConversation(tokens.accessToken, result.conversation.id));
      setAudioCall({ participants: "", phone: "", title: "" });
      setShowAudioForm(false);
      setNotice(t("conversations.audio.success"));
    } catch (recordingError) {
      setError(recordingError instanceof Error ? recordingError.message : t("conversations.audio.processFailed"));
    } finally {
      setRecordingState("idle");
      setRecordingStartedAt(null);
    }
  }

  function handleCancelRecording() {
    recorderRef.current?.stop();
    cleanupRecorder();
    chunksRef.current = [];
    setRecordingState("idle");
    setRecordingStartedAt(null);
    setNotice(t("conversations.audio.cancelled"));
  }

  async function handleDeleteCall(callId: string) {
    if (!tokens?.accessToken) return;
    setActiveCallId(callId);
    setError(null);
    try {
      await deleteCall(tokens.accessToken, callId);
      setDetail((current) =>
        current ? { ...current, calls: current.calls.filter((call) => call.id !== callId) } : current,
      );
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : t("conversations.errors.deleteFailed"));
    } finally {
      setActiveCallId(null);
    }
  }

  async function handleAnalyze() {
    if (!tokens?.accessToken || !selectedId) return;
    setAnalyzing(true);
    setError(null);
    try {
      const job = await requestConversationAnalysis(tokens.accessToken, selectedId);
      setAnalysisJobs((current) => [job, ...current.filter((item) => item.id !== job.id)]);
    } catch (analyzeError) {
      setError(analyzeError instanceof Error ? analyzeError.message : t("conversations.errors.analyzeFailed"));
    } finally {
      setAnalyzing(false);
    }
  }

  function startRenamingConversation() {
    if (!detail) return;
    setEditingTitleValue(detail.title);
    setEditingTitle(true);
    setError(null);
    setNotice(null);
  }

  async function handleRenameConversation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const title = editingTitle.trim();
    if (!tokens?.accessToken || !detail || !title) return;

    setRenaming(true);
    setError(null);
    setNotice(null);
    try {
      const updated = await updateConversation(tokens.accessToken, detail.id, { title });
      setDetail(updated);
      setConversations((current) =>
        current.map((conversation) => (conversation.id === updated.id ? { ...conversation, title: updated.title } : conversation)),
      );
      setEditingTitle(false);
      setEditingTitleValue("");
      setNotice(t("conversations.notices.renamed"));
    } catch (renameError) {
      setError(renameError instanceof Error ? renameError.message : t("conversations.errors.renameFailed"));
    } finally {
      setRenaming(false);
    }
  }

  const job = findLatestCompletedJob(analysisJobs, selectedId);
  const summaryText = job ? extractText(job, "conversation_summary", "summary_text") : null;
  const extractedItems = job ? extractItems(job) : [];

  return (
    <div className="flex h-[calc(100vh-64px)] overflow-hidden">
      <section className="w-80 bg-surface border-r border-surface-container-highest flex flex-col shrink-0">
        <div className="px-lg py-md border-b border-surface-container-highest">
          <h2 className="font-headline-md text-headline-md text-on-surface">{t("conversations.recentCalls")}</h2>
          <div className="mt-3 grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => {
                setShowAudioForm((value) => !value);
                setShowCreateForm(false);
              }}
              className={
                "flex items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-label-sm font-bold transition-colors " +
                (showAudioForm
                  ? "bg-primary text-on-primary"
                  : "bg-primary-container/20 text-primary hover:bg-primary-container/30")
              }
              aria-pressed={showAudioForm}
            >
              <span className="material-symbols-outlined text-[18px]">mic</span>
              {t("conversations.audio.openButton")}
            </button>
            <button
              type="button"
              onClick={() => {
                setShowCreateForm((value) => !value);
                setShowAudioForm(false);
              }}
              className={
                "flex items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-label-sm font-bold transition-colors " +
                (showCreateForm
                  ? "bg-surface-container-highest text-on-surface"
                  : "bg-surface-container-low text-on-surface-variant hover:bg-surface-container-high")
              }
              aria-pressed={showCreateForm}
            >
              <span className="material-symbols-outlined text-[18px]">edit_note</span>
              {t("conversations.form.openButton")}
            </button>
          </div>
        </div>

        {showAudioForm ? (
          <div className="p-md space-y-3 border-b border-surface-container-highest">
            {error ? <p className="text-error text-[11px]">{error}</p> : null}
            <div className="rounded-lg border border-surface-container-highest bg-surface-container-low p-3 space-y-2">
              <div className="flex items-center gap-2 text-primary font-label-sm text-label-sm">
                <span className="material-symbols-outlined text-[18px]">mic</span>
                <span>{t("conversations.audio.title")}</span>
              </div>
              <input
                className="w-full bg-white rounded-lg px-3 py-2 text-body-sm"
                onChange={(e) => setAudioCall((c) => ({ ...c, title: e.target.value }))}
                placeholder={t("conversations.audio.titlePlaceholder")}
                value={audioCall.title}
              />
              <input
                className="w-full bg-white rounded-lg px-3 py-2 text-body-sm"
                onChange={(e) => setAudioCall((c) => ({ ...c, participants: e.target.value }))}
                placeholder={t("conversations.form.participantsPlaceholder")}
                value={audioCall.participants}
              />
              <input
                className="w-full bg-white rounded-lg px-3 py-2 text-body-sm"
                onChange={(e) => setAudioCall((c) => ({ ...c, phone: e.target.value }))}
                placeholder={t("conversations.audio.phonePlaceholder")}
                value={audioCall.phone}
              />
              <div className="flex gap-2">
                {recordingState === "recording" ? (
                  <>
                    <button
                      type="button"
                      onClick={handleStopRecording}
                      className="flex-1 py-2 bg-primary text-on-primary rounded-lg text-label-sm font-bold"
                    >
                      {t("conversations.audio.stop")}
                    </button>
                    <button
                      type="button"
                      onClick={handleCancelRecording}
                      className="px-3 py-2 bg-surface text-on-surface-variant rounded-lg text-label-sm font-bold"
                    >
                      {t("conversations.audio.cancel")}
                    </button>
                  </>
                ) : (
                  <button
                    type="button"
                    disabled={recordingState !== "idle"}
                    onClick={handleStartRecording}
                    className="w-full py-2 bg-primary text-on-primary rounded-lg text-label-sm font-bold disabled:opacity-60"
                  >
                    {recordingState === "idle" ? t("conversations.audio.start") : t(`conversations.audio.${recordingState}`)}
                  </button>
                )}
              </div>
              <p className="text-[11px] text-on-surface-variant">{t("conversations.audio.hint")}</p>
            </div>
          </div>
        ) : null}

        {showCreateForm ? (
          <div className="p-md border-b border-surface-container-highest">
            {error ? <p className="text-error text-[11px] mb-2">{error}</p> : null}
            <form onSubmit={handleCreateCall} className="space-y-2">
              <input
                className="w-full bg-surface-container-low rounded-lg px-3 py-2 text-body-sm"
                onChange={(e) => setNewCall((c) => ({ ...c, title: e.target.value }))}
                placeholder={t("conversations.form.titlePlaceholder")}
                value={newCall.title}
              />
              <input
                className="w-full bg-surface-container-low rounded-lg px-3 py-2 text-body-sm"
                onChange={(e) => setNewCall((c) => ({ ...c, participants: e.target.value }))}
                placeholder={t("conversations.form.participantsPlaceholder")}
                value={newCall.participants}
              />
              <textarea
                className="w-full bg-surface-container-low rounded-lg px-3 py-2 text-body-sm"
                onChange={(e) => setNewCall((c) => ({ ...c, transcript: e.target.value }))}
                placeholder={t("conversations.form.transcriptPlaceholder")}
                rows={3}
                value={newCall.transcript}
              />
              <button
                type="submit"
                disabled={isCreating || !newCall.title.trim() || !newCall.transcript.trim()}
                className="w-full py-2 bg-primary text-on-primary rounded-lg text-label-sm font-bold disabled:opacity-60"
              >
                {isCreating ? t("conversations.form.submitting") : t("conversations.form.submit")}
              </button>
            </form>
          </div>
        ) : null}

        <div className="flex-1 overflow-y-auto custom-scrollbar">
          {isLoading ? <p className="p-lg text-body-sm text-on-surface-variant">{t("common.loading")}</p> : null}
          {!isLoading && conversations.length === 0 ? (
            <p className="p-lg text-body-sm text-on-surface-variant">{t("conversations.emptyList")}</p>
          ) : null}
          {conversations.map((conversation) => {
            const active = conversation.id === selectedId;
            return (
              <button
                key={conversation.id}
                type="button"
                onClick={() => setSelectedId(conversation.id)}
                className={
                  "w-full text-left px-lg py-4 border-b border-surface-container-highest/50 transition-colors " +
                  (active
                    ? "bg-primary-container/5 border-l-4 border-l-primary"
                    : "hover:bg-surface-container-low")
                }
              >
                <div className="flex justify-between items-start mb-1">
                  <p className="font-label-md text-label-md font-bold text-on-surface truncate">
                    {conversation.title}
                  </p>
                  <span className="font-body-sm text-body-sm text-on-surface-variant shrink-0">
                    {formatTime(conversation.created_at, language)}
                  </span>
                </div>
                <div
                  className={
                    "flex gap-2 text-[10px] font-bold tracking-wider " +
                    (active ? "text-primary" : "text-on-surface-variant")
                  }
                >
                  <span className={(active ? "bg-primary/10" : "bg-surface-container-highest") + " px-1.5 py-0.5 rounded"}>
                    {conversation.source_type}
                  </span>
                  <span className={(active ? "bg-primary/10" : "bg-surface-container-highest") + " px-1.5 py-0.5 rounded uppercase"}>
                    {conversation.status}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </section>

      <section className="flex-1 flex flex-col bg-surface-container-lowest overflow-hidden">
        {isDetailLoading ? <p className="p-xl text-body-md text-on-surface-variant">{t("common.loading")}</p> : null}
        {!isDetailLoading && !detail ? (
          <p className="p-xl text-body-md text-on-surface-variant">{t("conversations.selectPrompt")}</p>
        ) : null}
        {!isDetailLoading && detail ? (
          <>
            <div className="p-xl border-b border-surface-container-highest bg-white">
              <div className="flex justify-between items-start mb-6">
                <div className="min-w-0 flex-1">
                  {isEditingTitle ? (
                    <form onSubmit={handleRenameConversation} className="flex items-center gap-2 mb-2 max-w-xl">
                      <input
                        autoFocus
                        className="min-w-0 flex-1 bg-surface-container-low border border-outline-variant/40 rounded-lg px-3 py-2 text-body-md"
                        onChange={(event) => setEditingTitleValue(event.target.value)}
                        placeholder={t("conversations.form.titlePlaceholder")}
                        value={editingTitle}
                      />
                      <button
                        type="submit"
                        disabled={isRenaming || !editingTitle.trim()}
                        className="w-10 h-10 rounded-lg bg-primary text-on-primary flex items-center justify-center disabled:opacity-60"
                        aria-label={t("common.save")}
                      >
                        <span className="material-symbols-outlined text-[18px]">{isRenaming ? "hourglass_top" : "check"}</span>
                      </button>
                      <button
                        type="button"
                        disabled={isRenaming}
                        onClick={() => {
                          setEditingTitle(false);
                          setEditingTitleValue("");
                        }}
                        className="w-10 h-10 rounded-lg border border-outline-variant/40 text-on-surface-variant bg-white flex items-center justify-center disabled:opacity-60"
                        aria-label={t("common.cancel")}
                      >
                        <span className="material-symbols-outlined text-[18px]">close</span>
                      </button>
                    </form>
                  ) : (
                    <div className="flex items-center gap-2 mb-2">
                      <h1 className="font-headline-lg text-headline-lg text-on-surface truncate">{detail.title}</h1>
                      <button
                        type="button"
                        onClick={startRenamingConversation}
                        className="w-9 h-9 rounded-lg text-on-surface-variant hover:bg-surface-container-high flex items-center justify-center shrink-0"
                        aria-label={t("common.edit")}
                      >
                        <span className="material-symbols-outlined text-[18px]">edit</span>
                      </button>
                    </div>
                  )}
                  <div className="flex items-center gap-4 text-on-surface-variant font-label-md text-label-md flex-wrap">
                    <div className="flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[18px]">calendar_today</span>
                      {formatDateTime(detail.created_at, language)}
                    </div>
                    {detail.participants.length > 0 ? (
                      <div className="flex items-center gap-1.5">
                        <span className="material-symbols-outlined text-[18px]">person</span>
                        {detail.participants.map((p) => p.display_name).join(", ")}
                      </div>
                    ) : null}
                    <span className="px-2 py-0.5 bg-surface-container-high rounded text-[11px] uppercase">
                      {detail.status}
                    </span>
                  </div>
                </div>
                <button
                  type="button"
                  disabled={isAnalyzing}
                  onClick={handleAnalyze}
                  className="flex items-center gap-2 px-4 py-2 bg-primary text-on-primary rounded-lg font-label-md text-label-md hover:opacity-90 active:scale-95 transition-all disabled:opacity-60 shrink-0"
                >
                  <span className="material-symbols-outlined text-[20px]">auto_awesome</span>
                  {isAnalyzing ? t("conversations.analyzing") : t("conversations.analyzeButton")}
                </button>
              </div>

              {error ? <p className="text-error text-body-sm mb-4">{error}</p> : null}
              {notice ? <p className="text-primary text-body-sm mb-4">{notice}</p> : null}

              {summaryText ? (
                <div className="bg-primary-container/5 rounded-xl p-lg border border-primary/10 relative overflow-hidden">
                  <div className="flex items-center gap-2 mb-3 min-w-0">
                    <span className="material-symbols-outlined text-primary text-[20px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                      smart_toy
                    </span>
                    <p className="font-label-sm text-label-sm uppercase tracking-widest text-primary">
                      {t("conversations.aiInsightSummary")}
                    </p>
                  </div>
                  <p className="font-body-md text-body-md text-on-surface leading-relaxed max-w-4xl whitespace-pre-wrap break-words">
                    {summaryText}
                  </p>
                </div>
              ) : (
                <p className="text-body-sm text-on-surface-variant">{t("conversations.noAnalysisYet")}</p>
              )}

              {extractedItems.length > 0 ? (
                <div className="mt-xl">
                  <p className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant mb-4">
                    {t("conversations.extractedItemsTitle")}
                  </p>
                  <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
                    {extractedItems.map((item, index) => (
                      <div
                        key={`${item.type}-${index}`}
                        className="flex items-start gap-2 px-3 py-2.5 bg-surface-container-high rounded-lg border border-surface-container-highest min-w-0"
                      >
                        <span className="material-symbols-outlined text-[18px] text-primary shrink-0 mt-0.5">
                          {EXTRACT_ICON[item.type] ?? "auto_awesome"}
                        </span>
                        <span className="font-label-md text-label-md leading-snug break-words min-w-0">
                          {item.title}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar p-xl transcript-container">
              <div className="max-w-4xl mx-auto space-y-8 pb-16">
                {detail.calls.length === 0 ? (
                  <p className="text-body-sm text-on-surface-variant">{t("conversations.noCallsInConversation")}</p>
                ) : null}
                {detail.calls.map((call) => (
                  <CallBlock
                    key={call.id}
                    call={call}
                    isBusy={activeCallId === call.id}
                    onDelete={() => handleDeleteCall(call.id)}
                  />
                ))}
              </div>
            </div>
          </>
        ) : null}
      </section>
    </div>
  );
}

function CallBlock({ call, isBusy, onDelete }: { call: Call; isBusy: boolean; onDelete: () => void }) {
  const { t } = useLanguage();
  const transcriptText = call.transcriptions[0]?.transcript_text ?? null;
  const turns = transcriptText ? parseTranscript(transcriptText) : [];

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <span className="px-2 py-0.5 bg-surface-container-high rounded text-[11px] text-on-surface-variant">
          {call.phone_number ?? t("conversations.textCallFallback")} · {call.status}
        </span>
        <button
          type="button"
          disabled={isBusy}
          onClick={onDelete}
          className="text-error text-[11px] font-bold hover:underline disabled:opacity-60"
        >
          {isBusy ? t("conversations.deleting") : t("conversations.deleteCallButton")}
        </button>
      </div>
      {turns.length > 0 ? (
        <div className="space-y-6">
          {turns.map((turn, index) => (
            <div className="flex gap-6" key={index}>
              <div className="flex-shrink-0 w-12 pt-1 text-right font-label-sm text-label-sm text-outline-variant font-mono">
                {String(index).padStart(2, "0")}:00
              </div>
              <div className="flex-1">
                {turn.speaker ? (
                  <p className="font-label-md text-label-md text-primary mb-1">{turn.speaker}</p>
                ) : null}
                <p className="font-body-md text-body-md text-on-surface leading-relaxed">{turn.text}</p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-body-sm text-on-surface-variant">{t("conversations.noTranscript")}</p>
      )}
    </div>
  );
}

function stopRecorder(recorder: MediaRecorder, chunks: Blob[]): Promise<Blob> {
  return new Promise((resolve) => {
    recorder.onstop = () => {
      const type = recorder.mimeType || "audio/webm";
      resolve(new Blob(chunks, { type }));
    };
    recorder.stop();
  });
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
  if (!conversationId) return null;
  const matches = jobs.filter(
    (candidate) =>
      candidate.source_type === "conversation" &&
      candidate.source_id === conversationId &&
      candidate.status === "completed",
  );
  if (matches.length === 0) return null;
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
