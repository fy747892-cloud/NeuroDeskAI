"use client";

import { AuthHeroNetwork } from "@/components/auth/auth-hero-network";
import { useLanguage } from "@/lib/i18n/context";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const { t } = useLanguage();

  return (
    <main className="min-h-screen flex bg-background">
      <section className="auth-hero hidden lg:flex lg:w-1/2 relative flex-col justify-between p-12">
        <AuthHeroNetwork />

        <div className="relative z-10 flex items-center gap-2">
          <img src="/brand/neurodesk-mark.png" alt="" className="w-9 h-9 rounded-lg" />
          <span className="font-headline-md text-headline-md font-bold text-white">NeuroDesk AI</span>
        </div>

        <div className="relative z-10 max-w-md">
          <h1 className="font-headline-lg text-headline-lg leading-tight mb-4 text-white">
            {t("auth.marketing.headlineLine1")}
            <br />
            <span className="auth-hero-accent">{t("auth.marketing.headlineLine2")}</span>
          </h1>
          <p className="text-body-lg text-white/80 mb-xl">{t("auth.marketing.tagline")}</p>
          <ul className="space-y-4">
            <li className="flex items-center gap-3 text-white/90">
              <span className="material-symbols-outlined">auto_awesome</span>
              {t("auth.marketing.feature1")}
            </li>
            <li className="flex items-center gap-3 text-white/90">
              <span className="material-symbols-outlined">task_alt</span>
              {t("auth.marketing.feature2")}
            </li>
            <li className="flex items-center gap-3 text-white/90">
              <span className="material-symbols-outlined">shield</span>
              {t("auth.marketing.feature3")}
            </li>
          </ul>
        </div>

        <div className="relative z-10 flex items-center justify-between text-body-sm text-white/60">
          <span>{t("auth.marketing.copyright")}</span>
          <span className="flex items-center gap-1.5">
            <span className="auth-hero-live-dot" />
            {t("auth.marketing.livePill")}
          </span>
        </div>
      </section>

      <section className="flex-1 flex items-center justify-center p-xl">
        <div className="w-full max-w-md">{children}</div>
      </section>
    </main>
  );
}
