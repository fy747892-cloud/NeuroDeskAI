"use client";

import { useEffect, useMemo, useState } from "react";
import { AIActionApproval, approveAction, listApprovals, rejectAction } from "@/lib/api";
import { useSession } from "@/lib/session";

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
      setError(loadError instanceof Error ? loadError.message : "AI onaylari alinamadi.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadApprovals();
  }, [tokens?.accessToken]);

  const summary = useMemo(() => {
    return {
      pending: approvals.filter((approval) => approval.status === "pending").length,
      approved: approvals.filter((approval) => approval.status === "approved").length,
      rejected: approvals.filter((approval) => approval.status === "rejected").length,
      highConfidence: approvals.filter((approval) => (approval.confidence_score ?? 0) >= 0.8).length,
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
    <section className="moduleSurface">
      {error ? <p className="notice">{error}</p> : null}

      <div className="moduleGrid">
        <SummaryCard label="Bekleyen" value={summary.pending} />
        <SummaryCard label="Onaylanan" value={summary.approved} />
        <SummaryCard label="Reddedilen" value={summary.rejected} />
        <SummaryCard label="Yuksek guven" value={summary.highConfidence} />
      </div>

      <div className="panel">
        <div className="panelHeader">
          <h2>AI aksiyon kuyrugu</h2>
          <button disabled={isLoading} onClick={loadApprovals} type="button">
            {isLoading ? "Yukleniyor" : "Yenile"}
          </button>
        </div>

        <div className="dataList">
          {isLoading ? <p className="emptyState">AI onaylari yukleniyor.</p> : null}
          {!isLoading && approvals.length === 0 ? (
            <p className="emptyState">Bekleyen AI onerisi yok.</p>
          ) : null}
          {approvals.map((approval) => (
            <article className="dataRow" key={approval.id}>
              <div>
                <div className="rowTitle">
                  <h3>{approval.action_type}</h3>
                  <span>{approval.source_type}</span>
                </div>
                <p>{summarizePayload(approval.suggested_payload)}</p>
                <small>
                  Guven: {formatConfidence(approval.confidence_score)} | {formatDateTime(approval.created_at)}
                </small>
              </div>
              <div className="rowActions horizontal">
                <span className={approval.status === "rejected" ? "statusPill danger" : "statusPill"}>
                  {approval.status}
                </span>
                <button
                  disabled={approval.status !== "pending" || activeId === approval.id}
                  onClick={() => decide(approval.id, "approve")}
                  type="button"
                >
                  Onayla
                </button>
                <button
                  disabled={approval.status !== "pending" || activeId === approval.id}
                  onClick={() => decide(approval.id, "reject")}
                  type="button"
                >
                  Reddet
                </button>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function SummaryCard({ label, value }: { label: string; value: number }) {
  return (
    <article className="moduleCard compact">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function summarizePayload(payload: Record<string, unknown>): string {
  const title = payload.title ?? payload.summary ?? payload.description ?? payload.body;
  if (typeof title === "string" && title.trim()) {
    return title;
  }
  return "AI tarafindan uretilen aksiyon onay bekliyor.";
}

function formatConfidence(value: number | null): string {
  if (value === null) {
    return "--";
  }
  return `${Math.round(value * 100)}%`;
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
  }).format(new Date(value));
}
