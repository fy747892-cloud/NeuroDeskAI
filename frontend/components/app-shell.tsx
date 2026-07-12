"use client";

import Link from "next/link";
import type { Route } from "next";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";
import { HealthStatus } from "@/lib/api";
import { UserMenu } from "@/components/user-menu";

const navItems = [
  { icon: "A", label: "Ana Sayfa", href: "/" },
  { icon: "AI", label: "AI Chat", href: "/ai-chat" },
  { icon: "AR", label: "Arama", href: "/arama" },
  { icon: "G", label: "Görüşmeler", href: "/gorusmeler" },
  { icon: "GV", label: "Görevler", href: "/gorevler" },
  { icon: "T", label: "Takvim", href: "/takvim" },
  { icon: "Ö", label: "Öncelik", href: "/oncelik" },
  { icon: "K", label: "Kişiler", href: "/kisiler" },
  { icon: "D", label: "Dosyalar", href: "/dosyalar" },
  { icon: "M", label: "Mailler", href: "/mailler" },
  { icon: "B", label: "Bildirimler", href: "/bildirimler" },
  { icon: "O", label: "Onay Merkezi", href: "/onay-merkezi" },
  { icon: "AN", label: "Analitik", href: "/analitik" },
  { icon: "AY", label: "Ayarlar", href: "/ayarlar" },
] satisfies Array<{ icon: string; label: string; href: Route }>;

type AppShellProps = {
  children: ReactNode;
  eyebrow?: string;
  health: HealthStatus;
};

export function AppShell({ children, eyebrow = "Çalışma alanı", health }: AppShellProps) {
  const pathname = usePathname();
  const currentItem = navItems.find((item) => isActive(pathname, item.href));
  const title = currentItem?.label ?? "Dashboard";

  return (
    <main className="shell">
      <aside className="sidebar" aria-label="Primary navigation">
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
          <div>
            <p className="eyebrow">{eyebrow}</p>
            <h1>{title}</h1>
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
