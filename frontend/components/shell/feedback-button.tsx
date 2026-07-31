"use client";

import { FormEvent, useState } from "react";
import { usePathname } from "next/navigation";
import { FeedbackCategory, submitFeedback } from "@/lib/api";
import { useSession } from "@/lib/session";
import { useLanguage } from "@/lib/i18n/context";
import { useToast } from "@/lib/toast";

const CATEGORIES: FeedbackCategory[] = ["bug", "idea", "other"];

export function FeedbackButton() {
  const { tokens } = useSession();
  const { t } = useLanguage();
  const { showToast } = useToast();
  const pathname = usePathname();
  const [isOpen, setOpen] = useState(false);
  const [category, setCategory] = useState<FeedbackCategory>("idea");
  const [message, setMessage] = useState("");
  const [isSubmitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function close() {
    setOpen(false);
    setError(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !message.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await submitFeedback(tokens.accessToken, {
        category,
        message: message.trim(),
        page_url: pathname ?? undefined,
      });
      setMessage("");
      setCategory("idea");
      setOpen(false);
      showToast(t("shell.feedback.success"), "success");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : t("shell.feedback.error"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="text-on-surface-variant hover:text-primary transition-colors"
        aria-label={t("shell.feedback.aria")}
      >
        <span className="material-symbols-outlined">chat_bubble</span>
      </button>

      {isOpen ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-md"
          onClick={close}
        >
          <div
            className="w-full max-w-md bg-surface-container-lowest border border-outline-variant/30 rounded-xl shadow-xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="px-lg py-md border-b border-outline-variant/20 flex items-center justify-between">
              <h4 className="font-headline-md text-headline-md">{t("shell.feedback.title")}</h4>
              <button
                type="button"
                onClick={close}
                className="text-on-surface-variant hover:text-primary"
                aria-label={t("common.cancel")}
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-lg space-y-3">
              <p className="text-body-sm text-on-surface-variant">{t("shell.feedback.subtitle")}</p>
              <div className="flex gap-2">
                {CATEGORIES.map((option) => (
                  <button
                    key={option}
                    type="button"
                    onClick={() => setCategory(option)}
                    className={
                      "flex-1 py-2 rounded-lg text-label-sm font-bold border transition-colors " +
                      (category === option
                        ? "bg-primary text-on-primary border-primary"
                        : "border-outline-variant text-on-surface-variant hover:bg-surface-container-high")
                    }
                  >
                    {t(`shell.feedback.categories.${option}`)}
                  </button>
                ))}
              </div>
              <textarea
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                placeholder={t("shell.feedback.placeholder")}
                rows={4}
                maxLength={4000}
                className="w-full bg-surface-container-low border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm focus:ring-2 focus:ring-primary/20 focus:outline-none resize-none"
              />
              {error ? <p className="text-error text-body-sm">{error}</p> : null}
              <button
                type="submit"
                disabled={isSubmitting || !message.trim()}
                className="w-full py-2.5 bg-primary text-on-primary rounded-lg font-label-md hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-60"
              >
                {isSubmitting ? t("common.loading") : t("shell.feedback.submit")}
              </button>
            </form>
          </div>
        </div>
      ) : null}
    </>
  );
}
