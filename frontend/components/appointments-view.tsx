"use client";

import { useEffect, useMemo, useState } from "react";
import { Appointment, cancelAppointment, listAppointments } from "@/lib/api";
import { useSession } from "@/lib/session";

export function AppointmentsView() {
  const { tokens } = useSession();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [activeId, setActiveId] = useState<string | null>(null);

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
      setAppointments(
        await listAppointments(tokens.accessToken, {
          startDate: now.toISOString(),
          endDate: end.toISOString(),
        }),
      );
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Randevular alinamadi.");
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
      locations: new Set(appointments.map((appointment) => appointment.location).filter(Boolean)).size,
    };
  }, [appointments]);

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

  return (
    <section className="moduleSurface">
      {error ? <p className="notice">{error}</p> : null}

      <div className="moduleGrid">
        <SummaryCard label="Yaklasan" value={summary.upcoming} />
        <SummaryCard label="Bugun" value={summary.today} />
        <SummaryCard label="Iptal" value={summary.cancelled} />
        <SummaryCard label="Lokasyon" value={summary.locations} />
      </div>

      <div className="panel">
        <div className="panelHeader">
          <h2>14 gunluk takvim</h2>
          <button disabled={isLoading} onClick={loadAppointments} type="button">
            {isLoading ? "Yukleniyor" : "Yenile"}
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
                  {activeId === appointment.id ? "Isleniyor" : "Iptal et"}
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
