import { ModulePlaceholder } from "@/components/module-placeholder";

export default function SettingsPage() {
  return (
    <ModulePlaceholder
      description="Kullanici, organizasyon, entegrasyon ve AI ayarlari bu alanda duzenlenecek."
      items={[
        { label: "Backend modules", value: "users/orgs" },
        { label: "Primary data", value: "Settings" },
        { label: "Sprint focus", value: "Admin basics" },
      ]}
    />
  );
}
