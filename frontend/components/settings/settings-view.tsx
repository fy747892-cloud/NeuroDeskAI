"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  AuditLog,
  BillingPlan,
  CalendarAccount,
  connectGoogleCalendar,
  ConsentSettings,
  EmailAccount,
  getConsentSettings,
  getCurrentOrganization,
  getSubscription,
  getUsageSummary,
  inviteOrganizationMember,
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
  updateConsentSettings,
  updateMemberRole,
  updateProfile,
  UsageSummary,
} from "@/lib/api";
import { useSession } from "@/lib/session";
import { useLanguage } from "@/lib/i18n/context";
import { formatDateTime, formatMoney, getInitials } from "@/lib/format";

const INTEGRATION_META: Record<string, { label: string; icon: string; tint: string }> = {
  gmail: { label: "Gmail", icon: "mail", tint: "bg-red-50 text-red-600" },
  outlook: { label: "Outlook", icon: "alternate_email", tint: "bg-blue-50 text-blue-600" },
  google: { label: "Google Calendar", icon: "calendar_today", tint: "bg-blue-50 text-blue-500" },
};

const DEFAULT_CONSENT: ConsentSettings = {
  ai_processing: true,
  contact_memory: true,
  operational_reminders: true,
};

export function SettingsView() {
  const { user, tokens, refreshUser } = useSession();
  const { t, language } = useLanguage();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [plans, setPlans] = useState<BillingPlan[]>([]);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [emailAccounts, setEmailAccounts] = useState<EmailAccount[]>([]);
  const [calendarAccounts, setCalendarAccounts] = useState<CalendarAccount[]>([]);
  const [consent, setConsent] = useState<ConsentSettings>(DEFAULT_CONSENT);
  const [isSavingConsent, setSavingConsent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [busyPlanCode, setBusyPlanCode] = useState<string | null>(null);
  const [busyMemberId, setBusyMemberId] = useState<string | null>(null);
  const [isEditingProfile, setEditingProfile] = useState(false);
  const [profileForm, setProfileForm] = useState({ fullName: "", title: "" });
  const [isSavingProfile, setSavingProfile] = useState(false);
  const [showInviteForm, setShowInviteForm] = useState(false);
  const [inviteForm, setInviteForm] = useState({ email: "", role: "member" });
  const [isInviting, setInviting] = useState(false);
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
      const [nextOrganization, nextMembers, nextAuditLogs, nextConsent] = await Promise.all([
        getCurrentOrganization(tokens.accessToken),
        listOrganizationMembers(tokens.accessToken),
        listAuditLogs(tokens.accessToken, 10),
        getConsentSettings(tokens.accessToken),
      ]);
      setOrganization(nextOrganization);
      setMembers(nextMembers);
      setAuditLogs(nextAuditLogs);
      setConsent(nextConsent);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : t("settings.loadError"));
    } finally {
      setLoading(false);
    }
  }, [tokens?.accessToken]);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  useEffect(() => {
    const connected = searchParams.get("connected");
    if (!connected) return;
    const label = connected === "gmail" ? "Gmail" : connected === "outlook" ? "Outlook" : connected;
    setNotice(t("settings.integrations.connectedNotice", { provider: label }));
    router.replace("/ayarlar");
  }, [searchParams, router]);

  useEffect(() => {
    if (!user?.profile) return;
    setProfileForm({ fullName: user.profile.full_name, title: user.profile.title ?? "" });
  }, [user?.profile]);

  async function handleSaveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !profileForm.fullName.trim()) return;
    setSavingProfile(true);
    setError(null);
    try {
      await updateProfile(tokens.accessToken, {
        full_name: profileForm.fullName.trim(),
        title: profileForm.title.trim() || null,
      });
      await refreshUser();
      setEditingProfile(false);
      setNotice(t("settings.account.profileUpdated"));
    } catch (profileError) {
      setError(profileError instanceof Error ? profileError.message : t("settings.account.profileUpdateError"));
    } finally {
      setSavingProfile(false);
    }
  }

  async function handleInviteMember(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !inviteForm.email.trim()) return;
    setInviting(true);
    setError(null);
    try {
      const member = await inviteOrganizationMember(
        tokens.accessToken,
        inviteForm.email.trim(),
        inviteForm.role,
      );
      setMembers((current) => [...current, member]);
      setInviteForm({ email: "", role: "member" });
      setShowInviteForm(false);
      setNotice(t("settings.team.inviteSent", { email: member.email ?? inviteForm.email.trim() }));
    } catch (inviteError) {
      setError(inviteError instanceof Error ? inviteError.message : t("settings.team.inviteError"));
    } finally {
      setInviting(false);
    }
  }

  async function handleSwitchPlan(planCode: string) {
    if (!tokens?.accessToken) return;
    setBusyPlanCode(planCode);
    setError(null);
    try {
      const updated = await switchPlan(tokens.accessToken, planCode);
      setSubscription(updated);
      setNotice(t("settings.billing.planUpdated", { planName: updated.plan.name }));
    } catch (switchError) {
      setError(switchError instanceof Error ? switchError.message : t("settings.billing.planUpdateError"));
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
      setError(roleError instanceof Error ? roleError.message : t("settings.team.roleUpdateError"));
    } finally {
      setBusyMemberId(null);
    }
  }

  async function handleConnectEmail(provider: "gmail" | "outlook") {
    if (!tokens?.accessToken) return;
    setBusyIntegration(provider);
    setError(null);
    try {
      const { authorize_url } =
        provider === "gmail"
          ? await startGmailConnect(tokens.accessToken)
          : await startOutlookConnect(tokens.accessToken);
      // Full-page redirect: the provider's consent screen must see the real
      // top-level navigation, then it redirects the browser back to our
      // backend callback, which in turn redirects here with ?connected=.
      window.location.href = authorize_url;
    } catch (connectError) {
      setError(connectError instanceof Error ? connectError.message : t("settings.integrations.connectError"));
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
      setError(revokeError instanceof Error ? revokeError.message : t("settings.integrations.disconnectError"));
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
      setNotice(t("settings.integrations.googleCalendarConnected"));
    } catch (connectError) {
      setError(connectError instanceof Error ? connectError.message : t("tasks.calendarConnectError"));
    } finally {
      setBusyIntegration(null);
    }
  }

  async function updateConsent(key: keyof ConsentSettings, value: boolean) {
    if (!tokens?.accessToken) return;
    const next = { ...consent, [key]: value };
    setConsent(next);
    setSavingConsent(true);
    setError(null);
    try {
      await updateConsentSettings(tokens.accessToken, next);
      setNotice(t("settings.consent.saved"));
    } catch (consentError) {
      setConsent(consent);
      setError(consentError instanceof Error ? consentError.message : t("settings.consent.saveError"));
    } finally {
      setSavingConsent(false);
    }
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
        <h2 className="font-headline-lg text-headline-lg text-on-surface">{t("settings.pageTitle")}</h2>
        <p className="text-body-lg text-on-surface-variant">{t("settings.pageSubtitle")}</p>
      </header>

      {error ? <p className="text-error text-body-sm mb-md">{error}</p> : null}
      {notice ? <p className="text-primary text-body-sm mb-md">{notice}</p> : null}

      <div className="grid grid-cols-12 gap-lg">
        <section className="col-span-12 lg:col-span-8 space-y-md">
          <div className="flex items-center justify-between mb-sm">
            <h3 className="font-headline-md text-headline-md flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">extension</span>
              {t("settings.integrations.title")}
            </h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
            <IntegrationCard
              meta={INTEGRATION_META.gmail}
              detail={gmailAccount?.email_address ?? t("common.notConnected")}
              isConnected={Boolean(gmailAccount)}
              isBusy={busyIntegration === "gmail" || busyIntegration === gmailAccount?.id}
              onConnect={() => handleConnectEmail("gmail")}
              onDisconnect={gmailAccount ? () => handleDisconnectEmail(gmailAccount.id) : undefined}
            />
            <IntegrationCard
              meta={INTEGRATION_META.outlook}
              detail={outlookAccount?.email_address ?? t("common.notConnected")}
              isConnected={Boolean(outlookAccount)}
              isBusy={busyIntegration === "outlook" || busyIntegration === outlookAccount?.id}
              onConnect={() => handleConnectEmail("outlook")}
              onDisconnect={outlookAccount ? () => handleDisconnectEmail(outlookAccount.id) : undefined}
            />
            <IntegrationCard
              meta={INTEGRATION_META.google}
              detail={googleCalendarAccount?.external_account_id ?? t("common.notConnected")}
              isConnected={Boolean(googleCalendarAccount)}
              isBusy={busyIntegration === "google-calendar"}
              onConnect={handleConnectCalendar}
            />
            <div
              aria-disabled="true"
              className="border-2 border-dashed border-outline-variant p-lg rounded-xl flex flex-col items-center justify-center opacity-60 cursor-not-allowed select-none"
            >
              <span className="px-2 py-0.5 mb-sm rounded-full bg-surface-container-highest text-outline text-[10px] font-bold uppercase tracking-wide">
                {t("settings.integrations.comingSoonBadge")}
              </span>
              <div className="w-10 h-10 rounded-full bg-surface-container flex items-center justify-center mb-sm">
                <span className="material-symbols-outlined">add</span>
              </div>
              <p className="font-label-md text-on-surface-variant">{t("settings.integrations.addNew")}</p>
              <p className="text-[10px] text-outline text-center mt-xs">{t("settings.integrations.addNewHint")}</p>
            </div>
          </div>
        </section>

        <section className="col-span-12 lg:col-span-4 space-y-md">
          <h3 className="font-headline-md text-headline-md flex items-center gap-2 mb-sm">
            <span className="material-symbols-outlined text-primary">payments</span>
            {t("settings.billing.title")}
          </h3>
          <div className="bg-inverse-surface text-on-primary-fixed p-lg rounded-xl relative overflow-hidden shadow-xl">
            <div className="absolute -top-12 -right-12 w-32 h-32 bg-primary/20 blur-3xl rounded-full" />
            <div className="relative z-10">
              <div className="flex justify-between items-center mb-lg">
                <span className="font-label-sm text-primary-fixed-dim uppercase tracking-widest">
                  {t("settings.billing.activePlan")}
                </span>
                <span className="px-3 py-1 bg-primary text-white text-xs font-bold rounded-full uppercase">
                  {subscription?.plan.code ?? "--"}
                </span>
              </div>
              <div className="mb-xl">
                <h4 className="text-headline-lg font-bold text-white">
                  {subscription ? formatMoney(subscription.plan.price, "USD", language) : "--"}{" "}
                  <span className="text-body-md font-normal text-outline-variant">
                    / {subscription?.plan.billing_period ?? "-"}
                  </span>
                </h4>
                <p className="text-body-sm text-outline-variant mt-xs">
                  {subscription
                    ? t("settings.billing.statusLine", {
                        status: subscription.status,
                        periodEnd: formatDateTime(subscription.current_period_end, language),
                      })
                    : t("settings.billing.awaitingData")}
                </p>
              </div>
              <div className="space-y-2 mb-xl max-h-32 overflow-y-auto custom-scrollbar">
                {plans.map((plan) => (
                  <div key={plan.id} className="flex items-center justify-between text-body-sm text-on-primary-container">
                    <span>
                      {plan.name} · {formatMoney(plan.price, "USD", language)}/{plan.billing_period}
                    </span>
                    {plan.code === subscription?.plan.code ? (
                      <span className="text-[10px] opacity-70">{t("settings.billing.currentPlanBadge")}</span>
                    ) : (
                      <button
                        type="button"
                        disabled={busyPlanCode === plan.code}
                        onClick={() => handleSwitchPlan(plan.code)}
                        className="text-[11px] font-bold underline disabled:opacity-60"
                      >
                        {busyPlanCode === plan.code ? "..." : t("settings.billing.selectPlan")}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="glass-card p-lg rounded-xl">
            <h5 className="font-label-md mb-md">{t("settings.usage.title")}</h5>
            <div className="space-y-2">
              <div className="flex justify-between text-body-sm">
                <span className="text-on-surface-variant">
                  {usage?.quota_type ?? t("settings.usage.fallbackQuotaType")}
                </span>
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
          <div className="flex items-center justify-between mb-sm flex-wrap gap-2">
            <h3 className="font-headline-md text-headline-md flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">groups</span>
              {t("settings.team.title")}
            </h3>
            <div className="flex items-center gap-3">
              <span className="text-body-sm text-on-surface-variant">
                {t("settings.team.memberCount", { count: members.length })}
              </span>
              <button
                type="button"
                onClick={() => setShowInviteForm((v) => !v)}
                className="flex items-center gap-1.5 text-primary text-[12px] font-bold hover:underline"
              >
                <span className="material-symbols-outlined text-[16px]">person_add</span>
                {t("settings.team.inviteButton")}
              </button>
            </div>
          </div>

          {showInviteForm ? (
            <form onSubmit={handleInviteMember} className="glass-card p-lg rounded-xl flex flex-wrap gap-2 items-start">
              <input
                className="flex-1 min-w-[200px] bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                onChange={(e) => setInviteForm((f) => ({ ...f, email: e.target.value }))}
                placeholder={t("settings.team.invitePlaceholder")}
                type="email"
                value={inviteForm.email}
              />
              <select
                className="bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                onChange={(e) => setInviteForm((f) => ({ ...f, role: e.target.value }))}
                value={inviteForm.role}
              >
                <option value="admin">{t("settings.team.roles.admin")}</option>
                <option value="member">{t("settings.team.roles.member")}</option>
                <option value="viewer">{t("settings.team.roles.viewer")}</option>
              </select>
              <button
                type="submit"
                disabled={isInviting || !inviteForm.email.trim()}
                className="py-2 px-4 bg-primary text-on-primary rounded-lg text-label-sm font-bold disabled:opacity-60"
              >
                {isInviting ? t("common.loading") : t("settings.team.inviteSubmit")}
              </button>
            </form>
          ) : null}

          <div className="glass-card rounded-xl overflow-hidden">
            {members.length === 0 ? (
              <p className="p-lg text-body-sm text-on-surface-variant">{t("settings.team.noMembers")}</p>
            ) : (
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-surface-container-high border-b border-outline-variant">
                    <th className="px-lg py-md text-label-sm uppercase tracking-wider text-on-surface-variant">
                      {t("settings.team.memberColumn")}
                    </th>
                    <th className="px-lg py-md text-label-sm uppercase tracking-wider text-on-surface-variant">
                      {t("common.status")}
                    </th>
                    <th className="px-lg py-md text-label-sm uppercase tracking-wider text-on-surface-variant">
                      {t("settings.team.roleColumn")}
                    </th>
                    <th className="px-lg py-md text-label-sm uppercase tracking-wider text-on-surface-variant">
                      {t("settings.team.joinedColumn")}
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-outline-variant">
                  {members.map((member) => (
                    <tr key={member.id} className="hover:bg-primary-container/5 transition-colors">
                      <td className="px-lg py-md">
                        <div className="flex items-center gap-md">
                          <div className="w-9 h-9 rounded-full bg-primary-container/20 flex items-center justify-center text-primary text-[11px] font-bold">
                            {getInitials(member.full_name ?? member.email)}
                          </div>
                          <span className="font-label-md text-on-surface truncate">
                            {member.full_name ?? member.email ?? member.user_id}
                          </span>
                        </div>
                      </td>
                      <td className="px-lg py-md text-body-sm">
                        {member.status === "invited" ? (
                          <span className="px-2 py-0.5 rounded-full bg-secondary/10 text-secondary text-[11px] font-bold uppercase tracking-wide">
                            {t("settings.team.statusInvited")}
                          </span>
                        ) : (
                          member.status
                        )}
                      </td>
                      <td className="px-lg py-md">
                        <select
                          className="bg-transparent border-none focus:ring-0 text-body-md font-medium text-on-surface cursor-pointer"
                          disabled={busyMemberId === member.id}
                          onChange={(e) => handleRoleChange(member.id, e.target.value)}
                          value={member.role}
                        >
                          <option value="owner">{t("settings.team.roles.owner")}</option>
                          <option value="admin">{t("settings.team.roles.admin")}</option>
                          <option value="member">{t("settings.team.roles.member")}</option>
                          <option value="viewer">{t("settings.team.roles.viewer")}</option>
                        </select>
                      </td>
                      <td className="px-lg py-md text-body-sm text-outline">
                        {formatDateTime(member.created_at, language)}
                      </td>
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
          <div className="flex items-center justify-between mb-md">
            <h3 className="font-headline-md text-headline-md">{t("settings.account.title")}</h3>
            {!isEditingProfile ? (
              <button
                type="button"
                onClick={() => setEditingProfile(true)}
                className="text-primary text-[12px] font-bold hover:underline"
              >
                {t("common.edit")}
              </button>
            ) : null}
          </div>

          {isEditingProfile ? (
            <form onSubmit={handleSaveProfile} className="space-y-2">
              <input
                className="w-full bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                onChange={(e) => setProfileForm((f) => ({ ...f, fullName: e.target.value }))}
                placeholder={t("auth.fullName")}
                value={profileForm.fullName}
              />
              <input
                className="w-full bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                onChange={(e) => setProfileForm((f) => ({ ...f, title: e.target.value }))}
                placeholder={t("contacts.titleRolePlaceholder")}
                value={profileForm.title}
              />
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={isSavingProfile || !profileForm.fullName.trim()}
                  className="flex-1 py-2 bg-primary text-on-primary rounded-lg text-label-sm font-bold disabled:opacity-60"
                >
                  {isSavingProfile ? t("common.loading") : t("common.save")}
                </button>
                <button
                  type="button"
                  onClick={() => setEditingProfile(false)}
                  className="px-3 py-2 bg-surface text-on-surface-variant rounded-lg text-label-sm font-bold"
                >
                  {t("common.cancel")}
                </button>
              </div>
            </form>
          ) : (
            <div className="space-y-2">
              <MetricLine label={t("auth.fullName")} value={user?.profile?.full_name ?? "--"} />
              <MetricLine label={t("common.email")} value={user?.email ?? "--"} />
              <MetricLine label={t("settings.account.userStatus")} value={user?.status ?? "--"} />
              <MetricLine label={t("settings.account.organizationName")} value={organization?.name ?? "--"} />
            </div>
          )}
        </section>

        <section className="glass-card p-lg rounded-xl">
          <h3 className="font-headline-md text-headline-md mb-md">{t("settings.consent.title")}</h3>
          <div className="space-y-3">
            <ConsentToggle
              checked={consent.ai_processing}
              description={t("settings.consent.aiProcessingDescription")}
              disabled={isSavingConsent}
              label={t("settings.consent.aiProcessingLabel")}
              onChange={(value) => updateConsent("ai_processing", value)}
            />
            <ConsentToggle
              checked={consent.contact_memory}
              description={t("settings.consent.contactMemoryDescription")}
              disabled={isSavingConsent}
              label={t("settings.consent.contactMemoryLabel")}
              onChange={(value) => updateConsent("contact_memory", value)}
            />
            <ConsentToggle
              checked={consent.operational_reminders}
              description={t("settings.consent.operationalRemindersDescription")}
              disabled={isSavingConsent}
              label={t("settings.consent.operationalRemindersLabel")}
              onChange={(value) => updateConsent("operational_reminders", value)}
            />
          </div>
        </section>
      </div>

      <section className="glass-card p-lg rounded-xl mt-lg">
        <h3 className="font-headline-md text-headline-md flex items-center gap-2">
          <span className="material-symbols-outlined text-primary">support_agent</span>
          {t("settings.support.title")}
        </h3>
        <p className="text-body-sm text-on-surface-variant mt-xs mb-md">{t("settings.support.subtitle")}</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-md">
          <a
            href="mailto:neurodeskkai@gmail.com"
            className="flex items-center gap-3 p-md rounded-lg border border-outline-variant hover:bg-surface-container-high transition-colors"
          >
            <span className="material-symbols-outlined text-primary">mail</span>
            <span>
              <span className="block text-label-sm text-on-surface-variant">{t("settings.support.emailLabel")}</span>
              <strong className="font-label-md text-on-surface">neurodeskkai@gmail.com</strong>
            </span>
          </a>
          <a
            href="tel:+905530682570"
            className="flex items-center gap-3 p-md rounded-lg border border-outline-variant hover:bg-surface-container-high transition-colors"
          >
            <span className="material-symbols-outlined text-primary">call</span>
            <span>
              <span className="block text-label-sm text-on-surface-variant">{t("settings.support.phoneLabel")}</span>
              <strong className="font-label-md text-on-surface">+90 553 068 25 70</strong>
            </span>
          </a>
        </div>
      </section>

      <section className="glass-card rounded-xl overflow-hidden mt-lg">
        <div className="px-lg py-md border-b border-outline-variant/30">
          <h3 className="font-headline-md text-headline-md">{t("settings.audit.title")}</h3>
        </div>
        {isLoading ? <p className="p-lg text-body-sm text-on-surface-variant">{t("common.loading")}</p> : null}
        {!isLoading && auditLogs.length === 0 ? (
          <p className="p-lg text-body-sm text-on-surface-variant">{t("settings.audit.empty")}</p>
        ) : null}
        {auditLogs.length > 0 ? (
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-container text-outline font-label-sm uppercase tracking-wider">
                <th className="px-lg py-3">{t("settings.audit.actionColumn")}</th>
                <th className="px-lg py-3">{t("settings.audit.entityColumn")}</th>
                <th className="px-lg py-3 text-right">{t("settings.audit.timeColumn")}</th>
              </tr>
            </thead>
            <tbody className="text-body-sm">
              {auditLogs.map((log) => (
                <tr key={log.id} className="border-b border-outline-variant/10">
                  <td className="px-lg py-3">{log.action}</td>
                  <td className="px-lg py-3">{log.entity_type}</td>
                  <td className="px-lg py-3 text-right text-outline">
                    {formatDateTime(log.created_at, language)}
                  </td>
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
  const { t } = useLanguage();
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
              {isConnected ? t("common.connected") : t("common.notConnected")}
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
        {isBusy ? t("auth.submitting") : isConnected ? t("common.disconnect") : t("common.connect")}
      </button>
    </div>
  );
}

function ConsentToggle({
  checked,
  description,
  disabled = false,
  label,
  onChange,
}: {
  checked: boolean;
  description: string;
  disabled?: boolean;
  label: string;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className="flex items-start gap-3 cursor-pointer">
      <input
        checked={checked}
        disabled={disabled}
        onChange={(event) => onChange(event.target.checked)}
        type="checkbox"
        className="mt-1 disabled:opacity-60"
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
