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
  const [visibleMonth, setVisibleMonth] = useState(() => startOfMonth(new Date()));
  const [selectedDate, setSelectedDate] = useState<string>(dateKey(new Date()));
  const [newAppointment, setNewAppointment] = useState({
    description: "",
    endAt: "",
    location: "",
    startAt: "",
    title: "",
  });

  const grid = useMemo(() => getCalendarGrid(visibleMonth), [visibleMonth]);

  async function loadAppointments(month: Date) {
    if (!tokens?.accessToken) {
      return;
    }

    const cells = getCalendarGrid(month);
    const rangeStart = cells[0];
    const rangeEnd = new Date(cells[cells.length - 1]);
    rangeEnd.setDate(rangeEnd.getDate() + 1);

    setLoading(true);
    setError(null);
    try {
      const [nextAppointments, nextAccounts] = await Promise.all([
        listAppointments(tokens.accessToken, {
          startDate: rangeStart.toISOString(),
          endDate: rangeEnd.toISOString(),
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
    loadAppointments(visibleMonth);
  }, [tokens?.accessToken, visibleMonth]);

  const appointmentsByDay = useMemo(() => {
    const map = new Map<string, Appointment[]>();
    for (const appointment of appointments) {
      const key = dateKey(new Date(appointment.start_at));
      const existing = map.get(key) ?? [];
      existing.push(appointment);
      map.set(key, existing);
    }
    return map;
  }, [appointments]);

  const conflictDays = useMemo(() => {
    const conflicts = new Set<string>();
    for (const [day, items] of appointmentsByDay.entries()) {
      const active = items.filter((item) => item.status !== "cancelled");
      for (let i = 0; i < active.length; i += 1) {
        for (let j = i + 1; j < active.length; j += 1) {
          const a = active[i];
          const b = active[j];
          if (new Date(a.start_at) < new Date(b.end_at) && new Date(b.start_at) < new Date(a.end_at)) {
            conflicts.add(day);
          }
        }
      }
    }
    return conflicts;
  }, [appointmentsByDay]);

  const selectedDayAppointments = appointmentsByDay.get(selectedDate) ?? [];

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
        <div className="calendarHead">
          <h2>{formatMonthLabel(visibleMonth)}</h2>
          <div className="calendarNav">
            <button
              aria-label="Önceki ay"
              onClick={() => setVisibleMonth((month) => addMonths(month, -1))}
              type="button"
            >
              <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 18 }}>
                chevron_left
              </span>
            </button>
            <button
              aria-label="Sonraki ay"
              onClick={() => setVisibleMonth((month) => addMonths(month, 1))}
              type="button"
            >
              <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 18 }}>
                chevron_right
              </span>
            </button>
            <button disabled={isLoading} onClick={() => loadAppointments(visibleMonth)} type="button">
              {isLoading ? "Yükleniyor" : "Yenile"}
            </button>
          </div>
        </div>

        <div className="calendarGrid">
          {DAY_LABELS.map((label) => (
            <div className="calendarDayLabel" key={label}>
              {label}
            </div>
          ))}
          {grid.map((day) => {
            const key = dateKey(day);
            const isCurrentMonth = day.getMonth() === visibleMonth.getMonth();
            const dayAppointments = appointmentsByDay.get(key) ?? [];
            const hasConflict = conflictDays.has(key);
            const cellClass = [
              "calendarCell",
              !isCurrentMonth ? "muted" : "",
              key === dateKey(new Date()) ? "today" : "",
              key === selectedDate ? "selected" : "",
              hasConflict ? "conflict" : "",
            ]
              .filter(Boolean)
              .join(" ");

            return (
              <div className={cellClass} key={key} onClick={() => setSelectedDate(key)}>
                {hasConflict ? (
                  <span className="calendarWarnIcon material-symbols-outlined" aria-hidden="true" style={{ fontSize: 14 }}>
                    warning
                  </span>
                ) : null}
                <span>{day.getDate()}</span>
                {dayAppointments.slice(0, 2).map((appointment) => (
                  <span
                    className={appointment.status === "cancelled" ? "calendarChip cancelled" : "calendarChip"}
                    key={appointment.id}
                  >
                    {appointment.title}
                  </span>
                ))}
                {dayAppointments.length > 2 ? (
                  <span className="calendarMore">+{dayAppointments.length - 2} daha</span>
                ) : null}
              </div>
            );
          })}
        </div>

        {conflictDays.size > 0 ? (
          <div className="notice" style={{ marginTop: 16 }}>
            {conflictDays.size} günde çakışan randevu tespit edildi. Çakışma işaretli günlere tıklayıp
            detayları inceleyebilirsin.
          </div>
        ) : null}

        <div className="panelHeader" style={{ marginTop: 20 }}>
          <h2>{formatDayLabel(selectedDate)}</h2>
        </div>
        <div className="dataList">
          {isLoading ? <p className="emptyState">Randevular yukleniyor.</p> : null}
          {!isLoading && selectedDayAppointments.length === 0 ? (
            <p className="emptyState">Bu gün için randevu yok.</p>
          ) : null}
          {selectedDayAppointments.map((appointment) => (
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

const DAY_LABELS = ["Paz", "Pzt", "Sal", "Çar", "Per", "Cum", "Cmt"];

function startOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

function addMonths(date: Date, amount: number): Date {
  return new Date(date.getFullYear(), date.getMonth() + amount, 1);
}

function dateKey(date: Date): string {
  return `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
}

function getCalendarGrid(month: Date): Date[] {
  const firstOfMonth = new Date(month.getFullYear(), month.getMonth(), 1);
  const startOffset = firstOfMonth.getDay();
  const gridStart = new Date(month.getFullYear(), month.getMonth(), 1 - startOffset);
  return Array.from({ length: 42 }, (_, index) => {
    return new Date(gridStart.getFullYear(), gridStart.getMonth(), gridStart.getDate() + index);
  });
}

function formatMonthLabel(date: Date): string {
  return new Intl.DateTimeFormat("tr-TR", { month: "long", year: "numeric" }).format(date);
}

function formatDayLabel(key: string): string {
  const [year, month, day] = key.split("-").map(Number);
  const date = new Date(year, month, day);
  return new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    month: "long",
    weekday: "long",
  }).format(date);
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
