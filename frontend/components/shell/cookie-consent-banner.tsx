"use client";

import { useEffect, useState } from "react";
import { useLanguage } from "@/lib/i18n/context";

const CONSENT_KEY = "neurodesk-cookie-consent";

export function CookieConsentBanner() {
  const { t } = useLanguage();
  const [isVisible, setVisible] = useState(false);

  useEffect(() => {
    if (window.localStorage.getItem(CONSENT_KEY) !== "accepted") {
      setVisible(true);
    }
  }, []);

  function handleAccept() {
    window.localStorage.setItem(CONSENT_KEY, "accepted");
    setVisible(false);
  }

  if (!isVisible) return null;

  return (
    <div
      role="region"
      aria-label={t("cookieConsent.aria")}
      className="fixed bottom-0 inset-x-0 z-[100] p-md sm:p-lg"
    >
      <div className="max-w-3xl mx-auto bg-surface-container-lowest border border-outline-variant/40 rounded-2xl shadow-2xl p-lg flex flex-col sm:flex-row items-start sm:items-center gap-md">
        <span className="material-symbols-outlined text-primary shrink-0 hidden sm:block">cookie</span>
        <p className="flex-1 text-body-sm text-on-surface-variant">
          {t("cookieConsent.message")}{" "}
          <a href="/gizlilik" className="text-primary hover:underline">
            {t("cookieConsent.privacyLink")}
          </a>
        </p>
        <button
          type="button"
          onClick={handleAccept}
          className="w-full sm:w-auto shrink-0 bg-primary text-on-primary px-lg py-2 rounded-full font-label-md hover:opacity-90 transition-opacity"
        >
          {t("cookieConsent.accept")}
        </button>
      </div>
    </div>
  );
}
