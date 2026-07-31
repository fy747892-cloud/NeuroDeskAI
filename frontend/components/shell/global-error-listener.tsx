"use client";

import { useEffect } from "react";
import { reportClientError } from "@/lib/error-reporting";

/**
 * Catches errors React's own error boundaries never see: exceptions thrown
 * outside render (event handlers, timers) and unhandled promise rejections.
 */
export function GlobalErrorListener() {
  useEffect(() => {
    function handleError(event: ErrorEvent) {
      reportClientError(event.error ?? new Error(event.message), "window-onerror");
    }
    function handleRejection(event: PromiseRejectionEvent) {
      reportClientError(event.reason, "unhandled-rejection");
    }

    window.addEventListener("error", handleError);
    window.addEventListener("unhandledrejection", handleRejection);
    return () => {
      window.removeEventListener("error", handleError);
      window.removeEventListener("unhandledrejection", handleRejection);
    };
  }, []);

  return null;
}
