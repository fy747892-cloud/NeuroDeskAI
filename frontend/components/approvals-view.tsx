"use client";

import { useEffect, useMemo, useState } from "react";
import { AIActionApproval, approveAction, listApprovals, rejectAction } from "@/lib/api";
import { useSession } from "@/lib/session";

const ACTION_ICON: Record<string, string> = {
  task: "checklist",
  appointment: "calendar_today",
  deal: "payments",
};

const ACTION_LABEL: Record<string, string> = {
  task: "Görev Önerisi",
  appointment: "Randevu Önerisi",
  deal: "Fırsat Önerisi",
};

export function ApprovalsView() {
  const { tokens } = useSession();
  const [approvals, setApprovals] = useState<AIActionApproval[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [activeId, setActiveId] = useState<string | null>(null);

  async function loadApprovals() {
    if (!tokens?.accessToken) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      setApprovals(await listApprovals(tokens.accessToken));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "AI onayları alınamadı.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadApprovals();
  }, [tokens?.accessToken]);

  const summary = useMemo(() => {
    const pending = approvals.filter((approval) => approval.status === "pending");
    const decided = approvals.filter(
      (approval) => approval.status === "approved" || approval.status === "rejected",
    );
    const approvedCount = decided.filter((approval) => approval.status === "approved").length;

    const acceptanceRate =
      decided.length > 0 ? Math.round((approvedCount / decided.length) * 100) : null;

    const responseMinutes = decided
      .filter((approval) => approval.decided_at)
      .map(
        (approval) =>
          (new Date(approval.decided_at as string).getTime() - new Date(approval.created_at).getTime()) /
          60000,
      )
      .filter((minutes) => Number.isFinite(minutes) && minutes >= 0);
    const avgResponseMinutes =
      responseMinutes.length > 0
        ? Math.round(responseMinutes.reduce((sum, value) => sum + value, 0) / responseMinutes.length)
        : null;

    return {
      pending: pending.length,
      resolved: decided.length,
      acceptanceRate,
      avgResponseMinutes,
    };
  }, [approvals]);

  async function decide(approvalId: string, decision: "approve" | "reject") {
    if (!tokens?.accessToken) {
      return;
    }

    setActiveId(approvalId);
    setError(null);
    try {
      const updatedApproval =
        decision === "approve"
          ? await approveAction(tokens.accessToken, approvalId)
          : await rejectAction(tokens.accessToken, approvalId);
      setApprovals((currentApprovals) =>
        currentApprovals.map((approval) =>
          approval.id === updatedApproval.id ? updatedApproval : approval,
        ),
      );
    } catch (decisionError) {
      setError(decisionError instanceof Error ? decisionError.message : "Onay aksiyonu tamamlanamadi.");
    } finally {
      setActiveId(null);
    }
  }

  return (
    <>
      {error ? <p className="notice">{error}</p> : null}

      <div className="actionHeader">
        <div>
          <div className="actionEyebrow">
            <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 20 }}>
              auto_awesome
            </span>
            AI Akıllı İşleme
          </div>
          <p className="moduleLead">
            Son aktivitelerinizden çıkarılan önerilen görev, randevu ve fırsatları inceleyip onaylayın.
          </p>
        </div>
        <div className="actionStats">
          <div className="statPill highlight">
            <strong>{summary.pending}</strong>
            <span>Bekleyen</span>
          </div>
          <div className="statPill">
            <strong>{summary.resolved}</strong>
            <span>Sonuçlanan</span>
          </div>
        </div>
      </div>

      <div className="actionLayout">
        <div className="actionFeed">
          {isLoading ? <p className="emptyState">AI onayları yükleniyor.</p> : null}
          {!isLoading && approvals.length === 0 ? (
            <p className="emptyState">Bekleyen AI önerisi yok.</p>
          ) : null}
          {approvals.map((approval) => (
            <ActionCard
              key={approval.id}
              approval={approval}
              isBusy={activeId === approval.id}
              onApprove={() => decide(approval.id, "approve")}
              onReject={() => decide(approval.id, "reject")}
            />
          ))}
        </div>

        <aside className="velocityPanel">
          <h4>İşleme Hızı</h4>
          <div className="velocityStat">
            <div>
              <p>{summary.acceptanceRate !== null ? `%${summary.acceptanceRate}` : "--"}</p>
              <p>Kabul Oranı</p>
            </div>
            {summary.acceptanceRate !== null ? (
              <div className="velocityBar">
                <span style={{ width: `${summary.acceptanceRate}%` }} />
              </div>
            ) : null}
          </div>
          <div className="velocityStat">
            <div>
              <p>{summary.avgResponseMinutes !== null ? `${summary.avgResponseMinutes}dk` : "--"}</p>
              <p>Ort. Yanıt Süresi</p>
            </div>
          </div>
        </aside>
      </div>
    </>
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
  const icon = ACTION_ICON[approval.action_type] ?? "auto_awesome";
  const label = ACTION_LABEL[approval.action_type] ?? approval.action_type;
  const title = summarizePayload(approval.suggested_payload);
  const fields = payloadFields(approval.suggested_payload);
  const isResolved = approval.status !== "pending";
  const confidence = approval.confidence_score;
  const confidenceTier = confidence === null ? "low" : confidence >= 0.9 ? "high" : confidence >= 0.7 ? "mid" : "low";
  const confidenceIcon = confidenceTier === "high" ? "verified" : confidenceTier === "mid" ? "insights" : "help";

  return (
    <article className={`actionCard${isResolved ? " resolved" : ""}`}>
      <div className="actionCardHead">
        <div className="actionCardMain">
          <div className="actionIcon">
            <span className="material-symbols-outlined" aria-hidden="true">
              {icon}
            </span>
          </div>
          <div>
            <div className="actionBadgeRow">
              <span className="actionBadge">{label}</span>
              <span className="actionSource">Kaynak: {approval.source_type}</span>
            </div>
            <h3>{title}</h3>
          </div>
        </div>
        <div className="actionConfidence">
          <span className={`confidenceValue ${confidenceTier}`}>
            <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 14 }}>
              {confidenceIcon}
            </span>
            {formatConfidence(confidence)}
          </span>
          <small>{formatDateTime(approval.created_at)}</small>
        </div>
      </div>

      {fields.length > 0 ? (
        <div className="actionFields">
          {fields.map(([key, value]) => (
            <div className="actionField" key={key}>
              <label>{key}</label>
              <span>{value}</span>
            </div>
          ))}
        </div>
      ) : null}

      {approval.status === "pending" ? (
        <div className="actionFooter">
          <button className="approveBtn" disabled={isBusy} onClick={onApprove} type="button">
            <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 18 }}>
              check_circle
            </span>
            Onayla
          </button>
          <button className="rejectBtn" disabled={isBusy} onClick={onReject} type="button">
            <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 18 }}>
              close
            </span>
            Reddet
          </button>
        </div>
      ) : (
        <span className={approval.status === "rejected" ? "statusPill danger" : "statusPill done"}>
          {approval.status === "approved" ? "Onaylandı" : "Reddedildi"}
        </span>
      )}
    </article>
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
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

function formatConfidence(value: number | null): string {
  if (value === null) {
    return "--";
  }
  return `%${Math.round(value * 100)}`;
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
  }).format(new Date(value));
}
