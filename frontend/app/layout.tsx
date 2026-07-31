import type { Metadata, Viewport } from "next";
import { Suspense } from "react";
import { SessionProvider } from "@/lib/session";
import { LanguageProvider } from "@/lib/i18n/context";
import { ServiceWorkerRegister } from "@/components/shell/service-worker-register";
import { CookieConsentBanner } from "@/components/shell/cookie-consent-banner";
import { GlobalErrorListener } from "@/components/shell/global-error-listener";
import { RouteProgressBar } from "@/components/shell/route-progress-bar";
import { ToastProvider } from "@/lib/toast";
import { Toaster } from "@/components/shell/toaster";
import "./globals.css";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
const siteDescription =
  "Görüşmeleri, görevleri, randevuları ve CRM'i tek panelde birleştiren AI destekli çalışma alanı.";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "NeuroDesk AI",
    template: "%s · NeuroDesk AI",
  },
  description: siteDescription,
  openGraph: {
    type: "website",
    locale: "tr_TR",
    siteName: "NeuroDesk AI",
    title: "NeuroDesk AI",
    description: siteDescription,
  },
  twitter: {
    card: "summary_large_image",
    title: "NeuroDesk AI",
    description: siteDescription,
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#faf8ff" },
    { media: "(prefers-color-scheme: dark)", color: "#121022" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="tr">
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var s=localStorage.getItem("neurodesk-theme");var d=s?s==="dark":window.matchMedia("(prefers-color-scheme: dark)").matches;document.documentElement.classList.toggle("dark",d);}catch(e){}})();`,
          }}
        />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Geist:wght@100..900&family=Inter:wght@100..900&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <ServiceWorkerRegister />
        <GlobalErrorListener />
        <Suspense fallback={null}>
          <RouteProgressBar />
        </Suspense>
        <LanguageProvider>
          <ToastProvider>
            <SessionProvider>{children}</SessionProvider>
            <CookieConsentBanner />
            <Toaster />
          </ToastProvider>
        </LanguageProvider>
      </body>
    </html>
  );
}
