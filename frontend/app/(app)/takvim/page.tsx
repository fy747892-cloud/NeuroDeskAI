import { ModulePlaceholder } from "@/components/module-placeholder";

export default function CalendarPage() {
  return (
    <ModulePlaceholder
      description="Randevular, cakisma kontrolleri ve hatirlaticilar takvim gorunumune baglanacak."
      items={[
        { label: "Backend module", value: "appointments" },
        { label: "Primary data", value: "Upcoming" },
        { label: "Sprint focus", value: "Calendar" },
      ]}
    />
  );
}
