"use client";

import { useEffect } from "react";
import { reportClientError } from "@/lib/error-reporting";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    reportClientError(error, "app-error-boundary");
  }, [error]);

  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-md px-xl text-center bg-background">
      <span className="material-symbols-outlined text-error text-[64px]">error</span>
      <h1 className="font-headline-lg text-headline-lg text-on-background">Bir şeyler ters gitti</h1>
      <p className="text-body-md text-on-surface-variant max-w-md">
        Beklenmeyen bir hata oluştu. Bu otomatik olarak bize bildirildi, tekrar deneyebilirsin.
      </p>
      <div className="flex gap-md mt-md">
        <button
          type="button"
          onClick={() => reset()}
          className="bg-primary text-on-primary px-lg py-sm rounded-full font-label-md hover:opacity-90 transition-opacity"
        >
          Tekrar dene
        </button>
        <a
          href="/"
          className="border border-outline-variant text-on-surface px-lg py-sm rounded-full font-label-md hover:bg-surface-container-high transition-colors"
        >
          Ana sayfaya dön
        </a>
      </div>
    </main>
  );
}
