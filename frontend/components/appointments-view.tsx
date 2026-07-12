"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  Appointment,
  CalendarAccount,
  cancelAppointment,
  connectGoogleCalendar,
  createAppointment,
  listAppointments,
  listCalendarAccounts,
} from "@/lib/api";
import { useSession } from "@/lib/session";

export function AppointmentsView() {
  const { tokens } = useSession();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [calendarAccounts, setCalendarAccounts] = useState<CalendarAccount[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [isCreating, setCreating] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [newAppointment, setNewAppointment] = useState({
    description: "",
    endAt: "",
    location: "",
    startAt: "",
    title: "",
  });

  async function loadAppointments() {
    if (!tokens?.accessToken) {
      return;
    }

    const now = new Date();
    const end = new Date(now);
    end.setDate(now.getDate() + 14);

    setLoading(true);
    setError(null);
    try {
      const [nextAppointments, nextAccounts] = await Promise.all([
        listAppointments(tokens.accessToken, {
          startDate: now.toISOString(),
          endDate: end.toISOString(),
        }),
        listCalendarAccounts(tokens.accessToken),
      ]);
      setAppointments(nextAppointments);
      setCalendarAccounts(nextAccounts);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Randevular alınamadı.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAppointments();
  }, [tokens?.accessToken]);

  const summary = useMemo(() => {
    return {
      upcoming: appointments.filter((appointment) => appointment.status !== "cancelled").length,
      today: appointments.filter((appointment) => isToday(appointment.start_at)).length,
      cancelled: appointments.filter((appointment) => appointment.status === "cancelled").length,
      calendars: calendarAccounts.length,
    };
  }, [appointments, calendarAccounts.length]);

  async function handleCancel(appointmentId: string) {
    if (!tokens?.accessToken) {
      return;
    }

    setActiveId(appointmentId);
    setError(null);
    try {
      const updatedAppointment = await cancelAppointment(tokens.accessToken, appointmentId);
      setAppointments((currentAppointments) =>
        currentAppointments.map((appointment) =>
          appointment.id === updatedAppointment.id ? updatedAppointment : appointment,
        ),
      );
    } catch (cancelError) {
      setError(cancelError instanceof Error ? cancelError.message : "Randevu iptal edilemedi.");
    } finally {
      setActiveId(null);
    }
  }

  async function handleConnectCalendar() {
    if (!tokens?.accessToken) {
      return;
    }

    setActiveId("calendar-connect");
    setError(null);
    try {
      const account = await connectGoogleCalendar(tokens.accessToken);
      setCalendarAccounts((currentAccounts) => [account, ...currentAccounts]);
    } catch (connectError) {
      setError(connectError instanceof Error ? connectError.message : "Takvim baglanamadi.");
    } finally {
      setActiveId(null);
    }
  }

  async function handleCreateAppointment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !newAppointment.title.trim() || !newAppointment.startAt || !newAppointment.endAt) {
      return;
    }

    setCreating(true);
    setError(null);
    setNotice(null);
    try {
      const appointment = await createAppointment(tokens.accessToken, {
        title: newAppointment.title.trim(),
        description: newAppointment.description.trim() || null,
        location: newAppointment.location.trim() || null,
        start_at: new Date(newAppointment.startAt).toISOString(),
        end_at: new Date(newAppointment.endAt).toISOString(),
      });
      setAppointments((currentAppointments) => [appointment, ...currentAppointments]);
      setNewAppointment({ description: "", endAt: "", location: "", startAt: "", title: "" });
      setNotice("Randevu oluşturuldu.");
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Randevu oluşturulamadı.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <section className="moduleSurface">
      {error ? <p className="notice">{error}</p> : null}
      {notice ? <p className="notice success">{notice}</p> : null}

      <div className="moduleGrid">
        <SummaryCard label="Yaklasan" value={summary.upcoming} />
        <SummaryCard label="Bugün" value={summary.today} />
        <SummaryCard label="İptal" value={summary.cancelled} />
        <SummaryCard label="Takvim" value={summary.calendars} />
      </div>

      <div className="panel">
        <div className="panelHeader">
          <h2>Yeni randevu</h2>
          <span className="tag">Manual</span>
        </div>
        <form className="createForm" onSubmit={handleCreateAppointment}>
          <label>
            Başlık
            <input
              onChange={(event) =>
                setNewAppointment((appointment) => ({ ...appointment, title: event.target.value }))
              }
              placeholder="Kontrol görüşmesi"
              value={newAppointment.title}
            />
          </label>
          <label>
            Baslangic
            <input
              onChange={(event) =>
                setNewAppointment((appointment) => ({ ...appointment, startAt: event.target.value }))
              }
              type="datetime-local"
              value={newAppointment.startAt}
            />
          </label>
          <label>
            Bitis
            <input
              onChange={(event) =>
                setNewAppointment((appointment) => ({ ...appointment, endAt: event.target.value }))
              }
              type="datetime-local"
              value={newAppointment.endAt}
            />
          </label>
          <label>
            Lokasyon
            <input
              onChange={(event) =>
                setNewAppointment((appointment) => ({ ...appointment, location: event.target.value }))
              }
              placeholder="Online"
              value={newAppointment.location}
            />
          </label>
          <button
            disabled={
              isCreating ||
              !newAppointment.title.trim() ||
              !newAppointment.startAt ||
              !newAppointment.endAt
            }
            type="submit"
          >
            {isCreating ? "Oluşturuluyor" : "Oluştur"}
          </button>
        </form>
      </div>

      <div className="panel">
        <div className="panelHeader">
          <h2>Takvim hesaplari</h2>
          <button
            disabled={activeId === "calendar-connect"}
            onClick={handleConnectCalendar}
            type="button"
          >
            Google bagla
          </button>
        </div>
        <div className="dataList">
          {calendarAccounts.length === 0 ? <p className="emptyState">Bagli takvim hesabi yok.</p> : null}
          {calendarAccounts.map((account) => (
            <article className="dataRow" key={account.id}>
              <div>
                <div className="rowTitle">
                  <h3>{account.provider}</h3>
                  <span>{account.status}</span>
                </div>
                <p>{account.external_account_id ?? "Harici hesap id yok."}</p>
                <small>{account.connected_at ? formatDateTime(account.connected_at) : "Baglanti bekliyor"}</small>
              </div>
            </article>
          ))}
        </div>
      </div>

      <div className="panel">
        <div className="panelHeader">
          <h2>14 günlük takvim</h2>
          <button disabled={isLoading} onClick={loadAppointments} type="button">
            {isLoading ? "Yükleniyor" : "Yenile"}
          </button>
        </div>

        <div className="dataList">
          {isLoading ? <p className="emptyState">Randevular yukleniyor.</p> : null}
          {!isLoading && appointments.length === 0 ? (
            <p className="emptyState">Yaklasan randevu bulunmuyor.</p>
          ) : null}
          {appointments.map((appointment) => (
            <article className="dataRow" key={appointment.id}>
              <div>
                <div className="rowTitle">
                  <h3>{appointment.title}</h3>
                  <span>{appointment.status}</span>
                </div>
                <p>{appointment.description ?? appointment.location ?? "Detay eklenmemis."}</p>
                <small>
                  {formatDateTime(appointment.start_at)} - {formatTime(appointment.end_at)}
                </small>
              </div>
              <div className="rowActions">
                <span className={appointment.status === "cancelled" ? "statusPill danger" : "statusPill"}>
                  {appointment.location ?? appointment.timezone ?? "Online"}
                </span>
                <button
                  disabled={appointment.status === "cancelled" || activeId === appointment.id}
                  onClick={() => handleCancel(appointment.id)}
                  type="button"
                >
                  {activeId === appointment.id ? "İşleniyor" : "İptal et"}
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

function formatTime(value: string): string {
  return new Intl.DateTimeFormat("tr-TR", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function isToday(value: string): boolean {
  const date = new Date(value);
  const today = new Date();
  return (
    date.getDate() === today.getDate() &&
    date.getMonth() === today.getMonth() &&
    date.getFullYear() === today.getFullYear()
  );
}
