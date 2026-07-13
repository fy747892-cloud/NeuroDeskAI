"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  addContactNote,
  ContactDetail,
  ContactMemory,
  ContactNote,
  ContactTimelineEvent,
  getContact,
  getContactMemory,
} from "@/lib/api";
import { useSession } from "@/lib/session";

const EVENT_ICON: Record<string, string> = {
  call: "call",
  email: "mail",
  appointment: "event",
  task: "task_alt",
  ai_note: "auto_awesome",
  ai_insight: "auto_awesome",
  note: "sticky_note_2",
};

const EVENT_LABEL: Record<string, string> = {
  call: "Görüşmeler",
  email: "E-postalar",
  appointment: "Randevular",
  task: "Görevler",
};

export function ContactDetailView({ contactId }: { contactId: string }) {
  const { tokens } = useSession();
  const [contact, setContact] = useState<ContactDetail | null>(null);
  const [memory, setMemory] = useState<ContactMemory | null>(null);
  const [notes, setNotes] = useState<ContactNote[]>([]);
  const [newNote, setNewNote] = useState("");
  const [timelineFilter, setTimelineFilter] = useState<string>("all");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [isAddingNote, setAddingNote] = useState(false);

  async function load() {
    if (!tokens?.accessToken) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const [contactDetail, contactMemory] = await Promise.all([
        getContact(tokens.accessToken, contactId),
        getContactMemory(tokens.accessToken, contactId),
      ]);
      setContact(contactDetail);
      setNotes(contactDetail.notes);
      setMemory(contactMemory);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Kişi bilgisi alınamadı.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [tokens?.accessToken, contactId]);

  async function handleAddNote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !newNote.trim()) {
      return;
    }

    setAddingNote(true);
    setError(null);
    try {
      const note = await addContactNote(tokens.accessToken, contactId, newNote.trim());
      setNotes((current) => [note, ...current]);
      setNewNote("");
    } catch (noteError) {
      setError(noteError instanceof Error ? noteError.message : "Not eklenemedi.");
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
    if (timelineFilter === "all") {
      return timeline;
    }
    return timeline.filter((event) => event.event_type === timelineFilter);
  }, [contact, timelineFilter]);

  if (isLoading && !contact) {
    return <p className="emptyState">Kişi bilgisi yükleniyor.</p>;
  }

  if (!contact) {
    return <p className="notice">{error ?? "Kişi bulunamadı."}</p>;
  }

  const initials = contact.full_name
    .split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <>
      <Link className="backLink" href="/kisiler">
        <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 16 }}>
          arrow_back
        </span>
        Kişi listesi
      </Link>

      {error ? <p className="notice">{error}</p> : null}

      <div className="contactDetailGrid">
        <div>
          <div className="contactProfileCard">
            <div className="contactAvatar">{initials || "?"}</div>
            <h2>{contact.full_name}</h2>
            <p className="contactRole">
              {[contact.title, contact.company].filter(Boolean).join(", ") || contact.status}
            </p>
            <div className="contactInfoList">
              {contact.email ? (
                <div>
                  <span className="material-symbols-outlined" aria-hidden="true">
                    mail
                  </span>
                  {contact.email}
                </div>
              ) : null}
              {contact.phone ? (
                <div>
                  <span className="material-symbols-outlined" aria-hidden="true">
                    call
                  </span>
                  {contact.phone}
                </div>
              ) : null}
              <div>
                <span className="material-symbols-outlined" aria-hidden="true">
                  calendar_today
                </span>
                Kayıt: {formatDate(contact.created_at)}
              </div>
            </div>
            <div className="contactActionRow">
              {contact.email ? (
                <a className="primaryBtn" href={`mailto:${contact.email}`}>
                  E-posta
                </a>
              ) : null}
              {contact.phone ? (
                <a className="ghostBtn" href={`tel:${contact.phone}`}>
                  Ara
                </a>
              ) : null}
            </div>
          </div>

          <div className="notesCard">
            <h4>Notlar</h4>
            {notes.length === 0 ? <p className="emptyState">Henüz not eklenmemiş.</p> : null}
            {notes.map((note) => (
              <div className="noteItem" key={note.id}>
                {note.note_text}
                <small>{formatDateTime(note.created_at)}</small>
              </div>
            ))}
            <form className="noteForm" onSubmit={handleAddNote}>
              <textarea
                onChange={(event) => setNewNote(event.target.value)}
                placeholder="Bu kişiyle ilgili bir not ekle"
                value={newNote}
              />
              <button disabled={isAddingNote || !newNote.trim()} type="submit">
                {isAddingNote ? "Ekleniyor" : "Not Ekle"}
              </button>
            </form>
          </div>
        </div>

        <div className="timelineCard">
          <div className="timelineHead">
            <h3 style={{ margin: 0 }}>Zaman Çizelgesi</h3>
            <div className="timelineFilters">
              <button
                className={timelineFilter === "all" ? "active" : ""}
                onClick={() => setTimelineFilter("all")}
                type="button"
              >
                Tümü
              </button>
              {eventTypes.map((type) => (
                <button
                  className={timelineFilter === type ? "active" : ""}
                  key={type}
                  onClick={() => setTimelineFilter(type)}
                  type="button"
                >
                  {EVENT_LABEL[type] ?? type}
                </button>
              ))}
            </div>
          </div>

          {filteredTimeline.length === 0 ? (
            <p className="emptyState">Bu kişi için zaman çizelgesi kaydı yok.</p>
          ) : (
            <div className="timelineList">
              {filteredTimeline.map((event) => (
                <TimelineRow key={event.id} event={event} />
              ))}
            </div>
          )}
        </div>

        <div>
          <div className="memoryCard">
            <h4>Açık Fırsat Değeri</h4>
            <strong>
              {memory ? memory.open_deals_total_value.toLocaleString("tr-TR") : "--"}
            </strong>
            <span>{memory ? `${memory.open_deals_count} açık fırsat` : "--"}</span>
          </div>

          <div className="memoryList">
            <h4>Müşteri Hafızası</h4>
            <div className="memoryRow">
              <span className="material-symbols-outlined" aria-hidden="true">
                forum
              </span>
              <div>
                <p>Son görüşme</p>
                <p>
                  {memory?.last_conversation
                    ? `${memory.last_conversation.title} · ${formatDate(memory.last_conversation.occurred_at)}`
                    : "Kayıt yok"}
                </p>
              </div>
            </div>
            <div className="memoryRow">
              <span className="material-symbols-outlined" aria-hidden="true">
                mail
              </span>
              <div>
                <p>Son e-posta</p>
                <p>
                  {memory?.last_email
                    ? `${memory.last_email.subject ?? "Konu yok"} · ${memory.last_email.received_at ? formatDate(memory.last_email.received_at) : ""}`
                    : "Kayıt yok"}
                </p>
              </div>
            </div>
            <div className="memoryRow">
              <span className="material-symbols-outlined" aria-hidden="true">
                event
              </span>
              <div>
                <p>Sonraki randevu</p>
                <p>
                  {memory?.next_appointment
                    ? `${memory.next_appointment.title} · ${formatDate(memory.next_appointment.start_at)}`
                    : "Planlanmış randevu yok"}
                </p>
              </div>
            </div>
            <div className="memoryRow">
              <span className="material-symbols-outlined" aria-hidden="true">
                task_alt
              </span>
              <div>
                <p>Bekleyen iş</p>
                <p>{memory ? `${memory.pending_items_count} açık görev` : "--"}</p>
              </div>
            </div>
            {memory?.last_topic ? (
              <div className="memoryRow">
                <span className="material-symbols-outlined" aria-hidden="true">
                  topic
                </span>
                <div>
                  <p>Son konu</p>
                  <p>{memory.last_topic}</p>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </>
  );
}

function TimelineRow({ event }: { event: ContactTimelineEvent }) {
  const icon = EVENT_ICON[event.event_type] ?? "history";
  const title = typeof event.event_metadata?.title === "string" ? event.event_metadata.title : event.event_type;
  const detail =
    typeof event.event_metadata?.summary === "string"
      ? event.event_metadata.summary
      : typeof event.event_metadata?.description === "string"
        ? event.event_metadata.description
        : null;

  return (
    <div className="timelineItem">
      <div className="timelineIcon">
        <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 18 }}>
          {icon}
        </span>
      </div>
      <div className="timelineBody">
        <div className="timelineTitleRow">
          <strong>{title}</strong>
          <span>{formatDateTime(event.occurred_at)}</span>
        </div>
        {detail ? <p>{detail}</p> : null}
        {event.source_type ? <p style={{ color: "var(--outline)" }}>Kaynak: {event.source_type}</p> : null}
      </div>
    </div>
  );
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("tr-TR", { day: "2-digit", month: "short", year: "numeric" }).format(
    new Date(value),
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
