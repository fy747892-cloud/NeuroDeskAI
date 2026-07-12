"use client";

import { useEffect, useMemo, useState } from "react";
import {
  completeGmailConnect,
  EmailAccount,
  EmailConnectStart,
  EmailMessage,
  EmailSyncSummary,
  listEmailAccounts,
  listEmailMessages,
  refreshEmailAccountToken,
  revokeEmailAccount,
  startGmailConnect,
  syncEmailAccount,
} from "@/lib/api";
import { useSession } from "@/lib/session";

export function EmailView() {
  const { tokens } = useSession();
  const [accounts, setAccounts] = useState<EmailAccount[]>([]);
  const [activeAccountId, setActiveAccountId] = useState<string | null>(null);
  const [messages, setMessages] = useState<EmailMessage[]>([]);
  const [lastSync, setLastSync] = useState<EmailSyncSummary | null>(null);
  const [pendingConnect, setPendingConnect] = useState<EmailConnectStart | null>(null);
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

  async function handleStartGmailConnect() {
    if (!tokens?.accessToken) {
      return;
    }

    setActiveActionId("gmail-connect");
    setError(null);
    try {
      setPendingConnect(await startGmailConnect(tokens.accessToken));
    } catch (connectError) {
      setError(connectError instanceof Error ? connectError.message : "Gmail bağlantısı başlatılamadı.");
    } finally {
      setActiveActionId(null);
    }
  }

  async function handleCompleteGmailConnect() {
    if (!pendingConnect) {
      return;
    }

    setActiveActionId("gmail-callback");
    setError(null);
    try {
      const account = await completeGmailConnect(pendingConnect.state, mockCode.trim() || "mock-code");
      setPendingConnect(null);
      setActiveAccountId(account.id);
      await loadAccounts();
      await loadMessages(account.id);
    } catch (connectError) {
      setError(connectError instanceof Error ? connectError.message : "Gmail bağlantısı tamamlanamadı.");
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

  async function handleRevoke(accountId: string) {
    if (!tokens?.accessToken) {
      return;
    }

    setActiveActionId(`revoke-${accountId}`);
    setError(null);
    try {
      await revokeEmailAccount(tokens.accessToken, accountId);
      await loadAccounts();
      if (activeAccountId === accountId) {
        setMessages([]);
      }
    } catch (revokeError) {
      setError(revokeError instanceof Error ? revokeError.message : "Gmail bağlantısı kaldırılamadı.");
    } finally {
      setActiveActionId(null);
    }
  }

  return (
    <section className="moduleSurface">
      {error ? <p className="notice">{error}</p> : null}

      <div className="moduleGrid">
        <SummaryCard label="Hesap" value={summary.accounts} />
        <SummaryCard label="Bağlı" value={summary.connected} />
        <SummaryCard label="Mesaj" value={summary.messages} />
        <SummaryCard label="Sağlayıcı" value={summary.providers} />
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
                onClick={handleStartGmailConnect}
                type="button"
              >
                {activeActionId === "gmail-connect" ? "Başlatılıyor" : "Gmail bağla"}
              </button>
              <button disabled={isLoading} onClick={loadAccounts} type="button">
                {isLoading ? "Yükleniyor" : "Yenile"}
              </button>
            </div>
          </div>

          {pendingConnect ? (
            <div className="connectBox">
              <div>
                <strong>Gmail yetkilendirme hazır</strong>
                <p>
                  Sprint 15 yerel mock akışında Google sayfasına yönlendirme yapılmaz. URL ve
                  state üretilir, ardından test kodu ile callback tamamlanır.
                </p>
                <a href={pendingConnect.authorize_url} rel="noreferrer" target="_blank">
                  Yetki URL'sini aç
                </a>
              </div>
              <label>
                Test kodu
                <input onChange={(event) => setMockCode(event.target.value)} value={mockCode} />
              </label>
              <button
                disabled={activeActionId === "gmail-callback"}
                onClick={handleCompleteGmailConnect}
                type="button"
              >
                {activeActionId === "gmail-callback" ? "Tamamlanıyor" : "Mock callback'i tamamla"}
              </button>
            </div>
          ) : null}

          <div className="dataList">
            {accounts.length === 0 ? <p className="emptyState">Bağlı e-posta hesabı yok.</p> : null}
            {accounts.map((account) => (
              <article className="dataRow" key={account.id}>
                <div>
                  <div className="rowTitle">
                    <h3>{account.email_address ?? account.provider}</h3>
                    <span>{account.provider}</span>
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
                    onClick={() => handleRevoke(account.id)}
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
                    <h3>{message.subject ?? "Konu yok"}</h3>
                  </div>
                  <p>{message.snippet ?? "Ön izleme yok."}</p>
                  <small>{message.from_address ?? "Gönderen yok"}</small>
                </div>
              </article>
            ))}
          </div>
        </section>
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

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
  }).format(new Date(value));
}
