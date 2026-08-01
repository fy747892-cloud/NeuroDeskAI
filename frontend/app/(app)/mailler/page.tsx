import type { Metadata } from "next";
import { MaillerView } from "@/components/mailler/mailler-view";

export const metadata: Metadata = { title: "Mailler" };

export default function MaillerPage() {
  return <MaillerView />;
}
