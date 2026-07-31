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
  deleteAppointment,
  deleteTask,
  getPriorityQueue,
  listAppointments,
  listCalendarAccounts,
  PriorityQueue,
  updateAppointment,
  updateTask,
} from "@/lib/api";
import { useSession } from "@/lib/session";
import { Language, useLanguage } from "@/lib/i18n/context";
import { useToast } from "@/lib/toast";
import { Skeleton, SkeletonList } from "@/components/shell/skeleton";
import { EmptyState } from "@/components/shell/empty-state";
import { formatDateTime, formatTime } from "@/lib/format";
import { deferredExecute, UNDO_WINDOW_MS } from "@/lib/undo";

export function TasksAppointmentsView() {
  const { tokens } = useSession();
  const { t, language } = useLanguage();
  const { showToast } = useToast();
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
  const [newTask, setNewTask] = useState({
    title: "",
    description: "",
    priority: "medium",
    dueAt: "",
    repeat: "none",
    repeatCount: "4",
  });
  const [editingTaskId, setEditingTaskId] = useState<string | null>(null);
  const [taskEditForm, setTaskEditForm] = useState({ title: "", priority: "medium", dueAt: "" });
  const [isSavingTaskEdit, setSavingTaskEdit] = useState(false);
  const [selectedTaskIds, setSelectedTaskIds] = useState<Set<string>>(new Set());
  const [taskSearch, setTaskSearch] = useState("");
  const [priorityFilter, setPriorityFilter] = useState<"all" | "low" | "medium" | "high">("all");

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
    repeat: "none",
    repeatCount: "4",
  });
  const [editingApptId, setEditingApptId] = useState<string | null>(null);
  const [apptEditForm, setApptEditForm] = useState({ title: "", startAt: "", endAt: "", location: "" });
  const [isSavingApptEdit, setSavingApptEdit] = useState(false);

  const [error, setError] = useState<string | null>(null);

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

  function handleCompletePriorityItem(itemId: string) {
    if (!tokens?.accessToken || !queue) return;
    const accessToken = tokens.accessToken;
    const previousQueue = queue;

    setQueue((current) =>
      current ? { ...current, items: current.items.filter((item) => item.item_id !== itemId) } : current,
    );

    const pending = deferredExecute(async () => {
      try {
        await completeTask(accessToken, itemId);
      } catch (actionError) {
        setQueue(previousQueue);
        setError(actionError instanceof Error ? actionError.message : t("tasks.taskCompleteError"));
      }
    });

    showToast(t("tasks.taskCompletedToast"), "success", {
      duration: UNDO_WINDOW_MS,
      action: {
        label: t("common.undo"),
        onClick: () => {
          pending.cancel();
          setQueue(previousQueue);
        },
      },
    });
  }

  async function handleCreateTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !newTask.title.trim()) return;
    setCreatingTask(true);
    setError(null);
    try {
      const repeat = repeatToPayload(newTask.repeat, newTask.repeatCount);
      await createTask(tokens.accessToken, {
        title: newTask.title.trim(),
        description: newTask.description.trim() || null,
        priority: newTask.priority,
        due_at: newTask.dueAt ? new Date(newTask.dueAt).toISOString() : null,
        repeat_count: repeat.repeat_count,
        repeat_interval_days: repeat.repeat_interval_days,
      });
      setNewTask({ title: "", description: "", priority: "medium", dueAt: "", repeat: "none", repeatCount: "4" });
      setShowTaskForm(false);
      showToast(t("tasks.taskCreated"), "success");
      await loadQueue();
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : t("tasks.taskCreateError"));
    } finally {
      setCreatingTask(false);
    }
  }

  function startEditingTask(item: PriorityQueue["items"][number]) {
    setEditingTaskId(item.item_id);
    setTaskEditForm({
      title: item.title,
      priority: item.priority,
      dueAt: item.due_at ? toDateTimeLocal(item.due_at) : "",
    });
    setError(null);
  }

  async function handleSaveTaskEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !editingTaskId || !taskEditForm.title.trim()) return;
    setSavingTaskEdit(true);
    setError(null);
    try {
      await updateTask(tokens.accessToken, editingTaskId, {
        title: taskEditForm.title.trim(),
        priority: taskEditForm.priority,
        due_at: taskEditForm.dueAt ? new Date(taskEditForm.dueAt).toISOString() : null,
      });
      setEditingTaskId(null);
      showToast(t("tasks.taskUpdated"), "success");
      await loadQueue();
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : t("tasks.taskUpdateError"));
    } finally {
      setSavingTaskEdit(false);
    }
  }

  function handleDeleteTask(itemId: string) {
    if (!tokens?.accessToken || !queue) return;
    const accessToken = tokens.accessToken;
    const previousQueue = queue;
    setError(null);

    setQueue((current) =>
      current ? { ...current, items: current.items.filter((item) => item.item_id !== itemId) } : current,
    );

    const pending = deferredExecute(async () => {
      try {
        await deleteTask(accessToken, itemId);
      } catch (deleteError) {
        setQueue(previousQueue);
        setError(deleteError instanceof Error ? deleteError.message : t("tasks.taskDeleteError"));
      }
    });

    showToast(t("tasks.taskDeletedToast"), "success", {
      duration: UNDO_WINDOW_MS,
      action: {
        label: t("common.undo"),
        onClick: () => {
          pending.cancel();
          setQueue(previousQueue);
        },
      },
    });
  }

  const filteredQueueItems = useMemo(() => {
    if (!queue) return [];
    const query = taskSearch.trim().toLowerCase();
    return queue.items.filter((item) => {
      if (query && !item.title.toLowerCase().includes(query)) return false;
      if (priorityFilter !== "all" && item.item_type === "task" && item.priority !== priorityFilter) return false;
      return true;
    });
  }, [queue, taskSearch, priorityFilter]);

  const taskIds = useMemo(
    () => filteredQueueItems.filter((item) => item.item_type === "task").map((item) => item.item_id),
    [filteredQueueItems],
  );

  function toggleTaskSelected(itemId: string) {
    setSelectedTaskIds((current) => {
      const next = new Set(current);
      if (next.has(itemId)) next.delete(itemId);
      else next.add(itemId);
      return next;
    });
  }

  function toggleSelectAllTasks() {
    setSelectedTaskIds((current) => (current.size === taskIds.length ? new Set() : new Set(taskIds)));
  }

  function handleBulkCompleteTasks() {
    if (!tokens?.accessToken || selectedTaskIds.size === 0 || !queue) return;
    const accessToken = tokens.accessToken;
    const ids = Array.from(selectedTaskIds);
    const previousQueue = queue;
    setError(null);

    setQueue((current) =>
      current ? { ...current, items: current.items.filter((item) => !selectedTaskIds.has(item.item_id)) } : current,
    );
    setSelectedTaskIds(new Set());

    const pending = deferredExecute(async () => {
      const results = await Promise.allSettled(ids.map((id) => completeTask(accessToken, id)));
      const failedCount = results.filter((result) => result.status === "rejected").length;
      if (failedCount > 0) {
        await loadQueue();
        showToast(t("tasks.bulk.completePartialError", { count: failedCount }), "error");
      }
    });

    showToast(t("tasks.bulk.completed", { count: ids.length }), "success", {
      duration: UNDO_WINDOW_MS,
      action: {
        label: t("common.undo"),
        onClick: () => {
          pending.cancel();
          setQueue(previousQueue);
        },
      },
    });
  }

  function handleBulkDeleteTasks() {
    if (!tokens?.accessToken || selectedTaskIds.size === 0 || !queue) return;
    const accessToken = tokens.accessToken;
    const ids = Array.from(selectedTaskIds);
    const previousQueue = queue;
    setError(null);

    setQueue((current) =>
      current ? { ...current, items: current.items.filter((item) => !selectedTaskIds.has(item.item_id)) } : current,
    );
    setSelectedTaskIds(new Set());

    const pending = deferredExecute(async () => {
      const results = await Promise.allSettled(ids.map((id) => deleteTask(accessToken, id)));
      const failedCount = results.filter((result) => result.status === "rejected").length;
      if (failedCount > 0) {
        await loadQueue();
        showToast(t("tasks.bulk.deletePartialError", { count: failedCount }), "error");
      }
    });

    showToast(t("tasks.bulk.deleted", { count: ids.length }), "success", {
      duration: UNDO_WINDOW_MS,
      action: {
        label: t("common.undo"),
        onClick: () => {
          pending.cancel();
          setQueue(previousQueue);
        },
      },
    });
  }

  function handleCancelAppointment(appointmentId: string) {
    if (!tokens?.accessToken) return;
    const accessToken = tokens.accessToken;
    const original = appointments.find((item) => item.id === appointmentId);
    if (!original) return;

    setAppointments((current) =>
      current.map((item) => (item.id === appointmentId ? { ...item, status: "cancelled" } : item)),
    );

    const pending = deferredExecute(async () => {
      try {
        const updated = await cancelAppointment(accessToken, appointmentId);
        setAppointments((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      } catch (cancelError) {
        setAppointments((current) => current.map((item) => (item.id === appointmentId ? original : item)));
        setError(cancelError instanceof Error ? cancelError.message : t("tasks.appointmentCancelError"));
      }
    });

    showToast(t("tasks.appointmentCancelledToast"), "success", {
      duration: UNDO_WINDOW_MS,
      action: {
        label: t("common.undo"),
        onClick: () => {
          pending.cancel();
          setAppointments((current) => current.map((item) => (item.id === appointmentId ? original : item)));
        },
      },
    });
  }

  function handleDeleteAppointment(appointmentId: string) {
    if (!tokens?.accessToken) return;
    const accessToken = tokens.accessToken;
    const previousAppointments = appointments;
    setError(null);

    setAppointments((current) => current.filter((item) => item.id !== appointmentId));

    const pending = deferredExecute(async () => {
      try {
        await deleteAppointment(accessToken, appointmentId);
      } catch (deleteError) {
        setAppointments(previousAppointments);
        setError(deleteError instanceof Error ? deleteError.message : t("tasks.appointmentDeleteError"));
      }
    });

    showToast(t("tasks.appointmentDeletedToast"), "success", {
      duration: UNDO_WINDOW_MS,
      action: {
        label: t("common.undo"),
        onClick: () => {
          pending.cancel();
          setAppointments(previousAppointments);
        },
      },
    });
  }

  function startEditingAppointment(appointment: Appointment) {
    setEditingApptId(appointment.id);
    setApptEditForm({
      title: appointment.title,
      startAt: toDateTimeLocal(appointment.start_at),
      endAt: toDateTimeLocal(appointment.end_at),
      location: appointment.location ?? "",
    });
    setError(null);
  }

  async function handleSaveAppointmentEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !editingApptId || !apptEditForm.title.trim()) return;
    setSavingApptEdit(true);
    setError(null);
    try {
      const updated = await updateAppointment(tokens.accessToken, editingApptId, {
        title: apptEditForm.title.trim(),
        start_at: apptEditForm.startAt ? new Date(apptEditForm.startAt).toISOString() : undefined,
        end_at: apptEditForm.endAt ? new Date(apptEditForm.endAt).toISOString() : undefined,
        location: apptEditForm.location.trim() || null,
      });
      setAppointments((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      setEditingApptId(null);
      showToast(t("tasks.appointmentUpdated"), "success");
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : t("tasks.appointmentUpdateError"));
    } finally {
      setSavingApptEdit(false);
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
      const repeat = repeatToPayload(newAppointment.repeat, newAppointment.repeatCount);
      const appointment = await createAppointment(tokens.accessToken, {
        title: newAppointment.title.trim(),
        description: newAppointment.description.trim() || null,
        location: newAppointment.location.trim() || null,
        start_at: new Date(newAppointment.startAt).toISOString(),
        end_at: new Date(newAppointment.endAt).toISOString(),
        repeat_count: repeat.repeat_count,
        repeat_interval_days: repeat.repeat_interval_days,
      });
      setAppointments((current) => [appointment, ...current]);
      setNewAppointment({ title: "", startAt: "", endAt: "", location: "", description: "", repeat: "none", repeatCount: "4" });
      setShowApptForm(false);
      showToast(t("tasks.appointmentCreated"), "success");
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
              (activeView === "list" ? "bg-surface-container-lowest shadow-sm text-primary" : "text-on-surface-variant hover:text-on-surface")
            }
          >
            {t("tasks.listView")}
          </button>
          <button
            type="button"
            onClick={() => setActiveView("calendar")}
            className={
              "px-4 py-1.5 rounded-md font-label-sm text-label-sm transition-all " +
              (activeView === "calendar" ? "bg-surface-container-lowest shadow-sm text-primary" : "text-on-surface-variant hover:text-on-surface")
            }
          >
            {t("tasks.calendarView")}
          </button>
        </div>
      </div>

      {error ? <p className="text-error text-body-sm mb-md">{error}</p> : null}

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

          <div className="flex items-center gap-2 flex-wrap">
            <div className="relative flex-1 min-w-[160px]">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-[16px]">
                search
              </span>
              <input
                className="w-full bg-surface-container-low border-none rounded-full pl-9 pr-4 py-1.5 text-body-sm"
                onChange={(e) => setTaskSearch(e.target.value)}
                placeholder={t("tasks.searchPlaceholder")}
                value={taskSearch}
              />
            </div>
            <select
              className="bg-surface-container-low border-none rounded-lg px-3 py-1.5 text-body-sm text-on-surface-variant"
              onChange={(e) => setPriorityFilter(e.target.value as typeof priorityFilter)}
              value={priorityFilter}
              aria-label={t("tasks.priorityFilterAria")}
            >
              <option value="all">{t("tasks.priorityFilterAll")}</option>
              <option value="low">{t("tasks.priorityLow")}</option>
              <option value="medium">{t("tasks.priorityMedium")}</option>
              <option value="high">{t("tasks.priorityHigh")}</option>
            </select>
          </div>

          {!isQueueLoading && taskIds.length > 0 ? (
            <div className="flex items-center gap-md flex-wrap">
              <label className="flex items-center gap-2 text-body-sm text-on-surface-variant cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={selectedTaskIds.size === taskIds.length}
                  onChange={toggleSelectAllTasks}
                  aria-label={t("tasks.bulk.selectAll")}
                />
                {t("tasks.bulk.selectAll")}
              </label>
              {selectedTaskIds.size > 0 ? (
                <div className="flex items-center gap-3 bg-primary-container/10 border border-primary/20 rounded-lg px-3 py-1.5">
                  <span className="text-body-sm text-primary font-bold">
                    {t("tasks.bulk.selectedCount", { count: selectedTaskIds.size })}
                  </span>
                  <button
                    type="button"
                    onClick={handleBulkCompleteTasks}
                    className="text-primary text-[12px] font-bold hover:underline"
                  >
                    {t("tasks.bulk.completeSelected")}
                  </button>
                  <button
                    type="button"
                    onClick={handleBulkDeleteTasks}
                    className="text-error text-[12px] font-bold hover:underline"
                  >
                    {t("tasks.bulk.deleteSelected")}
                  </button>
                  <button
                    type="button"
                    onClick={() => setSelectedTaskIds(new Set())}
                    className="text-on-surface-variant text-[12px] font-bold hover:underline"
                  >
                    {t("common.clear")}
                  </button>
                </div>
              ) : null}
            </div>
          ) : null}

          {showTaskForm ? (
            <form onSubmit={handleCreateTask} className="glass-card p-lg rounded-xl space-y-2">
              <input
                className="w-full bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                onChange={(e) => setNewTask((current) => ({ ...current, title: e.target.value }))}
                placeholder={t("tasks.taskTitlePlaceholder")}
                value={newTask.title}
              />
              <input
                className="w-full bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                onChange={(e) => setNewTask((current) => ({ ...current, description: e.target.value }))}
                placeholder={t("tasks.descriptionPlaceholder")}
                value={newTask.description}
              />
              <div className="flex gap-2">
                <select
                  className="flex-1 bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                  onChange={(e) => setNewTask((current) => ({ ...current, priority: e.target.value }))}
                  value={newTask.priority}
                >
                  <option value="low">{t("tasks.priorityLow")}</option>
                  <option value="medium">{t("tasks.priorityMedium")}</option>
                  <option value="high">{t("tasks.priorityHigh")}</option>
                </select>
                <input
                  className="flex-1 bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                  onChange={(e) => setNewTask((current) => ({ ...current, dueAt: e.target.value }))}
                  type="datetime-local"
                  value={newTask.dueAt}
                />
              </div>
              <div className="flex gap-2">
                <select
                  className="flex-1 bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                  onChange={(e) => setNewTask((current) => ({ ...current, repeat: e.target.value }))}
                  value={newTask.repeat}
                >
                  <option value="none">{t("tasks.repeatNone")}</option>
                  <option value="daily">{t("tasks.repeatDaily")}</option>
                  <option value="weekly">{t("tasks.repeatWeekly")}</option>
                  <option value="monthly">{t("tasks.repeatMonthly")}</option>
                </select>
                {newTask.repeat !== "none" ? (
                  <input
                    className="w-24 bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                    min={2}
                    max={52}
                    onChange={(e) => setNewTask((current) => ({ ...current, repeatCount: e.target.value }))}
                    type="number"
                    value={newTask.repeatCount}
                    aria-label={t("tasks.repeatCountAria")}
                  />
                ) : null}
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={
                    isCreatingTask || !newTask.title.trim() || (newTask.repeat !== "none" && !newTask.dueAt)
                  }
                  className="flex-1 py-2 bg-primary text-on-primary rounded-lg text-label-sm font-bold disabled:opacity-60"
                >
                  {isCreatingTask ? t("tasks.creating") : t("tasks.create")}
                </button>
                <button
                  type="button"
                  onClick={() =>
                    setNewTask({ title: "", description: "", priority: "medium", dueAt: "", repeat: "none", repeatCount: "4" })
                  }
                  className="px-3 py-2 bg-surface text-on-surface-variant rounded-lg text-label-sm font-bold"
                >
                  {t("common.clear")}
                </button>
              </div>
            </form>
          ) : null}

          <div className="flex-1 overflow-y-auto space-y-md pr-2 max-h-[calc(100vh-320px)]">
            {isQueueLoading ? <SkeletonList count={3} /> : null}
            {!isQueueLoading && !queue?.items.length ? (
              <EmptyState icon="task_alt" size="lg" title={t("tasks.noPrioritizedWork")} />
            ) : null}
            {!isQueueLoading && (queue?.items.length ?? 0) > 0 && filteredQueueItems.length === 0 ? (
              <EmptyState icon="search_off" title={t("tasks.noSearchResults")} />
            ) : null}
            {filteredQueueItems.map((item) => {
              const borderClass = item.score >= 80 ? "border-l-error" : item.priority === "high" ? "border-l-secondary" : "border-l-primary/30";
              const badgeClass = item.score >= 80 ? "bg-error-container text-on-error-container" : "bg-surface-container-highest text-on-surface-variant";

              if (item.item_type === "task" && editingTaskId === item.item_id) {
                return (
                  <form
                    key={`${item.item_type}-${item.item_id}`}
                    onSubmit={handleSaveTaskEdit}
                    className={`glass-card p-lg rounded-xl space-y-2 border-l-4 ${borderClass}`}
                  >
                    <input
                      className="w-full bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                      onChange={(e) => setTaskEditForm((f) => ({ ...f, title: e.target.value }))}
                      value={taskEditForm.title}
                    />
                    <div className="flex gap-2">
                      <select
                        className="flex-1 bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                        onChange={(e) => setTaskEditForm((f) => ({ ...f, priority: e.target.value }))}
                        value={taskEditForm.priority}
                      >
                        <option value="low">{t("tasks.priorityLow")}</option>
                        <option value="medium">{t("tasks.priorityMedium")}</option>
                        <option value="high">{t("tasks.priorityHigh")}</option>
                      </select>
                      <input
                        className="flex-1 bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                        onChange={(e) => setTaskEditForm((f) => ({ ...f, dueAt: e.target.value }))}
                        type="datetime-local"
                        value={taskEditForm.dueAt}
                      />
                    </div>
                    <div className="flex gap-2">
                      <button
                        type="submit"
                        disabled={isSavingTaskEdit || !taskEditForm.title.trim()}
                        className="flex-1 py-2 bg-primary text-on-primary rounded-lg text-label-sm font-bold disabled:opacity-60"
                      >
                        {isSavingTaskEdit ? t("common.loading") : t("common.save")}
                      </button>
                      <button
                        type="button"
                        onClick={() => setEditingTaskId(null)}
                        className="px-3 py-2 bg-surface text-on-surface-variant rounded-lg text-label-sm font-bold"
                      >
                        {t("common.cancel")}
                      </button>
                    </div>
                  </form>
                );
              }

              return (
                <div
                  key={`${item.item_type}-${item.item_id}`}
                  className={`glass-card p-lg rounded-xl hover:shadow-md transition-shadow group flex items-start gap-md border-l-4 ${borderClass}`}
                >
                  {item.item_type === "task" ? (
                    <input
                      type="checkbox"
                      checked={selectedTaskIds.has(item.item_id)}
                      onChange={() => toggleTaskSelected(item.item_id)}
                      aria-label={t("tasks.bulk.selectOne", { title: item.title })}
                      className="mt-1.5 w-3.5 h-3.5 shrink-0"
                    />
                  ) : null}
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
                  {item.item_type === "task" ? (
                    <div className="hidden group-hover:flex items-center gap-1 shrink-0">
                      <button
                        type="button"
                        onClick={() => startEditingTask(item)}
                        aria-label={t("common.edit")}
                        className="w-7 h-7 rounded-lg flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high"
                      >
                        <span className="material-symbols-outlined text-[16px]">edit</span>
                      </button>
                      <button
                        type="button"
                        disabled={busyItemId === item.item_id}
                        onClick={() => handleDeleteTask(item.item_id)}
                        aria-label={t("common.delete")}
                        className="w-7 h-7 rounded-lg flex items-center justify-center text-error hover:bg-error-container/20 disabled:opacity-60"
                      >
                        <span className="material-symbols-outlined text-[16px]">delete</span>
                      </button>
                    </div>
                  ) : null}
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
                className="w-full bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                onChange={(e) => setNewAppointment((a) => ({ ...a, title: e.target.value }))}
                placeholder={t("tasks.titlePlaceholder")}
                value={newAppointment.title}
              />
              <div className="flex gap-2">
                <input
                  className="flex-1 bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                  onChange={(e) => setNewAppointment((a) => ({ ...a, startAt: e.target.value }))}
                  type="datetime-local"
                  value={newAppointment.startAt}
                />
                <input
                  className="flex-1 bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                  onChange={(e) => setNewAppointment((a) => ({ ...a, endAt: e.target.value }))}
                  type="datetime-local"
                  value={newAppointment.endAt}
                />
              </div>
              <input
                className="w-full bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                onChange={(e) => setNewAppointment((a) => ({ ...a, location: e.target.value }))}
                placeholder={t("tasks.locationPlaceholder")}
                value={newAppointment.location}
              />
              <div className="flex gap-2">
                <select
                  className="flex-1 bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                  onChange={(e) => setNewAppointment((a) => ({ ...a, repeat: e.target.value }))}
                  value={newAppointment.repeat}
                >
                  <option value="none">{t("tasks.repeatNone")}</option>
                  <option value="daily">{t("tasks.repeatDaily")}</option>
                  <option value="weekly">{t("tasks.repeatWeekly")}</option>
                  <option value="monthly">{t("tasks.repeatMonthly")}</option>
                </select>
                {newAppointment.repeat !== "none" ? (
                  <input
                    className="w-24 bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                    min={2}
                    max={52}
                    onChange={(e) => setNewAppointment((a) => ({ ...a, repeatCount: e.target.value }))}
                    type="number"
                    value={newAppointment.repeatCount}
                    aria-label={t("tasks.repeatCountAria")}
                  />
                ) : null}
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={isCreatingAppt || !newAppointment.title.trim() || !newAppointment.startAt || !newAppointment.endAt}
                  className="flex-1 py-2 bg-primary text-on-primary rounded-lg text-label-sm font-bold disabled:opacity-60"
                >
                  {isCreatingAppt ? t("tasks.creating") : t("tasks.create")}
                </button>
                <button
                  type="button"
                  onClick={() =>
                    setNewAppointment({
                      title: "",
                      startAt: "",
                      endAt: "",
                      location: "",
                      description: "",
                      repeat: "none",
                      repeatCount: "4",
                    })
                  }
                  className="px-3 py-2 bg-surface text-on-surface-variant rounded-lg text-label-sm font-bold"
                >
                  {t("common.clear")}
                </button>
              </div>
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
              {isCalendarLoading ? (
                <>
                  <Skeleton className="h-16 w-full rounded-xl" />
                  <Skeleton className="h-16 w-full rounded-xl" />
                </>
              ) : null}
              {!isCalendarLoading && selectedDayAppointments.length === 0 ? (
                <EmptyState icon="event_available" title={t("tasks.noAppointmentsToday")} />
              ) : null}
              {selectedDayAppointments.map((appointment) =>
                editingApptId === appointment.id ? (
                  <form
                    key={appointment.id}
                    onSubmit={handleSaveAppointmentEdit}
                    className="bg-surface-container-lowest rounded-xl border border-outline-variant/30 p-md space-y-2"
                  >
                    <input
                      className="w-full bg-surface-container-low border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                      onChange={(e) => setApptEditForm((f) => ({ ...f, title: e.target.value }))}
                      value={apptEditForm.title}
                    />
                    <div className="flex gap-2">
                      <input
                        className="flex-1 bg-surface-container-low border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                        onChange={(e) => setApptEditForm((f) => ({ ...f, startAt: e.target.value }))}
                        type="datetime-local"
                        value={apptEditForm.startAt}
                      />
                      <input
                        className="flex-1 bg-surface-container-low border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                        onChange={(e) => setApptEditForm((f) => ({ ...f, endAt: e.target.value }))}
                        type="datetime-local"
                        value={apptEditForm.endAt}
                      />
                    </div>
                    <input
                      className="w-full bg-surface-container-low border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                      onChange={(e) => setApptEditForm((f) => ({ ...f, location: e.target.value }))}
                      placeholder={t("tasks.locationPlaceholder")}
                      value={apptEditForm.location}
                    />
                    <div className="flex gap-2">
                      <button
                        type="submit"
                        disabled={isSavingApptEdit || !apptEditForm.title.trim()}
                        className="flex-1 py-2 bg-primary text-on-primary rounded-lg text-label-sm font-bold disabled:opacity-60"
                      >
                        {isSavingApptEdit ? t("common.loading") : t("common.save")}
                      </button>
                      <button
                        type="button"
                        onClick={() => setEditingApptId(null)}
                        className="px-3 py-2 bg-surface text-on-surface-variant rounded-lg text-label-sm font-bold"
                      >
                        {t("common.cancel")}
                      </button>
                    </div>
                  </form>
                ) : (
                  <div
                    key={appointment.id}
                    className="bg-surface-container-lowest rounded-xl border border-outline-variant/30 p-md flex items-center justify-between gap-md"
                  >
                    <div className="min-w-0">
                      <p className="font-label-md text-on-surface truncate">{appointment.title}</p>
                      <p className="text-body-sm text-on-surface-variant truncate">
                        {formatDateTime(appointment.start_at, language)} - {formatTime(appointment.end_at, language)} ·{" "}
                        {appointment.location ?? t("tasks.online")}
                      </p>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <button
                        type="button"
                        disabled={appointment.status === "cancelled" || activeApptId === appointment.id}
                        onClick={() => startEditingAppointment(appointment)}
                        aria-label={t("common.edit")}
                        className="w-7 h-7 rounded-lg flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high disabled:opacity-40"
                      >
                        <span className="material-symbols-outlined text-[16px]">edit</span>
                      </button>
                      <button
                        type="button"
                        disabled={appointment.status === "cancelled" || activeApptId === appointment.id}
                        onClick={() => handleCancelAppointment(appointment.id)}
                        className="text-error text-[12px] font-bold hover:underline disabled:opacity-60 px-1"
                      >
                        {appointment.status === "cancelled" ? t("tasks.cancelled") : t("tasks.cancel")}
                      </button>
                      <button
                        type="button"
                        disabled={activeApptId === appointment.id}
                        onClick={() => handleDeleteAppointment(appointment.id)}
                        aria-label={t("common.delete")}
                        className="w-7 h-7 rounded-lg flex items-center justify-center text-error hover:bg-error-container/20 disabled:opacity-60"
                      >
                        <span className="material-symbols-outlined text-[16px]">delete</span>
                      </button>
                    </div>
                  </div>
                ),
              )}
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

function toDateTimeLocal(iso: string): string {
  const date = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function repeatToPayload(
  repeat: string,
  countStr: string,
): { repeat_count: number | null; repeat_interval_days: number } {
  const count = Math.max(2, Math.min(52, Number(countStr) || 2));
  switch (repeat) {
    case "daily":
      return { repeat_count: count, repeat_interval_days: 1 };
    case "weekly":
      return { repeat_count: count, repeat_interval_days: 7 };
    case "monthly":
      return { repeat_count: count, repeat_interval_days: 30 };
    default:
      return { repeat_count: null, repeat_interval_days: 7 };
  }
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
