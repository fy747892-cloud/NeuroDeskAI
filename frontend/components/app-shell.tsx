"use client";

import Link from "next/link";
import type { Route } from "next";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";
import { HealthStatus } from "@/lib/api";
import { UserMenu } from "@/components/user-menu";

const navItems = [
  {
    description: "Günlük özet, öncelikler ve AI aksiyonlarını tek ekranda takip et.",
    icon: "dashboard",
    label: "Ana Sayfa",
    href: "/",
  },
  {
    description: "Çalışma alanındaki veriler üzerinden AI destekli sorular sor.",
    icon: "smart_toy",
    label: "AI Chat",
    href: "/ai-chat",
  },
  {
    description: "Görev, kişi, görüşme ve randevuları anlamsal arama ile bul.",
    icon: "search",
    label: "Arama",
    href: "/arama",
  },
  {
    description: "Görüşme kayıtlarını, çağrı transkriptlerini ve konuşma geçmişini yönet.",
    icon: "forum",
    label: "Görüşmeler",
    href: "/gorusmeler",
  },
  {
    description: "Açık işleri, son tarihleri ve tamamlanan görevleri organize et.",
    icon: "task_alt",
    label: "Görevler",
    href: "/gorevler",
  },
  {
    description: "Yaklaşan randevuları, takvim hesaplarını ve zaman planını izle.",
    icon: "calendar_today",
    label: "Takvim",
    href: "/takvim",
  },
  {
    description: "AI skorlarıyla bugün hangi işe odaklanacağını hızlıca gör.",
    icon: "bolt",
    label: "Öncelik",
    href: "/oncelik",
  },
  {
    description: "Kişi hafızasını, şirket bilgilerini ve CRM kayıtlarını düzenle.",
    icon: "contacts",
    label: "Kişiler",
    href: "/kisiler",
  },
  {
    description: "Satış fırsatlarını pipeline aşamalarına göre kanban panosunda takip et.",
    icon: "handshake",
    label: "Fırsatlar",
    href: "/firsatlar",
  },
  {
    description: "Yüklenen dosyaları, analiz durumlarını ve belge özetlerini takip et.",
    icon: "folder",
    label: "Dosyalar",
    href: "/dosyalar",
  },
  {
    description: "E-posta hesaplarını, mesaj özetlerini ve senkronizasyonu yönet.",
    icon: "mail",
    label: "Mailler",
    href: "/mailler",
  },
  {
    description: "Planlanan bildirimleri, hatırlatmaları ve teslim durumlarını incele.",
    icon: "notifications",
    label: "Bildirimler",
    href: "/bildirimler",
  },
  {
    description: "AI önerilerini insan onayıyla güvenli şekilde aksiyona dönüştür.",
    icon: "auto_awesome",
    label: "Onay Merkezi",
    href: "/onay-merkezi",
  },
  {
    description: "Kullanım metrikleri, AI maliyeti ve operasyon performansını gör.",
    icon: "analytics",
    label: "Analitik",
    href: "/analitik",
  },
] satisfies Array<{ description: string; icon: string; label: string; href: Route }>;

const settingsItem = {
  description: "Hesap, organizasyon, abonelik, rıza ve denetim ayarlarını yönet.",
  icon: "settings",
  label: "Ayarlar",
  href: "/ayarlar",
} satisfies { description: string; icon: string; label: string; href: Route };

type AppShellProps = {
  children: ReactNode;
  eyebrow?: string;
  health: HealthStatus;
};

export function AppShell({ children, eyebrow = "Çalışma alanı", health }: AppShellProps) {
  const pathname = usePathname();
  const currentItem = [...navItems, settingsItem].find((item) => isActive(pathname, item.href));
  const title = currentItem?.label ?? "Ana Sayfa";
  const description =
    currentItem?.description ?? "NeuroDesk AI çalışma alanındaki günlük operasyonlarını yönet.";

  return (
    <main className="shell">
      <aside className="sidebar" aria-label="Ana navigasyon">
        <div className="brand">
          <div className="brandMark">N</div>
          <div>
            <strong>NeuroDesk AI</strong>
            <span>Akıllı operasyon paneli</span>
          </div>
        </div>

        <nav>
          {navItems.map((item) => (
            <Link
              aria-current={isActive(pathname, item.href) ? "page" : undefined}
              className={isActive(pathname, item.href) ? "active" : ""}
              href={item.href}
              key={item.href}
            >
              <span className="material-symbols-outlined navIcon" aria-hidden="true">
                {item.icon}
              </span>
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="sidebarBottom">
          <Link
            aria-current={isActive(pathname, settingsItem.href) ? "page" : undefined}
            className={isActive(pathname, settingsItem.href) ? "active" : ""}
            href={settingsItem.href}
          >
            <span className="material-symbols-outlined navIcon" aria-hidden="true">
              {settingsItem.icon}
            </span>
            {settingsItem.label}
          </Link>
          <UserMenu />
          <Link className="voiceLink" href="/ai-chat">
            <span className="material-symbols-outlined" aria-hidden="true">
              mic
            </span>
            Sesli Komut
          </Link>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div className="topbarTitle">
            <p className="eyebrow">{eyebrow}</p>
            <h1>{title}</h1>
            <p>{description}</p>
          </div>
          <div className="topbarActions">
            <div className={`status ${health.ok ? "online" : "offline"}`}>
              <span aria-hidden="true" />
              {health.label}
            </div>
          </div>
        </header>

        {children}
      </section>

      <Link className="voiceFab" href="/ai-chat" aria-label="Sesli komut için AI Chat'e git">
        <span className="material-symbols-outlined" aria-hidden="true">
          mic
        </span>
      </Link>
    </main>
  );
}

function isActive(pathname: string, href: string): boolean {
  if (href === "/") {
    return pathname === "/";
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}
