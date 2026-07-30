"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import {
  addContactNote,
  ContactDetail,
  ContactMemory,
  ContactNote,
  ContactTimelineEvent,
  Deal,
  DEAL_STAGES,
  getContact,
  getContactMemory,
  listDeals,
} from "@/lib/api";
import { useSession } from "@/lib/session";
import { useLanguage } from "@/lib/i18n/context";
import { formatDate, formatDateTime, formatMoney, getInitials } from "@/lib/format";

const EVENT_ICON: Record<string, string> = {
  call: "call",
  email: "mail",
  appointment: "event",
  task: "task_alt",
  ai_note: "auto_awesome",
  ai_insight: "auto_awesome",
  note: "sticky_note_2",
};

const EVENT_LABEL_KEY: Record<string, string> = {
  call: "contactDetail.eventType.call",
  email: "contactDetail.eventType.email",
  appointment: "contactDetail.eventType.appointment",
  task: "contactDetail.eventType.task",
};

export function ContactDetailView({ contactId }: { contactId: string }) {
  const { tokens } = useSession();
  const { t, language } = useLanguage();
  const [contact, setContact] = useState<ContactDetail | null>(null);
  const [memory, setMemory] = useState<ContactMemory | null>(null);
  const [deals, setDeals] = useState<Deal[]>([]);
  const [notes, setNotes] = useState<ContactNote[]>([]);
  const [newNote, setNewNote] = useState("");
  const [timelineFilter, setTimelineFilter] = useState<string>("all");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [isAddingNote, setAddingNote] = useState(false);

  const load = useCallback(async () => {
    if (!tokens?.accessToken) return;
    setLoading(true);
    setError(null);
    try {
      const [contactDetail, contactMemory, allDeals] = await Promise.all([
        getContact(tokens.accessToken, contactId),
        getContactMemory(tokens.accessToken, contactId),
        listDeals(tokens.accessToken),
      ]);
      setContact(contactDetail);
      setNotes(contactDetail.notes);
      setMemory(contactMemory);
      setDeals(allDeals.filter((deal) => deal.contact_id === contactId));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : t("contactDetail.loadError"));
    } finally {
      setLoading(false);
    }
  }, [tokens?.accessToken, contactId]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleAddNote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !newNote.trim()) return;
    setAddingNote(true);
    setError(null);
    try {
      const note = await addContactNote(tokens.accessToken, contactId, newNote.trim());
      setNotes((current) => [note, ...current]);
      setNewNote("");
    } catch (noteError) {
      setError(noteError instanceof Error ? noteError.message : t("contactDetail.noteAddError"));
    } finally {
      setAddingNote(false);
    }
  }

  const eventTypes = useMemo(() => {
    const types = new Set<string>();
    for (const event of contact?.recent_timeline ?? []) {
      types.add(event.event_type);
    }
    return Array.from(types);
  }, [contact]);

  const filteredTimeline = useMemo(() => {
    const timeline = contact?.recent_timeline ?? [];
    if (timelineFilter === "all") return timeline;
    return timeline.filter((event) => event.event_type === timelineFilter);
  }, [contact, timelineFilter]);

  const openDeals = useMemo(() => deals.filter((deal) => deal.stage !== "won" && deal.stage !== "lost"), [deals]);

  if (isLoading && !contact) {
    return <p className="p-xl text-body-md text-on-surface-variant">{t("contactDetail.loadingContact")}</p>;
  }

  if (!contact) {
    return <p className="p-xl text-error text-body-md">{error ?? t("contactDetail.notFound")}</p>;
  }

  return (
    <div className="p-xl max-w-[1440px] mx-auto">
      <Link href="/kisiler" className="inline-flex items-center gap-1 text-primary text-body-sm mb-lg hover:underline">
        <span className="material-symbols-outlined text-[16px]">arrow_back</span>
        {t("contactDetail.backToList")}
      </Link>

      {error ? <p className="text-error text-body-sm mb-md">{error}</p> : null}

      <section className="mb-lg">
        <div className="relative overflow-hidden p-lg rounded-2xl bg-surface-container border border-primary/10 flex items-start gap-4 shadow-sm flex-wrap">
          <div className="bg-primary/10 p-3 rounded-xl shrink-0">
            <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>
              auto_awesome
            </span>
          </div>
          <div className="flex-1 min-w-[240px]">
            <h3 className="font-headline-md text-label-md text-primary mb-1 uppercase tracking-wider">
              {t("contactDetail.aiQuickRecap")}
            </h3>
            <p className="font-body-md text-on-surface-variant max-w-4xl leading-relaxed">
              {memory?.last_topic ? (
                <>
                  {t("contactDetail.lastTopicPrefix")}
                  <span className="font-bold text-on-surface">{memory.last_topic}</span>.{" "}
                </>
              ) : null}
              {memory?.next_appointment ? (
                <>
                  {t("contactDetail.nextAppointmentSummary", {
                    title: memory.next_appointment.title,
                    date: formatDate(memory.next_appointment.start_at, language),
                  })}
                </>
              ) : null}
              {memory && memory.pending_items_count > 0 ? (
                <>{t("contactDetail.pendingItemsSummary", { count: memory.pending_items_count })}</>
              ) : null}
              {!memory?.last_topic && !memory?.next_appointment && !memory?.pending_items_count
                ? t("contactDetail.noAiSummary")
                : null}
            </p>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-12 gap-lg">
        <div className="col-span-12 lg:col-span-3 space-y-lg">
          <div className="bg-surface-container-lowest border border-outline-variant p-xl rounded-2xl bento-card flex flex-col items-center text-center">
            <div className="w-20 h-20 rounded-2xl bg-primary-container/20 flex items-center justify-center text-primary font-bold text-2xl mb-md shrink-0">
              {getInitials(contact.full_name)}
            </div>
            <h2 className="font-headline-md text-headline-md text-on-surface">{contact.full_name}</h2>
            <p className="text-primary font-label-md mb-xl">
              {[contact.title, contact.company].filter(Boolean).join(", ") || contact.status}
            </p>
            <div className="w-full space-y-4 text-left">
              {contact.email ? (
                <div className="flex items-center gap-3">
                  <span className="material-symbols-outlined text-outline">mail</span>
                  <span className="text-body-md truncate">{contact.email}</span>
                </div>
              ) : null}
              {contact.phone ? (
                <div className="flex items-center gap-3">
                  <span className="material-symbols-outlined text-outline">call</span>
                  <span className="text-body-md">{contact.phone}</span>
                </div>
              ) : null}
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-outline">calendar_today</span>
                <span className="text-body-md">
                  {t("contactDetail.registeredPrefix")}
                  {formatDate(contact.created_at, language)}
                </span>
              </div>
            </div>
            <div className="w-full flex gap-2 mt-xl">
              {contact.email ? (
                <a href={`mailto:${contact.email}`} className="flex-1 bg-primary text-on-primary py-2 rounded-lg font-label-sm active:scale-95 transition-transform">
                  {t("common.email")}
                </a>
              ) : null}
              {contact.phone ? (
                <a href={`tel:${contact.phone}`} className="flex-1 border border-outline-variant text-on-surface-variant py-2 rounded-lg font-label-sm active:scale-95 transition-transform">
                  {t("contactDetail.callAction")}
                </a>
              ) : null}
            </div>
          </div>

          <div className="bg-surface-container-lowest border border-outline-variant p-lg rounded-2xl">
            <h4 className="font-label-sm text-label-sm uppercase tracking-widest text-outline mb-md">
              {t("contactDetail.personalNotes")}
            </h4>
            <div className="space-y-2 mb-md max-h-48 overflow-y-auto custom-scrollbar">
              {notes.length === 0 ? (
                <p className="text-body-sm text-on-surface-variant">{t("contactDetail.noNotesYet")}</p>
              ) : null}
              {notes.map((note) => (
                <div key={note.id} className="bg-surface-container-low p-3 rounded-xl text-body-sm text-on-surface-variant border-l-4 border-secondary">
                  {note.note_text}
                  <p className="text-[10px] text-outline mt-1">{formatDateTime(note.created_at, language)}</p>
                </div>
              ))}
            </div>
            <form onSubmit={handleAddNote} className="space-y-2">
              <textarea
                className="w-full bg-white border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                onChange={(e) => setNewNote(e.target.value)}
                placeholder={t("contactDetail.addNotePlaceholder")}
                rows={2}
                value={newNote}
              />
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={isAddingNote || !newNote.trim()}
                  className="flex-1 py-2 bg-primary text-on-primary rounded-lg text-label-sm font-bold disabled:opacity-60"
                >
                  {isAddingNote ? t("contactDetail.addingNote") : t("contactDetail.addNote")}
                </button>
                <button
                  type="button"
                  onClick={() => setNewNote("")}
                  className="px-3 py-2 bg-surface text-on-surface-variant rounded-lg text-label-sm font-bold"
                >
                  {t("common.clear")}
                </button>
              </div>
            </form>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-6 space-y-lg">
          <div className="bg-surface-container-lowest border border-outline-variant p-xl rounded-2xl min-h-[600px]">
            <div className="flex justify-between items-center mb-xl flex-wrap gap-2">
              <h3 className="font-headline-md text-headline-md">{t("contactDetail.unifiedTimeline")}</h3>
              <div className="flex gap-2 flex-wrap">
                <button
                  type="button"
                  onClick={() => setTimelineFilter("all")}
                  className={
                    "px-3 py-1.5 rounded-full text-label-sm border transition-colors " +
                    (timelineFilter === "all"
                      ? "bg-primary-container/10 text-primary border-primary/20"
                      : "text-on-surface-variant border-transparent hover:bg-surface-container-high")
                  }
                >
                  {t("common.all")}
                </button>
                {eventTypes.map((type) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => setTimelineFilter(type)}
                    className={
                      "px-3 py-1.5 rounded-full text-label-sm border transition-colors " +
                      (timelineFilter === type
                        ? "bg-primary-container/10 text-primary border-primary/20"
                        : "text-on-surface-variant border-transparent hover:bg-surface-container-high")
                    }
                  >
                    {EVENT_LABEL_KEY[type] ? t(EVENT_LABEL_KEY[type]) : type}
                  </button>
                ))}
              </div>
            </div>

            {filteredTimeline.length === 0 ? (
              <p className="text-body-sm text-on-surface-variant">{t("contactDetail.noTimelineRecords")}</p>
            ) : (
              <div className="space-y-8 relative before:content-[''] before:absolute before:left-[19px] before:top-2 before:bottom-2 before:w-px before:bg-outline-variant">
                {filteredTimeline.map((event) => (
                  <TimelineRow key={event.id} event={event} />
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="col-span-12 lg:col-span-3 space-y-lg">
          <div className="bg-primary text-on-primary p-xl rounded-2xl shadow-lg relative overflow-hidden">
            <div className="relative z-10">
              <h4 className="font-label-sm text-label-sm uppercase tracking-widest opacity-80 mb-2">
                {t("contactDetail.openDealValue")}
              </h4>
              <div className="text-3xl font-bold tracking-tight mb-2">
                {memory ? formatMoney(memory.open_deals_total_value, "TRY", language) : "--"}
              </div>
              <p className="text-body-sm opacity-80">
                {memory ? t("contactDetail.openDealsCountShort", { count: memory.open_deals_count }) : "--"}
              </p>
            </div>
            <span className="material-symbols-outlined absolute -right-8 -bottom-8 opacity-20 text-9xl">
              monetization_on
            </span>
          </div>

          <div className="bg-surface-container-lowest border border-outline-variant p-xl rounded-2xl">
            <h3 className="font-headline-md text-label-md mb-lg">{t("contactDetail.activeDeals")}</h3>
            {openDeals.length === 0 ? (
              <p className="text-body-sm text-on-surface-variant">{t("contactDetail.noOpenDeals")}</p>
            ) : (
              <div className="space-y-6">
                {openDeals.map((deal) => {
                  const stageIndex = DEAL_STAGES.indexOf(deal.stage as (typeof DEAL_STAGES)[number]);
                  const progress = stageIndex >= 0 ? ((stageIndex + 1) / DEAL_STAGES.length) * 100 : 10;
                  return (
                    <div key={deal.id} className="group">
                      <div className="flex justify-between mb-2">
                        <span className="font-label-md text-on-surface truncate">{deal.title}</span>
                        <span className="font-bold text-on-surface shrink-0 ml-2">
                          {formatMoney(deal.value, deal.currency, language)}
                        </span>
                      </div>
                      <div className="w-full bg-surface-container-high h-2 rounded-full mb-2">
                        <div className="bg-primary h-full rounded-full" style={{ width: `${progress}%` }} />
                      </div>
                      <div className="text-[11px] font-bold uppercase text-outline">{deal.stage}</div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="bg-surface-container-lowest border border-outline-variant p-lg rounded-2xl">
            <h4 className="font-label-sm text-label-sm uppercase tracking-widest text-outline mb-md">
              {t("contactDetail.customerMemory")}
            </h4>
            <div className="space-y-4">
              <MemoryRow icon="forum" label={t("contactDetail.memory.lastConversation")}>
                {memory?.last_conversation
                  ? `${memory.last_conversation.title} · ${formatDate(memory.last_conversation.occurred_at, language)}`
                  : t("contactDetail.memory.noRecord")}
              </MemoryRow>
              <MemoryRow icon="mail" label={t("contactDetail.memory.lastEmail")}>
                {memory?.last_email
                  ? `${memory.last_email.subject ?? t("contactDetail.memory.noSubject")}${memory.last_email.received_at ? " · " + formatDate(memory.last_email.received_at, language) : ""}`
                  : t("contactDetail.memory.noRecord")}
              </MemoryRow>
              <MemoryRow icon="event" label={t("contactDetail.memory.nextAppointment")}>
                {memory?.next_appointment
                  ? `${memory.next_appointment.title} · ${formatDate(memory.next_appointment.start_at, language)}`
                  : t("contactDetail.memory.noPlannedAppointment")}
              </MemoryRow>
              <MemoryRow icon="task_alt" label={t("contactDetail.memory.pendingWork")}>
                {memory ? t("contactDetail.memory.openTasksCount", { count: memory.pending_items_count }) : "--"}
              </MemoryRow>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function MemoryRow({ icon, label, children }: { icon: string; label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-3">
      <span className="material-symbols-outlined text-outline text-[20px] mt-0.5">{icon}</span>
      <div className="min-w-0">
        <p className="text-[11px] text-outline uppercase tracking-wider">{label}</p>
        <p className="text-body-sm text-on-surface truncate">{children}</p>
      </div>
    </div>
  );
}

function TimelineRow({ event }: { event: ContactTimelineEvent }) {
  const { t, language } = useLanguage();
  const icon = EVENT_ICON[event.event_type] ?? "history";
  const title = typeof event.event_metadata?.title === "string" ? event.event_metadata.title : event.event_type;
  const detail =
    typeof event.event_metadata?.summary === "string"
      ? event.event_metadata.summary
      : typeof event.event_metadata?.description === "string"
        ? event.event_metadata.description
        : null;

  return (
    <div className="relative pl-12">
      <div className="absolute left-0 top-0 w-10 h-10 rounded-full bg-surface-container-high flex items-center justify-center z-10 border-4 border-surface-container-lowest">
        <span className="material-symbols-outlined text-primary text-[20px]">{icon}</span>
      </div>
      <div className="flex justify-between mb-1 flex-wrap gap-1">
        <span className="font-label-md text-on-surface">{title}</span>
        <span className="text-body-sm text-outline">{formatDateTime(event.occurred_at, language)}</span>
      </div>
      {detail ? <p className="text-body-md text-on-surface-variant">{detail}</p> : null}
      {event.source_type ? (
        <p className="text-[11px] text-outline mt-1">
          {t("contactDetail.sourcePrefix")}
          {event.source_type}
        </p>
      ) : null}
    </div>
  );
}
