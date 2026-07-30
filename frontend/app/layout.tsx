import type { Metadata } from "next";
import { SessionProvider } from "@/lib/session";
import { LanguageProvider } from "@/lib/i18n/context";
import "./globals.css";

export const metadata: Metadata = {
  title: "NeuroDeskAI",
  description: "AI workspace dashboard for NeuroDeskAI operations.",
  icons: {
    icon: "/brand/neurodesk-mark.svg",
    shortcut: "/brand/neurodesk-mark.svg",
    apple: "/brand/neurodesk-mark.svg",
  },
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
        <LanguageProvider>
          <SessionProvider>{children}</SessionProvider>
        </LanguageProvider>
      </body>
    </html>
  );
}
