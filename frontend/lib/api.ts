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

export type TaskCreatePayload = {
  title: string;
  description?: string | null;
  priority?: string;
  due_at?: string | null;
  repeat_count?: number | null;
  repeat_interval_days?: number;
};

export type TaskUpdatePayload = {
  title?: string;
  description?: string | null;
  status?: string;
  priority?: string;
  due_at?: string | null;
  contact_id?: string | null;
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

export type AppointmentCreatePayload = {
  title: string;
  description?: string | null;
  location?: string | null;
  start_at: string;
  end_at: string;
  timezone?: string | null;
  force?: boolean;
  repeat_count?: number | null;
  repeat_interval_days?: number;
};

export type AppointmentUpdatePayload = {
  title?: string;
  description?: string | null;
  location?: string | null;
  start_at?: string;
  end_at?: string;
  timezone?: string | null;
  status?: string;
  contact_id?: string | null;
  force?: boolean;
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

export type ConversationParticipant = {
  id: string;
  display_name: string;
  participant_type: string;
  participant_id?: string | null;
};

export type ConversationDetail = Conversation & {
  participants: ConversationParticipant[];
  calls: Call[];
};

export type AIAnalysisResult = {
  id: string;
  job_id: string;
  result_type: string;
  result_payload: Record<string, unknown>;
  created_at: string;
};

export type AIAnalysisJob = {
  id: string;
  tenant_id: string;
  organization_id: string;
  requested_by: string;
  source_type: string;
  source_id: string;
  status: string;
  attempts: number;
  error_message: string | null;
  queued_at: string;
  started_at: string | null;
  completed_at: string | null;
  results: AIAnalysisResult[];
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

export type ContactCreatePayload = {
  full_name: string;
  email?: string | null;
  phone?: string | null;
  company?: string | null;
  title?: string | null;
  tags?: string[];
};

export type ContactUpdatePayload = {
  full_name?: string;
  email?: string | null;
  phone?: string | null;
  company?: string | null;
  title?: string | null;
  tags?: string[];
  status?: string;
};

export type ContactNote = {
  id: string;
  contact_id: string;
  user_id: string;
  note_text: string;
  created_at: string;
};

export type ContactTimelineEvent = {
  id: string;
  contact_id: string;
  event_type: string;
  source_type: string | null;
  source_id: string | null;
  occurred_at: string;
  event_metadata: Record<string, unknown> | null;
};

export type ContactDetail = Contact & {
  notes: ContactNote[];
  recent_timeline: ContactTimelineEvent[];
};

export type ContactMemory = {
  contact_id: string;
  full_name: string;
  last_conversation: { id: string; title: string; occurred_at: string } | null;
  last_email: { id: string; subject: string | null; from_address: string | null; received_at: string | null } | null;
  last_topic: string | null;
  pending_items_count: number;
  open_deals_count: number;
  open_deals_total_value: number;
  next_appointment: { id: string; title: string; start_at: string } | null;
  generated_at: string;
};

export type AIActionApproval = DashboardApproval & {
  tenant_id: string;
  organization_id: string;
  requested_by: string;
  decided_by: string | null;
  analysis_result_id: string;
  source_id: string;
  source_title: string | null;
  suggested_payload: Record<string, unknown>;
  approved_payload: Record<string, unknown> | null;
  expires_at: string | null;
  decided_at: string | null;
};

export type Deal = {
  id: string;
  tenant_id: string;
  organization_id: string;
  owner_user_id: string;
  contact_id: string | null;
  title: string;
  description: string | null;
  value: number | null;
  currency: string;
  stage: string;
  expected_close_date: string | null;
  source_type: string;
  source_id: string | null;
  ai_action_approval_id: string | null;
  created_at: string;
};

export const DEAL_STAGES = [
  "lead",
  "proposal_sent",
  "negotiation",
  "invoiced",
  "won",
  "lost",
] as const;

export type DealStage = (typeof DEAL_STAGES)[number];

export type DealCreatePayload = {
  title: string;
  description?: string | null;
  value?: number | null;
  currency?: string;
  stage?: string;
  expected_close_date?: string | null;
  contact_id?: string | null;
};

export type DealUpdatePayload = Partial<DealCreatePayload>;

export type ConversationUpdatePayload = {
  title?: string;
  status?: string;
};

export type ConversationParticipantCreatePayload = {
  display_name: string;
  participant_type?: string;
  participant_id?: string | null;
};

export type ChatSource = {
  source_type: string;
  source_id: string;
  title: string;
  snippet: string;
};

export type ChatMessage = {
  id: string;
  session_id: string;
  role: string;
  content: string;
  confidence: number | null;
  sources: ChatSource[] | null;
  created_at: string;
};

export type ChatSession = {
  id: string;
  tenant_id: string;
  organization_id: string;
  user_id: string;
  title: string | null;
  status: string;
  created_at: string;
};

export type ChatSessionDetail = ChatSession & {
  messages: ChatMessage[];
};

export type SearchResult = {
  source_type: string;
  source_id: string;
  title: string;
  snippet: string;
  score: number;
};

export type ReindexSummary = {
  processed: number;
  created: number;
  updated: number;
  skipped: number;
};

export type AnalyticsOverview = {
  date_from: string;
  date_to: string;
  tasks_created: number;
  tasks_completed: number;
  tasks_overdue: number;
  calls_total: number;
  calls_analyzed: number;
  appointments_completed: number;
  appointments_upcoming: number;
  ai_requests: number;
  ai_cost_amount: number;
};

export type TaskMetric = {
  date: string;
  created_count: number;
  completed_count: number;
  overdue_count: number;
};

export type CallMetric = {
  date: string;
  call_count: number;
  analyzed_count: number;
};

export type AppointmentMetric = {
  date: string;
  completed_count: number;
  upcoming_count: number;
};

export type AIMetric = {
  date: string;
  request_count: number;
  cost_amount: number;
  avg_latency_ms: number;
};

export type EmailAccount = {
  id: string;
  tenant_id: string;
  organization_id: string;
  user_id: string;
  provider: string;
  email_address: string | null;
  status: string;
  consent_granted_at: string | null;
  consent_scope: string | null;
  last_synced_at: string | null;
  created_at: string;
};

export type EmailMessage = {
  id: string;
  email_account_id: string;
  provider_message_id: string;
  thread_id: string | null;
  subject: string | null;
  from_address: string | null;
  snippet: string | null;
  received_at: string | null;
  is_replied: boolean;
};

export type EmailSyncSummary = {
  fetched: number;
  created: number;
  skipped: number;
};

export type EmailConnectStart = {
  authorize_url: string;
  state: string;
};

export type EmailProvider = "gmail" | "outlook";

export type FileRecord = {
  id: string;
  tenant_id: string;
  organization_id: string;
  owner_user_id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  status: string;
  created_at: string;
};

export type FileUpdatePayload = {
  filename: string;
};

export type FileAnalysis = {
  file_id: string;
  summary: string | null;
  status: string;
};

export type FileText = {
  file_id: string;
  extracted_text: string | null;
  status: string;
};

export type BillingPlan = {
  id: string;
  code: string;
  name: string;
  price: number;
  billing_period: string;
  status: string;
};

export type Subscription = {
  tenant_id: string;
  status: string;
  current_period_end: string;
  plan: BillingPlan;
};

export type UsageSummary = {
  quota_type: string;
  period: string;
  limit_value: number;
  used: number;
  remaining: number;
};

export type Notification = {
  id: string;
  tenant_id: string;
  organization_id: string;
  user_id: string;
  title: string;
  body: string;
  notification_type: string;
  channel: string;
  source_type: string | null;
  source_id: string | null;
  status: string;
  scheduled_at: string;
  sent_at: string | null;
  read_at: string | null;
  attempts: number;
  max_attempts: number;
  error_message: string | null;
  created_at: string;
};

export type ProcessDueSummary = {
  processed: number;
  sent: number;
  failed: number;
  dead_lettered: number;
};

export type MarkAllReadResult = {
  updated: number;
};

export type ConsentSettings = {
  ai_processing: boolean;
  contact_memory: boolean;
  operational_reminders: boolean;
};

export type PriorityFactor = {
  key: string;
  label: string;
  weight: number;
};

export type PriorityItem = {
  item_type: string;
  item_id: string;
  title: string;
  status: string;
  score: number;
  priority: string;
  due_at: string | null;
  contact_id: string | null;
  factors: PriorityFactor[];
};

export type PriorityQueue = {
  generated_at: string;
  items: PriorityItem[];
};

export type CallTranscription = {
  id: string;
  call_id: string;
  language: string | null;
  status: string;
  transcript_text: string;
  created_at: string;
};

export type Call = {
  id: string;
  conversation_id: string;
  call_direction: string | null;
  phone_number: string | null;
  started_at: string | null;
  duration_seconds: number | null;
  status: string;
  created_at: string;
  transcriptions: CallTranscription[];
};

export type CallTextCreatePayload = {
  title: string;
  transcript_text: string;
  participant_names?: string[];
  call_direction?: string | null;
  phone_number?: string | null;
  language?: string | null;
};

export type CallTextResult = {
  conversation: Conversation;
  call: Call;
  transcription: CallTranscription;
};

export type CallAudioCreatePayload = {
  title: string;
  audio: Blob;
  participant_names?: string[];
  call_direction?: string | null;
  phone_number?: string | null;
  language?: string;
  duration_seconds?: number | null;
};

export type CalendarAccount = {
  id: string;
  tenant_id: string;
  organization_id: string;
  user_id: string;
  provider: string;
  external_account_id: string | null;
  status: string;
  connected_at: string | null;
  created_at: string;
};

export type VoiceCommandResult = {
  transcript: {
    text: string;
    language: string;
    provider: string;
    confidence: number;
  };
  action: {
    intent: string;
    action_type: string;
    confidence: number;
    suggested_payload: Record<string, unknown>;
    requires_approval: boolean;
  };
  spoken_response: string;
};

export type Organization = {
  id: string;
  tenant_id: string;
  name: string;
  type: string;
  status: string;
  created_at: string;
};

export type OrganizationMember = {
  id: string;
  tenant_id: string;
  organization_id: string;
  user_id: string;
  role: string;
  status: string;
  created_at: string;
  email: string | null;
  full_name: string | null;
  avatar_url: string | null;
};

export type AuditLog = {
  id: string;
  tenant_id: string;
  actor_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  request_id: string | null;
  ip_address: string | null;
  user_agent: string | null;
  audit_metadata: Record<string, unknown> | null;
  created_at: string;
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
  totpCode?: string;
  recoveryCode?: string;
};

export type MfaRequiredResponse = {
  mfa_required: true;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
    });
  } catch {
    throw new Error(`Sunucuya bağlanılamadı. Kullanılan backend adresi: ${API_BASE_URL}. Backend'in çalıştığını, NEXT_PUBLIC_API_BASE_URL ayarını ve CORS izinlerini kontrol edin.`);
  }

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
      return { ok: false, label: "Backend erişilemiyor" };
    }

    const payload = (await response.json()) as { status?: string };
    return {
      ok: payload.status === "ok",
      label: payload.status === "ok" ? "Backend çalışıyor" : "Backend kararsız",
    };
  } catch {
    return { ok: false, label: "Backend çevrim dışı" };
  }
}

