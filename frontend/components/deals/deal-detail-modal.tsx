"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  Contact,
  createDealLineItem,
  CustomFieldDefinition,
  Deal,
  DealLineItem,
  deleteDealLineItem,
  listDealLineItems,
  updateDeal,
  updateDealLineItem,
} from "@/lib/api";
import { useSession } from "@/lib/session";
import { useLanguage } from "@/lib/i18n/context";
import { useToast } from "@/lib/toast";
import { CustomFieldsForm } from "@/components/shell/custom-fields-form";
import { formatMoney } from "@/lib/format";

export function DealDetailModal({
  deal,
  contacts,
  customFieldDefs,
  onClose,
  onUpdated,
}: {
  deal: Deal;
  contacts: Contact[];
  customFieldDefs: CustomFieldDefinition[];
  onClose: () => void;
  onUpdated: (deal: Deal) => void;
}) {
  const { tokens } = useSession();
  const { t, language } = useLanguage();
  const { showToast } = useToast();

  const [form, setForm] = useState({
    title: deal.title,
    description: deal.description ?? "",
    contactId: deal.contact_id ?? "",
    expectedCloseDate: deal.expected_close_date ? deal.expected_close_date.slice(0, 10) : "",
    value: deal.value ?? "",
  });
  const [customFields, setCustomFields] = useState<Record<string, unknown>>(deal.custom_fields ?? {});
  const [lineItems, setLineItems] = useState<DealLineItem[]>([]);
  const [itemsLoading, setItemsLoading] = useState(true);
  const [isSaving, setSaving] = useState(false);
  const [isAddingItem, setAddingItem] = useState(false);
  const [newItem, setNewItem] = useState({ productName: "", quantity: "1", unitPrice: "" });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!tokens?.accessToken) return;
    setItemsLoading(true);
    listDealLineItems(tokens.accessToken, deal.id)
      .then(setLineItems)
      .catch(() => setLineItems([]))
      .finally(() => setItemsLoading(false));
  }, [tokens?.accessToken, deal.id]);

  const hasLineItems = lineItems.length > 0;
  const itemsTotal = lineItems.reduce((sum, item) => sum + item.line_total, 0);

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !form.title.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await updateDeal(tokens.accessToken, deal.id, {
        title: form.title.trim(),
        description: form.description || null,
        contact_id: form.contactId || null,
        expected_close_date: form.expectedCloseDate ? new Date(form.expectedCloseDate).toISOString() : null,
        value: hasLineItems ? undefined : form.value === "" ? null : Number(form.value),
        custom_fields: customFields,
      });
      onUpdated(updated);
      showToast(t("deals.detail.saved"), "success");
      onClose();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : t("deals.detail.saveError"));
    } finally {
      setSaving(false);
    }
  }

  async function handleAddItem(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !newItem.productName.trim()) return;
    setAddingItem(true);
    setError(null);
    try {
      const created = await createDealLineItem(tokens.accessToken, deal.id, {
        product_name: newItem.productName.trim(),
        quantity: newItem.quantity ? Number(newItem.quantity) : 1,
        unit_price: newItem.unitPrice ? Number(newItem.unitPrice) : 0,
      });
      setLineItems((current) => [...current, created]);
      setNewItem({ productName: "", quantity: "1", unitPrice: "" });
      onUpdated({ ...deal, value: [...lineItems, created].reduce((sum, i) => sum + i.line_total, 0) });
    } catch (addError) {
      setError(addError instanceof Error ? addError.message : t("deals.detail.addItemError"));
    } finally {
      setAddingItem(false);
    }
  }

  async function handleUpdateItem(item: DealLineItem, patch: { quantity?: number; unit_price?: number }) {
    if (!tokens?.accessToken) return;
    setError(null);
    try {
      const updated = await updateDealLineItem(tokens.accessToken, deal.id, item.id, patch);
      const nextItems = lineItems.map((i) => (i.id === updated.id ? updated : i));
      setLineItems(nextItems);
      onUpdated({ ...deal, value: nextItems.reduce((sum, i) => sum + i.line_total, 0) });
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : t("deals.detail.updateItemError"));
    }
  }

  async function handleDeleteItem(item: DealLineItem) {
    if (!tokens?.accessToken) return;
    setError(null);
    try {
      await deleteDealLineItem(tokens.accessToken, deal.id, item.id);
      const nextItems = lineItems.filter((i) => i.id !== item.id);
      setLineItems(nextItems);
      onUpdated({ ...deal, value: nextItems.reduce((sum, i) => sum + i.line_total, 0) });
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : t("deals.detail.deleteItemError"));
    }
  }

  return (
    <div className="fixed inset-0 z-[80] bg-black/40 flex items-center justify-center p-xl" role="dialog" aria-modal="true">
      <div className="bg-surface rounded-xl shadow-2xl max-w-2xl w-full max-h-[85vh] flex flex-col">
        <header className="p-lg border-b border-outline-variant/30 flex items-start justify-between gap-md">
          <h3 className="font-headline-md text-headline-md text-on-surface">{t("deals.detail.title")}</h3>
          <button type="button" onClick={onClose} className="text-on-surface-variant hover:text-on-surface">
            <span className="material-symbols-outlined">close</span>
          </button>
        </header>

        <div className="overflow-y-auto p-lg flex flex-col gap-lg">
          {error ? <p className="text-error text-body-sm">{error}</p> : null}

          <form id="deal-detail-form" onSubmit={handleSave} className="flex flex-col gap-3">
            <h4 className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wide">
              {t("deals.detail.basicInfoTitle")}
            </h4>
            <input
              className="bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
              onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              placeholder={t("deals.detail.titleLabel")}
              value={form.title}
            />
            <textarea
              className="bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              placeholder={t("deals.detail.descriptionLabel")}
              rows={2}
              value={form.description}
            />
            <div className="grid grid-cols-2 gap-3">
              <select
                className="bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                onChange={(e) => setForm((f) => ({ ...f, contactId: e.target.value }))}
                value={form.contactId}
              >
                <option value="">{t("deals.selectContact")}</option>
                {contacts.map((contact) => (
                  <option key={contact.id} value={contact.id}>
                    {contact.full_name}
                  </option>
                ))}
              </select>
              <input
                className="bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                onChange={(e) => setForm((f) => ({ ...f, expectedCloseDate: e.target.value }))}
                type="date"
                value={form.expectedCloseDate}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-[11px] text-on-surface-variant font-bold uppercase tracking-wide">
                {t("deals.detail.valueLabel")}
              </label>
              {hasLineItems ? (
                <p className="bg-surface-container-lowest rounded-lg px-3 py-2 text-body-sm text-on-surface-variant">
                  {t("deals.detail.valueComputedNote", { value: formatMoney(itemsTotal, deal.currency, language) })}
                </p>
              ) : (
                <input
                  className="bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                  onChange={(e) => setForm((f) => ({ ...f, value: e.target.value }))}
                  placeholder={t("deals.valuePlaceholder")}
                  type="number"
                  value={form.value}
                />
              )}
            </div>

            {customFieldDefs.length > 0 ? (
              <>
                <h4 className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wide mt-2">
                  {t("deals.detail.customFieldsTitle")}
                </h4>
                <CustomFieldsForm
                  definitions={customFieldDefs}
                  values={customFields}
                  onChange={(key, value) => setCustomFields((current) => ({ ...current, [key]: value }))}
                />
              </>
            ) : null}
          </form>

          <div className="flex flex-col gap-3">
            <h4 className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wide">
              {t("deals.detail.lineItemsTitle")}
            </h4>
            {itemsLoading ? (
              <p className="text-body-sm text-on-surface-variant">{t("common.loading")}</p>
            ) : lineItems.length === 0 ? (
              <p className="text-body-sm text-on-surface-variant">{t("deals.detail.lineItemsEmpty")}</p>
            ) : (
              <div className="flex flex-col gap-2">
                {lineItems.map((item) => (
                  <div
                    key={item.id}
                    className="grid grid-cols-[1fr_70px_100px_100px_32px] gap-2 items-center bg-surface-container-lowest rounded-lg px-3 py-2"
                  >
                    <span className="text-body-sm text-on-surface truncate">{item.product_name}</span>
                    <input
                      className="bg-surface border border-outline-variant/30 rounded px-2 py-1 text-body-sm w-full"
                      type="number"
                      defaultValue={item.quantity}
                      onBlur={(e) => {
                        const next = Number(e.target.value);
                        if (next !== item.quantity && next > 0) handleUpdateItem(item, { quantity: next });
                      }}
                    />
                    <input
                      className="bg-surface border border-outline-variant/30 rounded px-2 py-1 text-body-sm w-full"
                      type="number"
                      defaultValue={item.unit_price}
                      onBlur={(e) => {
                        const next = Number(e.target.value);
                        if (next !== item.unit_price && next >= 0) handleUpdateItem(item, { unit_price: next });
                      }}
                    />
                    <span className="text-body-sm text-on-surface-variant text-right">
                      {formatMoney(item.line_total, deal.currency, language)}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleDeleteItem(item)}
                      aria-label={t("deals.detail.deleteItem")}
                      className="w-6 h-6 rounded flex items-center justify-center text-error hover:bg-error-container/20"
                    >
                      <span className="material-symbols-outlined text-[15px]">delete</span>
                    </button>
                  </div>
                ))}
                <div className="flex justify-end px-3 text-body-sm text-primary font-bold">
                  {t("deals.detail.totalLabel")}: {formatMoney(itemsTotal, deal.currency, language)}
                </div>
              </div>
            )}

            <form onSubmit={handleAddItem} className="grid grid-cols-[1fr_70px_100px_auto] gap-2 items-center">
              <input
                className="bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
                onChange={(e) => setNewItem((i) => ({ ...i, productName: e.target.value }))}
                placeholder={t("deals.detail.productNamePlaceholder")}
                value={newItem.productName}
              />
              <input
                className="bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-2 py-2 text-body-sm"
                onChange={(e) => setNewItem((i) => ({ ...i, quantity: e.target.value }))}
                placeholder={t("deals.detail.quantityLabel")}
                type="number"
                value={newItem.quantity}
              />
              <input
                className="bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-2 py-2 text-body-sm"
                onChange={(e) => setNewItem((i) => ({ ...i, unitPrice: e.target.value }))}
                placeholder={t("deals.detail.unitPriceLabel")}
                type="number"
                value={newItem.unitPrice}
              />
              <button
                type="submit"
                disabled={isAddingItem || !newItem.productName.trim()}
                className="px-3 py-2 bg-surface-container-high text-on-surface rounded-lg text-label-sm font-bold disabled:opacity-60 whitespace-nowrap"
              >
                {isAddingItem ? t("deals.detail.adding") : t("deals.detail.addItem")}
              </button>
            </form>
          </div>
        </div>

        <footer className="p-lg border-t border-outline-variant/30 flex gap-2 justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-surface text-on-surface-variant rounded-lg text-label-sm font-bold"
          >
            {t("deals.detail.close")}
          </button>
          <button
            type="submit"
            form="deal-detail-form"
            disabled={isSaving || !form.title.trim()}
            className="px-4 py-2 bg-primary text-on-primary rounded-lg text-label-sm font-bold disabled:opacity-60"
          >
            {isSaving ? t("deals.detail.saving") : t("deals.detail.save")}
          </button>
        </footer>
      </div>
    </div>
  );
}
