"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { completeTask, createTask, listTasks, Task } from "@/lib/api";
import { useSession } from "@/lib/session";

export function TasksView() {
  const { tokens } = useSession();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [isCreating, setCreating] = useState(false);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [newTask, setNewTask] = useState({
    description: "",
    dueAt: "",
    priority: "medium",
    title: "",
  });

  async function loadTasks() {
    if (!tokens?.accessToken) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      setTasks(await listTasks(tokens.accessToken));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Görevler alınamadı.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTasks();
  }, [tokens?.accessToken]);

  const summary = useMemo(() => {
    return {
      open: tasks.filter((task) => task.status !== "completed").length,
      overdue: tasks.filter((task) => task.due_at && new Date(task.due_at) < new Date()).length,
      high: tasks.filter((task) => task.priority === "high").length,
      completed: tasks.filter((task) => task.status === "completed").length,
    };
  }, [tasks]);

  async function handleComplete(taskId: string) {
    if (!tokens?.accessToken) {
      return;
    }

    setActiveTaskId(taskId);
    setError(null);
    try {
      const updatedTask = await completeTask(tokens.accessToken, taskId);
      setTasks((currentTasks) =>
        currentTasks.map((task) => (task.id === updatedTask.id ? updatedTask : task)),
      );
    } catch (completeError) {
      setError(completeError instanceof Error ? completeError.message : "Görev tamamlanamadı.");
    } finally {
      setActiveTaskId(null);
    }
  }

  async function handleCreateTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !newTask.title.trim()) {
      return;
    }

    setCreating(true);
    setError(null);
    setNotice(null);
    try {
      const createdTask = await createTask(tokens.accessToken, {
        title: newTask.title.trim(),
        description: newTask.description.trim() || null,
        priority: newTask.priority,
        due_at: newTask.dueAt ? new Date(newTask.dueAt).toISOString() : null,
      });
      setTasks((currentTasks) => [createdTask, ...currentTasks]);
      setNewTask({ description: "", dueAt: "", priority: "medium", title: "" });
      setNotice("Görev oluşturuldu.");
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Görev oluşturulamadı.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <section className="moduleSurface">
      {error ? <p className="notice">{error}</p> : null}
      {notice ? <p className="notice success">{notice}</p> : null}

      <div className="moduleGrid">
        <SummaryCard label="Açık" value={summary.open} />
        <SummaryCard label="Gecikmis" value={summary.overdue} />
        <SummaryCard label="Yüksek öncelik" value={summary.high} />
        <SummaryCard label="Tamamlanan" value={summary.completed} />
      </div>

      <div className="panel">
        <div className="panelHeader">
          <h2>Yeni görev</h2>
          <span className="tag">Manual</span>
        </div>
        <form className="createForm" onSubmit={handleCreateTask}>
          <label>
            Başlık
            <input
              onChange={(event) => setNewTask((task) => ({ ...task, title: event.target.value }))}
              placeholder="Hastayi geri ara"
              value={newTask.title}
            />
          </label>
          <label>
            Açıklama
            <input
              onChange={(event) =>
                setNewTask((task) => ({ ...task, description: event.target.value }))
              }
              placeholder="Kisa not"
              value={newTask.description}
            />
          </label>
          <label>
            Öncelik
            <select
              onChange={(event) => setNewTask((task) => ({ ...task, priority: event.target.value }))}
              value={newTask.priority}
            >
              <option value="low">low</option>
              <option value="medium">medium</option>
              <option value="high">high</option>
            </select>
          </label>
          <label>
            Son tarih
            <input
              onChange={(event) => setNewTask((task) => ({ ...task, dueAt: event.target.value }))}
              type="datetime-local"
              value={newTask.dueAt}
            />
          </label>
          <button disabled={isCreating || !newTask.title.trim()} type="submit">
            {isCreating ? "Oluşturuluyor" : "Oluştur"}
          </button>
        </form>
      </div>

      <div className="panel">
        <div className="panelHeader">
          <h2>Görev listesi</h2>
          <button disabled={isLoading} onClick={loadTasks} type="button">
            {isLoading ? "Yükleniyor" : "Yenile"}
          </button>
        </div>

        <div className="dataList">
          {isLoading ? <p className="emptyState">Görevler yükleniyor.</p> : null}
          {!isLoading && tasks.length === 0 ? (
            <p className="emptyState">Henüz görev bulunmuyor.</p>
          ) : null}
          {tasks.map((task) => (
            <article className="dataRow" key={task.id}>
              <div>
                <div className="rowTitle">
                  <h3>{task.title}</h3>
                  <span>{task.priority}</span>
                </div>
                <p>{task.description ?? "Açıklama eklenmemiş."}</p>
                <small>
                  {task.due_at ? `Son tarih ${formatDateTime(task.due_at)}` : "Son tarih yok"}
                </small>
              </div>
              <div className="rowActions">
                <span className={task.status === "completed" ? "statusPill done" : "statusPill"}>
                  {task.status}
                </span>
                <button
                  disabled={task.status === "completed" || activeTaskId === task.id}
                  onClick={() => handleComplete(task.id)}
                  type="button"
                >
                  {activeTaskId === task.id ? "İşleniyor" : "Tamamla"}
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