export async function authenticate(
  mode: AuthMode,
  payload: AuthPayload,
): Promise<TokenResponse | MfaRequiredResponse> {
  const path = mode === "login" ? "/api/v1/auth/login" : "/api/v1/auth/register";
  const body =
    mode === "login"
      ? {
          email: payload.email,
          password: payload.password,
          totp_code: payload.totpCode || undefined,
          recovery_code: payload.recoveryCode || undefined,
        }
      : {
          email: payload.email,
          password: payload.password,
          display_name: payload.displayName,
        };

  const response = await request<{
    mfa_required: boolean;
    access_token: string | null;
    refresh_token: string | null;
    token_type: string;
  }>(path, {
    method: "POST",
    body: JSON.stringify(body),
  });

  if (response.mfa_required || !response.access_token || !response.refresh_token) {
    return { mfa_required: true };
  }

  return {
    access_token: response.access_token,
    refresh_token: response.refresh_token,
    token_type: response.token_type,
  };
}

export async function getGoogleLoginUrl(): Promise<{ authorize_url: string }> {
  return request<{ authorize_url: string }>("/api/v1/auth/google/login", {
    cache: "no-store",
  });
}

export async function exchangeGoogleLoginCode(loginCode: string): Promise<TokenResponse> {
  return request<TokenResponse>("/api/v1/auth/google/exchange", {
    method: "POST",
    body: JSON.stringify({ login_code: loginCode }),
  });
}

