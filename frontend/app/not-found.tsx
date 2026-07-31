import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Sayfa Bulunamadı" };

export default function NotFound() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-md px-xl text-center bg-background">
      <span className="material-symbols-outlined text-primary text-[64px]">search_off</span>
      <h1 className="font-headline-lg text-headline-lg text-on-background">Sayfa bulunamadı</h1>
      <p className="text-body-md text-on-surface-variant max-w-md">
        Aradığın sayfa taşınmış, silinmiş olabilir ya da hiç var olmamış olabilir.
      </p>
      <Link
        href="/"
        className="mt-md bg-primary text-on-primary px-lg py-sm rounded-full font-label-md hover:opacity-90 transition-opacity"
      >
        Ana sayfaya dön
      </Link>
    </main>
  );
}
