export type HealthStatus = {
  ok: boolean;
  label: string;
};

export type AuthMode = "login" | "register";

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type AuthPayload = {
  email: string;
  password: string;
  displayName?: string;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    const message = await readErrorMessage(response);
    throw new Error(message);
  }

  return (await response.json()) as T;
}

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

export async function authenticate(mode: AuthMode, payload: AuthPayload): Promise<TokenResponse> {
  const path = mode === "login" ? "/api/v1/auth/login" : "/api/v1/auth/register";
  const body =
    mode === "login"
      ? { email: payload.email, password: payload.password }
      : {
          email: payload.email,
          password: payload.password,
          display_name: payload.displayName,
        };

  return request<TokenResponse>(path, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown; message?: string };
    if (typeof payload.message === "string") {
      return payload.message;
    }
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
    if (Array.isArray(payload.detail)) {
      return payload.detail
        .map((item) => {
          if (typeof item === "object" && item !== null && "msg" in item) {
            return String(item.msg);
          }
          return String(item);
        })
        .join(", ");
    }
  } catch {
    // Fall through to status text.
  }
  return response.statusText || "Request failed";
}
