import type { MetadataRoute } from "next";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      // The app is auth-gated; only the public marketing/legal/auth pages
      // are worth crawling. Token-bearing pages (reset/invite links) are
      // explicitly excluded so a crawler never caches a live token.
      allow: ["/giris", "/kayit", "/gizlilik", "/sifremi-unuttum"],
      disallow: ["/"],
    },
    sitemap: `${siteUrl}/sitemap.xml`,
  };
}
