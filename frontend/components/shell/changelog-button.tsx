"use client";

import { useEffect, useRef, useState } from "react";
import { CHANGELOG, LATEST_CHANGELOG_VERSION } from "@/lib/changelog";
import { useLanguage } from "@/lib/i18n/context";
import { formatDate } from "@/lib/format";

const SEEN_VERSION_KEY = "neurodesk-changelog-seen-version";

export function ChangelogButton() {
  const { t, language } = useLanguage();
  const [isOpen, setOpen] = useState(false);
  const [hasUnseen, setHasUnseen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const seenVersion = window.localStorage.getItem(SEEN_VERSION_KEY);
    setHasUnseen(seenVersion !== LATEST_CHANGELOG_VERSION);
  }, []);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function handleOpen() {
    setOpen((prev) => !prev);
    setHasUnseen(false);
    window.localStorage.setItem(SEEN_VERSION_KEY, LATEST_CHANGELOG_VERSION);
  }

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        onClick={handleOpen}
        className="relative text-on-surface-variant hover:text-primary transition-colors"
        aria-label={t("shell.changelog.aria")}
      >
        <span className="material-symbols-outlined">campaign</span>
        {hasUnseen ? (
          <span className="absolute top-0 right-0 w-2 h-2 bg-primary rounded-full border-2 border-surface" />
        ) : null}
      </button>

      {isOpen ? (
        <div className="absolute right-0 mt-2 w-[calc(100vw-2rem)] max-w-96 max-h-[70vh] overflow-y-auto custom-scrollbar bg-surface-container-lowest border border-outline-variant/30 rounded-xl shadow-xl z-50">
          <div className="px-lg py-md border-b border-outline-variant/20">
            <h4 className="font-label-md text-label-md">{t("shell.changelog.title")}</h4>
          </div>
          <ul className="divide-y divide-outline-variant/10">
            {CHANGELOG.map((entry) => (
              <li key={entry.version} className="px-lg py-md">
                <p className="text-[10px] font-bold text-primary uppercase tracking-wide mb-1">
                  {formatDate(entry.date, language)}
                </p>
                <ul className="space-y-1.5">
                  {entry.items.map((item) => (
                    <li
                      key={item.en}
                      className="text-body-sm text-on-surface-variant flex items-start gap-2"
                    >
                      <span className="material-symbols-outlined text-[14px] text-primary mt-0.5 shrink-0">
                        check_circle
                      </span>
                      {language === "tr" ? item.tr : item.en}
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
