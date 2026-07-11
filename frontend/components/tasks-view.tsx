"use client";

import { useEffect, useMemo, useState } from "react";
import { completeTask, listTasks, Task } from "@/lib/api";
import { useSession } from "@/lib/session";

export function TasksView() {
  const { tokens } = useSession();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);

  async function loadTasks() {
    if (!tokens?.accessToken) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      setTasks(await listTasks(tokens.accessToken));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Gorevler alinamadi.");
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
      setError(completeError instanceof Error ? completeError.message : "Gorev tamamlanamadi.");
    } finally {
      setActiveTaskId(null);
    }
  }

  return (
    <section className="moduleSurface">
      {error ? <p className="notice">{error}</p> : null}

      <div className="moduleGrid">
        <SummaryCard label="Acik" value={summary.open} />
        <SummaryCard label="Gecikmis" value={summary.overdue} />
        <SummaryCard label="Yuksek oncelik" value={summary.high} />
        <SummaryCard label="Tamamlanan" value={summary.completed} />
      </div>

      <div className="panel">
        <div className="panelHeader">
          <h2>Gorev listesi</h2>
          <button disabled={isLoading} onClick={loadTasks} type="button">
            {isLoading ? "Yukleniyor" : "Yenile"}
          </button>
        </div>

        <div className="dataList">
          {isLoading ? <p className="emptyState">Gorevler yukleniyor.</p> : null}
          {!isLoading && tasks.length === 0 ? (
            <p className="emptyState">Henuz gorev bulunmuyor.</p>
          ) : null}
          {tasks.map((task) => (
            <article className="dataRow" key={task.id}>
              <div>
                <div className="rowTitle">
                  <h3>{task.title}</h3>
                  <span>{task.priority}</span>
                </div>
                <p>{task.description ?? "Aciklama eklenmemis."}</p>
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
                  {activeTaskId === task.id ? "Isleniyor" : "Tamamla"}
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
