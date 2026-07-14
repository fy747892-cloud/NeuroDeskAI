"use client";

import { useRouter } from "next/navigation";
import type { Route } from "next";
import { ReactNode, useEffect } from "react";
import { useSession } from "@/lib/session";

export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, isInitializing } = useSession();

  useEffect(() => {
    if (!isInitializing && !isAuthenticated) {
      router.replace("/giris" as Route);
    }
  }, [isInitializing, isAuthenticated, router]);

  if (isInitializing || !isAuthenticated) {
    return (
      <main className="authPage">
        <section className="authCard">
          <p className="eyebrow">NeuroDeskAI</p>
          <h1>Oturum kontrol ediliyor</h1>
          <p className="formMessage">
            {isInitializing
              ? "Oturum bilgin doğrulanıyor..."
              : "Devam etmek için giriş sayfasına yönlendiriliyorsun."}
          </p>
        </section>
      </main>
    );
  }

  return children;
}
