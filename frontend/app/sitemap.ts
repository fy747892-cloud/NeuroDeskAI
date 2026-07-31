import type { MetadataRoute } from "next";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  const routes = ["/giris", "/kayit", "/gizlilik", "/sifremi-unuttum"];

  return routes.map((route) => ({
    url: `${siteUrl}${route}`,
    lastModified: now,
    changeFrequency: "monthly",
    priority: route === "/giris" ? 1 : 0.5,
  }));
}
