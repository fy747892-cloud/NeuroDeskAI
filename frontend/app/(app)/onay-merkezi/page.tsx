import type { Metadata } from "next";
import { ApprovalsView } from "@/components/approvals/approvals-view";

export const metadata: Metadata = { title: "Onay Merkezi" };

export default function OnayMerkeziPage() {
  return <ApprovalsView />;
}
