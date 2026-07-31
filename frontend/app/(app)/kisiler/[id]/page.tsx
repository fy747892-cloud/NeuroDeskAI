import type { Metadata } from "next";
import { ContactDetailView } from "@/components/contacts/contact-detail-view";

export const metadata: Metadata = { title: "Kişi Detayı" };

export default async function ContactDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <ContactDetailView contactId={id} />;
}
