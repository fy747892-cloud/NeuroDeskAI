"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AIActionApproval,
  approveAction,
  createAppointmentFromApproval,
  createDealFromApproval,
  createTaskFromApproval,
  listApprovals,
  rejectAction,
} from "@/lib/api";
import { useSession } from "@/lib/session";
import { formatDateTime } from "@/lib/format";

const ACTION_META: Record<string, { icon: string; label: string; confirmLabel: string; confirmIcon: string }> = {
  appointment: {
    icon: "calendar_today",
    label: "MEETING SUGGESTION",
    confirmLabel: "Approve & Schedule",
    confirmIcon: "check_circle",
  },
  deal: {
    icon: "payments",
    label: "NEW OPPORTUNITY",
    confirmLabel: "Create Opportunity",
    confirmIcon: "rocket_launch",
  },
  task: {
    icon: "checklist",
    label: "ACTION ITEM",
    confirmLabel: "Add to My Tasks",
    confirmIcon: "add_task",
  },
};

export function ApprovalsView() {
  const { tokens } = useSession();
  const [approvals, setApprovals] = useState<AIActionApproval[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!tokens?.accessToken) return;
    setLoading(true);
    setError(null);
    try {
      setApprovals(await listApprovals(tokens.accessToken));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "AI onayları alınamadı.");
    } finally {
      setLoading(false);
    }
  }, [tokens?.accessToken]);

  useEffect(() => {
    load();
  }, [load]);

  const summary = useMemo(() => {
    const pending = approvals.filter((approval) => approval.status === "pending");
    const decided = approvals.filter(
      (approval) => approval.status === "approved" || approval.status === "rejected",
    );
    const approvedCount = decided.filter((approval) => approval.status === "approved").length;
    const acceptanceRate =
      decided.length > 0 ? Math.round((approvedCount / decided.length) * 100) : null;
    return { pending: pending.length, resolved: decided.length, acceptanceRate };
  }, [approvals]);

  async function handleApprove(approval: AIActionApproval) {
    if (!tokens?.accessToken) return;
    setBusyId(approval.id);
    setError(null);
    try {
      await approveAction(tokens.accessToken, approval.id);
      if (approval.action_type === "task") {
        await createTaskFromApproval(tokens.accessToken, approval.id);
      } else if (approval.action_type === "appointment") {
        await createAppointmentFromApproval(tokens.accessToken, approval.id);
      } else if (approval.action_type === "deal") {
        await createDealFromApproval(tokens.accessToken, approval.id);
      }
      await load();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Öneri onaylanamadı.");
    } finally {
      setBusyId(null);
    }
  }

  async function handleReject(approvalId: string) {
    if (!tokens?.accessToken) return;
    setBusyId(approvalId);
    setError(null);
    try {
      await rejectAction(tokens.accessToken, approvalId);
      await load();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Öneri reddedilemedi.");
    } finally {
      setBusyId(null);
    }
  }

  const pendingApprovals = approvals.filter((approval) => approval.status === "pending");

  return (
    <div className="flex">
      <div className="flex-1 px-xl py-lg">
        <div className="flex items-end justify-between mb-xl">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="material-symbols-outlined text-primary text-[24px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                auto_awesome
              </span>
              <span className="text-primary font-label-sm uppercase tracking-wider">
                AI Intelligent Processing
              </span>
            </div>
            <h2 className="font-headline-lg text-headline-lg text-on-surface">AI Action Center</h2>
            <p className="font-body-md text-on-surface-variant mt-1">
              Review and approve suggested tasks and actions identified from your recent activity.
            </p>
          </div>
          <div className="flex gap-2">
            <div className="bg-primary-container/10 border border-primary/20 px-4 py-2 rounded-xl flex flex-col items-center min-w-[80px]">
              <span className="text-primary font-bold text-lg">{summary.pending}</span>
              <span className="text-[10px] text-primary/70 uppercase font-bold">Pending</span>
            </div>
            <div className="bg-surface-container-high px-4 py-2 rounded-xl flex flex-col items-center min-w-[80px]">
              <span className="text-on-surface-variant font-bold text-lg">{summary.resolved}</span>
              <span className="text-[10px] text-on-surface-variant/70 uppercase font-bold">Resolved</span>
            </div>
          </div>
        </div>

        {error ? <p className="text-error text-body-sm mb-md">{error}</p> : null}

        <div className="max-w-4xl space-y-md">
          {isLoading ? <p className="text-body-md text-on-surface-variant">Yükleniyor...</p> : null}
          {!isLoading && pendingApprovals.length === 0 ? (
            <div className="max-w-4xl flex flex-col items-center justify-center py-xl border-2 border-dashed border-outline-variant/30 rounded-2xl opacity-50">
              <span className="material-symbols-outlined text-[48px] text-outline-variant mb-md">
                auto_awesome
              </span>
              <p className="font-headline-md text-on-surface-variant">Bekleyen öneri yok.</p>
              <p className="font-body-md text-on-surface-variant mt-2 text-center max-w-sm">
                NeuroDesk AI, aksiyon alınabilir öneriler bulmak için verilerini işlemeye devam ediyor.
              </p>
            </div>
          ) : null}
          {pendingApprovals.map((approval) => (
            <ActionCard
              key={approval.id}
              approval={approval}
              isBusy={busyId === approval.id}
              onApprove={() => handleApprove(approval)}
              onReject={() => handleReject(approval.id)}
            />
          ))}
        </div>
      </div>

      <aside className="w-[320px] bg-white border-l border-outline-variant/20 flex flex-col p-xl shrink-0">
        <div className="mb-xl">
          <h4 className="font-label-md text-on-surface uppercase tracking-widest text-[11px] font-black mb-md opacity-40">
            Intelligence Velocity
          </h4>
          <div className="space-y-md">
            <div className="flex items-end justify-between">
              <div>
                <p className="text-[24px] font-bold text-on-surface">
                  {summary.acceptanceRate !== null ? `${summary.acceptanceRate}%` : "--"}
                </p>
                <p className="text-[12px] text-on-surface-variant">Acceptance Rate</p>
              </div>
              <div className="w-32 h-2 bg-surface-container-high rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary"
                  style={{ width: `${summary.acceptanceRate ?? 0}%` }}
                />
              </div>
            </div>
          </div>
        </div>
        <div className="mt-auto">
          <div className="bg-primary-container/10 p-lg rounded-2xl relative overflow-hidden border border-primary/10">
            <div className="relative z-10">
              <p className="font-label-md text-primary font-bold mb-1">AI Assistant</p>
              <p className="text-[12px] text-primary/80 leading-snug">
                {summary.resolved} öneri şu ana kadar karara bağlandı.
              </p>
            </div>
            <span
              className="material-symbols-outlined absolute -right-4 -bottom-4 text-[80px] text-primary opacity-5"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              bolt
            </span>
          </div>
        </div>
      </aside>
    </div>
  );
}

