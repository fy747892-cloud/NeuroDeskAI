"use client";

import { FormEvent, useState } from "react";
import { requestPasswordReset } from "@/lib/api";
import { useLanguage } from "@/lib/i18n/context";

export function ForgotPasswordForm() {
  const { t } = useLanguage();
  const [email, setEmail] = useState("");
  const [isSubmitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSent, setSent] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!email.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      await requestPasswordReset(email.trim());
      setSent(true);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : t("auth.forgotPassword.error"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-headline-lg text-headline-lg text-on-surface">{t("auth.forgotPassword.title")}</h1>
        <p className="text-body-md text-on-surface-variant mt-1">{t("auth.forgotPassword.subtitle")}</p>
      </div>

      {isSent ? (
        <p className="text-primary text-body-sm bg-primary-container/10 rounded-lg p-4">
          {t("auth.forgotPassword.success")}
        </p>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-5">
          <label className="block">
            <span className="text-label-sm font-label-sm text-on-surface-variant mb-1 block">{t("common.email")}</span>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">mail</span>
              <input
                autoComplete="email"
                autoFocus
                onChange={(e) => setEmail(e.target.value)}
                placeholder={t("auth.emailPlaceholder")}
                type="email"
                value={email}
                className="w-full pl-10 pr-4 py-2.5 bg-surface-container-low border border-outline-variant/30 rounded-lg text-body-md focus:ring-2 focus:ring-primary/20 focus:outline-none"
              />
            </div>
          </label>

          <button
            type="submit"
            disabled={isSubmitting || !email.trim()}
            className="w-full flex items-center justify-center gap-2 py-3 bg-primary text-on-primary rounded-lg font-label-md hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-60"
          >
            <span className="material-symbols-outlined text-[18px]">
              {isSubmitting ? "hourglass_empty" : "send"}
            </span>
            {isSubmitting ? t("auth.submitting") : t("auth.forgotPassword.submit")}
          </button>

          {error ? <p className="text-error text-body-sm">{error}</p> : null}
        </form>
      )}

      <p className="text-body-sm text-on-surface-variant text-center">
        <a href="/giris" className="text-primary font-bold hover:underline">
          {t("auth.backToLogin")}
        </a>
      </p>
    </div>
  );
}
