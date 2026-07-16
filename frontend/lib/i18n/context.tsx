"use client";

import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from "react";
import { tr } from "./dictionaries/tr";
import { en } from "./dictionaries/en";
import type { TranslationDictionary } from "./dictionaries/types";

export type Language = "tr" | "en";

const dictionaries: Record<Language, TranslationDictionary> = { tr, en };

const LANGUAGE_STORAGE_KEY = "neurodesk-language";

type LanguageState = {
  language: Language;
  setLanguage: (language: Language) => void;
  t: (path: string, vars?: Record<string, string | number>) => string;
};

const LanguageContext = createContext<LanguageState | null>(null);

function resolvePath(dictionary: TranslationDictionary, path: string): string | undefined {
  const value = path
    .split(".")
    .reduce<TranslationDictionary | string | undefined>((acc, key) => {
      if (acc && typeof acc === "object") return acc[key];
      return undefined;
    }, dictionary);
  return typeof value === "string" ? value : undefined;
}

function interpolate(template: string, vars?: Record<string, string | number>): string {
  if (!vars) return template;
  return template.replace(/\{\{(\w+)\}\}/g, (_, key: string) => String(vars[key] ?? ""));
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>("tr");

  useEffect(() => {
    const stored = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
    if (stored === "tr" || stored === "en") {
      setLanguageState(stored);
    }
  }, []);

  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  function setLanguage(next: Language) {
    setLanguageState(next);
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, next);
  }

  const value = useMemo<LanguageState>(() => {
    const dictionary = dictionaries[language];
    const fallback = dictionaries.tr;
    return {
      language,
      setLanguage,
      t: (path, vars) => interpolate(resolvePath(dictionary, path) ?? resolvePath(fallback, path) ?? path, vars),
    };
  }, [language]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === null) {
    throw new Error("useLanguage must be used inside LanguageProvider.");
  }
  return context;
}
