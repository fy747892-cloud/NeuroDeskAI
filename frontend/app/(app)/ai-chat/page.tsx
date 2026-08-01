import type { Metadata } from "next";
import { Suspense } from "react";
import { AIChatView } from "@/components/ai-chat/ai-chat-view";

export const metadata: Metadata = { title: "AI Sohbet" };

export default function AIChatPage() {
  return (
    <Suspense>
      <AIChatView />
    </Suspense>
  );
}
