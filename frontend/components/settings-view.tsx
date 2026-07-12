"use client";

import { useEffect, useMemo, useState } from "react";
import {
  BillingPlan,
  AuditLog,
  getSubscription,
  getCurrentOrganization,
  getUsageSummary,
  listAuditLogs,
  listBillingPlans,
  listOrganizationMembers,
  Organization,
  OrganizationMember,
  Subscription,
  UsageSummary,
} from "@/lib/api";
import { useSession } from "@/lib/session";

export function SettingsView() {
  const { user, tokens } = useSession();
  const [plans, setPlans] = useState<BillingPlan[]>([]);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);

  async function loadSettings() {
    if (!tokens?.accessToken) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const [nextPlans, nextSubscription, nextUsage] = await Promise.all([
        listBillingPlans(tokens.accessToken),
        getSubscription(tokens.accessToken),
        getUsageSummary(tokens.accessToken),
      ]);
      setPlans(nextPlans);
      setSubscription(nextSubscription);
      setUsage(nextUsage);
      const [nextOrganization, nextMembers, nextAuditLogs] = await Promise.all([
        getCurrentOrganization(tokens.accessToken),
        listOrganizationMembers(tokens.accessToken),
        listAuditLogs(tokens.accessToken, 25),
      ]);
      setOrganization(nextOrganization);
      setMembers(nextMembers);
      setAuditLogs(nextAuditLogs);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Ayarlar alinamadi.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSettings();
  }, [tokens?.accessToken]);

  const usagePercent = useMemo(() => {
    if (!usage || usage.limit_value === 0) {
      return 0;
    }
    return Math.round((usage.used / usage.limit_value) * 100);
  }, [usage]);

  return (
    <section className="moduleSurface">
      {error ? <p className="notice">{error}</p> : null}

      <div className="moduleGrid">
        <SummaryCard label="Plan" value={subscription?.plan.name ?? "--"} />
        <SummaryCard label="Durum" value={subscription?.status ?? "--"} />
        <SummaryCard label="Kullanim" value={`${usagePercent}%`} />
        <SummaryCard label="Uye" value={members.length} />
      </div>

      <div className="contentGrid">
        <section className="panel">
          <div className="panelHeader">
            <h2>Hesap</h2>
            <button disabled={isLoading} onClick={loadSettings} type="button">
              {isLoading ? "Yukleniyor" : "Yenile"}
            </button>
          </div>
          <div className="metricList">
            <MetricLine label="Email" value={user?.email ?? "--"} />
            <MetricLine label="Kullanici durumu" value={user?.status ?? "--"} />
            <MetricLine label="Organizasyon" value={user?.organization_id ?? "--"} />
            <MetricLine label="Organizasyon adi" value={organization?.name ?? "--"} />
            <MetricLine label="Tenant" value={user?.tenant_id ?? "--"} />
          </div>
        </section>

        <section className="panel">
          <div className="panelHeader">
            <h2>Abonelik</h2>
            <span className="tag">{usage?.quota_type ?? "quota"}</span>
          </div>
          <div className="metricList">
            <MetricLine label="Limit" value={String(usage?.limit_value ?? 0)} />
            <MetricLine label="Kullanilan" value={String(usage?.used ?? 0)} />
            <MetricLine label="Kalan" value={String(usage?.remaining ?? 0)} />
            <MetricLine label="Donem" value={usage?.period ?? "--"} />
          </div>
        </section>
      </div>

      <section className="panel">
        <div className="panelHeader">
          <h2>Planlar</h2>
          <span className="tag">{plans.length}</span>
        </div>
        <div className="dataList">
          {plans.length === 0 ? <p className="emptyState">Plan bulunmuyor.</p> : null}
          {plans.map((plan) => (
            <article className="dataRow" key={plan.id}>
              <div>
                <div className="rowTitle">
                  <h3>{plan.name}</h3>
                  <span>{plan.code}</span>
                </div>
                <p>{formatCurrency(plan.price)} / {plan.billing_period}</p>
                <small>{plan.status}</small>
              </div>
            </article>
          ))}
        </div>
      </section>

      <div className="contentGrid">
        <section className="panel">
          <div className="panelHeader">
            <h2>Organizasyon uyeleri</h2>
            <span className="tag">{members.length}</span>
          </div>
          <div className="dataList">
            {members.length === 0 ? <p className="emptyState">Uye bulunmuyor.</p> : null}
            {members.map((member) => (
              <article className="dataRow" key={member.id}>
                <div>
                  <div className="rowTitle">
                    <h3>{member.user_id}</h3>
                    <span>{member.role}</span>
                  </div>
                  <p>{member.status}</p>
                  <small>{formatDateTime(member.created_at)}</small>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="panelHeader">
            <h2>Audit logs</h2>
            <span className="tag">{auditLogs.length}</span>
          </div>
          <div className="dataList">
            {auditLogs.length === 0 ? <p className="emptyState">Audit log bulunmuyor.</p> : null}
            {auditLogs.map((log) => (
              <article className="dataRow" key={log.id}>
                <div>
                  <div className="rowTitle">
                    <h3>{log.action}</h3>
                    <span>{log.entity_type}</span>
                  </div>
                  <p>{log.request_id ?? log.ip_address ?? "Request bilgisi yok."}</p>
                  <small>{formatDateTime(log.created_at)}</small>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </section>
  );
}

function SummaryCard({ label, value }: { label: string; value: number | string }) {
  return (
    <article className="moduleCard compact">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function MetricLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="metricLine">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("tr-TR", {
    currency: "USD",
    maximumFractionDigits: 2,
    style: "currency",
  }).format(value);
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
  }).format(new Date(value));
}
