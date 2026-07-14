"use client";

import { useRouter } from "next/navigation";
import type { Route } from "next";
import { useState } from "react";
import { useSession } from "@/lib/session";

export function UserMenu() {
  const router = useRouter();
  const { signOut } = useSession();
  const [isSigningOut, setSigningOut] = useState(false);

  async function handleSignOut() {
    setSigningOut(true);
    try {
      await signOut();
    } finally {
      router.replace("/giris" as Route);
      setSigningOut(false);
    }
  }

  return (
    <button
      type="button"
      onClick={handleSignOut}
      disabled={isSigningOut}
      aria-label="Çıkış yap"
      title="Çıkış yap"
      className="p-1.5 rounded-lg text-outline hover:text-error hover:bg-error/5 transition-colors shrink-0"
    >
      <span className="material-symbols-outlined text-[20px]">logout</span>
    </button>
  );
}
