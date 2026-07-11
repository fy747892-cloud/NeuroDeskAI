import { ModulePlaceholder } from "@/components/module-placeholder";

export default function AIChatPage() {
  return (
    <ModulePlaceholder
      description="LLM destekli operasyon sohbeti ve tenant kapsamli bilgi kullanimi burada gelisecek."
      items={[
        { label: "Backend module", value: "ai_chat" },
        { label: "Next integration", value: "Pending" },
        { label: "Sprint focus", value: "AI Chat" },
      ]}
    />
  );
}
