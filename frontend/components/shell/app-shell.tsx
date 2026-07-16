"use client";

import Link from "next/link";
import type { Route } from "next";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";
import { openSearchPalette, SearchPalette } from "@/components/shell/search-palette";
import { NotificationBell } from "@/components/shell/notification-bell";
import { UserMenu } from "@/components/shell/user-menu";
import { LanguageSwitcher } from "@/components/shell/language-switcher";
import { useSession } from "@/lib/session";
import { useLanguage } from "@/lib/i18n/context";
import { getInitials } from "@/lib/format";

const navItems = [
  { icon: "dashboard", labelKey: "dashboard", href: "/" },
  { icon: "auto_awesome", labelKey: "aiActionCenter", href: "/onay-merkezi" },
  { icon: "forum", labelKey: "conversations", href: "/gorusmeler" },
  { icon: "task_alt", labelKey: "tasks", href: "/gorevler" },
  { icon: "contacts", labelKey: "contacts", href: "/kisiler" },
  { icon: "handshake", labelKey: "deals", href: "/firsatlar" },
  { icon: "smart_toy", labelKey: "aiChat", href: "/ai-chat" },
  { icon: "analytics", labelKey: "analytics", href: "/analitik" },
  { icon: "settings", labelKey: "settings", href: "/ayarlar" },
] satisfies Array<{ icon: string; labelKey: string; href: Route }>;

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { user } = useSession();
  const { t } = useLanguage();

  const displayName = user?.profile?.full_name ?? user?.email ?? "NeuroDesk";
  const planLabel = t("shell.planLabel");

  return (
    <div className="flex min-h-screen">
      <aside
        className="fixed h-full w-[260px] left-0 top-0 bg-surface-container-low shadow-sm flex flex-col py-md z-50"
        aria-label={t("shell.ariaMainNav")}
      >
        <div className="px-lg mb-xl">
          <h1 className="font-headline-md text-headline-md font-bold text-primary">NeuroDesk AI</h1>
          <p className="font-label-sm text-label-sm text-on-surface-variant opacity-70">
            {t("shell.subtitle")}
          </p>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto custom-scrollbar">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              aria-current={isActive(pathname, item.href) ? "page" : undefined}
              className={
                "flex items-center gap-3 px-4 py-3 font-label-md text-label-md transition-colors active:scale-95 duration-150 " +
                (isActive(pathname, item.href)
                  ? "text-primary bg-primary-container/10 border-l-2 border-primary"
                  : "text-on-surface-variant hover:bg-surface-container-high")
              }
            >
              <span className="material-symbols-outlined">{item.icon}</span>
              <span>{t(`shell.nav.${item.labelKey}`)}</span>
            </Link>
          ))}
          <button
            type="button"
            onClick={openSearchPalette}
            className="w-full flex items-center gap-3 px-4 py-3 font-label-md text-label-md text-on-surface-variant hover:bg-surface-container-high transition-colors active:scale-95 duration-150"
          >
            <span className="material-symbols-outlined">search</span>
            <span>{t("shell.nav.search")}</span>
            <kbd className="ml-auto text-[10px] text-outline border border-outline-variant/40 rounded px-1.5 py-0.5">
              ⌘K
            </kbd>
          </button>
        </nav>

        <div className="px-md mt-auto pt-md border-t border-outline-variant/30">
          <Link
            href="/ai-chat"
            className="w-full flex items-center justify-center gap-2 bg-primary text-on-primary py-3 rounded-xl font-label-md text-label-md active:scale-95 transition-transform"
          >
            <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>
              mic
            </span>
            {t("shell.voiceTrigger")}
          </Link>

          <div className="flex items-center gap-3 mt-md p-2 rounded-lg hover:bg-surface-container-high transition-colors">
            <div className="w-10 h-10 rounded-full bg-primary-container/20 flex items-center justify-center text-primary font-bold text-sm shrink-0">
              {getInitials(displayName)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-label-md text-label-md truncate">{displayName}</p>
              <p className="text-[10px] text-outline uppercase tracking-wider">{planLabel}</p>
            </div>
            <UserMenu />
          </div>
        </div>
      </aside>

      <div className="flex-1 ml-[260px] flex flex-col min-h-screen">
        <header className="flex justify-between items-center w-full px-xl py-md bg-surface sticky top-0 z-40">
          <div className="flex items-center gap-lg flex-1">
            <div className="relative w-full max-w-md">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">
                search
              </span>
              <button
                type="button"
                onClick={openSearchPalette}
                className="w-full text-left pl-10 pr-4 py-2 bg-surface-container-low border-none rounded-full font-body-sm text-on-surface-variant hover:bg-surface-container-high transition-colors"
              >
                {t("shell.topSearchPlaceholder")}
              </button>
            </div>
          </div>
          <div className="flex items-center gap-lg">
            <LanguageSwitcher />
            <NotificationBell />
            <Link
              href="/ayarlar"
              className="text-on-surface-variant hover:text-primary transition-colors"
              aria-label={t("shell.accountSettingsAria")}
            >
              <span className="material-symbols-outlined">account_circle</span>
            </Link>
          </div>
        </header>

        <main className="flex-1">{children}</main>
      </div>

      <Link
        href="/ai-chat"
        aria-label={t("shell.voiceAria")}
        className="fixed bottom-xl right-xl z-50 w-16 h-16 bg-primary text-on-primary rounded-full shadow-2xl flex items-center justify-center hover:scale-110 active:scale-95 transition-all"
      >
        <span className="material-symbols-outlined text-[32px]" style={{ fontVariationSettings: "'FILL' 1" }}>
          mic
        </span>
      </Link>

      <SearchPalette />
    </div>
  );
}

function isActive(pathname: string, href: string): boolean {
  if (href === "/") {
    return pathname === "/";
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}
