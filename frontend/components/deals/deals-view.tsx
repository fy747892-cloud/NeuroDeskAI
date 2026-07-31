"use client";

import {
  FormEvent,
  PointerEvent as ReactPointerEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Contact, createDeal, Deal, DEAL_STAGES, deleteDeal, listContacts, listDeals, updateDeal } from "@/lib/api";
import { useSession } from "@/lib/session";
import { useLanguage } from "@/lib/i18n/context";
import { useToast } from "@/lib/toast";
import { Skeleton } from "@/components/shell/skeleton";
import { EmptyState } from "@/components/shell/empty-state";
import { formatMoney } from "@/lib/format";
import { deferredExecute, UNDO_WINDOW_MS } from "@/lib/undo";

const STAGE_LABEL_KEY: Record<string, string> = {
  lead: "deals.stage.lead",
  proposal_sent: "deals.stage.proposalSent",
  negotiation: "deals.stage.negotiation",
  invoiced: "deals.stage.invoiced",
  won: "deals.stage.won",
  lost: "deals.stage.lost",
};

const STAGE_DOT: Record<string, string> = {
  lead: "bg-outline-variant",
  proposal_sent: "bg-primary",
  negotiation: "bg-secondary",
  invoiced: "bg-surface-container-highest",
  won: "bg-primary",
  lost: "bg-error",
};

const OPEN_STAGES = new Set(["lead", "proposal_sent", "negotiation", "invoiced"]);

