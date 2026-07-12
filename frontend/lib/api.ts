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

export type UserProfile = {
  full_name: string;
  title: string | null;
  avatar_url: string | null;
};

export type CurrentUser = {
  id: string;
  email: string;
  tenant_id: string;
  organization_id: string | null;
  status: string;
  is_email_verified: boolean;
  created_at: string;
  profile: UserProfile | null;
};

export type DashboardSummary = {
  open_tasks_count: number;
  overdue_tasks_count: number;
  upcoming_appointments_count: number;
  pending_ai_approvals_count: number;
};

export type DashboardTask = {
  id: string;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  due_at: string | null;
  created_at: string;
};

export type Task = DashboardTask & {
  tenant_id: string;
  organization_id: string;
  user_id: string;
  contact_id: string | null;
  source_type: string;
  source_id: string | null;
  ai_action_approval_id: string | null;
};

export type DashboardAppointment = {
  id: string;
  title: string;
  description: string | null;
  location: string | null;
  start_at: string;
  end_at: string;
  status: string;
  created_at: string;
};

export type Appointment = DashboardAppointment & {
  tenant_id: string;
  organization_id: string;
  user_id: string;
  contact_id: string | null;
  timezone: string | null;
  source_type: string;
  source_id: string | null;
  ai_action_approval_id: string | null;
};

export type DashboardConversation = {
  id: string;
  title: string;
  status: string;
  created_at: string;
};

export type DashboardApproval = {
  id: string;
  action_type: string;
  source_type: string;
  status: string;
  confidence_score: number | null;
  created_at: string;
};

export type Conversation = DashboardConversation & {
  tenant_id: string;
  organization_id: string;
  user_id: string;
  source_type: string;
};

export type Contact = {
  id: string;
  tenant_id: string;
  organization_id: string;
  owner_user_id: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  company: string | null;
  title: string | null;
  tags: string[];
  status: string;
  created_at: string;
};

export type AIActionApproval = DashboardApproval & {
  tenant_id: string;
  organization_id: string;
  requested_by: string;
  decided_by: string | null;
  analysis_result_id: string;
  source_id: string;
  suggested_payload: Record<string, unknown>;
  approved_payload: Record<string, unknown> | null;
  expires_at: string | null;
  decided_at: string | null;
};

export type DashboardData = {
  summary: DashboardSummary;
  open_tasks: DashboardTask[];
  overdue_tasks: DashboardTask[];
  upcoming_appointments: DashboardAppointment[];
  recent_conversations: DashboardConversation[];
  pending_ai_approvals: DashboardApproval[];
  generated_at: string;
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

export async function getCurrentUser(accessToken: string): Promise<CurrentUser> {
  return request<CurrentUser>("/api/v1/users/me", {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function getDashboard(accessToken: string): Promise<DashboardData> {
  return request<DashboardData>("/api/v1/dashboard", {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function listTasks(accessToken: string, status?: string): Promise<Task[]> {
  const search = status ? `?status_filter=${encodeURIComponent(status)}` : "";
  return request<Task[]>(`/api/v1/tasks${search}`, {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function listOverdueTasks(accessToken: string): Promise<Task[]> {
  return request<Task[]>("/api/v1/tasks/overdue", {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function completeTask(accessToken: string, taskId: string): Promise<Task> {
  return request<Task>(`/api/v1/tasks/${taskId}/complete`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function listAppointments(
  accessToken: string,
  params: { startDate?: string; endDate?: string; status?: string } = {},
): Promise<Appointment[]> {
  const searchParams = new URLSearchParams();
  if (params.status) {
    searchParams.set("status_filter", params.status);
  }
  if (params.startDate) {
    searchParams.set("start_date", params.startDate);
  }
  if (params.endDate) {
    searchParams.set("end_date", params.endDate);
  }

  const search = searchParams.size > 0 ? `?${searchParams.toString()}` : "";
  return request<Appointment[]>(`/api/v1/appointments${search}`, {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function cancelAppointment(
  accessToken: string,
  appointmentId: string,
): Promise<Appointment> {
  return request<Appointment>(`/api/v1/appointments/${appointmentId}/cancel`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function listConversations(accessToken: string): Promise<Conversation[]> {
  return request<Conversation[]>("/api/v1/conversations", {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function listContacts(
  accessToken: string,
  params: { search?: string; status?: string } = {},
): Promise<Contact[]> {
  const searchParams = new URLSearchParams();
  if (params.search) {
    searchParams.set("search", params.search);
  }
  if (params.status) {
    searchParams.set("status_filter", params.status);
  }

  const search = searchParams.size > 0 ? `?${searchParams.toString()}` : "";
  return request<Contact[]>(`/api/v1/contacts${search}`, {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function listApprovals(
  accessToken: string,
  status?: string,
): Promise<AIActionApproval[]> {
  const search = status ? `?status_filter=${encodeURIComponent(status)}` : "";
  return request<AIActionApproval[]>(`/api/v1/ai/approvals${search}`, {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function approveAction(
  accessToken: string,
  approvalId: string,
): Promise<AIActionApproval> {
  return request<AIActionApproval>(`/api/v1/ai/approvals/${approvalId}/approve`, {
    method: "POST",
    body: JSON.stringify({ approved_payload: null }),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function rejectAction(
  accessToken: string,
  approvalId: string,
): Promise<AIActionApproval> {
  return request<AIActionApproval>(`/api/v1/ai/approvals/${approvalId}/reject`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function logout(refreshToken: string): Promise<void> {
  await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
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