function ActionCard({
  approval,
  isBusy,
  onApprove,
  onReject,
}: {
  approval: AIActionApproval;
  isBusy: boolean;
  onApprove: () => void;
  onReject: () => void;
}) {
  const meta = ACTION_META[approval.action_type] ?? {
    icon: "auto_awesome",
    label: approval.action_type.toUpperCase(),
    confirmLabel: "Approve",
    confirmIcon: "check_circle",
  };
  const title = summarizePayload(approval.suggested_payload);
  const fields = payloadFields(approval.suggested_payload);
  const confidence = approval.confidence_score;
  const confidenceTier = confidence === null ? "low" : confidence >= 0.9 ? "high" : confidence >= 0.7 ? "mid" : "low";
  const confidenceIcon = confidenceTier === "high" ? "verified" : confidenceTier === "mid" ? "insights" : "help";

  return (
    <div className="ai-glow bg-surface-container-low p-lg rounded-2xl transition-all duration-300">
      <div className="flex justify-between items-start mb-lg">
        <div className="flex gap-lg">
          <div className="w-12 h-12 rounded-xl bg-primary-container/10 flex items-center justify-center text-primary shrink-0">
            <span className="material-symbols-outlined text-[28px]">{meta.icon}</span>
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <span className="bg-surface-container-highest text-primary font-label-sm px-2 py-0.5 rounded text-[10px]">
                {meta.label}
              </span>
              <span className="text-on-surface-variant text-[11px] font-medium opacity-60">
                Source: {approval.source_type}
              </span>
            </div>
            <h3 className="font-headline-md text-on-surface">{title}</h3>
          </div>
        </div>
        <div className="flex flex-col items-end shrink-0">
          <div
            className={
              "flex items-center gap-1 " + (confidenceTier === "high" ? "text-[#059669]" : "text-primary")
            }
          >
            <span className="material-symbols-outlined text-[14px]" style={{ fontVariationSettings: "'FILL' 1" }}>
              {confidenceIcon}
            </span>
            <span className="font-label-sm text-[12px] font-bold">{formatConfidence(confidence)} CONFIDENCE</span>
          </div>
          <span className="text-[11px] text-on-surface-variant opacity-50">{formatDateTime(approval.created_at)}</span>
        </div>
      </div>

      {fields.length > 0 ? (
        <div className="grid grid-cols-2 gap-md mb-xl">
          {fields.map(([key, value]) => (
            <div key={key} className="bg-white/50 border border-outline-variant/30 rounded-lg p-3">
              <label className="block text-[10px] font-bold text-on-surface-variant opacity-60 uppercase mb-1">
                {key}
              </label>
              <span className="text-[13px] text-on-surface font-medium">{value}</span>
            </div>
          ))}
        </div>
      ) : null}

      <div className="flex gap-3">
        <button
          type="button"
          disabled={isBusy}
          onClick={onApprove}
          className="flex-1 py-3.5 bg-primary text-on-primary rounded-xl font-label-md flex items-center justify-center gap-2 hover:brightness-110 active:scale-[0.98] transition-all disabled:opacity-60"
        >
          <span className="material-symbols-outlined text-[20px]">{meta.confirmIcon}</span>
          <span>{isBusy ? "İşleniyor..." : meta.confirmLabel}</span>
        </button>
        <button
          type="button"
          disabled={isBusy}
          onClick={onReject}
          className="px-4 py-3.5 border border-error/20 text-error rounded-xl font-label-md flex items-center justify-center gap-2 hover:bg-error/5 active:scale-[0.98] transition-all disabled:opacity-60"
        >
          <span className="material-symbols-outlined text-[20px]">close</span>
        </button>
      </div>
    </div>
  );
}

function summarizePayload(payload: Record<string, unknown>): string {
  const title = payload.title ?? payload.summary ?? payload.description ?? payload.body;
  if (typeof title === "string" && title.trim()) {
    return title;
  }
  return "AI tarafından üretilen aksiyon onay bekliyor.";
}

function payloadFields(payload: Record<string, unknown>): [string, string][] {
  const skipKeys = new Set(["title", "summary", "description", "body"]);
  return Object.entries(payload)
    .filter(([key, value]) => !skipKeys.has(key) && value !== null && value !== undefined && value !== "")
    .slice(0, 4)
    .map(([key, value]) => [formatFieldLabel(key), formatFieldValue(value)]);
}

function formatFieldLabel(key: string): string {
  return key.replace(/_/g, " ");
}

function formatFieldValue(value: unknown): string {
  if (Array.isArray(value)) {
    return value.map((item) => String(item)).join(", ");
  }
  if (typeof value === "object" && value !== null) {
    return JSON.stringify(value);
  }
  return String(value);
}

function formatConfidence(value: number | null): string {
  if (value === null) return "--";
  return `${Math.round(value * 100)}%`;
}
