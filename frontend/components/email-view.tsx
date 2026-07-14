"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import {
  completeEmailConnect,
  EmailAccount,
  EmailConnectStart,
  EmailMessage,
  EmailProvider,
  EmailSyncSummary,
  listEmailAccounts,
  listEmailMessages,
  markEmailReplied,
  refreshEmailAccountToken,
  revokeEmailAccount,
  startEmailConnect,
  syncEmailAccount,
} from "@/lib/api";
import { useSession } from "@/lib/session";

type PendingConnect = EmailConnectStart & {
  provider: EmailProvider;
};

const providerLabels: Record<EmailProvider, string> = {
  gmail: "Gmail",
  outlook: "Outlook",
};

const providerIcons: Record<EmailProvider, string> = {
  gmail: "mail",
  outlook: "alternate_email",
};

const providerDescriptions: Record<EmailProvider, string> = {
  gmail: "Google Gmail readonly scope ile yerel mock OAuth akışı.",
  outlook: "Microsoft Graph Mail.Read ve offline_access scope ile yerel mock OAuth akışı.",
};

export function EmailView() {
  const { tokens } = useSession();
  const searchParams = useSearchParams();
  const justConnectedProvider = searchParams.get("connected");
  const [accounts, setAccounts] = useState<EmailAccount[]>([]);
  const [activeAccountId, setActiveAccountId] = useState<string | null>(null);
  const [messages, setMessages] = useState<EmailMessage[]>([]);
  const [lastSync, setLastSync] = useState<EmailSyncSummary | null>(null);
  const [pendingConnect, setPendingConnect] = useState<PendingConnect | null>(null);
  const [mockCode, setMockCode] = useState("mock-code");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [activeActionId, setActiveActionId] = useState<string | null>(null);

  async function loadMessages(accountId: string) {
    if (!tokens?.accessToken) {
      return;
    }

    setError(null);
    try {
      setMessages(await listEmailMessages(tokens.accessToken, accountId));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "E-posta mesajları alınamadı.");
    }
  }

  async function loadAccounts() {
    if (!tokens?.accessToken) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const nextAccounts = await listEmailAccounts(tokens.accessToken);
      setAccounts(nextAccounts);

      const nextActiveId =
        activeAccountId && nextAccounts.some((account) => account.id === activeAccountId)
          ? activeAccountId
          : nextAccounts[0]?.id;

      if (nextActiveId) {
        setActiveAccountId(nextActiveId);
        await loadMessages(nextActiveId);
      } else {
        setActiveAccountId(null);
        setMessages([]);
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "E-posta hesapları alınamadı.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAccounts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tokens?.accessToken]);

  const summary = useMemo(() => {
    return {
      accounts: accounts.length,
      connected: accounts.filter((account) => account.status === "connected").length,
      messages: messages.length,
      providers: new Set(accounts.map((account) => account.provider)).size,
    };
  }, [accounts, messages.length]);

  async function selectAccount(accountId: string) {
    setActiveAccountId(accountId);
    await loadMessages(accountId);
  }

  async function handleStartConnect(provider: EmailProvider) {
    if (!tokens?.accessToken) {
      return;
    }

    setActiveActionId(`${provider}-connect`);
    setError(null);
    try {
      const connectStart = await startEmailConnect(tokens.accessToken, provider);
      setPendingConnect({ ...connectStart, provider });
    } catch (connectError) {
      setError(
        connectError instanceof Error
          ? connectError.message
          : `${providerLabels[provider]} bağlantısı başlatılamadı.`,
      );
    } finally {
      setActiveActionId(null);
    }
  }

  async function handleCompleteConnect() {
    if (!pendingConnect) {
      return;
    }

    setActiveActionId(`${pendingConnect.provider}-callback`);
    setError(null);
    try {
      const account = await completeEmailConnect(
        pendingConnect.provider,
        pendingConnect.state,
        mockCode.trim() || "mock-code",
      );
      setPendingConnect(null);
      setActiveAccountId(account.id);
      await loadAccounts();
      await loadMessages(account.id);
    } catch (connectError) {
      setError(
        connectError instanceof Error
          ? connectError.message
          : `${providerLabels[pendingConnect.provider]} bağlantısı tamamlanamadı.`,
      );
    } finally {
      setActiveActionId(null);
    }
  }

  async function handleSync(accountId: string) {
    if (!tokens?.accessToken) {
      return;
    }

    setActiveActionId(accountId);
    setError(null);
    try {
      const syncSummary = await syncEmailAccount(tokens.accessToken, accountId);
      setLastSync(syncSummary);
      await loadMessages(accountId);
    } catch (syncError) {
      setError(syncError instanceof Error ? syncError.message : "E-posta senkronizasyonu tamamlanamadı.");
    } finally {
      setActiveActionId(null);
    }
  }

  async function handleRefreshToken(accountId: string) {
    if (!tokens?.accessToken) {
      return;
    }

    setActiveActionId(`refresh-${accountId}`);
    setError(null);
    try {
      await refreshEmailAccountToken(tokens.accessToken, accountId);
      await loadAccounts();
    } catch (refreshError) {
      setError(refreshError instanceof Error ? refreshError.message : "Token yenileme tamamlanamadı.");
    } finally {
      setActiveActionId(null);
    }
  }

  async function handleMarkReplied(messageId: string) {
    if (!tokens?.accessToken) {
      return;
    }

    setActiveActionId(`replied-${messageId}`);
    setError(null);
    try {
      const updated = await markEmailReplied(tokens.accessToken, messageId);
      setMessages((currentMessages) =>
        currentMessages.map((message) => (message.id === updated.id ? updated : message)),
      );
    } catch (markError) {
      setError(markError instanceof Error ? markError.message : "Mesaj işaretlenemedi.");
    } finally {
      setActiveActionId(null);
    }
  }

  async function handleRevoke(account: EmailAccount) {
    if (!tokens?.accessToken) {
      return;
    }

    setActiveActionId(`revoke-${account.id}`);
    setError(null);
    try {
      await revokeEmailAccount(tokens.accessToken, account.id);
      await loadAccounts();
      if (activeAccountId === account.id) {
        setMessages([]);
      }
    } catch (revokeError) {
      const providerLabel = getProviderLabel(account.provider);
      setError(
        revokeError instanceof Error
          ? revokeError.message
          : `${providerLabel} bağlantısı kaldırılamadı.`,
      );
    } finally {
      setActiveActionId(null);
    }
  }

  return (
    <section className="moduleSurface">
      {error ? <p className="notice">{error}</p> : null}
      {justConnectedProvider ? (
        <p className="notice success">
          {getProviderLabel(justConnectedProvider)} hesabı başarıyla bağlandı.
        </p>
      ) : null}

      <div className="statTileRow">
        <StatTile icon="account_circle" label="Hesap" value={summary.accounts} />
        <StatTile icon="link" label="Bağlı" value={summary.connected} />
        <StatTile icon="mail" label="Mesaj" value={summary.messages} />
        <StatTile icon="hub" label="Sağlayıcı" value={summary.providers} />
      </div>

      {lastSync ? (
        <p className="notice">
          Senkronizasyon tamamlandı: {lastSync.fetched} alındı, {lastSync.created} eklendi,{" "}
          {lastSync.skipped} atlandı.
        </p>
      ) : null}

      <div className="contentGrid">
        <section className="panel">
          <div className="panelHeader">
            <h2>E-posta hesapları</h2>
            <div className="rowActions horizontal">
              <button
                disabled={activeActionId === "gmail-connect"}
                onClick={() => handleStartConnect("gmail")}
                type="button"
              >
                {activeActionId === "gmail-connect" ? "Başlatılıyor" : "Gmail bağla"}
              </button>
              <button
                disabled={activeActionId === "outlook-connect"}
                onClick={() => handleStartConnect("outlook")}
                type="button"
              >
                {activeActionId === "outlook-connect" ? "Başlatılıyor" : "Outlook bağla"}
              </button>
              <button disabled={isLoading} onClick={loadAccounts} type="button">
                {isLoading ? "Yükleniyor" : "Yenile"}
              </button>
            </div>
          </div>

          {pendingConnect ? (
            <div className="connectBox">
              <div>
                <strong>{providerLabels[pendingConnect.provider]} yetkilendirme hazır</strong>
                <p>{providerDescriptions[pendingConnect.provider]}</p>
                <a href={pendingConnect.authorize_url} rel="noreferrer" target="_blank">
                  Yetki URL'sini aç
                </a>
              </div>
              <label>
                Test kodu
                <input onChange={(event) => setMockCode(event.target.value)} value={mockCode} />
              </label>
              <button
                disabled={activeActionId === `${pendingConnect.provider}-callback`}
                onClick={handleCompleteConnect}
                type="button"
              >
                {activeActionId === `${pendingConnect.provider}-callback`
                  ? "Tamamlanıyor"
                  : "Mock callback'i tamamla"}
              </button>
            </div>
          ) : null}

          <div className="dataList">
            {accounts.length === 0 ? <p className="emptyState">Bağlı e-posta hesabı yok.</p> : null}
            {accounts.map((account) => (
              <article className="dataRow" key={account.id}>
                <div>
                  <div className="rowTitle">
                    <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 16 }}>
                      {account.provider === "gmail" || account.provider === "outlook"
                        ? providerIcons[account.provider]
                        : "mail"}
                    </span>
                    <h3>{account.email_address ?? getProviderLabel(account.provider)}</h3>
                    <span>{getProviderLabel(account.provider)}</span>
                  </div>
                  <p>{account.consent_scope ?? "Scope bilgisi yok."}</p>
                  <small>
                    {account.last_synced_at
                      ? `Son senkronizasyon ${formatDateTime(account.last_synced_at)}`
                      : "Henüz senkronizasyon yok"}
                  </small>
                </div>
                <div className="rowActions horizontal">
                  <span className="statusPill">{account.status}</span>
                  <button onClick={() => selectAccount(account.id)} type="button">
                    Aç
                  </button>
                  <button
                    disabled={activeActionId === account.id || account.status !== "connected"}
                    onClick={() => handleSync(account.id)}
                    type="button"
                  >
                    {activeActionId === account.id ? "Senkronize ediliyor" : "Senkronize et"}
                  </button>
                  <button
                    disabled={activeActionId === `refresh-${account.id}` || account.status !== "connected"}
                    onClick={() => handleRefreshToken(account.id)}
                    type="button"
                  >
                    {activeActionId === `refresh-${account.id}` ? "Yenileniyor" : "Token yenile"}
                  </button>
                  <button
                    disabled={activeActionId === `revoke-${account.id}` || account.status === "revoked"}
                    onClick={() => handleRevoke(account)}
                    type="button"
                  >
                    {activeActionId === `revoke-${account.id}` ? "Kaldırılıyor" : "Bağlantıyı kaldır"}
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="panelHeader">
            <h2>Mesajlar</h2>
            <span className="tag">{messages.length}</span>
          </div>
          <div className="dataList">
            {messages.length === 0 ? <p className="emptyState">Seçili hesapta mesaj yok.</p> : null}
            {messages.map((message) => (
              <article className="dataRow" key={message.id}>
                <div>
                  <div className="rowTitle">
                    <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 16 }}>
                      {message.is_replied ? "mark_email_read" : "mail"}
                    </span>
                    <h3>{message.subject ?? "Konu yok"}</h3>
                    {message.is_replied ? <span className="statusPill done">Yanıtlandı</span> : null}
                  </div>
                  <p>{message.snippet ?? "Ön izleme yok."}</p>
                  <small>{message.from_address ?? "Gönderen yok"}</small>
                </div>
                {!message.is_replied ? (
                  <div className="rowActions horizontal">
                    <button
                      disabled={activeActionId === `replied-${message.id}`}
                      onClick={() => handleMarkReplied(message.id)}
                      type="button"
                    >
                      Yanıtlandı işaretle
                    </button>
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        </section>
      </div>
    </section>
  );
}

function StatTile({ icon, label, value }: { icon: string; label: string; value: number }) {
  return (
    <div className="statTile">
      <div className="statTileHead">
        <div className="statTileIcon">
          <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 18 }}>
            {icon}
          </span>
        </div>
      </div>
      <p>{label}</p>
      <strong>{value}</strong>
    </div>
  );
}

function getProviderLabel(provider: string): string {
  if (provider === "gmail" || provider === "outlook") {
    return providerLabels[provider];
  }
  return provider;
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
  }).format(new Date(value));
}
