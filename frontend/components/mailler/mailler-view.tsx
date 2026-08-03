"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  EmailAccount,
  EmailMessage,
  listEmailAccounts,
  listEmailMessages,
  markEmailReplied,
  syncEmailAccount,
} from "@/lib/api";
import { useSession } from "@/lib/session";
import { Language, useLanguage } from "@/lib/i18n/context";
import { useToast } from "@/lib/toast";
import { formatDateTime } from "@/lib/format";
import { SkeletonList } from "@/components/shell/skeleton";
import { EmptyState } from "@/components/shell/empty-state";

export function MaillerView() {
  const { tokens } = useSession();
  const { t, language } = useLanguage();
  const { showToast } = useToast();
  const router = useRouter();
  const [accounts, setAccounts] = useState<EmailAccount[]>([]);
  const [messagesByAccount, setMessagesByAccount] = useState<Record<string, EmailMessage[]>>({});
  const [isLoading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyAccountId, setBusyAccountId] = useState<string | null>(null);
  const [busyMessageId, setBusyMessageId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const connectedAccounts = useMemo(
    () => accounts.filter((account) => account.status !== "revoked"),
    [accounts],
  );

  const load = useCallback(async () => {
    if (!tokens?.accessToken) return;
    setLoading(true);
    setError(null);
    try {
      const accessToken = tokens.accessToken;
      const nextAccounts = await listEmailAccounts(accessToken);
      setAccounts(nextAccounts);
      const connected = nextAccounts.filter((account) => account.status !== "revoked");
      const entries = await Promise.all(
        connected.map(async (account) => [account.id, await listEmailMessages(accessToken, account.id)] as const),
      );
      setMessagesByAccount(Object.fromEntries(entries));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : t("mailler.loadError"));
    } finally {
      setLoading(false);
    }
  }, [tokens?.accessToken, t]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleSync(accountId: string) {
    if (!tokens?.accessToken) return;
    const accessToken = tokens.accessToken;
    setBusyAccountId(accountId);
    setError(null);
    try {
      const summary = await syncEmailAccount(accessToken, accountId);
      showToast(t("mailler.syncSuccess", { count: summary.created }), "success");
      const [messages, nextAccounts] = await Promise.all([
        listEmailMessages(accessToken, accountId),
        listEmailAccounts(accessToken),
      ]);
      setMessagesByAccount((current) => ({ ...current, [accountId]: messages }));
      setAccounts(nextAccounts);
    } catch (syncError) {
      setError(syncError instanceof Error ? syncError.message : t("mailler.syncError"));
    } finally {
      setBusyAccountId(null);
    }
  }

  async function handleMarkReplied(accountId: string, message: EmailMessage) {
    if (!tokens?.accessToken) return;
    setBusyMessageId(message.id);
    setError(null);
    try {
      const updated = await markEmailReplied(tokens.accessToken, message.id);
      setMessagesByAccount((current) => ({
        ...current,
        [accountId]: (current[accountId] ?? []).map((item) => (item.id === updated.id ? updated : item)),
      }));
    } catch (markError) {
      setError(markError instanceof Error ? markError.message : t("mailler.markRepliedError"));
    } finally {
      setBusyMessageId(null);
    }
  }

  function filterMessages(messages: EmailMessage[]): EmailMessage[] {
    const query = searchQuery.trim().toLocaleLowerCase(language === "tr" ? "tr-TR" : "en-US");
    if (!query) return messages;
    return messages.filter((message) =>
      `${message.subject ?? ""} ${message.from_address ?? ""}`.toLocaleLowerCase().includes(query),
    );
  }

  const totalMessages = useMemo(
    () => Object.values(messagesByAccount).reduce((sum, list) => sum + list.length, 0),
    [messagesByAccount],
  );

  return (
    <div className="p-xl space-y-xl">
      <header className="flex items-start justify-between gap-lg flex-wrap">
        <div>
          <h2 className="font-headline-lg text-headline-lg text-on-surface">{t("mailler.title")}</h2>
          <p className="text-body-md text-on-surface-variant mt-1">{t("mailler.subtitle")}</p>
        </div>
      </header>

      {error ? <p className="text-error text-body-sm">{error}</p> : null}

      {isLoading ? <SkeletonList count={3} /> : null}

      {!isLoading && connectedAccounts.length === 0 ? (
        <div className="glass-card rounded-xl">
          <EmptyState
            icon="mail"
            size="lg"
            title={t("mailler.noAccountsTitle")}
            action={{ label: t("mailler.noAccountsCta"), onClick: () => router.push("/ayarlar") }}
          />
        </div>
      ) : null}

      {!isLoading && connectedAccounts.length > 0 ? (
        <>
          {totalMessages > 0 ? (
            <div className="relative max-w-md">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-[18px]">
                search
              </span>
              <input
                className="w-full bg-surface-container-low border-none rounded-full pl-10 pr-4 py-2 text-body-sm"
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t("mailler.searchPlaceholder")}
                value={searchQuery}
              />
            </div>
          ) : null}

          {connectedAccounts.map((account) => (
            <AccountSection
              key={account.id}
              account={account}
              messages={filterMessages(messagesByAccount[account.id] ?? [])}
              hasAnyMessages={(messagesByAccount[account.id] ?? []).length > 0}
              isSyncing={busyAccountId === account.id}
              busyMessageId={busyMessageId}
              language={language}
              onSync={() => handleSync(account.id)}
              onMarkReplied={(message) => handleMarkReplied(account.id, message)}
            />
          ))}
        </>
      ) : null}
    </div>
  );
}

