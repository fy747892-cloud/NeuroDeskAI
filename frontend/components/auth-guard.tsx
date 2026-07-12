"use client";

import { useRouter } from "next/navigation";
import type { Route } from "next";
import { ReactNode, useEffect } from "react";
import { useSession } from "@/lib/session";

export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { isAuthenticated } = useSession();

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/giris" as Route);
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) {
    return (
      <main className="authPage">
        <section className="authCard">
          <p className="eyebrow">NeuroDeskAI</p>
          <h1>Oturum kontrol ediliyor</h1>
          <p className="formMessage">Devam etmek için giriş sayfasına yönlendiriliyorsun.</p>
        </section>
      </main>
    );
  }

  return children;
}