export async function requestPasswordReset(email: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
}

export async function resetPassword(token: string, newPassword: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, new_password: newPassword }),
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
}

export async function acceptInvite(
  token: string,
  password: string,
  displayName: string,
): Promise<TokenResponse> {
  return request<TokenResponse>("/api/v1/auth/accept-invite", {
    method: "POST",
    body: JSON.stringify({ token, password, display_name: displayName }),
  });
}

export async function getCurrentUser(accessToken: string): Promise<CurrentUser> {
  return request<CurrentUser>("/api/v1/users/me", {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function updateProfile(
  accessToken: string,
  payload: { full_name?: string; title?: string | null; avatar_url?: string | null },
): Promise<CurrentUser> {
  return request<CurrentUser>("/api/v1/users/me", {
    method: "PATCH",
    body: JSON.stringify(payload),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function uploadAvatar(accessToken: string, file: File): Promise<CurrentUser> {
  const formData = new FormData();
  formData.set("file", file);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/users/me/avatar`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      body: formData,
    });
  } catch {
    throw new Error(
      "Profil fotoğrafı backend'e gönderilemedi. Backend'in çalıştığını, API adresini ve ağ bağlantınızı kontrol edin.",
    );
  }

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return (await response.json()) as CurrentUser;
}

export async function deleteAvatar(accessToken: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/users/me/avatar`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
}

export async function getConsentSettings(accessToken: string): Promise<ConsentSettings> {
  return request<ConsentSettings>("/api/v1/users/me/consent", {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function updateConsentSettings(
  accessToken: string,
  consent: ConsentSettings,
): Promise<ConsentSettings> {
  return request<ConsentSettings>("/api/v1/users/me/consent", {
    method: "PATCH",
    body: JSON.stringify(consent),
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

export async function updateTask(
  accessToken: string,
  taskId: string,
  payload: TaskUpdatePayload,
): Promise<Task> {
  return request<Task>(`/api/v1/tasks/${taskId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function deleteTask(accessToken: string, taskId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/tasks/${taskId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
}

export async function createTask(
  accessToken: string,
  payload: TaskCreatePayload,
): Promise<Task> {
  return request<Task>("/api/v1/tasks", {
    method: "POST",
    body: JSON.stringify({
      title: payload.title,
      description: payload.description ?? null,
      priority: payload.priority ?? "medium",
      due_at: payload.due_at ?? null,
      repeat_count: payload.repeat_count ?? null,
      repeat_interval_days: payload.repeat_interval_days ?? 7,
    }),
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

export async function createAppointment(
  accessToken: string,
  payload: AppointmentCreatePayload,
): Promise<Appointment> {
  return request<Appointment>("/api/v1/appointments", {
    method: "POST",
    body: JSON.stringify({
      title: payload.title,
      description: payload.description ?? null,
      location: payload.location ?? null,
      start_at: payload.start_at,
      end_at: payload.end_at,
      timezone: payload.timezone ?? "Europe/Istanbul",
      force: payload.force ?? false,
      repeat_count: payload.repeat_count ?? null,
      repeat_interval_days: payload.repeat_interval_days ?? 7,
    }),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function updateAppointment(
  accessToken: string,
  appointmentId: string,
  payload: AppointmentUpdatePayload,
): Promise<Appointment> {
  return request<Appointment>(`/api/v1/appointments/${appointmentId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function deleteAppointment(accessToken: string, appointmentId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/appointments/${appointmentId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
}

export async function listConversations(accessToken: string): Promise<Conversation[]> {
  return request<Conversation[]>("/api/v1/conversations", {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function getConversation(
  accessToken: string,
  conversationId: string,
): Promise<ConversationDetail> {
  return request<ConversationDetail>(`/api/v1/conversations/${conversationId}`, {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function updateConversation(
  accessToken: string,
  conversationId: string,
  payload: ConversationUpdatePayload,
): Promise<ConversationDetail> {
  return request<ConversationDetail>(`/api/v1/conversations/${conversationId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function addConversationParticipant(
  accessToken: string,
  conversationId: string,
  payload: ConversationParticipantCreatePayload,
): Promise<ConversationParticipant> {
  return request<ConversationParticipant>(`/api/v1/conversations/${conversationId}/participants`, {
    method: "POST",
    body: JSON.stringify({
      display_name: payload.display_name,
      participant_type: payload.participant_type ?? "manual",
      participant_id: payload.participant_id ?? null,
    }),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function listAnalysisJobs(accessToken: string): Promise<AIAnalysisJob[]> {
  return request<AIAnalysisJob[]>("/api/v1/ai/analysis/jobs", {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function requestConversationAnalysis(
  accessToken: string,
  conversationId: string,
): Promise<AIAnalysisJob> {
  return request<AIAnalysisJob>(`/api/v1/ai/analysis/conversations/${conversationId}`, {
    method: "POST",
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

export async function createContact(
  accessToken: string,
  payload: ContactCreatePayload,
): Promise<Contact> {
  return request<Contact>("/api/v1/contacts", {
    method: "POST",
    body: JSON.stringify({
      full_name: payload.full_name,
      email: payload.email ?? null,
      phone: payload.phone ?? null,
      company: payload.company ?? null,
      title: payload.title ?? null,
      tags: payload.tags ?? [],
    }),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function getContact(accessToken: string, contactId: string): Promise<ContactDetail> {
  return request<ContactDetail>(`/api/v1/contacts/${contactId}`, {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function updateContact(
  accessToken: string,
  contactId: string,
  payload: ContactUpdatePayload,
): Promise<Contact> {
  return request<Contact>(`/api/v1/contacts/${contactId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function deleteContact(accessToken: string, contactId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/contacts/${contactId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
}

export async function getContactMemory(accessToken: string, contactId: string): Promise<ContactMemory> {
  return request<ContactMemory>(`/api/v1/contacts/${contactId}/memory`, {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function addContactNote(
  accessToken: string,
  contactId: string,
  noteText: string,
): Promise<ContactNote> {
  return request<ContactNote>(`/api/v1/contacts/${contactId}/notes`, {
    method: "POST",
    body: JSON.stringify({ note_text: noteText }),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function listDeals(accessToken: string, stage?: string): Promise<Deal[]> {
  const search = stage ? `?stage=${encodeURIComponent(stage)}` : "";
  return request<Deal[]>(`/api/v1/deals${search}`, {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function createDeal(accessToken: string, payload: DealCreatePayload): Promise<Deal> {
  return request<Deal>("/api/v1/deals", {
    method: "POST",
    body: JSON.stringify({
      title: payload.title,
      description: payload.description ?? null,
      value: payload.value ?? null,
      currency: payload.currency ?? "TRY",
      stage: payload.stage ?? "lead",
      expected_close_date: payload.expected_close_date ?? null,
      contact_id: payload.contact_id ?? null,
    }),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function updateDeal(
  accessToken: string,
  dealId: string,
  payload: DealUpdatePayload,
): Promise<Deal> {
  return request<Deal>(`/api/v1/deals/${dealId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function deleteDeal(accessToken: string, dealId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/deals/${dealId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
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
  const approval = await request<AIActionApproval>(`/api/v1/ai/approvals/${approvalId}/approve`, {
    method: "POST",
    body: JSON.stringify({ approved_payload: null }),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  await materializeApprovedAction(accessToken, approval);
  return approval;
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

// Newer backend deployments may materialize during approval; this fallback
// keeps older deployments creating the task/appointment/deal as well.
async function materializeApprovedAction(accessToken: string, approval: AIActionApproval): Promise<void> {
  const endpoint =
    approval.action_type === "task" || approval.action_type === "create_task" || approval.action_type === "task/create_task"
      ? "/api/v1/tasks/from-approval"
      : approval.action_type === "appointment" ||
          approval.action_type === "create_appointment" ||
          approval.action_type === "appointment/create_appointment"
        ? "/api/v1/appointments/from-approval"
        : approval.action_type === "deal" || approval.action_type === "create_deal" || approval.action_type === "deal/create_deal"
          ? "/api/v1/deals/from-approval"
          : null;

  if (!endpoint) return;

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ approval_id: approval.id }),
  });

  if (!response.ok && response.status !== 409) {
    throw new Error(await readErrorMessage(response));
  }
}

export async function createTaskFromApproval(accessToken: string, approvalId: string): Promise<Task> {
  return request<Task>("/api/v1/tasks/from-approval", {
    method: "POST",
    body: JSON.stringify({ approval_id: approvalId }),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function createAppointmentFromApproval(
  accessToken: string,
  approvalId: string,
): Promise<Appointment> {
  return request<Appointment>("/api/v1/appointments/from-approval", {
    method: "POST",
    body: JSON.stringify({ approval_id: approvalId }),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function createDealFromApproval(accessToken: string, approvalId: string): Promise<Deal> {
  return request<Deal>("/api/v1/deals/from-approval", {
    method: "POST",
    body: JSON.stringify({ approval_id: approvalId }),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function listChatSessions(accessToken: string): Promise<ChatSession[]> {
  return request<ChatSession[]>("/api/v1/ai/chat/sessions", {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function getChatSession(
  accessToken: string,
  sessionId: string,
): Promise<ChatSessionDetail> {
  return request<ChatSessionDetail>(`/api/v1/ai/chat/sessions/${sessionId}`, {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function renameChatSession(
  accessToken: string,
  sessionId: string,
  title: string,
): Promise<ChatSession> {
  return request<ChatSession>(`/api/v1/ai/chat/sessions/${sessionId}`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function deleteChatSession(accessToken: string, sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/ai/chat/sessions/${sessionId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
}

export async function sendChatMessage(
  accessToken: string,
  payload: { message: string; sessionId?: string | null },
): Promise<ChatMessage> {
  return request<ChatMessage>("/api/v1/ai/chat", {
    method: "POST",
    body: JSON.stringify({
      message: payload.message,
      session_id: payload.sessionId ?? null,
    }),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function semanticSearch(
  accessToken: string,
  query: string,
  limit = 8,
): Promise<SearchResult[]> {
  return request<SearchResult[]>("/api/v1/search/semantic", {
    method: "POST",
    body: JSON.stringify({ query, limit }),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function reindexSearch(accessToken: string): Promise<ReindexSummary> {
  return request<ReindexSummary>("/api/v1/search/reindex", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function getAnalyticsOverview(
  accessToken: string,
  params: { dateFrom?: string; dateTo?: string } = {},
): Promise<AnalyticsOverview> {
  const search = new URLSearchParams();
  if (params.dateFrom) search.set("date_from", params.dateFrom);
  if (params.dateTo) search.set("date_to", params.dateTo);
  const query = search.size > 0 ? `?${search.toString()}` : "";
  return request<AnalyticsOverview>(`/api/v1/analytics/overview${query}`, {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function getTaskAnalytics(accessToken: string): Promise<TaskMetric[]> {
  return request<TaskMetric[]>("/api/v1/analytics/tasks", {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function getCallAnalytics(accessToken: string): Promise<CallMetric[]> {
  return request<CallMetric[]>("/api/v1/analytics/calls", {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function getAiAnalytics(accessToken: string): Promise<AIMetric[]> {
  return request<AIMetric[]>("/api/v1/analytics/ai", {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function runAnalyticsAggregate(accessToken: string): Promise<void> {
  await request("/api/v1/analytics/aggregate", {
    method: "POST",
    body: JSON.stringify({}),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function listEmailAccounts(accessToken: string): Promise<EmailAccount[]> {
  return request<EmailAccount[]>("/api/v1/email/accounts", {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function startGmailConnect(accessToken: string): Promise<EmailConnectStart> {
  return startEmailConnect(accessToken, "gmail");
}

export async function startOutlookConnect(accessToken: string): Promise<EmailConnectStart> {
  return startEmailConnect(accessToken, "outlook");
}

export async function startEmailConnect(
  accessToken: string,
  provider: EmailProvider,
): Promise<EmailConnectStart> {
  return request<EmailConnectStart>(`/api/v1/email/${provider}/connect`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function revokeEmailAccount(
  accessToken: string,
  accountId: string,
): Promise<EmailAccount> {
  return request<EmailAccount>(`/api/v1/email/accounts/${accountId}/revoke`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function refreshEmailAccountToken(
  accessToken: string,
  accountId: string,
): Promise<EmailAccount> {
  return request<EmailAccount>(`/api/v1/email/accounts/${accountId}/refresh-token`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function listEmailMessages(
  accessToken: string,
  accountId: string,
): Promise<EmailMessage[]> {
  return request<EmailMessage[]>(`/api/v1/email/accounts/${accountId}/messages`, {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function markEmailReplied(accessToken: string, messageId: string): Promise<EmailMessage> {
  return request<EmailMessage>(`/api/v1/email/messages/${messageId}/mark-replied`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function syncEmailAccount(
  accessToken: string,
  accountId: string,
): Promise<EmailSyncSummary> {
  return request<EmailSyncSummary>(`/api/v1/email/accounts/${accountId}/sync`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function listFiles(accessToken: string): Promise<FileRecord[]> {
  return request<FileRecord[]>("/api/v1/files", {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function analyzeFile(accessToken: string, fileId: string): Promise<FileAnalysis> {
  return request<FileAnalysis>(`/api/v1/files/${fileId}/analyze`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function updateFile(
  accessToken: string,
  fileId: string,
  payload: FileUpdatePayload,
): Promise<FileRecord> {
  return request<FileRecord>(`/api/v1/files/${fileId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function deleteFile(accessToken: string, fileId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/files/${fileId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
}

export async function listBillingPlans(accessToken: string): Promise<BillingPlan[]> {
  return request<BillingPlan[]>("/api/v1/billing/plans", {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function switchPlan(accessToken: string, planCode: string): Promise<Subscription> {
  return request<Subscription>("/api/v1/billing/subscription", {
    method: "PATCH",
    body: JSON.stringify({ plan_code: planCode }),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function inviteOrganizationMember(
  accessToken: string,
  email: string,
  role: string,
): Promise<OrganizationMember> {
  return request<OrganizationMember>("/api/v1/organizations/members/invite", {
    method: "POST",
    body: JSON.stringify({ email, role }),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function updateMemberRole(
  accessToken: string,
  memberId: string,
  role: string,
): Promise<OrganizationMember> {
  return request<OrganizationMember>(`/api/v1/organizations/members/${memberId}/role`, {
    method: "PATCH",
    body: JSON.stringify({ role }),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function getSubscription(accessToken: string): Promise<Subscription> {
  return request<Subscription>("/api/v1/billing/subscription", {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function getUsageSummary(accessToken: string): Promise<UsageSummary> {
  return request<UsageSummary>("/api/v1/billing/usage", {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function listNotifications(
  accessToken: string,
  status?: string,
): Promise<Notification[]> {
  const search = status ? `?status_filter=${encodeURIComponent(status)}` : "";
  return request<Notification[]>(`/api/v1/notifications${search}`, {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function markNotificationRead(
  accessToken: string,
  notificationId: string,
): Promise<Notification> {
  return request<Notification>(`/api/v1/notifications/${notificationId}/read`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function markAllNotificationsRead(accessToken: string): Promise<MarkAllReadResult> {
  return request<MarkAllReadResult>("/api/v1/notifications/read-all", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function processDueNotifications(accessToken: string): Promise<ProcessDueSummary> {
  return request<ProcessDueSummary>("/api/v1/notifications/process-due", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function getPriorityQueue(accessToken: string, limit = 25): Promise<PriorityQueue> {
  return request<PriorityQueue>(`/api/v1/priority/queue?limit=${limit}`, {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function listCalls(accessToken: string): Promise<Call[]> {
  return request<Call[]>("/api/v1/calls", {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function createCallFromText(
  accessToken: string,
  payload: CallTextCreatePayload,
): Promise<CallTextResult> {
  return request<CallTextResult>("/api/v1/calls/text", {
    method: "POST",
    body: JSON.stringify({
      title: payload.title,
      transcript_text: payload.transcript_text,
      participant_names: payload.participant_names ?? [],
      call_direction: payload.call_direction ?? null,
      phone_number: payload.phone_number ?? null,
      language: payload.language ?? "tr",
    }),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function getFileAnalysis(accessToken: string, fileId: string): Promise<FileAnalysis> {
  return request<FileAnalysis>(`/api/v1/files/${fileId}/analysis`, {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function getFileText(accessToken: string, fileId: string): Promise<FileText> {
  return request<FileText>(`/api/v1/files/${fileId}/text`, {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function getFileDownloadUrl(accessToken: string, fileId: string): Promise<string> {
  const response = await request<{ download_url: string }>(`/api/v1/files/${fileId}/download-url`, {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  return response.download_url;
}

export async function uploadFile(accessToken: string, file: File): Promise<FileRecord> {
  const mimeType = mimeTypeForFile(file);
  const start = await request<{ file_id: string; upload_url: string; expires_in: number }>("/api/v1/files/upload-url", {
    method: "POST",
    body: JSON.stringify({
      filename: file.name,
      mime_type: mimeType,
      size_bytes: file.size,
    }),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  const uploadResponse = await fetch(start.upload_url, {
    method: "PUT",
    headers: {
      "Content-Type": mimeType,
    },
    body: file,
  });

  if (!uploadResponse.ok) {
    throw new Error(await readErrorMessage(uploadResponse));
  }

  return request<FileRecord>("/api/v1/files/complete-upload", {
    method: "POST",
    body: JSON.stringify({ file_id: start.file_id }),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function createCallFromAudio(
  accessToken: string,
  payload: CallAudioCreatePayload,
): Promise<CallTextResult> {
  const formData = new FormData();
  formData.set("title", payload.title);
  formData.set("participant_names", payload.participant_names?.join(",") ?? "");
  formData.set("language", payload.language ?? "tr");
  if (payload.call_direction) {
    formData.set("call_direction", payload.call_direction);
  }
  if (payload.phone_number) {
    formData.set("phone_number", payload.phone_number);
  }
  if (typeof payload.duration_seconds === "number") {
    formData.set("duration_seconds", String(payload.duration_seconds));
  }
  formData.set("audio", payload.audio, "web-recording.webm");

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/calls/audio`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      body: formData,
    });
  } catch {
    throw new Error(
      "Ses kaydı backend'e gönderilemedi. Backend'in çalıştığını, API adresini ve ağ bağlantınızı kontrol edin.",
    );
  }

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return (await response.json()) as CallTextResult;
}

export async function deleteCall(accessToken: string, callId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/calls/${callId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
}

export async function deleteConversation(accessToken: string, conversationId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/conversations/${conversationId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
}

export async function listCalendarAccounts(accessToken: string): Promise<CalendarAccount[]> {
  return request<CalendarAccount[]>("/api/v1/calendar/accounts", {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function connectGoogleCalendar(accessToken: string): Promise<CalendarAccount> {
  return request<CalendarAccount>("/api/v1/calendar/google/connect", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function interpretVoiceCommand(
  accessToken: string,
  text: string,
): Promise<VoiceCommandResult> {
  return request<VoiceCommandResult>("/api/v1/voice/commands/interpret", {
    method: "POST",
    body: JSON.stringify({ text, locale: "tr-TR" }),
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function getCurrentOrganization(accessToken: string): Promise<Organization> {
  return request<Organization>("/api/v1/organizations/current", {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function listOrganizationMembers(accessToken: string): Promise<OrganizationMember[]> {
  return request<OrganizationMember[]>("/api/v1/organizations/members", {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function listAuditLogs(accessToken: string, limit = 50): Promise<AuditLog[]> {
  return request<AuditLog[]>(`/api/v1/audit-logs?limit=${limit}`, {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function refreshAccessToken(refreshToken: string): Promise<TokenResponse> {
  return request<TokenResponse>("/api/v1/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
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

export async function logoutAllSessions(accessToken: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/logout-all`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
}

export type UserSession = {
  id: string;
  device_id: string | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
  expires_at: string;
};

export async function listSessions(accessToken: string): Promise<UserSession[]> {
  return request<UserSession[]>("/api/v1/auth/sessions", {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function revokeSession(accessToken: string, sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/sessions/${sessionId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
}

export async function exportMyData(accessToken: string): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>("/api/v1/users/me/export", {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function deleteMyAccount(accessToken: string, password: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/users/me`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ password }),
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
}

export type TotpStatus = {
  enabled: boolean;
};

export async function getTotpStatus(accessToken: string): Promise<TotpStatus> {
  return request<TotpStatus>("/api/v1/auth/2fa/status", {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export type TotpSetup = {
  secret: string;
  otpauth_url: string;
};

export async function setupTotp(accessToken: string): Promise<TotpSetup> {
  return request<TotpSetup>("/api/v1/auth/2fa/setup", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function verifyTotp(accessToken: string, code: string): Promise<{ recovery_codes: string[] }> {
  return request<{ recovery_codes: string[] }>("/api/v1/auth/2fa/verify", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ code }),
  });
}

export async function disableTotp(accessToken: string, code: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/2fa/disable`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ code }),
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
}

export type FeedbackCategory = "bug" | "idea" | "other";

export type Feedback = {
  id: string;
  category: FeedbackCategory;
  message: string;
  page_url: string | null;
  created_at: string;
};

export async function submitFeedback(
  accessToken: string,
  payload: { category: FeedbackCategory; message: string; page_url?: string },
): Promise<Feedback> {
  return request<Feedback>("/api/v1/feedback", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(payload),
  });
}

async function readErrorMessage(response: Response): Promise<string> {
  const fallback = messageForStatus(response.status, response.statusText);
  try {
    const payload = (await response.json()) as {
      detail?: unknown;
      error?: unknown;
      error_code?: unknown;
      message?: unknown;
    };
    const message = friendlyPayloadMessage(payload, response.status);
    if (message) return message;
  } catch {
    // Fall through to status text.
  }
  return fallback;
}

function friendlyPayloadMessage(
  payload: { detail?: unknown; error?: unknown; error_code?: unknown; message?: unknown },
  status: number,
): string | null {
  const message = extractPayloadMessage(payload);
  const translated = message ? translateBackendMessage(message, status) : null;
  if (translated) return translated;
  if (message && isTurkishMessage(message) && !looksTechnical(message)) return message;

  switch (payload.error_code) {
    case "auth_error": return "Oturum bilgisi doğrulanamadı. Tekrar giriş yapın.";
    case "forbidden": return "Bu işlem için yetkiniz yok. Hesap rolünüzü veya ekip izinlerinizi kontrol edin.";
    case "not_found": return "İstenen kayıt bulunamadı. Listeyi yenileyip tekrar deneyin.";
    case "conflict": return "Bu işlem mevcut kayıtla çakışıyor. Sayfayı yenileyip son durumu kontrol edin.";
    case "validation_error": return "Gönderilen bilgiler eksik veya hatalı. Form alanlarını kontrol edip tekrar deneyin.";
    case "rate_limited": return "Kısa sürede çok fazla istek gönderildi. Biraz bekleyip tekrar deneyin.";
    case "quota_exceeded": return "Kullanım kotası doldu. Plan limitlerini kontrol edin veya daha sonra tekrar deneyin.";
    case "provider_error": return "AI sağlayıcısı isteği tamamlayamadı. API anahtarı, kota ve dosya formatını kontrol edip tekrar deneyin.";
    default: return status === 400 || status === 422 ? "Gönderilen bilgiler eksik veya hatalı. Form alanlarını kontrol edip tekrar deneyin." : null;
  }
}

function extractPayloadMessage(payload: { detail?: unknown; error?: unknown; message?: unknown }): string | null {
  const source = payload.message ?? payload.detail ?? payload.error;
  if (typeof source === "string") return source.trim() || null;
  if (Array.isArray(source)) {
    const messages = source.map((item) => {
      if (typeof item === "object" && item !== null) {
        const record = item as Record<string, unknown>;
        return record.msg ?? record.message ?? record.detail;
      }
      return item;
    }).filter((item): item is string | number | boolean => ["string", "number", "boolean"].includes(typeof item)).map(String).filter(Boolean);
    return messages.length > 0 ? messages.join(" ") : null;
  }
  if (typeof source === "object" && source !== null) {
    const record = source as Record<string, unknown>;
    const nested = record.msg ?? record.message ?? record.detail;
    return typeof nested === "string" ? nested.trim() || null : null;
  }
  return null;
}

function messageForStatus(status: number, statusText: string): string {
  if (status === 400 || status === 422) return "Gönderilen bilgiler eksik veya hatalı. Form alanlarını kontrol edip tekrar deneyin.";
  if (status === 401) return "Oturum süresi doldu. Tekrar giriş yapın.";
  if (status === 403) return "Bu işlem için yetkiniz yok.";
  if (status === 404) return "İstenen kayıt bulunamadı.";
  if (status === 409) return "Bu işlem mevcut kayıtla çakışıyor. Sayfayı yenileyip son durumu kontrol edin.";
  if (status === 429) return "Çok fazla istek gönderildi. Biraz bekleyip tekrar deneyin.";
  if (status >= 500) return "Sunucu tarafında geçici bir sorun oluştu. Biraz sonra tekrar deneyin; devam ederse backend loglarını kontrol edin.";
  const translatedStatus = statusText ? translateBackendMessage(statusText, status) : null;
  return translatedStatus ?? "İstek tamamlanamadı. Lütfen tekrar deneyin.";
}

function looksTechnical(message: string): boolean {
  const lower = message.toLowerCase();
  return lower.includes("aadsts") || lower.includes("sqlalchemy") || lower.includes("psycopg") || lower.includes("syntaxerror") || lower.includes("typeerror") || lower.includes("valueerror") || lower.includes("dioexception") || lower.includes("httpexception") || lower.includes("runtimeerror") || lower.includes("traceback") || lower.includes("status code of") || lower.includes("requestoptions") || lower.includes("stack trace") || lower.includes("not-configured") || lower.includes("identifier");
}

function isTurkishMessage(message: string): boolean {
  return /[çğıöşüÇĞİÖŞÜ]/.test(message);
}

function translateBackendMessage(message: string, status: number): string | null {
  const normalized = message.trim();
  if (!normalized) return null;
  const lower = normalized.toLowerCase();
  if (lower.includes("invalid credentials") || lower.includes("incorrect username") || lower.includes("invalid email")) return "E-posta veya şifre hatalı. Bilgileri kontrol edip tekrar deneyin.";
  if (lower.includes("token expired") || lower.includes("not authenticated") || lower.includes("unauthorized")) return "Oturum süresi doldu. Tekrar giriş yapın.";
  if (lower.includes("forbidden") || lower.includes("permission")) return "Bu işlem için yetkiniz yok. Hesap rolünüzü veya ekip izinlerinizi kontrol edin.";
  if (lower.includes("not found")) return "İstenen kayıt bulunamadı. Listeyi yenileyip tekrar deneyin.";
  if (lower.includes("already exists") || lower.includes("duplicate") || lower.includes("conflict")) return "Bu kayıt zaten mevcut veya son durumla çakışıyor. Sayfayı yenileyip tekrar deneyin.";
  if (lower.includes("field required") || lower.includes("required") || lower.includes("validation")) return "Zorunlu alanları doldurup tekrar deneyin.";
  if (lower.includes("quota") || lower.includes("limit exceeded") || lower.includes("insufficient_quota")) return "Kullanım hakkı doldu. Limitleri kontrol edip tekrar deneyin.";
  if (lower.includes("rate limit") || lower.includes("too many requests")) return "Çok fazla istek gönderildi. Biraz bekleyip tekrar deneyin.";
  if (lower.includes("failed to fetch") || lower.includes("network") || lower.includes("fetch failed")) return "Sunucuya ulaşılamadı. İnternet bağlantınızı ve backend adresini kontrol edin.";
  if (lower.includes("gmail") || lower.includes("google oauth") || lower.includes("accounts.google")) return "Gmail bağlantısı tamamlanamadı. Google OAuth client ve redirect URI ayarlarını kontrol edin.";
  if (lower.includes("outlook") || lower.includes("microsoft") || lower.includes("aadsts700016") || lower.includes("not-configured")) return "Outlook bağlantısı tamamlanamadı. Microsoft uygulama kimliği, client secret ve redirect URI ayarlarını kontrol edin.";
  if (lower.includes("api key") || lower.includes("llm_api_key")) return "AI API anahtarı eksik veya geçersiz. Sunucu ortam değişkenlerini kontrol edin.";
  if (lower.includes("transcription") || lower.includes("empty text") || lower.includes("audio")) return "Ses kaydı işlenemedi. Mikrofon, kayıt kalitesi ve AI ses çözümleme ayarlarını kontrol edin.";
  if (lower.includes("not valid json") || lower.includes("json object")) return "AI yanıtı beklenen formatta gelmedi. İşlemi tekrar deneyin.";
  if (lower.includes("unsupported llm provider")) return "AI sağlayıcısı ayarı desteklenmiyor. Sunucu yapılandırmasını kontrol edin.";
  if (lower.includes("openai") || lower.includes("provider")) return "AI sağlayıcısı isteği tamamlayamadı. API anahtarı, kota ve dosya formatını kontrol edip tekrar deneyin.";
  if (lower.includes("storage") || lower.includes("bucket") || lower.includes("s3") || lower.includes("minio")) return "Dosya depolama bağlantısında sorun oluştu. Storage endpoint, bucket ve erişim anahtarlarını kontrol edin.";
  if (lower.includes("database") || lower.includes("db error") || lower.includes("sqlalchemy") || lower.includes("psycopg")) return "Veritabanı işleminde sorun oluştu. Bağlantı ayarlarını ve sunucu loglarını kontrol edin.";
  if (lower.includes("bad request")) return "İstek hatalı. Girilen bilgileri kontrol edip tekrar deneyin.";
  if (lower.includes("internal server error")) return "Sunucu tarafında geçici bir sorun oluştu. Biraz sonra tekrar deneyin.";
  if (looksTechnical(normalized)) return messageForStatus(status, "");
  return null;
}

function mimeTypeForFile(file: File): string {
  if (file.type) {
    return file.type;
  }

  const extension = file.name.split(".").pop()?.toLowerCase();
  switch (extension) {
    case "pdf":
      return "application/pdf";
    case "docx":
      return "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
    case "xlsx":
      return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
    case "txt":
      return "text/plain";
    case "mp3":
      return "audio/mpeg";
    case "wav":
      return "audio/wav";
    case "m4a":
      return "audio/x-m4a";
    case "eml":
      return "message/rfc822";
    default:
      return "text/plain";
  }
}
