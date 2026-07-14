"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AuditLog,
  BillingPlan,
  CalendarAccount,
  completeGmailConnect,
  completeOutlookConnect,
  connectGoogleCalendar,
  EmailAccount,
  getCurrentOrganization,
  getSubscription,
  getUsageSummary,
  listAuditLogs,
  listBillingPlans,
  listCalendarAccounts,
  listEmailAccounts,
  listOrganizationMembers,
  Organization,
  OrganizationMember,
  revokeEmailAccount,
  startGmailConnect,
  startOutlookConnect,
  Subscription,
  switchPlan,
  updateMemberRole,
  UsageSummary,
} from "@/lib/api";
import { useSession } from "@/lib/session";
import { formatDateTime, formatMoney, getInitials } from "@/lib/format";

const INTEGRATION_META: Record<string, { label: string; icon: string; tint: string }> = {
  gmail: { label: "Gmail", icon: "mail", tint: "bg-red-50 text-red-600" },
  outlook: { label: "Outlook", icon: "alternate_email", tint: "bg-blue-50 text-blue-600" },
  google: { label: "Google Calendar", icon: "calendar_today", tint: "bg-blue-50 text-blue-500" },
};

type ConsentPreferences = {
  aiProcessing: boolean;
  contactMemory: boolean;
  operationalReminders: boolean;
};

const CONSENT_STORAGE_KEY = "neurodesk-consent-preferences";
const DEFAULT_CONSENT: ConsentPreferences = {
  aiProcessing: true,
  contactMemory: true,
  operationalReminders: true,
};

