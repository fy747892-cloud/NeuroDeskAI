"use client";

import type { Route } from "next";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useState } from "react";
import { resetPassword } from "@/lib/api";
import { useLanguage } from "@/lib/i18n/context";

export function ResetPasswordForm() {
  const { t } = useLanguage();
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [newPassword, setNewPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDone, setDone] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || newPassword.length < 8) return;

    setSubmitting(true);
    setError(null);
    try {
      await resetPassword(token, newPassword);
      setDone(true);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : t("auth.resetPassword.error"));
    } finally {
      setSubmitting(false);
    }
  }

  if (!token) {
    return (
      <div className="space-y-5">
        <h1 className="font-headline-lg text-headline-lg text-on-surface">{t("auth.resetPassword.title")}</h1>
        <p className="text-error text-body-sm bg-error-container/10 rounded-lg p-4">
          {t("auth.resetPassword.missingToken")}
        </p>
        <a href="/sifremi-unuttum" className="text-primary font-bold hover:underline text-body-sm">
          {t("auth.forgotPasswordLink")}
        </a>
      </div>
    );
  }

  if (isDone) {
    return (
      <div className="space-y-5">
        <h1 className="font-headline-lg text-headline-lg text-on-surface">{t("auth.resetPassword.title")}</h1>
        <p className="text-primary text-body-sm bg-primary-container/10 rounded-lg p-4">
          {t("auth.resetPassword.success")}
        </p>
        <button
          type="button"
          onClick={() => router.push("/giris" as Route)}
          className="w-full py-3 bg-primary text-on-primary rounded-lg font-label-md hover:opacity-90 active:scale-[0.98] transition-all"
        >
          {t("auth.resetPassword.goToLogin")}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-headline-lg text-headline-lg text-on-surface">{t("auth.resetPassword.title")}</h1>
        <p className="text-body-md text-on-surface-variant mt-1">{t("auth.resetPassword.subtitle")}</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <label className="block">
          <span className="text-label-sm font-label-sm text-on-surface-variant mb-1 block">
            {t("auth.resetPassword.newPassword")}
          </span>
          <div className="relative">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">lock</span>
            <input
              autoComplete="new-password"
              autoFocus
              minLength={8}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder={t("auth.passwordPlaceholder")}
              type={showPassword ? "text" : "password"}
              value={newPassword}
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
          disabled={isSubmitting || newPassword.length < 8}
          className="w-full flex items-center justify-center gap-2 py-3 bg-primary text-on-primary rounded-lg font-label-md hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-60"
        >
          <span className="material-symbols-outlined text-[18px]">{isSubmitting ? "hourglass_empty" : "check"}</span>
          {isSubmitting ? t("auth.submitting") : t("auth.resetPassword.submit")}
        </button>

        {error ? <p className="text-error text-body-sm">{error}</p> : null}
      </form>
    </div>
  );
}
