import type { Metadata } from "next";
import { PublicLeadForm } from "@/components/lead-form/public-lead-form";

export const metadata: Metadata = { title: "İletişim Formu" };

export default async function LeadFormPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  return <PublicLeadForm token={token} />;
}