export function SettingsView() {
  const { user, tokens } = useSession();
  const [plans, setPlans] = useState<BillingPlan[]>([]);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [emailAccounts, setEmailAccounts] = useState<EmailAccount[]>([]);
  const [calendarAccounts, setCalendarAccounts] = useState<CalendarAccount[]>([]);
  const [consent, setConsent] = useState<ConsentPreferences>(DEFAULT_CONSENT);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [busyPlanCode, setBusyPlanCode] = useState<string | null>(null);
  const [busyMemberId, setBusyMemberId] = useState<string | null>(null);
  const [busyIntegration, setBusyIntegration] = useState<string | null>(null);

  const loadSettings = useCallback(async () => {
    if (!tokens?.accessToken) return;
    setLoading(true);
    setError(null);
    try {
      const [nextPlans, nextSubscription, nextUsage, nextEmailAccounts, nextCalendarAccounts] = await Promise.all([
        listBillingPlans(tokens.accessToken),
        getSubscription(tokens.accessToken),
        getUsageSummary(tokens.accessToken),
        listEmailAccounts(tokens.accessToken),
        listCalendarAccounts(tokens.accessToken),
      ]);
      setPlans(nextPlans);
      setSubscription(nextSubscription);
      setUsage(nextUsage);
      setEmailAccounts(nextEmailAccounts);
      setCalendarAccounts(nextCalendarAccounts);
      const [nextOrganization, nextMembers, nextAuditLogs] = await Promise.all([
        getCurrentOrganization(tokens.accessToken),
        listOrganizationMembers(tokens.accessToken),
        listAuditLogs(tokens.accessToken, 10),
      ]);
      setOrganization(nextOrganization);
      setMembers(nextMembers);
      setAuditLogs(nextAuditLogs);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Ayarlar alınamadı.");
    } finally {
      setLoading(false);
    }
  }, [tokens?.accessToken]);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  useEffect(() => {
    const stored = window.localStorage.getItem(CONSENT_STORAGE_KEY);
    if (!stored) return;
    try {
      setConsent({ ...DEFAULT_CONSENT, ...JSON.parse(stored) });
    } catch {
      window.localStorage.removeItem(CONSENT_STORAGE_KEY);
    }
  }, []);

  async function handleSwitchPlan(planCode: string) {
    if (!tokens?.accessToken) return;
    setBusyPlanCode(planCode);
    setError(null);
    try {
      const updated = await switchPlan(tokens.accessToken, planCode);
      setSubscription(updated);
      setNotice(`Plan "${updated.plan.name}" olarak güncellendi.`);
    } catch (switchError) {
      setError(switchError instanceof Error ? switchError.message : "Plan değiştirilemedi.");
    } finally {
      setBusyPlanCode(null);
    }
  }

  async function handleRoleChange(memberId: string, role: string) {
    if (!tokens?.accessToken) return;
    setBusyMemberId(memberId);
    setError(null);
    try {
      const updated = await updateMemberRole(tokens.accessToken, memberId, role);
      setMembers((current) => current.map((member) => (member.id === updated.id ? updated : member)));
    } catch (roleError) {
      setError(roleError instanceof Error ? roleError.message : "Rol güncellenemedi.");
    } finally {
      setBusyMemberId(null);
    }
  }

  async function handleConnectEmail(provider: "gmail" | "outlook") {
    if (!tokens?.accessToken) return;
    setBusyIntegration(provider);
    setError(null);
    try {
      const { state } = provider === "gmail" ? await startGmailConnect(tokens.accessToken) : await startOutlookConnect(tokens.accessToken);
      const account = provider === "gmail" ? await completeGmailConnect(state) : await completeOutlookConnect(state);
      setEmailAccounts((current) => [account, ...current.filter((item) => item.id !== account.id)]);
      setNotice(`${provider === "gmail" ? "Gmail" : "Outlook"} bağlandı.`);
    } catch (connectError) {
      setError(connectError instanceof Error ? connectError.message : "Bağlantı kurulamadı.");
    } finally {
      setBusyIntegration(null);
    }
  }

  async function handleDisconnectEmail(accountId: string) {
    if (!tokens?.accessToken) return;
    setBusyIntegration(accountId);
    setError(null);
    try {
      const updated = await revokeEmailAccount(tokens.accessToken, accountId);
      setEmailAccounts((current) => current.map((item) => (item.id === updated.id ? updated : item)));
    } catch (revokeError) {
      setError(revokeError instanceof Error ? revokeError.message : "Bağlantı kaldırılamadı.");
    } finally {
      setBusyIntegration(null);
    }
  }

  async function handleConnectCalendar() {
    if (!tokens?.accessToken) return;
    setBusyIntegration("google-calendar");
    setError(null);
    try {
      const account = await connectGoogleCalendar(tokens.accessToken);
      setCalendarAccounts((current) => [account, ...current]);
      setNotice("Google Takvim bağlandı.");
    } catch (connectError) {
      setError(connectError instanceof Error ? connectError.message : "Takvim bağlanamadı.");
    } finally {
      setBusyIntegration(null);
    }
  }

  function updateConsent(key: keyof ConsentPreferences, value: boolean) {
    const next = { ...consent, [key]: value };
    setConsent(next);
    window.localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify(next));
    setNotice("Tercih kaydedildi.");
  }

  const usagePercent = useMemo(() => {
    if (!usage || usage.limit_value === 0) return 0;
    return Math.round((usage.used / usage.limit_value) * 100);
  }, [usage]);

  const gmailAccount = useMemo(
    () => emailAccounts.find((account) => account.provider === "gmail" && account.status !== "revoked"),
    [emailAccounts],
  );
  const outlookAccount = useMemo(
    () => emailAccounts.find((account) => account.provider === "outlook" && account.status !== "revoked"),
    [emailAccounts],
  );
  const googleCalendarAccount = calendarAccounts[0] ?? null;

  return (
    <div className="p-xl max-w-[1200px]">
      <header className="mb-xl">
        <h2 className="font-headline-lg text-headline-lg text-on-surface">Settings &amp; Integrations</h2>
        <p className="text-body-lg text-on-surface-variant">
          Manage your workspace, billing, and third-party platform connections.
        </p>
      </header>

      {error ? <p className="text-error text-body-sm mb-md">{error}</p> : null}
      {notice ? <p className="text-primary text-body-sm mb-md">{notice}</p> : null}

      <div className="grid grid-cols-12 gap-lg">
        <section className="col-span-12 lg:col-span-8 space-y-md">
          <div className="flex items-center justify-between mb-sm">
            <h3 className="font-headline-md text-headline-md flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">extension</span>
              Connected Integrations
            </h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
            <IntegrationCard
              meta={INTEGRATION_META.gmail}
              detail={gmailAccount?.email_address ?? "Henüz bağlı değil"}
              isConnected={Boolean(gmailAccount)}
              isBusy={busyIntegration === "gmail" || busyIntegration === gmailAccount?.id}
              onConnect={() => handleConnectEmail("gmail")}
              onDisconnect={gmailAccount ? () => handleDisconnectEmail(gmailAccount.id) : undefined}
            />
            <IntegrationCard
              meta={INTEGRATION_META.outlook}
              detail={outlookAccount?.email_address ?? "Henüz bağlı değil"}
              isConnected={Boolean(outlookAccount)}
              isBusy={busyIntegration === "outlook" || busyIntegration === outlookAccount?.id}
              onConnect={() => handleConnectEmail("outlook")}
              onDisconnect={outlookAccount ? () => handleDisconnectEmail(outlookAccount.id) : undefined}
            />
            <IntegrationCard
              meta={INTEGRATION_META.google}
              detail={googleCalendarAccount?.external_account_id ?? "Henüz bağlı değil"}
              isConnected={Boolean(googleCalendarAccount)}
              isBusy={busyIntegration === "google-calendar"}
              onConnect={handleConnectCalendar}
            />
            <div className="border-2 border-dashed border-outline-variant p-lg rounded-xl flex flex-col items-center justify-center opacity-60">
              <div className="w-10 h-10 rounded-full bg-surface-container flex items-center justify-center mb-sm">
                <span className="material-symbols-outlined">add</span>
              </div>
              <p className="font-label-md text-on-surface-variant">Add New Integration</p>
              <p className="text-[10px] text-outline text-center mt-xs">Slack, Zoom, Salesforce ve daha fazlası</p>
            </div>
          </div>
        </section>

        <section className="col-span-12 lg:col-span-4 space-y-md">
          <h3 className="font-headline-md text-headline-md flex items-center gap-2 mb-sm">
            <span className="material-symbols-outlined text-primary">payments</span>
            Billing &amp; Plan
          </h3>
          <div className="bg-inverse-surface text-on-primary-fixed p-lg rounded-xl relative overflow-hidden shadow-xl">
            <div className="absolute -top-12 -right-12 w-32 h-32 bg-primary/20 blur-3xl rounded-full" />
            <div className="relative z-10">
              <div className="flex justify-between items-center mb-lg">
                <span className="font-label-sm text-primary-fixed-dim uppercase tracking-widest">Active Plan</span>
                <span className="px-3 py-1 bg-primary text-white text-xs font-bold rounded-full uppercase">
                  {subscription?.plan.code ?? "--"}
                </span>
              </div>
              <div className="mb-xl">
                <h4 className="text-headline-lg font-bold text-white">
                  {subscription ? formatMoney(subscription.plan.price, "USD") : "--"}{" "}
                  <span className="text-body-md font-normal text-outline-variant">
                    / {subscription?.plan.billing_period ?? "-"}
                  </span>
                </h4>
                <p className="text-body-sm text-outline-variant mt-xs">
                  {subscription
                    ? `Durum: ${subscription.status} · Dönem sonu: ${formatDateTime(subscription.current_period_end)}`
                    : "Veri bekleniyor"}
                </p>
              </div>
              <div className="space-y-2 mb-xl max-h-32 overflow-y-auto custom-scrollbar">
                {plans.map((plan) => (
                  <div key={plan.id} className="flex items-center justify-between text-body-sm text-on-primary-container">
                    <span>
                      {plan.name} · {formatMoney(plan.price, "USD")}/{plan.billing_period}
                    </span>
                    {plan.code === subscription?.plan.code ? (
                      <span className="text-[10px] opacity-70">Mevcut</span>
                    ) : (
                      <button
                        type="button"
                        disabled={busyPlanCode === plan.code}
                        onClick={() => handleSwitchPlan(plan.code)}
                        className="text-[11px] font-bold underline disabled:opacity-60"
                      >
                        {busyPlanCode === plan.code ? "..." : "Seç"}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="glass-card p-lg rounded-xl">
            <h5 className="font-label-md mb-md">Kullanım</h5>
            <div className="space-y-2">
              <div className="flex justify-between text-body-sm">
                <span className="text-on-surface-variant">{usage?.quota_type ?? "quota"}</span>
                <span className="font-bold">
                  {usage?.used ?? 0}/{usage?.limit_value ?? 0}
                </span>
              </div>
              <div className="w-full h-2 bg-surface-container-high rounded-full overflow-hidden">
                <div className="h-full bg-primary" style={{ width: `${usagePercent}%` }} />
              </div>
            </div>
          </div>
        </section>

        <section className="col-span-12 space-y-md">
          <div className="flex items-center justify-between mb-sm">
            <h3 className="font-headline-md text-headline-md flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">groups</span>
              Team Management
            </h3>
            <span className="text-body-sm text-on-surface-variant">{members.length} üye</span>
          </div>
          <div className="glass-card rounded-xl overflow-hidden">
            {members.length === 0 ? (
              <p className="p-lg text-body-sm text-on-surface-variant">Üye bulunmuyor.</p>
            ) : (
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-surface-container-high border-b border-outline-variant">
                    <th className="px-lg py-md text-label-sm uppercase tracking-wider text-on-surface-variant">Üye</th>
                    <th className="px-lg py-md text-label-sm uppercase tracking-wider text-on-surface-variant">Durum</th>
                    <th className="px-lg py-md text-label-sm uppercase tracking-wider text-on-surface-variant">Rol</th>
                    <th className="px-lg py-md text-label-sm uppercase tracking-wider text-on-surface-variant">Katılım</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-outline-variant">
                  {members.map((member) => (
                    <tr key={member.id} className="hover:bg-primary-container/5 transition-colors">
                      <td className="px-lg py-md">
                        <div className="flex items-center gap-md">
                          <div className="w-9 h-9 rounded-full bg-primary-container/20 flex items-center justify-center text-primary text-[11px] font-bold">
                            {getInitials(member.user_id)}
                          </div>
                          <span className="font-label-md text-on-surface truncate">{member.user_id}</span>
                        </div>
                      </td>
                      <td className="px-lg py-md text-body-sm">{member.status}</td>
                      <td className="px-lg py-md">
                        <select
                          className="bg-transparent border-none focus:ring-0 text-body-md font-medium text-on-surface cursor-pointer"
                          disabled={busyMemberId === member.id}
                          onChange={(e) => handleRoleChange(member.id, e.target.value)}
                          value={member.role}
                        >
                          <option value="owner">Owner</option>
                          <option value="admin">Admin</option>
                          <option value="member">Member</option>
                          <option value="viewer">Viewer</option>
                        </select>
                      </td>
                      <td className="px-lg py-md text-body-sm text-outline">{formatDateTime(member.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-lg mt-lg">
        <section className="glass-card p-lg rounded-xl">
          <h3 className="font-headline-md text-headline-md mb-md">Hesap</h3>
          <div className="space-y-2">
            <MetricLine label="Email" value={user?.email ?? "--"} />
            <MetricLine label="Kullanıcı durumu" value={user?.status ?? "--"} />
            <MetricLine label="Organizasyon adı" value={organization?.name ?? "--"} />
          </div>
        </section>

        <section className="glass-card p-lg rounded-xl">
          <h3 className="font-headline-md text-headline-md mb-md">Rıza ve Tercihler</h3>
          <div className="space-y-3">
            <ConsentToggle
              checked={consent.aiProcessing}
              description="AI chat, özetleme ve öneriler için çalışma alanı verilerinin işlenmesine izin verir."
              label="AI veri işleme"
              onChange={(value) => updateConsent("aiProcessing", value)}
            />
            <ConsentToggle
              checked={consent.contactMemory}
              description="Kişi hafızası ve CRM bağlamının arama/chat sonuçlarında kullanılmasına izin verir."
              label="Kişi hafızası"
              onChange={(value) => updateConsent("contactMemory", value)}
            />
            <ConsentToggle
              checked={consent.operationalReminders}
              description="Görev, randevu ve bildirim hatırlatmalarının kullanılmasına izin verir."
              label="Operasyonel hatırlatmalar"
              onChange={(value) => updateConsent("operationalReminders", value)}
            />
          </div>
        </section>
      </div>

      <section className="glass-card rounded-xl overflow-hidden mt-lg">
        <div className="px-lg py-md border-b border-outline-variant/30">
          <h3 className="font-headline-md text-headline-md">Audit Logs</h3>
        </div>
        {isLoading ? <p className="p-lg text-body-sm text-on-surface-variant">Yükleniyor...</p> : null}
        {!isLoading && auditLogs.length === 0 ? (
          <p className="p-lg text-body-sm text-on-surface-variant">Audit log bulunmuyor.</p>
        ) : null}
        {auditLogs.length > 0 ? (
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-container text-outline font-label-sm uppercase tracking-wider">
                <th className="px-lg py-3">Aksiyon</th>
                <th className="px-lg py-3">Varlık</th>
                <th className="px-lg py-3 text-right">Zaman</th>
              </tr>
            </thead>
            <tbody className="text-body-sm">
              {auditLogs.map((log) => (
                <tr key={log.id} className="border-b border-outline-variant/10">
                  <td className="px-lg py-3">{log.action}</td>
                  <td className="px-lg py-3">{log.entity_type}</td>
                  <td className="px-lg py-3 text-right text-outline">{formatDateTime(log.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
      </section>
    </div>
  );
}

function IntegrationCard({
  meta,
  detail,
  isConnected,
  isBusy,
  onConnect,
  onDisconnect,
}: {
  meta: { label: string; icon: string; tint: string };
  detail: string;
  isConnected: boolean;
  isBusy: boolean;
  onConnect: () => void;
  onDisconnect?: () => void;
}) {
  return (
    <div className="glass-card p-lg rounded-xl flex flex-col justify-between">
      <div className="flex justify-between items-start mb-lg">
        <div className="flex items-center gap-md">
          <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${meta.tint}`}>
            <span className="material-symbols-outlined text-3xl">{meta.icon}</span>
          </div>
          <div>
            <h4 className="font-label-md text-on-surface">{meta.label}</h4>
            <span
              className={
                "px-2 py-0.5 text-[10px] font-bold rounded-full uppercase tracking-wider " +
                (isConnected ? "bg-green-100 text-green-700" : "bg-surface-container-high text-on-surface-variant")
              }
            >
              {isConnected ? "Connected" : "Not connected"}
            </span>
          </div>
        </div>
      </div>
      <p className="text-body-sm text-on-surface-variant mb-lg leading-relaxed truncate">{detail}</p>
      <button
        type="button"
        disabled={isBusy}
        onClick={isConnected ? onDisconnect : onConnect}
        className="w-full py-2 border border-outline-variant rounded-lg text-on-surface-variant font-label-sm hover:bg-surface-container-high transition-colors active:scale-[0.98] disabled:opacity-60"
      >
        {isBusy ? "İşleniyor..." : isConnected ? "Disconnect" : "Connect"}
      </button>
    </div>
  );
}

function ConsentToggle({
  checked,
  description,
  label,
  onChange,
}: {
  checked: boolean;
  description: string;
  label: string;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className="flex items-start gap-3 cursor-pointer">
      <input
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
        type="checkbox"
        className="mt-1"
      />
      <span>
        <strong className="block text-body-sm text-on-surface">{label}</strong>
        <small className="text-[11px] text-on-surface-variant">{description}</small>
      </span>
    </label>
  );
}

function MetricLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-body-sm">
      <span className="text-on-surface-variant">{label}</span>
      <strong className="text-on-surface">{value}</strong>
    </div>
  );
}
