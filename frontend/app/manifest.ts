import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "NeuroDesk AI",
    short_name: "NeuroDesk AI",
    description: "Görüşmeleri, görevleri, randevuları ve CRM'i tek panelde birleştiren AI destekli çalışma alanı.",
    start_url: "/",
    display: "standalone",
    background_color: "#faf8ff",
    theme_color: "#3525cd",
    lang: "tr",
    icons: [
      {
        src: "/brand/neurodesk-mark.svg",
        sizes: "any",
        type: "image/svg+xml",
        purpose: "any",
      },
      {
        src: "/brand/neurodesk-mark.svg",
        sizes: "any",
        type: "image/svg+xml",
        purpose: "maskable",
      },
    ],
  };
}
