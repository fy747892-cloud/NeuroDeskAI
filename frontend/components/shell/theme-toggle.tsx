"use client";

import { useTheme } from "@/lib/theme";
import { useLanguage } from "@/lib/i18n/context";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const { t } = useLanguage();
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={isDark ? t("shell.theme.switchToLight") : t("shell.theme.switchToDark")}
      title={isDark ? t("shell.theme.switchToLight") : t("shell.theme.switchToDark")}
      className="text-on-surface-variant hover:text-primary transition-colors"
    >
      <span className="material-symbols-outlined">{isDark ? "light_mode" : "dark_mode"}</span>
    </button>
  );
}