export function DealsView() {
  const { tokens } = useSession();
  const { t, language } = useLanguage();
  const { showToast } = useToast();
  const [deals, setDeals] = useState<Deal[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [isCreating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [draggedDealId, setDraggedDealId] = useState<string | null>(null);
  const [dragOverStage, setDragOverStage] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<"recent" | "value_desc" | "value_asc" | "close_date">("recent");
  const cardRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  const columnRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  const dragGesture = useRef<{
    dealId: string;
    originStage: string;
    pointerId: number;
    startX: number;
    startY: number;
    dragging: boolean;
  } | null>(null);
  const [newDeal, setNewDeal] = useState({
    title: "",
    value: "",
    currency: "TRY",
    contactId: "",
    expectedCloseDate: "",
  });

  const loadData = useCallback(async () => {
    if (!tokens?.accessToken) return;
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
      setError(loadError instanceof Error ? loadError.message : t("deals.loadError"));
    } finally {
      setLoading(false);
    }
  }, [tokens?.accessToken]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const contactsById = useMemo(() => {
    const map = new Map<string, Contact>();
    for (const contact of contacts) map.set(contact.id, contact);
    return map;
  }, [contacts]);

  const filteredDeals = useMemo(() => {
    const query = search.trim().toLowerCase();
    let result = deals;
    if (query) {
      result = result.filter((deal) => {
        const contact = deal.contact_id ? contactsById.get(deal.contact_id) : null;
        return (
          deal.title.toLowerCase().includes(query) ||
          contact?.full_name.toLowerCase().includes(query) ||
          contact?.company?.toLowerCase().includes(query)
        );
      });
    }

    const sorted = [...result];
    switch (sortBy) {
      case "value_desc":
        sorted.sort((a, b) => (b.value ?? 0) - (a.value ?? 0));
        break;
      case "value_asc":
        sorted.sort((a, b) => (a.value ?? 0) - (b.value ?? 0));
        break;
      case "close_date":
        sorted.sort((a, b) => {
          if (!a.expected_close_date) return 1;
          if (!b.expected_close_date) return -1;
          return new Date(a.expected_close_date).getTime() - new Date(b.expected_close_date).getTime();
        });
        break;
      default:
        sorted.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    }
    return sorted;
  }, [deals, search, sortBy, contactsById]);

  const columns = useMemo(
    () => DEAL_STAGES.map((stage) => ({ stage, deals: filteredDeals.filter((deal) => deal.stage === stage) })),
    [filteredDeals],
  );

  const summary = useMemo(() => {
    const openDeals = deals.filter((deal) => OPEN_STAGES.has(deal.stage));
    const totalValue = openDeals.reduce((sum, deal) => sum + (deal.value ?? 0), 0);
    const currency = openDeals[0]?.currency ?? "TRY";
    return { openCount: openDeals.length, totalValue, currency, totalCount: deals.length };
  }, [deals]);

  async function handleStageChange(deal: Deal, stage: string) {
    if (!tokens?.accessToken || stage === deal.stage) return;
    setActiveId(deal.id);
    setError(null);
    try {
      const updated = await updateDeal(tokens.accessToken, deal.id, { stage });
      setDeals((current) => current.map((item) => (item.id === updated.id ? updated : item)));
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : t("deals.stageUpdateError"));
    } finally {
      setActiveId(null);
    }
  }

  function handleDeleteDeal(deal: Deal) {
    if (!tokens?.accessToken) return;
    const accessToken = tokens.accessToken;
    const previousDeals = deals;

    setDeals((current) => current.filter((item) => item.id !== deal.id));

    const pending = deferredExecute(async () => {
      try {
        await deleteDeal(accessToken, deal.id);
      } catch (deleteError) {
        setDeals((current) => [deal, ...current]);
        setError(deleteError instanceof Error ? deleteError.message : t("deals.dealDeleteError"));
      }
    });

    showToast(t("deals.dealDeleted"), "success", {
      duration: UNDO_WINDOW_MS,
      action: {
        label: t("common.undo"),
        onClick: () => {
          pending.cancel();
          setDeals(previousDeals);
        },
      },
    });
  }

  function toggleSelected(dealId: string) {
    setSelectedIds((current) => {
      const next = new Set(current);
      if (next.has(dealId)) next.delete(dealId);
      else next.add(dealId);
      return next;
    });
  }

  function toggleSelectAll() {
    setSelectedIds((current) =>
      current.size === filteredDeals.length ? new Set() : new Set(filteredDeals.map((deal) => deal.id)),
    );
  }

  function handleBulkDelete() {
    if (!tokens?.accessToken || selectedIds.size === 0) return;
    const accessToken = tokens.accessToken;
    const idsToDelete = Array.from(selectedIds);
    const previousDeals = deals;

    setDeals((current) => current.filter((deal) => !selectedIds.has(deal.id)));
    setSelectedIds(new Set());

    const pending = deferredExecute(async () => {
      const results = await Promise.allSettled(idsToDelete.map((id) => deleteDeal(accessToken, id)));
      const failedIds = new Set(idsToDelete.filter((_, index) => results[index].status === "rejected"));
      if (failedIds.size > 0) {
        setDeals((current) => [...current, ...previousDeals.filter((deal) => failedIds.has(deal.id))]);
        showToast(t("deals.bulk.deletePartialError", { count: failedIds.size }), "error");
      }
    });

    showToast(t("deals.bulk.deleted", { count: idsToDelete.length }), "success", {
      duration: UNDO_WINDOW_MS,
      action: {
        label: t("common.undo"),
        onClick: () => {
          pending.cancel();
          setDeals(previousDeals);
        },
      },
    });
  }

  function registerCardRef(dealId: string, node: HTMLDivElement | null) {
    if (node) cardRefs.current.set(dealId, node);
    else cardRefs.current.delete(dealId);
  }

  function registerColumnRef(stage: string, node: HTMLDivElement | null) {
    if (node) columnRefs.current.set(stage, node);
    else columnRefs.current.delete(stage);
  }

  function stageAtPoint(clientX: number, clientY: number): string | null {
    for (const [stage, node] of columnRefs.current) {
      const rect = node.getBoundingClientRect();
      if (clientX >= rect.left && clientX <= rect.right && clientY >= rect.top && clientY <= rect.bottom) {
        return stage;
      }
    }
    return null;
  }

  // Pointer Events (not the HTML5 Drag-and-Drop API) so dragging works the
  // same way for mouse, touch, and pen — native HTML5 drag has no touch
  // support at all, which made the board effectively desktop-only.
  function handleHandlePointerDown(event: ReactPointerEvent<HTMLSpanElement>, deal: Deal) {
    if (event.pointerType === "mouse" && event.button !== 0) return;
    dragGesture.current = {
      dealId: deal.id,
      originStage: deal.stage,
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      dragging: false,
    };
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function handleHandlePointerMove(event: ReactPointerEvent<HTMLSpanElement>) {
    const gesture = dragGesture.current;
    if (!gesture || gesture.pointerId !== event.pointerId) return;

    const dx = event.clientX - gesture.startX;
    const dy = event.clientY - gesture.startY;

    if (!gesture.dragging) {
      if (Math.abs(dx) < 6 && Math.abs(dy) < 6) return;
      gesture.dragging = true;
      setDraggedDealId(gesture.dealId);
    }

    const card = cardRefs.current.get(gesture.dealId);
    if (card) {
      card.style.transform = `translate(${dx}px, ${dy}px) scale(1.02)`;
    }

    const stage = stageAtPoint(event.clientX, event.clientY);
    setDragOverStage((current) => (current === stage ? current : stage));
  }

  async function handleHandlePointerUp(event: ReactPointerEvent<HTMLSpanElement>) {
    const gesture = dragGesture.current;
    if (!gesture || gesture.pointerId !== event.pointerId) return;
    dragGesture.current = null;

    const card = cardRefs.current.get(gesture.dealId);
    if (card) card.style.transform = "";

    if (!gesture.dragging) {
      setDraggedDealId(null);
      setDragOverStage(null);
      return;
    }

    const targetStage = stageAtPoint(event.clientX, event.clientY);
    setDraggedDealId(null);
    setDragOverStage(null);

    if (targetStage && targetStage !== gesture.originStage) {
      const deal = deals.find((item) => item.id === gesture.dealId);
      if (deal) await handleStageChange(deal, targetStage);
    }
  }

  function handleHandlePointerCancel(event: ReactPointerEvent<HTMLSpanElement>) {
    const gesture = dragGesture.current;
    if (!gesture || gesture.pointerId !== event.pointerId) return;
    dragGesture.current = null;
    const card = cardRefs.current.get(gesture.dealId);
    if (card) card.style.transform = "";
    setDraggedDealId(null);
    setDragOverStage(null);
  }

  async function handleCreateDeal(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !newDeal.title.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const created = await createDeal(tokens.accessToken, {
        title: newDeal.title.trim(),
        value: newDeal.value ? Number(newDeal.value) : null,
        currency: newDeal.currency,
        contact_id: newDeal.contactId || null,
        expected_close_date: newDeal.expectedCloseDate ? new Date(newDeal.expectedCloseDate).toISOString() : null,
      });
      setDeals((current) => [created, ...current]);
      setNewDeal({ title: "", value: "", currency: "TRY", contactId: "", expectedCloseDate: "" });
      showToast(t("deals.dealCreated"), "success");
      setShowForm(false);
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : t("deals.dealCreateError"));
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="p-xl">
      <div className="flex items-center justify-between mb-lg flex-wrap gap-md">
        <div>
          <h2 className="font-headline-lg text-headline-lg text-on-surface flex items-center gap-3 flex-wrap">
            {t("deals.pageTitle")}
            <span className="font-label-sm text-label-sm bg-primary/10 text-primary px-3 py-1 rounded-full">
              {isLoading ? t("common.loading") : t("deals.activeBadge")}
            </span>
          </h2>
          <p className="text-on-surface-variant font-body-md">
            {t("deals.totalPipelineValue")}: {formatMoney(summary.totalValue, summary.currency, language)} ·{" "}
            {t("deals.openDealsCount", { count: summary.openCount })}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-[18px]">
              search
            </span>
            <input
              className="bg-surface-container-low border-none rounded-full pl-10 pr-4 py-2 text-body-sm w-52"
              onChange={(e) => setSearch(e.target.value)}
              placeholder={t("deals.searchPlaceholder")}
              value={search}
            />
          </div>
          <select
            className="bg-surface-container-low border-none rounded-lg px-3 py-2 text-body-sm text-on-surface-variant"
            onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
            value={sortBy}
            aria-label={t("deals.sortAria")}
          >
            <option value="recent">{t("deals.sort.recent")}</option>
            <option value="value_desc">{t("deals.sort.valueDesc")}</option>
            <option value="value_asc">{t("deals.sort.valueAsc")}</option>
            <option value="close_date">{t("deals.sort.closeDate")}</option>
          </select>
          <button
            type="button"
            onClick={() => setShowForm((v) => !v)}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-on-primary rounded-lg font-label-md text-label-md shadow-sm active:scale-95 transition-transform"
          >
            <span className="material-symbols-outlined">add</span>
            {t("deals.newDeal")}
          </button>
        </div>
      </div>

      {error ? <p className="text-error text-body-sm mb-md">{error}</p> : null}

      {!isLoading && search.trim() && filteredDeals.length === 0 ? (
        <EmptyState icon="search_off" title={t("deals.noSearchResults")} />
      ) : null}

      {!isLoading && filteredDeals.length > 0 ? (
        <div className="flex items-center gap-md mb-md">
          <label className="flex items-center gap-2 text-body-sm text-on-surface-variant cursor-pointer select-none">
            <input
              type="checkbox"
              checked={selectedIds.size === filteredDeals.length}
              onChange={toggleSelectAll}
              aria-label={t("deals.bulk.selectAll")}
            />
            {t("deals.bulk.selectAll")}
          </label>
          {selectedIds.size > 0 ? (
            <div className="flex items-center gap-3 bg-primary-container/10 border border-primary/20 rounded-lg px-3 py-1.5">
              <span className="text-body-sm text-primary font-bold">
                {t("deals.bulk.selectedCount", { count: selectedIds.size })}
              </span>
              <button
                type="button"
                onClick={handleBulkDelete}
                className="text-error text-[12px] font-bold hover:underline"
              >
                {t("deals.bulk.deleteSelected")}
              </button>
              <button
                type="button"
                onClick={() => setSelectedIds(new Set())}
                className="text-on-surface-variant text-[12px] font-bold hover:underline"
              >
                {t("common.clear")}
              </button>
            </div>
          ) : null}
        </div>
      ) : null}

      {showForm ? (
        <form onSubmit={handleCreateDeal} className="glass-card p-lg rounded-xl mb-lg grid grid-cols-2 md:grid-cols-5 gap-3">
          <input
            className="bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm col-span-2"
            onChange={(e) => setNewDeal((d) => ({ ...d, title: e.target.value }))}
            placeholder={t("deals.titlePlaceholder")}
            value={newDeal.title}
          />
          <input
            className="bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
            onChange={(e) => setNewDeal((d) => ({ ...d, value: e.target.value }))}
            placeholder={t("deals.valuePlaceholder")}
            type="number"
            value={newDeal.value}
          />
          <select
            className="bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
            onChange={(e) => setNewDeal((d) => ({ ...d, currency: e.target.value }))}
            value={newDeal.currency}
          >
            <option value="TRY">TRY</option>
            <option value="USD">USD</option>
            <option value="EUR">EUR</option>
          </select>
          <select
            className="bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
            onChange={(e) => setNewDeal((d) => ({ ...d, contactId: e.target.value }))}
            value={newDeal.contactId}
          >
            <option value="">{t("deals.selectContact")}</option>
            {contacts.map((contact) => (
              <option key={contact.id} value={contact.id}>
                {contact.full_name}
              </option>
            ))}
          </select>
          <div className="col-span-2 md:col-span-5 flex gap-2">
            <button
              type="submit"
              disabled={isCreating || !newDeal.title.trim()}
              className="flex-1 py-2 bg-primary text-on-primary rounded-lg text-label-sm font-bold disabled:opacity-60"
            >
              {isCreating ? t("deals.creating") : t("deals.create")}
            </button>
            <button
              type="button"
              onClick={() => setNewDeal({ title: "", value: "", currency: "TRY", contactId: "", expectedCloseDate: "" })}
              className="px-3 py-2 bg-surface text-on-surface-variant rounded-lg text-label-sm font-bold"
            >
              {t("common.clear")}
            </button>
          </div>
        </form>
      ) : null}

      {!isLoading && deals.length === 0 ? (
        <section className="rounded-2xl p-lg glass-card border border-primary/10 mb-lg">
          <div className="flex items-center gap-2 mb-sm">
            <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>
              handshake
            </span>
            <span className="font-label-sm text-label-sm text-primary uppercase tracking-widest">
              {t("deals.onboarding.eyebrow")}
            </span>
          </div>
          <h3 className="font-headline-md text-headline-md text-on-surface mb-1">{t("deals.onboarding.title")}</h3>
          <p className="text-body-sm text-on-surface-variant max-w-2xl mb-md">{t("deals.onboarding.subtitle")}</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-md">
            <div className="flex items-start gap-3 p-md rounded-xl border border-outline-variant/30 bg-surface-container-lowest">
              <span className="material-symbols-outlined text-primary shrink-0">add_circle</span>
              <span>
                <span className="block font-label-md text-on-surface">{t("deals.onboarding.step1Title")}</span>
                <span className="block text-body-sm text-on-surface-variant mt-0.5">
                  {t("deals.onboarding.step1Body")}
                </span>
              </span>
            </div>
            <div className="flex items-start gap-3 p-md rounded-xl border border-outline-variant/30 bg-surface-container-lowest">
              <span className="material-symbols-outlined text-primary shrink-0">drag_indicator</span>
              <span>
                <span className="block font-label-md text-on-surface">{t("deals.onboarding.step2Title")}</span>
                <span className="block text-body-sm text-on-surface-variant mt-0.5">
                  {t("deals.onboarding.step2Body")}
                </span>
              </span>
            </div>
          </div>
        </section>
      ) : null}

      <div className="flex-1 overflow-x-auto pb-4">
        <div className="flex gap-gutter">
          {isLoading
            ? DEAL_STAGES.map((stage) => (
                <div key={stage} className="kanban-column flex flex-col bg-surface-container-low/50 rounded-xl p-sm shrink-0 gap-sm">
                  <Skeleton className="h-4 w-24 mx-2 mt-2" />
                  <Skeleton className="h-24 w-full rounded-lg" />
                  <Skeleton className="h-24 w-full rounded-lg" />
                </div>
              ))
            : columns.map(({ stage, deals: stageDeals }) => (
            <div
              key={stage}
              ref={(node) => registerColumnRef(stage, node)}
              className={
                "kanban-column flex flex-col bg-surface-container-low/50 rounded-xl p-sm shrink-0 transition-colors " +
                (dragOverStage === stage ? "ring-2 ring-primary bg-primary-container/5" : "")
              }
            >
              <div className="flex items-center justify-between px-3 py-2 mb-sm">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${STAGE_DOT[stage]}`} />
                  <h3 className="font-label-sm text-label-sm text-on-surface uppercase tracking-wider">
                    {t(STAGE_LABEL_KEY[stage])}
                  </h3>
                  <span className="text-on-surface-variant text-[11px] font-bold px-1.5 py-0.5 bg-surface-container-high rounded">
                    {stageDeals.length}
                  </span>
                </div>
              </div>
              <div className="flex-1 flex flex-col gap-sm overflow-y-auto pb-4 px-1 min-h-[120px]">
                {stageDeals.length === 0 ? (
                  <EmptyState icon="inbox" title={t("deals.noDealsInStage")} />
                ) : null}
                {stageDeals.map((deal) => {
                  const isAiSourced = deal.source_type !== "manual";
                  const contact = deal.contact_id ? contactsById.get(deal.contact_id) : null;
                  return (
                    <div
                      key={deal.id}
                      ref={(node) => registerCardRef(deal.id, node)}
                      className={
                        "bg-surface-container-lowest rounded-lg border border-outline-variant/30 p-md shadow-sm hover:shadow-md transition-shadow group/card " +
                        (isAiSourced ? "ai-glow " : "") +
                        (draggedDealId === deal.id ? "shadow-xl relative z-20 transition-none" : "")
                      }
                    >
                      <div className="flex justify-between items-start mb-base">
                        <div className="flex items-center gap-2 min-w-0">
                          <input
                            type="checkbox"
                            checked={selectedIds.has(deal.id)}
                            onChange={() => toggleSelected(deal.id)}
                            aria-label={t("deals.bulk.selectOne", { title: deal.title })}
                            className="shrink-0 w-3.5 h-3.5"
                          />
                          {isAiSourced ? (
                            <span className="bg-secondary/10 text-secondary text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
                              <span className="material-symbols-outlined !text-[12px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                                auto_awesome
                              </span>
                              {t("deals.aiSuggestedBadge")}
                            </span>
                          ) : (
                            <span className="text-on-surface-variant text-[10px] font-bold uppercase tracking-widest">
                              {t("deals.manualBadge")}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-1">
                          <button
                            type="button"
                            disabled={activeId === deal.id}
                            onClick={() => handleDeleteDeal(deal)}
                            aria-label={t("common.delete")}
                            className="opacity-0 group-hover/card:opacity-100 w-6 h-6 rounded flex items-center justify-center text-error hover:bg-error-container/20 disabled:opacity-60 transition-opacity"
                          >
                            <span className="material-symbols-outlined text-[15px]">delete</span>
                          </button>
                          <span
                            className="material-symbols-outlined text-outline-variant text-[16px] cursor-grab active:cursor-grabbing touch-none select-none p-1.5 -m-1.5"
                            onPointerDown={(event) => handleHandlePointerDown(event, deal)}
                            onPointerMove={handleHandlePointerMove}
                            onPointerUp={handleHandlePointerUp}
                            onPointerCancel={handleHandlePointerCancel}
                            aria-hidden="true"
                          >
                            drag_indicator
                          </span>
                        </div>
                      </div>
                      <h4 className="font-headline-md text-body-lg text-on-surface leading-tight mb-1 truncate">
                        {deal.title}
                      </h4>
                      {contact ? (
                        <p className="text-on-surface-variant text-[13px] mb-3 flex items-center gap-1 truncate">
                          <span className="material-symbols-outlined !text-[14px]">person</span>
                          {contact.full_name}
                          {contact.company ? ` · ${contact.company}` : ""}
                        </p>
                      ) : null}
                      <div className="flex justify-between items-end border-t border-outline-variant/10 pt-3 gap-2">
                        <div className="font-headline-md text-primary text-[15px]">
                          {formatMoney(deal.value, deal.currency, language)}
                        </div>
                        <select
                          className="bg-surface-container-high rounded px-2 py-1 text-[11px] border-none"
                          disabled={activeId === deal.id}
                          onChange={(e) => handleStageChange(deal, e.target.value)}
                          value={deal.stage}
                          aria-label={t("deals.stageSelectAria", { title: deal.title })}
                        >
                          {DEAL_STAGES.map((stageOption) => (
                            <option key={stageOption} value={stageOption}>
                              {t(STAGE_LABEL_KEY[stageOption])}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
