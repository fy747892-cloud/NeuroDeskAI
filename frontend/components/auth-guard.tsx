"use client";

import { useRouter } from "next/navigation";
import { ReactNode, useEffect } from "react";
import { useSession } from "@/lib/session";

export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { isAuthenticated } = useSession();

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/giris" as never);
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) {
    return (
      <main className="authPage">
        <section className="authCard">
          <p className="eyebrow">NeuroDeskAI</p>
          <h1>Oturum kontrol ediliyor</h1>
          <p className="formMessage">Devam etmek icin giris sayfasina yonlendiriliyorsun.</p>
        </section>
      </main>
    );
  }

  return children;
}
