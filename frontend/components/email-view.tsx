"use client";

import { useEffect, useMemo, useState } from "react";
import {
  EmailAccount,
  EmailMessage,
  EmailSyncSummary,
  listEmailAccounts,
  listEmailMessages,
  syncEmailAccount,
} from "@/lib/api";
import { useSession } from "@/lib/session";

export function EmailView() {
  const { tokens } = useSession();
  const [accounts, setAccounts] = useState<EmailAccount[]>([]);
  const [activeAccountId, setActiveAccountId] = useState<string | null>(null);
  const [messages, setMessages] = useState<EmailMessage[]>([]);
  const [lastSync, setLastSync] = useState<EmailSyncSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [activeActionId, setActiveActionId] = useState<string | null>(null);

  async function loadAccounts() {
    if (!tokens?.accessToken) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const nextAccounts = await listEmailAccounts(tokens.accessToken);
      setAccounts(nextAccounts);
      if (!activeAccountId && nextAccounts[0]) {
        setActiveAccountId(nextAccounts[0].id);
        await loadMessages(nextAccounts[0].id);
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Email hesaplari alinamadi.");
    } finally {
      setLoading(false);
    }
  }

  async function loadMessages(accountId: string) {
    if (!tokens?.accessToken) {
      return;
    }

    setError(null);
    try {
      setMessages(await listEmailMessages(tokens.accessToken, accountId));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Email mesajlari alinamadi.");
    }
  }

  useEffect(() => {
    loadAccounts();
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

  async function handleSync(accountId: string) {
    if (!tokens?.accessToken) {
      return;
    }

    setActiveActionId(accountId);
    setError(null);
    try {
      const summary = await syncEmailAccount(tokens.accessToken, accountId);
      setLastSync(summary);
      await loadMessages(accountId);
    } catch (syncError) {
      setError(syncError instanceof Error ? syncError.message : "Email senkronizasyonu tamamlanamadi.");
    } finally {
      setActiveActionId(null);
    }
  }

  return (
    <section className="moduleSurface">
      {error ? <p className="notice">{error}</p> : null}

      <div className="moduleGrid">
        <SummaryCard label="Hesap" value={summary.accounts} />
        <SummaryCard label="Bagli" value={summary.connected} />
        <SummaryCard label="Mesaj" value={summary.messages} />
        <SummaryCard label="Provider" value={summary.providers} />
      </div>

      {lastSync ? (
        <p className="notice">
          Sync tamamlandi: {lastSync.fetched} alindi, {lastSync.created} eklendi, {lastSync.skipped} atlandi.
        </p>
      ) : null}

      <div className="contentGrid">
        <section className="panel">
          <div className="panelHeader">
            <h2>Email hesaplari</h2>
            <button disabled={isLoading} onClick={loadAccounts} type="button">
              {isLoading ? "Yukleniyor" : "Yenile"}
            </button>
          </div>
          <div className="dataList">
            {accounts.length === 0 ? <p className="emptyState">Bagli email hesabi yok.</p> : null}
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
                      ? `Son sync ${formatDateTime(account.last_synced_at)}`
                      : "Henuz sync yok"}
                  </small>
                </div>
                <div className="rowActions horizontal">
                  <span className="statusPill">{account.status}</span>
                  <button onClick={() => selectAccount(account.id)} type="button">
                    Ac
                  </button>
                  <button
                    disabled={activeActionId === account.id}
                    onClick={() => handleSync(account.id)}
                    type="button"
                  >
                    {activeActionId === account.id ? "Sync" : "Senkronize"}
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
            {messages.length === 0 ? <p className="emptyState">Secili hesapta mesaj yok.</p> : null}
            {messages.map((message) => (
              <article className="dataRow" key={message.id}>
                <div>
                  <div className="rowTitle">
                    <h3>{message.subject ?? "Konu yok"}</h3>
                  </div>
                  <p>{message.snippet ?? "On izleme yok."}</p>
                  <small>{message.from_address ?? "Gonderen yok"}</small>
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
