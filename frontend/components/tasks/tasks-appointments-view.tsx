"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import {
  Appointment,
  CalendarAccount,
  cancelAppointment,
  completeTask,
  connectGoogleCalendar,
  createAppointment,
  createTask,
  getPriorityQueue,
  listAppointments,
  listCalendarAccounts,
  PriorityQueue,
} from "@/lib/api";
import { useSession } from "@/lib/session";
import { Language, useLanguage } from "@/lib/i18n/context";
import { formatDateTime, formatTime } from "@/lib/format";

export function TasksAppointmentsView() {
  const { tokens } = useSession();
  const { t, language } = useLanguage();
  const dayLabels = [
    t("tasks.day.sun"),
    t("tasks.day.mon"),
    t("tasks.day.tue"),
    t("tasks.day.wed"),
    t("tasks.day.thu"),
    t("tasks.day.fri"),
    t("tasks.day.sat"),
  ];
  const [activeView, setActiveView] = useState<"list" | "calendar">("list");

  // Priority / task list state
  const [queue, setQueue] = useState<PriorityQueue | null>(null);
  const [isQueueLoading, setQueueLoading] = useState(true);
  const [busyItemId, setBusyItemId] = useState<string | null>(null);
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [isCreatingTask, setCreatingTask] = useState(false);
  const [newTask, setNewTask] = useState({ title: "", description: "", priority: "medium", dueAt: "" });

  // Calendar state
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [calendarAccounts, setCalendarAccounts] = useState<CalendarAccount[]>([]);
  const [isCalendarLoading, setCalendarLoading] = useState(true);
  const [visibleMonth, setVisibleMonth] = useState(() => startOfMonth(new Date()));
  const [selectedDate, setSelectedDate] = useState<string>(dateKey(new Date()));
  const [showApptForm, setShowApptForm] = useState(false);
  const [isCreatingAppt, setCreatingAppt] = useState(false);
  const [activeApptId, setActiveApptId] = useState<string | null>(null);
  const [newAppointment, setNewAppointment] = useState({
    title: "",
    startAt: "",
    endAt: "",
    location: "",
    description: "",
  });

  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const grid = useMemo(() => getCalendarGrid(visibleMonth), [visibleMonth]);

  const loadQueue = useCallback(async () => {
    if (!tokens?.accessToken) return;
    setQueueLoading(true);
    try {
      setQueue(await getPriorityQueue(tokens.accessToken));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : t("tasks.queueLoadError"));
    } finally {
      setQueueLoading(false);
    }
  }, [tokens?.accessToken]);

  const loadAppointments = useCallback(
    async (month: Date) => {
      if (!tokens?.accessToken) return;
      const cells = getCalendarGrid(month);
      const rangeStart = cells[0];
      const rangeEnd = new Date(cells[cells.length - 1]);
      rangeEnd.setDate(rangeEnd.getDate() + 1);

      setCalendarLoading(true);
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
        setError(loadError instanceof Error ? loadError.message : t("tasks.appointmentsLoadError"));
      } finally {
        setCalendarLoading(false);
      }
    },
    [tokens?.accessToken],
  );

  useEffect(() => {
    loadQueue();
  }, [loadQueue]);

  useEffect(() => {
    loadAppointments(visibleMonth);
  }, [loadAppointments, visibleMonth]);

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

  async function handleCompletePriorityItem(itemId: string) {
    if (!tokens?.accessToken) return;
    setBusyItemId(itemId);
    try {
      await completeTask(tokens.accessToken, itemId);
      await loadQueue();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : t("tasks.taskCompleteError"));
    } finally {
      setBusyItemId(null);
    }
  }

  async function handleCreateTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !newTask.title.trim()) return;
    setCreatingTask(true);
    setError(null);
    try {
      await createTask(tokens.accessToken, {
        title: newTask.title.trim(),
        description: newTask.description.trim() || null,
        priority: newTask.priority,
        due_at: newTask.dueAt ? new Date(newTask.dueAt).toISOString() : null,
      });
      setNewTask({ title: "", description: "", priority: "medium", dueAt: "" });
      setShowTaskForm(false);
      setNotice(t("tasks.taskCreated"));
      await loadQueue();
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : t("tasks.taskCreateError"));
    } finally {
      setCreatingTask(false);
    }
  }

  async function handleCancelAppointment(appointmentId: string) {
    if (!tokens?.accessToken) return;
    setActiveApptId(appointmentId);
    try {
      const updated = await cancelAppointment(tokens.accessToken, appointmentId);
      setAppointments((current) => current.map((item) => (item.id === updated.id ? updated : item)));
    } catch (cancelError) {
      setError(cancelError instanceof Error ? cancelError.message : t("tasks.appointmentCancelError"));
    } finally {
      setActiveApptId(null);
    }
  }

  async function handleConnectCalendar() {
    if (!tokens?.accessToken) return;
    setActiveApptId("calendar-connect");
    try {
      const account = await connectGoogleCalendar(tokens.accessToken);
      setCalendarAccounts((current) => [account, ...current]);
    } catch (connectError) {
      setError(connectError instanceof Error ? connectError.message : t("tasks.calendarConnectError"));
    } finally {
      setActiveApptId(null);
    }
  }

  async function handleCreateAppointment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !newAppointment.title.trim() || !newAppointment.startAt || !newAppointment.endAt) {
      return;
    }
    setCreatingAppt(true);
    setError(null);
    try {
      const appointment = await createAppointment(tokens.accessToken, {
        title: newAppointment.title.trim(),
        description: newAppointment.description.trim() || null,
        location: newAppointment.location.trim() || null,
        start_at: new Date(newAppointment.startAt).toISOString(),
        end_at: new Date(newAppointment.endAt).toISOString(),
      });
      setAppointments((current) => [appointment, ...current]);
      setNewAppointment({ title: "", startAt: "", endAt: "", location: "", description: "" });
      setShowApptForm(false);
      setNotice(t("tasks.appointmentCreated"));
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : t("tasks.appointmentCreateError"));
    } finally {
      setCreatingAppt(false);
    }
  }

  return (
    <div className="p-xl">
      <div className="flex flex-wrap items-center gap-xl mb-xl">
        <h2 className="font-headline-md text-headline-md font-black text-on-surface">{t("tasks.pageTitle")}</h2>
        <div className="flex bg-surface-container-high p-1 rounded-lg">
          <button
            type="button"
            onClick={() => setActiveView("list")}
            className={
              "px-4 py-1.5 rounded-md font-label-sm text-label-sm transition-all " +
              (activeView === "list" ? "bg-white shadow-sm text-primary" : "text-on-surface-variant hover:text-on-surface")
            }
          >
            {t("tasks.listView")}
          </button>
          <button
            type="button"
            onClick={() => setActiveView("calendar")}
            className={
              "px-4 py-1.5 rounded-md font-label-sm text-label-sm transition-all " +
              (activeView === "calendar" ? "bg-white shadow-sm text-primary" : "text-on-surface-variant hover:text-on-surface")
            }
          >
            {t("tasks.calendarView")}
          </button>
        </div>
      </div>

      {error ? <p className="text-error text-body-sm mb-md">{error}</p> : null}
      {notice ? <p className="text-primary text-body-sm mb-md">{notice}</p> : null}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-xl">
        <section className={"lg:col-span-5 flex flex-col gap-lg " + (activeView === "calendar" ? "hidden lg:flex" : "")}>
          <div className="flex items-center justify-between">
            <h3 className="font-headline-md text-headline-md">{t("tasks.priorityEngine")}</h3>
            <button
              type="button"
              onClick={() => setShowTaskForm((v) => !v)}
              className="flex items-center gap-2 text-primary font-label-md hover:underline"
            >
              <span className="material-symbols-outlined text-body-lg">add</span>
              {t("tasks.newTask")}
            </button>
          </div>

          {showTaskForm ? (
            <form onSubmit={handleCreateTask} className="glass-card p-lg rounded-xl space-y-2">
              <input
                className="w-full bg-white border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                onChange={(e) => setNewTask((current) => ({ ...current, title: e.target.value }))}
                placeholder={t("tasks.taskTitlePlaceholder")}
                value={newTask.title}
              />
              <input
                className="w-full bg-white border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                onChange={(e) => setNewTask((current) => ({ ...current, description: e.target.value }))}
                placeholder={t("tasks.descriptionPlaceholder")}
                value={newTask.description}
              />
              <div className="flex gap-2">
                <select
                  className="flex-1 bg-white border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                  onChange={(e) => setNewTask((current) => ({ ...current, priority: e.target.value }))}
                  value={newTask.priority}
                >
                  <option value="low">{t("tasks.priorityLow")}</option>
                  <option value="medium">{t("tasks.priorityMedium")}</option>
                  <option value="high">{t("tasks.priorityHigh")}</option>
                </select>
                <input
                  className="flex-1 bg-white border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                  onChange={(e) => setNewTask((current) => ({ ...current, dueAt: e.target.value }))}
                  type="datetime-local"
                  value={newTask.dueAt}
                />
              </div>
              <button
                type="submit"
                disabled={isCreatingTask || !newTask.title.trim()}
                className="w-full py-2 bg-primary text-on-primary rounded-lg text-label-sm font-bold disabled:opacity-60"
              >
                {isCreatingTask ? t("tasks.creating") : t("tasks.create")}
              </button>
            </form>
          ) : null}

          <div className="flex-1 overflow-y-auto space-y-md pr-2 max-h-[calc(100vh-320px)]">
            {isQueueLoading ? <p className="text-body-sm text-on-surface-variant">{t("common.loading")}</p> : null}
            {!isQueueLoading && !queue?.items.length ? (
              <p className="text-body-sm text-on-surface-variant">{t("tasks.noPrioritizedWork")}</p>
            ) : null}
            {queue?.items.map((item) => {
              const borderClass = item.score >= 80 ? "border-l-error" : item.priority === "high" ? "border-l-secondary" : "border-l-primary/30";
              const badgeClass = item.score >= 80 ? "bg-error-container text-on-error-container" : "bg-surface-container-highest text-on-surface-variant";
              return (
                <div
                  key={`${item.item_type}-${item.item_id}`}
                  className={`glass-card p-lg rounded-xl hover:shadow-md transition-shadow group flex items-start gap-md border-l-4 ${borderClass}`}
                >
                  {item.item_type === "task" ? (
                    <button
                      type="button"
                      disabled={busyItemId === item.item_id}
                      onClick={() => handleCompletePriorityItem(item.item_id)}
                      aria-label={t("dashboard.completeTaskAria")}
                      className="mt-1 w-5 h-5 rounded border-outline-variant border text-primary shrink-0 disabled:opacity-60"
                    />
                  ) : (
                    <span className="material-symbols-outlined text-primary mt-0.5 shrink-0">event</span>
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${badgeClass}`}>
                        {item.score >= 80 ? t("tasks.urgent") : item.priority}
                      </span>
                      <span className="text-body-sm text-outline shrink-0">
                        {item.due_at ? formatDateTime(item.due_at, language) : t("tasks.noDueDate")}
                      </span>
                    </div>
                    <h4 className="font-label-md text-on-surface group-hover:text-primary transition-colors truncate">
                      {item.title}
                    </h4>
                    {item.factors.length > 0 ? (
                      <p className="text-body-sm text-on-surface-variant mt-1 truncate">
                        {item.factors.map((factor) => factor.label).join(" · ")}
                      </p>
                    ) : null}
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        <section className={"lg:col-span-7 flex flex-col " + (activeView === "list" ? "hidden lg:flex" : "")}>
          <div className="flex items-center justify-between mb-lg flex-wrap gap-2">
            <div className="flex items-center gap-md">
              <h3 className="font-headline-md text-headline-md">{formatMonthLabel(visibleMonth, language)}</h3>
              <div className="flex gap-1">
                <button
                  type="button"
                  aria-label={t("tasks.previousMonth")}
                  onClick={() => setVisibleMonth((m) => addMonths(m, -1))}
                  className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-surface-container-high"
                >
                  <span className="material-symbols-outlined">chevron_left</span>
                </button>
                <button
                  type="button"
                  aria-label={t("tasks.nextMonth")}
                  onClick={() => setVisibleMonth((m) => addMonths(m, 1))}
                  className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-surface-container-high"
                >
                  <span className="material-symbols-outlined">chevron_right</span>
                </button>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setShowApptForm((v) => !v)}
              className="bg-surface-container-high text-on-surface-variant font-label-sm px-4 py-2 rounded-lg hover:bg-surface-container-highest transition-colors flex items-center gap-2"
            >
              <span className="material-symbols-outlined text-body-lg">add</span>
              {t("tasks.newAppointment")}
            </button>
          </div>

          {showApptForm ? (
            <form onSubmit={handleCreateAppointment} className="glass-card p-lg rounded-xl space-y-2 mb-lg">
              <input
                className="w-full bg-white border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                onChange={(e) => setNewAppointment((a) => ({ ...a, title: e.target.value }))}
                placeholder={t("tasks.titlePlaceholder")}
                value={newAppointment.title}
              />
              <div className="flex gap-2">
                <input
                  className="flex-1 bg-white border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                  onChange={(e) => setNewAppointment((a) => ({ ...a, startAt: e.target.value }))}
                  type="datetime-local"
                  value={newAppointment.startAt}
                />
                <input
                  className="flex-1 bg-white border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                  onChange={(e) => setNewAppointment((a) => ({ ...a, endAt: e.target.value }))}
                  type="datetime-local"
                  value={newAppointment.endAt}
                />
              </div>
              <input
                className="w-full bg-white border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                onChange={(e) => setNewAppointment((a) => ({ ...a, location: e.target.value }))}
                placeholder={t("tasks.locationPlaceholder")}
                value={newAppointment.location}
              />
              <button
                type="submit"
                disabled={isCreatingAppt || !newAppointment.title.trim() || !newAppointment.startAt || !newAppointment.endAt}
                className="w-full py-2 bg-primary text-on-primary rounded-lg text-label-sm font-bold disabled:opacity-60"
              >
                {isCreatingAppt ? t("tasks.creating") : t("tasks.create")}
              </button>
            </form>
          ) : null}

          <div className="calendar-grid">
            {dayLabels.map((label) => (
              <div key={label} className="bg-surface-container-low text-center py-2 font-label-sm text-on-surface-variant">
                {label}
              </div>
            ))}
            {grid.map((day) => {
              const key = dateKey(day);
              const isCurrentMonth = day.getMonth() === visibleMonth.getMonth();
              const dayAppointments = appointmentsByDay.get(key) ?? [];
              const hasConflict = conflictDays.has(key);
              const isToday = key === dateKey(new Date());
              const isSelected = key === selectedDate;
              return (
                <div
                  key={key}
                  onClick={() => setSelectedDate(key)}
                  className={
                    "calendar-day text-body-sm cursor-pointer relative " +
                    (!isCurrentMonth ? "opacity-30 " : "") +
                    (isToday ? "font-bold text-primary ring-1 ring-primary/20 ring-inset bg-primary/5 " : "") +
                    (isSelected ? "ring-2 ring-primary " : "") +
                    (hasConflict ? "conflict-glow" : "")
                  }
                >
                  {hasConflict ? (
                    <span className="material-symbols-outlined text-error text-sm absolute top-1 right-1" style={{ fontVariationSettings: "'FILL' 1" }}>
                      warning
                    </span>
                  ) : null}
                  <span>{day.getDate()}</span>
                  <div className="mt-1 space-y-0.5">
                    {dayAppointments.slice(0, 2).map((appt) => (
                      <div
                        key={appt.id}
                        className={
                          "text-[9px] p-1 rounded font-bold truncate " +
                          (appt.status === "cancelled"
                            ? "bg-surface-container-highest text-on-surface-variant line-through"
                            : "bg-primary text-on-primary")
                        }
                      >
                        {appt.title}
                      </div>
                    ))}
                    {dayAppointments.length > 2 ? (
                      <div className="text-[9px] text-on-surface-variant">
                        {t("tasks.daysMore", { count: dayAppointments.length - 2 })}
                      </div>
                    ) : null}
                  </div>
                </div>
              );
            })}
          </div>

          {conflictDays.size > 0 ? (
            <div className="mt-lg p-lg bg-error-container/20 border border-error/20 rounded-xl flex items-center gap-lg">
              <div className="w-12 h-12 rounded-full bg-error/10 flex items-center justify-center text-error shrink-0">
                <span className="material-symbols-outlined text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                  warning
                </span>
              </div>
              <div className="flex-1">
                <h5 className="font-bold text-error text-label-md">{t("tasks.scheduleConflictTitle")}</h5>
                <p className="text-body-sm text-on-surface-variant">
                  {t("tasks.conflictDetected", { count: conflictDays.size })}
                </p>
              </div>
            </div>
          ) : null}

          <div className="mt-lg">
            <h4 className="font-headline-md text-headline-md mb-md">{formatDayLabel(selectedDate, language)}</h4>
            <div className="space-y-md">
              {isCalendarLoading ? <p className="text-body-sm text-on-surface-variant">{t("common.loading")}</p> : null}
              {!isCalendarLoading && selectedDayAppointments.length === 0 ? (
                <p className="text-body-sm text-on-surface-variant">{t("tasks.noAppointmentsToday")}</p>
              ) : null}
              {selectedDayAppointments.map((appointment) => (
                <div
                  key={appointment.id}
                  className="bg-white rounded-xl border border-outline-variant/30 p-md flex items-center justify-between gap-md"
                >
                  <div className="min-w-0">
                    <p className="font-label-md text-on-surface truncate">{appointment.title}</p>
                    <p className="text-body-sm text-on-surface-variant truncate">
                      {formatDateTime(appointment.start_at, language)} - {formatTime(appointment.end_at, language)} ·{" "}
                      {appointment.location ?? t("tasks.online")}
                    </p>
                  </div>
                  <button
                    type="button"
                    disabled={appointment.status === "cancelled" || activeApptId === appointment.id}
                    onClick={() => handleCancelAppointment(appointment.id)}
                    className="text-error text-[12px] font-bold hover:underline disabled:opacity-60 shrink-0"
                  >
                    {appointment.status === "cancelled" ? t("tasks.cancelled") : t("tasks.cancel")}
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-lg flex items-center justify-between p-md bg-surface-container-low rounded-xl">
            <p className="text-body-sm text-on-surface-variant">
              {calendarAccounts.length > 0
                ? t("tasks.connectedCalendarsCount", { count: calendarAccounts.length })
                : t("tasks.noConnectedCalendar")}
            </p>
            <button
              type="button"
              disabled={activeApptId === "calendar-connect"}
              onClick={handleConnectCalendar}
              className="text-primary text-[12px] font-bold hover:underline disabled:opacity-60"
            >
              {t("tasks.connectGoogleCalendar")}
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}

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

function formatMonthLabel(date: Date, language: Language): string {
  return new Intl.DateTimeFormat(localeFor(language), { month: "long", year: "numeric" }).format(date);
}

function formatDayLabel(key: string, language: Language): string {
  const [year, month, day] = key.split("-").map(Number);
  const date = new Date(year, month, day);
  return new Intl.DateTimeFormat(localeFor(language), {
    day: "2-digit",
    month: "long",
    weekday: "long",
  }).format(date);
}

function localeFor(language: Language): string {
  return language === "tr" ? "tr-TR" : "en-US";
}
