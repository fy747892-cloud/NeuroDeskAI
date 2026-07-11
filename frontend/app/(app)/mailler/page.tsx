import { ModulePlaceholder } from "@/components/module-placeholder";

export default function EmailPage() {
  return (
    <ModulePlaceholder
      description="Email entegrasyonlari, hesap senkronizasyonu ve mesaj isleme akislari burada gorunecek."
      items={[
        { label: "Backend module", value: "email" },
        { label: "Feature flag", value: "On" },
        { label: "Sprint focus", value: "Mail sync" },
      ]}
    />
  );
}
