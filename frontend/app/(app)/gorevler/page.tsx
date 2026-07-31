import type { Metadata } from "next";
import { TasksAppointmentsView } from "@/components/tasks/tasks-appointments-view";

export const metadata: Metadata = { title: "Görevler ve Randevular" };

export default function TasksPage() {
  return <TasksAppointmentsView />;
}
