"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  Contact,
  createDeal,
  Deal,
  DEAL_STAGES,
  listContacts,
  listDeals,
  updateDeal,
} from "@/lib/api";
import { useSession } from "@/lib/session";

const STAGE_LABEL: Record<string, string> = {
  lead: "Aday",
  proposal_sent: "Teklif Gönderildi",
  negotiation: "Müzakere",
  invoiced: "Faturalandı",
  won: "Kazanıldı",
  lost: "Kaybedildi",
};

const STAGE_DOT: Record<string, string> = {
  lead: "var(--muted)",
  proposal_sent: "var(--primary)",
  negotiation: "var(--purple)",
  invoiced: "var(--teal)",
  won: "#059669",
  lost: "var(--coral)",
};

const OPEN_STAGES = new Set(["lead", "proposal_sent", "negotiation", "invoiced"]);

export function DealsView() {
  const { tokens } = useSession();
  const [deals, setDeals] = useState<Deal[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [isCreating, setCreating] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [newDeal, setNewDeal] = useState({
    title: "",
    value: "",
    currency: "TRY",
    contactId: "",
    expectedCloseDate: "",
  });

  async function loadData() {
    if (!tokens?.accessToken) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const [nextDeals, nextContacts] = await Promise.all([
        listDeals(tokens.accessToken),
        listContacts(tokens.accessToken),
      ]);
      setDeals(nextDeals);
      setContacts(nextContacts);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Fırsatlar alınamadı.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [tokens?.accessToken]);

  const contactsById = useMemo(() => {
    const map = new Map<string, Contact>();
    for (const contact of contacts) {
      map.set(contact.id, contact);
    }
    return map;
  }, [contacts]);

  const columns = useMemo(() => {
    return DEAL_STAGES.map((stage) => ({
      stage,
      deals: deals.filter((deal) => deal.stage === stage),
    }));
  }, [deals]);

  const summary = useMemo(() => {
    const openDeals = deals.filter((deal) => OPEN_STAGES.has(deal.stage));
    const totalValue = openDeals.reduce((sum, deal) => sum + (deal.value ?? 0), 0);
    const currency = openDeals[0]?.currency ?? "TRY";
    return { openCount: openDeals.length, totalValue, currency };
  }, [deals]);

  async function handleStageChange(deal: Deal, stage: string) {
    if (!tokens?.accessToken || stage === deal.stage) {
      return;
    }

    setActiveId(deal.id);
    setError(null);
    try {
      const updated = await updateDeal(tokens.accessToken, deal.id, { stage });
      setDeals((current) => current.map((item) => (item.id === updated.id ? updated : item)));
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : "Aşama güncellenemedi.");
    } finally {
      setActiveId(null);
    }
  }

  async function handleCreateDeal(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !newDeal.title.trim()) {
      return;
    }

    setCreating(true);
    setError(null);
    setNotice(null);
    try {
      const created = await createDeal(tokens.accessToken, {
        title: newDeal.title.trim(),
        value: newDeal.value ? Number(newDeal.value) : null,
        currency: newDeal.currency,
        contact_id: newDeal.contactId || null,
        expected_close_date: newDeal.expectedCloseDate
          ? new Date(newDeal.expectedCloseDate).toISOString()
          : null,
      });
      setDeals((current) => [created, ...current]);
      setNewDeal({ title: "", value: "", currency: "TRY", contactId: "", expectedCloseDate: "" });
      setNotice("Fırsat oluşturuldu.");
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Fırsat oluşturulamadı.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <>
      {error ? <p className="notice">{error}</p> : null}
      {notice ? <p className="notice success">{notice}</p> : null}

      <div className="pipelineHead">
        <div>
          <h2>
            Satış Pipeline'ı
            <span className="tag">{isLoading ? "Yükleniyor" : "Aktif"}</span>
          </h2>
          <p className="moduleLead">
            Toplam açık pipeline değeri: {summary.totalValue.toLocaleString("tr-TR")} {summary.currency}{" "}
            · {summary.openCount} açık fırsat
          </p>
        </div>
        <button disabled={isLoading} onClick={loadData} type="button">
          {isLoading ? "Yükleniyor" : "Yenile"}
        </button>
      </div>

      <div className="panel" style={{ marginBottom: 20 }}>
        <div className="panelHeader">
          <h2>Yeni fırsat</h2>
          <span className="tag">Manual</span>
        </div>
        <form className="createForm" onSubmit={handleCreateDeal}>
          <label>
            Başlık
            <input
              onChange={(event) => setNewDeal((deal) => ({ ...deal, title: event.target.value }))}
              placeholder="Kurumsal genişleme paketi"
              value={newDeal.title}
            />
          </label>
          <label>
            Değer
            <input
              onChange={(event) => setNewDeal((deal) => ({ ...deal, value: event.target.value }))}
              placeholder="45000"
              type="number"
              value={newDeal.value}
            />
          </label>
          <label>
            Para birimi
            <select
              onChange={(event) => setNewDeal((deal) => ({ ...deal, currency: event.target.value }))}
              value={newDeal.currency}
            >
              <option value="TRY">TRY</option>
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
            </select>
          </label>
          <label>
            İlgili kişi
            <select
              onChange={(event) => setNewDeal((deal) => ({ ...deal, contactId: event.target.value }))}
              value={newDeal.contactId}
            >
              <option value="">Seçilmedi</option>
              {contacts.map((contact) => (
                <option key={contact.id} value={contact.id}>
                  {contact.full_name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Kapanış tahmini
            <input
              onChange={(event) =>
                setNewDeal((deal) => ({ ...deal, expectedCloseDate: event.target.value }))
              }
              type="date"
              value={newDeal.expectedCloseDate}
            />
          </label>
          <button disabled={isCreating || !newDeal.title.trim()} type="submit">
            {isCreating ? "Oluşturuluyor" : "Oluştur"}
          </button>
        </form>
      </div>

      <div className="pipelineBoard">
        {columns.map(({ stage, deals: stageDeals }) => (
          <div className="pipelineColumn" key={stage}>
            <div className="pipelineColumnHead">
              <span className="pipelineDot" style={{ background: STAGE_DOT[stage] }} />
              <h3>{STAGE_LABEL[stage]}</h3>
              <span className="pipelineCount">{stageDeals.length}</span>
            </div>
            <div className="pipelineColumnBody">
              {stageDeals.length === 0 ? <p className="emptyState">Fırsat yok.</p> : null}
              {stageDeals.map((deal) => {
                const isAiSourced = deal.source_type !== "manual";
                const contact = deal.contact_id ? contactsById.get(deal.contact_id) : null;
                return (
                  <article className={isAiSourced ? "dealCard ai" : "dealCard"} key={deal.id}>
                    <span className={isAiSourced ? "dealBadge ai" : "dealBadge"}>
                      {isAiSourced ? "AI Önerisi" : "Manuel"}
                    </span>
                    <h4>{deal.title}</h4>
                    {contact ? (
                      <p>
                        <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 14 }}>
                          person
                        </span>
                        {contact.full_name}
                        {contact.company ? ` · ${contact.company}` : ""}
                      </p>
                    ) : null}
                    <div className="dealFooter">
                      <div className="dealValue">
                        {deal.value !== null ? deal.value.toLocaleString("tr-TR") : "--"}{" "}
                        <span>{deal.currency}</span>
                      </div>
                      <select
                        className="dealStageSelect"
                        disabled={activeId === deal.id}
                        onChange={(event) => handleStageChange(deal, event.target.value)}
                        value={deal.stage}
                      >
                        {DEAL_STAGES.map((stageOption) => (
                          <option key={stageOption} value={stageOption}>
                            {STAGE_LABEL[stageOption]}
                          </option>
                        ))}
                      </select>
                    </div>
                  </article>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
