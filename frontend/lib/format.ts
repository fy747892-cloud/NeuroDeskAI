import type { Language } from "@/lib/i18n/context";

function localeFor(language: Language = "tr"): string {
  return language === "tr" ? "tr-TR" : "en-US";
}

export function getInitials(name: string | null | undefined): string {
  if (!name) return "?";
  return (
    name
      .trim()
      .split(/\s+/)
      .map((part) => part[0])
      .slice(0, 2)
      .join("")
      .toUpperCase() || "?"
  );
}

export function formatTime(value: string, language?: Language): string {
  return new Intl.DateTimeFormat(localeFor(language), {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function formatDate(value: string, language?: Language): string {
  return new Intl.DateTimeFormat(localeFor(language), {
    day: "2-digit",
    month: "long",
  }).format(new Date(value));
}

export function formatDateTime(value: string, language?: Language): string {
  return new Intl.DateTimeFormat(localeFor(language), {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function formatRelative(value: string, language?: Language): string {
  const diffMs = Date.now() - new Date(value).getTime();
  const diffMin = Math.round(diffMs / 60_000);
  const isTr = (language ?? "tr") === "tr";
  if (diffMin < 1) return isTr ? "az önce" : "just now";
  if (diffMin < 60) return isTr ? `${diffMin} dk önce` : `${diffMin}m ago`;
  const diffHour = Math.round(diffMin / 60);
  if (diffHour < 24) return isTr ? `${diffHour} sa önce` : `${diffHour}h ago`;
  const diffDay = Math.round(diffHour / 24);
  return isTr ? `${diffDay} gün önce` : `${diffDay}d ago`;
}

export function formatMoney(value: number | null | undefined, currency = "TRY", language?: Language): string {
  if (value === null || value === undefined) return "-";
  return new Intl.NumberFormat(localeFor(language), {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}
