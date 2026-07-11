import type { Metadata } from "next";
import { SessionProvider } from "@/lib/session";
import "./globals.css";

export const metadata: Metadata = {
  title: "NeuroDeskAI",
  description: "AI workspace dashboard for NeuroDeskAI operations.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="tr">
      <body>
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
