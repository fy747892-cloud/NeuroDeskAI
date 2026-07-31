import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const apiOrigin = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

  // 'unsafe-inline' on script-src is a deliberate, narrow tradeoff: the app
  // has exactly one first-party inline script (the pre-paint dark-mode
  // toggle in app/layout.tsx) and no dangerouslySetInnerHTML of user content
  // anywhere, so a nonce-based CSP would force the whole app into dynamic
  // (per-request) rendering for negligible extra protection.
  const csp = [
    `default-src 'self'`,
    `script-src 'self' 'unsafe-inline'`,
    `style-src 'self' 'unsafe-inline' https://fonts.googleapis.com`,
    `font-src 'self' https://fonts.gstatic.com`,
    `img-src 'self' data: blob:`,
    `connect-src 'self' ${apiOrigin}`,
    `frame-ancestors 'none'`,
    `base-uri 'self'`,
    `form-action 'self'`,
    `object-src 'none'`,
    `upgrade-insecure-requests`,
  ].join("; ");

  const response = NextResponse.next();

  response.headers.set("Content-Security-Policy", csp);
  response.headers.set("X-Content-Type-Options", "nosniff");
  response.headers.set("X-Frame-Options", "DENY");
  response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
  response.headers.set("Permissions-Policy", "camera=(), microphone=(self), geolocation=(), interest-cohort=()");
  response.headers.set("Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload");

  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|sw.js|offline.html).*)"],
};