function AccountSection({
  account,
  messages,
  hasAnyMessages,
  isSyncing,
  busyMessageId,
  language,
  onSync,
  onMarkReplied,
}: {
  account: EmailAccount;
  messages: EmailMessage[];
  hasAnyMessages: boolean;
  isSyncing: boolean;
  busyMessageId: string | null;
  language: Language;
  onSync: () => void;
  onMarkReplied: (message: EmailMessage) => void;
}) {
  const { t } = useLanguage();
  return (
    <section className="space-y-md">
      <div className="flex items-center justify-between gap-md flex-wrap glass-card p-lg rounded-xl">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-11 h-11 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0">
            <span className="material-symbols-outlined">mail</span>
          </div>
          <div className="min-w-0">
            <p className="font-label-md text-label-md text-on-surface truncate">
              {account.email_address ?? account.provider}
            </p>
            <p className="text-body-sm text-on-surface-variant">
              {account.last_synced_at
                ? `${t("mailler.lastSyncedPrefix")}${formatDateTime(account.last_synced_at, language)}`
                : t("mailler.neverSynced")}
            </p>
          </div>
        </div>
        <button
          type="button"
          disabled={isSyncing}
          onClick={onSync}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-on-primary rounded-lg font-label-md disabled:opacity-60 shrink-0"
        >
          <span className="material-symbols-outlined text-[18px]">{isSyncing ? "hourglass_top" : "sync"}</span>
          {isSyncing ? t("mailler.syncing") : t("mailler.syncButton")}
        </button>
      </div>

      {!hasAnyMessages ? (
        <div className="glass-card rounded-xl">
          <EmptyState icon="drafts" title={t("mailler.noMessagesTitle")} />
        </div>
      ) : (
        <div className="space-y-md">
          {messages.map((message) => (
            <MessageCard
              key={message.id}
              message={message}
              language={language}
              isBusy={busyMessageId === message.id}
              onMarkReplied={() => onMarkReplied(message)}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function MessageCard({
  message,
  language,
  isBusy,
  onMarkReplied,
}: {
  message: EmailMessage;
  language: Language;
  isBusy: boolean;
  onMarkReplied: () => void;
}) {
  const { t } = useLanguage();
  return (
    <article className="glass-card p-lg rounded-xl">
      <div className="flex items-start justify-between gap-md">
        <div className="min-w-0">
          <p className="font-label-md text-label-md text-on-surface truncate">
            {message.subject || t("mailler.noSubject")}
          </p>
          <p className="text-body-sm text-on-surface-variant truncate mt-0.5">{message.from_address}</p>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {message.opened_at ? (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary-container/10 text-primary text-[11px] font-bold">
              <span className="material-symbols-outlined text-[13px]">visibility</span>
              {t("mailler.openedBadge")}
            </span>
          ) : null}
          {message.click_count > 0 ? (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary-container/10 text-primary text-[11px] font-bold">
              <span className="material-symbols-outlined text-[13px]">ads_click</span>
              {t("mailler.clickedBadge", { count: message.click_count })}
            </span>
          ) : null}
          {message.is_replied ? (
            <span className="px-2 py-0.5 rounded-full bg-success-container text-on-success-container text-[11px] font-bold">
              {t("mailler.repliedBadge")}
            </span>
          ) : null}
        </div>
      </div>
      {message.snippet ? (
        <p className="text-body-sm text-on-surface-variant mt-2 line-clamp-2">{message.snippet}</p>
      ) : null}
      <div className="flex items-center justify-between gap-md mt-md">
        <span className="flex items-center gap-1 text-body-sm text-on-surface-variant">
          <span className="material-symbols-outlined text-[16px]">schedule</span>
          {message.received_at ? formatDateTime(message.received_at, language) : "--"}
        </span>
        {!message.is_replied ? (
          <button
            type="button"
            disabled={isBusy}
            onClick={onMarkReplied}
            className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-label-sm font-bold border border-outline-variant/40 text-on-surface-variant bg-surface-container-lowest disabled:opacity-60"
          >
            <span className="material-symbols-outlined text-[17px]">{isBusy ? "hourglass_top" : "check"}</span>
            {t("mailler.markRepliedButton")}
          </button>
        ) : null}
      </div>
    </article>
  );
}
