import { ModulePlaceholder } from "@/components/module-placeholder";

export default function AnalyticsPage() {
  return (
    <ModulePlaceholder
      description="Operasyon metrikleri, AI maliyetleri ve gunluk performans ozetleri burada toplanacak."
      items={[
        { label: "Backend module", value: "analytics" },
        { label: "Primary data", value: "Overview" },
        { label: "Sprint focus", value: "Charts" },
      ]}
    />
  );
}
