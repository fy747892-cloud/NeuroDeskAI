import { ImageResponse } from "next/og";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          justifyContent: "center",
          padding: "80px",
          background: "linear-gradient(135deg, #3525cd 0%, #6b38d4 100%)",
          color: "#ffffff",
          fontFamily: "sans-serif",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 20,
            marginBottom: 40,
          }}
        >
          <div
            style={{
              display: "flex",
              width: 72,
              height: 72,
              borderRadius: 20,
              background: "rgba(255,255,255,0.2)",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 40,
              fontWeight: 700,
            }}
          >
            N
          </div>
          <div style={{ fontSize: 44, fontWeight: 700, letterSpacing: -1 }}>NeuroDesk AI</div>
        </div>
        <div style={{ fontSize: 34, fontWeight: 600, maxWidth: 900, lineHeight: 1.3 }}>
          İşinizi yöneten yapay zeka ortağınız.
        </div>
        <div style={{ fontSize: 24, opacity: 0.85, maxWidth: 900, marginTop: 20, lineHeight: 1.4 }}>
          Görüşmeler, görevler, randevular ve CRM tek panelde — AI önerir, siz onaylarsınız.
        </div>
      </div>
    ),
    { ...size },
  );
}
