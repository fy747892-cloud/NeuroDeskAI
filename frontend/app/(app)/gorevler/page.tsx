import { ModulePlaceholder } from "@/components/module-placeholder";

export default function TasksPage() {
  return (
    <ModulePlaceholder
      description="Acik, gecikmis ve AI tarafindan onerilen gorevler burada operasyon listesine donecek."
      items={[
        { label: "Backend module", value: "tasks" },
        { label: "Primary data", value: "Task list" },
        { label: "Sprint focus", value: "Task board" },
      ]}
    />
  );
}
