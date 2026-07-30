"use client";

import type { Route } from "next";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useState } from "react";
import { acceptInvite } from "@/lib/api";
import { useSession } from "@/lib/session";
import { useLanguage } from "@/lib/i18n/context";

export function AcceptInviteForm() {
  const { t } = useLanguage();
  const router = useRouter();
  const { setAuthenticatedSession } = useSession();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDone, setDone] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !displayName.trim() || password.length < 8) return;

    setSubmitting(true);
    setError(null);
    try {
      const tokens = await acceptInvite(token, password, displayName.trim());
      setDone(true);
      await setAuthenticatedSession(tokens);
      router.push("/" as Route);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : t("auth.acceptInvite.error"));
    } finally {
      setSubmitting(false);
    }
  }

  if (!token) {
    return (
      <div className="space-y-5">
        <h1 className="font-headline-lg text-headline-lg text-on-surface">{t("auth.acceptInvite.title")}</h1>
        <p className="text-error text-body-sm bg-error-container/10 rounded-lg p-4">
          {t("auth.acceptInvite.missingToken")}
        </p>
        <a href="/giris" className="text-primary font-bold hover:underline text-body-sm">
          {t("auth.backToLogin")}
        </a>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-headline-lg text-headline-lg text-on-surface">{t("auth.acceptInvite.title")}</h1>
        <p className="text-body-md text-on-surface-variant mt-1">{t("auth.acceptInvite.subtitle")}</p>
      </div>

      {isDone ? (
        <p className="text-primary text-body-sm bg-primary-container/10 rounded-lg p-4">
          {t("auth.acceptInvite.success")}
        </p>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-5">
          <label className="block">
            <span className="text-label-sm font-label-sm text-on-surface-variant mb-1 block">{t("auth.fullName")}</span>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">badge</span>
              <input
                autoComplete="name"
                autoFocus
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder={t("auth.fullNamePlaceholder")}
                value={displayName}
                className="w-full pl-10 pr-4 py-2.5 bg-surface-container-low border border-outline-variant/30 rounded-lg text-body-md focus:ring-2 focus:ring-primary/20 focus:outline-none"
              />
            </div>
          </label>

          <label className="block">
            <span className="text-label-sm font-label-sm text-on-surface-variant mb-1 block">{t("auth.password")}</span>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">lock</span>
              <input
                autoComplete="new-password"
                minLength={8}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={t("auth.passwordPlaceholder")}
                type={showPassword ? "text" : "password"}
                value={password}
                className="w-full pl-10 pr-10 py-2.5 bg-surface-container-low border border-outline-variant/30 rounded-lg text-body-md focus:ring-2 focus:ring-primary/20 focus:outline-none"
              />
              <button
                type="button"
                aria-label={showPassword ? t("auth.hidePassword") : t("auth.showPassword")}
                onClick={() => setShowPassword((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-outline hover:text-primary"
              >
                <span className="material-symbols-outlined text-[18px]">
                  {showPassword ? "visibility_off" : "visibility"}
                </span>
              </button>
            </div>
          </label>

          <button
            type="submit"
            disabled={isSubmitting || !displayName.trim() || password.length < 8}
            className="w-full flex items-center justify-center gap-2 py-3 bg-primary text-on-primary rounded-lg font-label-md hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-60"
          >
            <span className="material-symbols-outlined text-[18px]">
              {isSubmitting ? "hourglass_empty" : "person_add"}
            </span>
            {isSubmitting ? t("auth.submitting") : t("auth.acceptInvite.submit")}
          </button>

          {error ? <p className="text-error text-body-sm">{error}</p> : null}
        </form>
      )}
    </div>
  );
}
