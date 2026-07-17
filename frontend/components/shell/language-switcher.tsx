"use client";

import { useLanguage } from "@/lib/i18n/context";

export function LanguageSwitcher() {
  const { language, setLanguage, t } = useLanguage();

  return (
    <div
      className="flex items-center rounded-full bg-surface-container-low p-0.5 text-[11px] font-bold"
      role="group"
      aria-label={t("shell.languageSwitcher.aria")}
    >
      {(["tr", "en"] as const).map((code) => (
        <button
          key={code}
          type="button"
          onClick={() => setLanguage(code)}
          className={
            "px-2.5 py-1 rounded-full uppercase tracking-wider transition-colors " +
            (language === code
              ? "bg-primary text-on-primary"
              : "text-on-surface-variant hover:text-primary")
          }
          aria-pressed={language === code}
        >
          {code}
        </button>
      ))}
    </div>
  );
}
