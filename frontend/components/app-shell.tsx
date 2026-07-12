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
    icon: "A",
    label: "Ana Sayfa",
    href: "/",
  },
  {
    description: "Çalışma alanındaki veriler üzerinden AI destekli sorular sor.",
    icon: "AI",
    label: "AI Chat",
    href: "/ai-chat",
  },
  {
    description: "Görev, kişi, görüşme ve randevuları anlamsal arama ile bul.",
    icon: "AR",
    label: "Arama",
    href: "/arama",
  },
  {
    description: "Görüşme kayıtlarını, çağrı transkriptlerini ve konuşma geçmişini yönet.",
    icon: "G",
    label: "Görüşmeler",
    href: "/gorusmeler",
  },
  {
    description: "Açık işleri, son tarihleri ve tamamlanan görevleri organize et.",
    icon: "GV",
    label: "Görevler",
    href: "/gorevler",
  },
  {
    description: "Yaklaşan randevuları, takvim hesaplarını ve zaman planını izle.",
    icon: "T",
    label: "Takvim",
    href: "/takvim",
  },
  {
    description: "AI skorlarıyla bugün hangi işe odaklanacağını hızlıca gör.",
    icon: "Ö",
    label: "Öncelik",
    href: "/oncelik",
  },
  {
    description: "Kişi hafızasını, şirket bilgilerini ve CRM kayıtlarını düzenle.",
    icon: "K",
    label: "Kişiler",
    href: "/kisiler",
  },
  {
    description: "Yüklenen dosyaları, analiz durumlarını ve belge özetlerini takip et.",
    icon: "D",
    label: "Dosyalar",
    href: "/dosyalar",
  },
  {
    description: "E-posta hesaplarını, mesaj özetlerini ve senkronizasyonu yönet.",
    icon: "M",
    label: "Mailler",
    href: "/mailler",
  },
  {
    description: "Planlanan bildirimleri, hatırlatmaları ve teslim durumlarını incele.",
    icon: "B",
    label: "Bildirimler",
    href: "/bildirimler",
  },
  {
    description: "AI önerilerini insan onayıyla güvenli şekilde aksiyona dönüştür.",
    icon: "O",
    label: "Onay Merkezi",
    href: "/onay-merkezi",
  },
  {
    description: "Kullanım metrikleri, AI maliyeti ve operasyon performansını gör.",
    icon: "AN",
    label: "Analitik",
    href: "/analitik",
  },
  {
    description: "Hesap, organizasyon, abonelik, rıza ve denetim ayarlarını yönet.",
    icon: "AY",
    label: "Ayarlar",
    href: "/ayarlar",
  },
] satisfies Array<{ description: string; icon: string; label: string; href: Route }>;

type AppShellProps = {
  children: ReactNode;
  eyebrow?: string;
  health: HealthStatus;
};

export function AppShell({ children, eyebrow = "Çalışma alanı", health }: AppShellProps) {
  const pathname = usePathname();
  const currentItem = navItems.find((item) => isActive(pathname, item.href));
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
              <span className="navIcon" aria-hidden="true">
                {item.icon}
              </span>
              {item.label}
            </Link>
          ))}
        </nav>
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
            <UserMenu />
          </div>
        </header>

        {children}
      </section>
    </main>
  );
}

function isActive(pathname: string, href: string): boolean {
  if (href === "/") {
    return pathname === "/";
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}
