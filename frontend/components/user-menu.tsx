"use client";

import { useRouter } from "next/navigation";
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
      router.replace("/giris" as never);
      setSigningOut(false);
    }
  }

  return (
    <div className="userMenu">
      <div>
        <span>Aktif oturum</span>
        <strong>{user?.profile?.full_name ?? user?.email ?? "Kullanici"}</strong>
      </div>
      <button disabled={isSigningOut} onClick={handleSignOut} type="button">
        {isSigningOut ? "Cikiliyor..." : "Cikis"}
      </button>
    </div>
  );
}
