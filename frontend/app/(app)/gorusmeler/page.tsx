import type { Metadata } from "next";
import { Suspense } from "react";
import { ConversationsView } from "@/components/conversations/conversations-view";

export const metadata: Metadata = { title: "Görüşmeler" };

export default function ConversationsPage() {
  return (
    <Suspense>
      <ConversationsView />
    </Suspense>
  );
}
