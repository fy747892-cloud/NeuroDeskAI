"use client";

import { FormEvent, useEffect, useState } from "react";
import { getPublicLeadForm, LeadFormPublicInfo, submitLeadForm } from "@/lib/api";
import { useLanguage } from "@/lib/i18n/context";

export function PublicLeadForm({ token }: { token: string }) {
  const { t } = useLanguage();
  const [info, setInfo] = useState<LeadFormPublicInfo | null | undefined>(undefined);
  const [form, setForm] = useState({ fullName: "", email: "", phone: "", company: "", message: "" });
  const [website, setWebsite] = useState("");
  const [isSubmitting, setSubmitting] = useState(false);
  const [isDone, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getPublicLeadForm(token)
      .then(setInfo)
      .catch(() => setInfo(null));
  }, [token]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form.fullName.trim() || (!form.email.trim() && !form.phone.trim())) {
      setError(t("leadForm.missingContact"));
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await submitLeadForm(token, {
        full_name: form.fullName.trim(),
        email: form.email.trim() || null,
        phone: form.phone.trim() || null,
        company: form.company.trim() || null,
        message: form.message.trim() || null,
        website,
      });
      setDone(true);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : t("leadForm.error"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-background p-xl">
      <div className="w-full max-w-md bg-surface rounded-xl shadow-lg p-lg">
        {info === undefined ? (
          <p className="text-body-md text-on-surface-variant">{t("common.loading")}</p>
        ) : info === null ? (
          <p className="text-body-md text-error">{t("leadForm.notFound")}</p>
        ) : !info.is_active ? (
          <p className="text-body-md text-on-surface-variant">{t("leadForm.inactive")}</p>
        ) : isDone ? (
          <div className="text-center py-lg">
            <span
              className="material-symbols-outlined text-primary text-[48px] mb-3 inline-block"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              check_circle
            </span>
            <h1 className="font-headline-md text-headline-md text-on-surface mb-2">
              {t("leadForm.successTitle")}
            </h1>
            <p className="text-body-md text-on-surface-variant">{t("leadForm.successBody")}</p>
          </div>
        ) : (
          <>
            <h1 className="font-headline-lg text-headline-lg text-on-surface mb-1">
              {t("leadForm.heading", { organization: info.organization_name })}
            </h1>
            <p className="text-body-md text-on-surface-variant mb-lg">{t("leadForm.subheading")}</p>

            <form onSubmit={handleSubmit} className="flex flex-col gap-3">
              <input
                className="bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2.5 text-body-md"
                onChange={(e) => setForm((f) => ({ ...f, fullName: e.target.value }))}
                placeholder={t("leadForm.fullNameLabel")}
                value={form.fullName}
                autoComplete="name"
              />
              <input
                className="bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2.5 text-body-md"
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                placeholder={t("leadForm.emailLabel")}
                type="email"
                value={form.email}
                autoComplete="email"
              />
              <input
                className="bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2.5 text-body-md"
                onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
                placeholder={t("leadForm.phoneLabel")}
                type="tel"
                value={form.phone}
                autoComplete="tel"
              />
              <input
                className="bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2.5 text-body-md"
                onChange={(e) => setForm((f) => ({ ...f, company: e.target.value }))}
                placeholder={t("leadForm.companyLabel")}
                value={form.company}
                autoComplete="organization"
              />
              <textarea
                className="bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2.5 text-body-md"
                onChange={(e) => setForm((f) => ({ ...f, message: e.target.value }))}
                placeholder={t("leadForm.messageLabel")}
                rows={3}
                value={form.message}
              />

              {/* Honeypot: hidden from real visitors, bots tend to fill every field. */}
              <input
                aria-hidden="true"
                autoComplete="off"
                onChange={(e) => setWebsite(e.target.value)}
                style={{ position: "absolute", opacity: 0, pointerEvents: "none", height: 0, width: 0 }}
                tabIndex={-1}
                value={website}
              />

              {error ? <p className="text-error text-body-sm">{error}</p> : null}

              <button
                type="submit"
                disabled={isSubmitting || !form.fullName.trim()}
                className="mt-2 py-3 bg-primary text-on-primary rounded-lg font-label-md hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-60"
              >
                {isSubmitting ? t("leadForm.submitting") : t("leadForm.submit")}
              </button>
            </form>
          </>
        )}
      </div>
    </main>
  );
}
