"use client";

import Link from "next/link";
import type { Route } from "next";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";
import { HealthStatus } from "@/lib/api";
import { UserMenu } from "@/components/user-menu";

const navItems = [
  { label: "Dashboard", href: "/" },
  { label: "AI Chat", href: "/ai-chat" },
  { label: "Gorusmeler", href: "/gorusmeler" },
  { label: "Gorevler", href: "/gorevler" },
  { label: "Takvim", href: "/takvim" },
  { label: "Oncelik", href: "/oncelik" },
  { label: "Kisiler", href: "/kisiler" },
  { label: "Dosyalar", href: "/dosyalar" },
  { label: "Mailler", href: "/mailler" },
  { label: "Bildirimler", href: "/bildirimler" },
  { label: "Onay Merkezi", href: "/onay-merkezi" },
  { label: "Analitik", href: "/analitik" },
  { label: "Ayarlar", href: "/ayarlar" },
] satisfies Array<{ label: string; href: Route }>;

type AppShellProps = {
  children: ReactNode;
  eyebrow?: string;
  health: HealthStatus;
};

export function AppShell({ children, eyebrow = "Workspace overview", health }: AppShellProps) {
  const pathname = usePathname();
  const currentItem = navItems.find((item) => isActive(pathname, item.href));
  const title = currentItem?.label ?? "Dashboard";

  return (
    <main className="shell">
      <aside className="sidebar" aria-label="Primary navigation">
        <div className="brand">
          <div className="brandMark">N</div>
          <div>
            <strong>NeuroDeskAI</strong>
            <span>Operations</span>
          </div>
        </div>

        <nav>
          {navItems.map((item) => (
            <Link
              className={isActive(pathname, item.href) ? "active" : ""}
              href={item.href}
              key={item.href}
            >
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
