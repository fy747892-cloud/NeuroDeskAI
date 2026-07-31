import type { Metadata } from "next";
import { Suspense } from "react";
import { AcceptInviteForm } from "@/components/auth/accept-invite-form";

export const metadata: Metadata = { title: "Daveti Kabul Et" };

export default function AcceptInvitePage() {
  return (
    <Suspense>
      <AcceptInviteForm />
    </Suspense>
  );
}
