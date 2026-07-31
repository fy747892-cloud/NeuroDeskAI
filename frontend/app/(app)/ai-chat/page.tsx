import type { Metadata } from "next";
import { AIChatView } from "@/components/ai-chat/ai-chat-view";

export const metadata: Metadata = { title: "AI Sohbet" };

export default function AIChatPage() {
  return <AIChatView />;
}
