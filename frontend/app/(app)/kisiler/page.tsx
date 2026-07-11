import { ModulePlaceholder } from "@/components/module-placeholder";

export default function ContactsPage() {
  return (
    <ModulePlaceholder
      description="Kisi ve CRM kayitlari, iliski gecmisi ve operasyon notlari burada yonetilecek."
      items={[
        { label: "Backend module", value: "contacts" },
        { label: "Primary data", value: "CRM" },
        { label: "Sprint focus", value: "Contacts" },
      ]}
    />
  );
}
