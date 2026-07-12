"use client";

import { useRouter } from "next/navigation";
import type { Route } from "next";
import { useState } from "react";
import { useSession } from "@/lib/session";

export function UserMenu() {
  const router = useRouter();
  const { user, signOut } = useSession();
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
    <div className="userMenu">
      <div>
        <span>Aktif oturum</span>
        <strong>{user?.profile?.full_name ?? user?.email ?? "Kullanıcı"}</strong>
      </div>
      <button disabled={isSigningOut} onClick={handleSignOut} type="button">
        {isSigningOut ? "Çıkılıyor..." : "Çıkış"}
      </button>
    </div>
  );
}
