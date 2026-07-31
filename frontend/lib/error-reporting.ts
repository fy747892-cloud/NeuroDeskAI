const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

type ReportedError = {
  message: string;
  stack?: string;
  digest?: string;
  url?: string;
  context?: string;
};

/**
 * Fire-and-forget client error report. Self-hosted Sentry substitute: logs
 * land in the backend's own DB/logs instead of a third-party SaaS account.
 */
export function reportClientError(error: unknown, context?: string): void {
  if (typeof window === "undefined") return;

  const payload: ReportedError = {
    message: error instanceof Error ? error.message : String(error),
    stack: error instanceof Error ? error.stack : undefined,
    digest: (error as { digest?: string } | undefined)?.digest,
    url: window.location.href,
    context,
  };

  fetch(`${API_BASE_URL}/api/v1/client-errors`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    keepalive: true,
  }).catch(() => {
    // Reporting is best-effort; never let a failed report cause a second error.
  });
}
