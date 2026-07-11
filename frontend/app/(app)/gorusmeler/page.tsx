import { ModulePlaceholder } from "@/components/module-placeholder";

export default function ConversationsPage() {
  return (
    <ModulePlaceholder
      description="Gorusme kayitlari, cagri transkriptleri ve AI analiz ciktilari bu alanda listelenecek."
      items={[
        { label: "Backend module", value: "conversations" },
        { label: "Primary data", value: "Calls" },
        { label: "Sprint focus", value: "Conversation UI" },
      ]}
    />
  );
}
