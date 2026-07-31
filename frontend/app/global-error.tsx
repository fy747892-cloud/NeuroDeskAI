"use client";

import { useEffect } from "react";
import { reportClientError } from "@/lib/error-reporting";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    reportClientError(error, "global-error-boundary");
  }, [error]);

  return (
    <html lang="tr">
      <body>
        <main
          style={{
            minHeight: "100vh",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: 16,
            padding: 32,
            textAlign: "center",
            fontFamily: "sans-serif",
            background: "#faf8ff",
            color: "#131b2e",
          }}
        >
          <h1 style={{ fontSize: 28, fontWeight: 700 }}>Uygulama başlatılamadı</h1>
          <p style={{ maxWidth: 420, color: "#464555" }}>
            Beklenmeyen bir hata oluştu. Bu otomatik olarak bize bildirildi.
          </p>
          <button
            type="button"
            onClick={() => reset()}
            style={{
              background: "#3525cd",
              color: "#ffffff",
              padding: "10px 24px",
              borderRadius: 999,
              border: "none",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Tekrar dene
          </button>
        </main>
      </body>
    </html>
  );
}
