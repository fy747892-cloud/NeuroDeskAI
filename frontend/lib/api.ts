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
    throw new Error(
      "API bağlantısı kurulamadı. Backend'in çalıştığını, adres ayarını ve internet bağlantınızı kontrol edin.",
    );
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
    }),
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

// Approving an AIActionApproval only flips its status — it does not create the
// real record. A separate materialize call against the matching from-approval
// endpoint is required to turn it into a real task/appointment/deal.
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
    if (message) {
      return message;
    }
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
  if (message && !looksTechnical(message)) {
    return message;
  }

  switch (payload.error_code) {
    case "auth_error":
      return "Oturum bilgisi doğrulanamadı. Tekrar giriş yapın.";
    case "forbidden":
      return "Bu işlem için yetkiniz yok. Hesap rolünüzü veya ekip izinlerinizi kontrol edin.";
    case "not_found":
      return "İstenen kayıt bulunamadı. Listeyi yenileyip tekrar deneyin.";
    case "conflict":
      return "Bu işlem mevcut kayıtla çakışıyor. Sayfayı yenileyip son durumu kontrol edin.";
    case "validation_error":
      return "Gönderilen bilgiler eksik veya hatalı. Form alanlarını kontrol edip tekrar deneyin.";
    case "rate_limited":
      return "Kısa sürede çok fazla istek gönderildi. Biraz bekleyip tekrar deneyin.";
    case "quota_exceeded":
      return "Kullanım kotası doldu. Plan limitlerini kontrol edin veya daha sonra tekrar deneyin.";
    case "provider_error":
      return "AI sağlayıcısı isteği tamamlayamadı. API anahtarı, kota ve dosya formatını kontrol edip tekrar deneyin.";
    default:
      return status === 400 || status === 422
        ? "Gönderilen bilgiler eksik veya hatalı. Form alanlarını kontrol edip tekrar deneyin."
        : null;
  }
}

function extractPayloadMessage(payload: { detail?: unknown; error?: unknown; message?: unknown }): string | null {
  const source = payload.message ?? payload.detail ?? payload.error;
  if (typeof source === "string") {
    return source.trim() || null;
  }
  if (Array.isArray(source)) {
    const messages = source
      .map((item) => {
        if (typeof item === "object" && item !== null) {
          const record = item as Record<string, unknown>;
          return record.msg ?? record.message ?? record.detail;
        }
        return item;
      })
      .filter((item): item is string | number | boolean => ["string", "number", "boolean"].includes(typeof item))
      .map(String)
      .filter(Boolean);
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
  if (status === 400 || status === 422) {
    return "Gönderilen bilgiler eksik veya hatalı. Form alanlarını kontrol edip tekrar deneyin.";
  }
  if (status === 401) {
    return "Oturum süresi doldu. Tekrar giriş yapın.";
  }
  if (status === 403) {
    return "Bu işlem için yetkiniz yok.";
  }
  if (status === 404) {
    return "İstenen kayıt bulunamadı.";
  }
  if (status === 409) {
    return "Bu işlem mevcut kayıtla çakışıyor. Sayfayı yenileyip son durumu kontrol edin.";
  }
  if (status === 429) {
    return "Çok fazla istek gönderildi. Biraz bekleyip tekrar deneyin.";
  }
  if (status >= 500) {
    return "Sunucu tarafında geçici bir sorun oluştu. Biraz sonra tekrar deneyin; devam ederse backend loglarını kontrol edin.";
  }
  return statusText || "İstek tamamlanamadı. Lütfen tekrar deneyin.";
}

function looksTechnical(message: string): boolean {
  const lower = message.toLowerCase();
  return (
    lower.includes("dioexception") ||
    lower.includes("httpexception") ||
    lower.includes("runtimeerror") ||
    lower.includes("traceback") ||
    lower.includes("status code of") ||
    lower.includes("requestoptions")
  );
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
