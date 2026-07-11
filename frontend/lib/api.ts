export type HealthStatus = {
  ok: boolean;
  label: string;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function getHealthStatus(): Promise<HealthStatus> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      cache: "no-store",
      next: { revalidate: 0 },
    });

    if (!response.ok) {
      return { ok: false, label: "Backend unavailable" };
    }

    const payload = (await response.json()) as { status?: string };
    return {
      ok: payload.status === "ok",
      label: payload.status === "ok" ? "Backend online" : "Backend degraded",
    };
  } catch {
    return { ok: false, label: "Backend offline" };
  }
}
