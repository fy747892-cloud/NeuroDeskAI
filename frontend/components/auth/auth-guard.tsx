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
      <main className="min-h-screen flex items-center justify-center bg-background">
        <section className="glass-card p-xl rounded-2xl text-center max-w-sm">
          <p className="font-label-sm text-label-sm text-primary uppercase tracking-widest mb-2">
            NeuroDeskAI
          </p>
          <h1 className="font-headline-md text-headline-md text-on-surface mb-2">
            Oturum kontrol ediliyor
          </h1>
          <p className="text-body-md text-on-surface-variant">
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
