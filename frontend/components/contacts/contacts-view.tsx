"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { Contact, createContact, listContacts } from "@/lib/api";
import { useSession } from "@/lib/session";
import { getInitials } from "@/lib/format";

export function ContactsView() {
  const { tokens } = useSession();
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [isCreating, setCreating] = useState(false);
  const [newContact, setNewContact] = useState({
    fullName: "",
    email: "",
    phone: "",
    company: "",
    title: "",
  });

  const loadContacts = useCallback(
    async (nextSearch = "") => {
      if (!tokens?.accessToken) return;
      setLoading(true);
      setError(null);
      try {
        setContacts(await listContacts(tokens.accessToken, { search: nextSearch.trim() || undefined }));
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Kişiler alınamadı.");
      } finally {
        setLoading(false);
      }
    },
    [tokens?.accessToken],
  );

  useEffect(() => {
    loadContacts();
  }, [loadContacts]);

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    loadContacts(search);
  }

  async function handleCreateContact(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !newContact.fullName.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const created = await createContact(tokens.accessToken, {
        full_name: newContact.fullName.trim(),
        email: newContact.email.trim() || null,
        phone: newContact.phone.trim() || null,
        company: newContact.company.trim() || null,
        title: newContact.title.trim() || null,
      });
      setContacts((current) => [created, ...current]);
      setNewContact({ fullName: "", email: "", phone: "", company: "", title: "" });
      setNotice("Kişi oluşturuldu.");
      setShowForm(false);
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Kişi oluşturulamadı.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="p-xl">
      <div className="flex items-center justify-between mb-xl flex-wrap gap-md">
        <div>
          <h2 className="font-headline-lg text-headline-lg text-on-surface">Contacts</h2>
          <p className="text-body-md text-on-surface-variant mt-1">
            Kişi hafızasını, şirket bilgilerini ve CRM kayıtlarını yönet.
          </p>
        </div>
        <div className="flex gap-2">
          <form onSubmit={handleSearch} className="relative">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-[18px]">
              search
            </span>
            <input
              className="bg-surface-container-low border-none rounded-full pl-10 pr-4 py-2 text-body-sm w-64"
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Kişi ara..."
              value={search}
            />
          </form>
          <button
            type="button"
            onClick={() => setShowForm((v) => !v)}
            className="flex items-center gap-2 bg-primary text-on-primary px-4 py-2 rounded-lg font-label-md text-label-sm"
          >
            <span className="material-symbols-outlined text-[18px]">person_add</span>
            Yeni Kişi
          </button>
        </div>
      </div>

      {error ? <p className="text-error text-body-sm mb-md">{error}</p> : null}
      {notice ? <p className="text-primary text-body-sm mb-md">{notice}</p> : null}

      {showForm ? (
        <form onSubmit={handleCreateContact} className="glass-card p-lg rounded-xl mb-lg grid grid-cols-2 gap-3">
          <input
            className="bg-white border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
            onChange={(e) => setNewContact((c) => ({ ...c, fullName: e.target.value }))}
            placeholder="Ad soyad"
            value={newContact.fullName}
          />
          <input
            className="bg-white border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
            onChange={(e) => setNewContact((c) => ({ ...c, email: e.target.value }))}
            placeholder="E-posta"
            type="email"
            value={newContact.email}
          />
          <input
            className="bg-white border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
            onChange={(e) => setNewContact((c) => ({ ...c, phone: e.target.value }))}
            placeholder="Telefon"
            value={newContact.phone}
          />
          <input
            className="bg-white border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm"
            onChange={(e) => setNewContact((c) => ({ ...c, company: e.target.value }))}
            placeholder="Şirket"
            value={newContact.company}
          />
          <input
            className="bg-white border border-outline-variant/30 rounded-lg px-3 py-2 text-body-sm col-span-2"
            onChange={(e) => setNewContact((c) => ({ ...c, title: e.target.value }))}
            placeholder="Ünvan"
            value={newContact.title}
          />
          <button
            type="submit"
            disabled={isCreating || !newContact.fullName.trim()}
            className="col-span-2 py-2 bg-primary text-on-primary rounded-lg text-label-sm font-bold disabled:opacity-60"
          >
            {isCreating ? "Oluşturuluyor..." : "Oluştur"}
          </button>
        </form>
      ) : null}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-md">
        {isLoading ? <p className="text-body-sm text-on-surface-variant">Yükleniyor...</p> : null}
        {!isLoading && contacts.length === 0 ? (
          <p className="text-body-sm text-on-surface-variant">Kişi kaydı bulunmuyor.</p>
        ) : null}
        {contacts.map((contact) => (
          <Link
            key={contact.id}
            href={`/kisiler/${contact.id}`}
            className="glass-card p-lg rounded-xl bento-card flex items-start gap-md"
          >
            <div className="w-11 h-11 rounded-full bg-primary-container/20 flex items-center justify-center text-primary font-bold text-sm shrink-0">
              {getInitials(contact.full_name)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-label-md text-label-md text-on-surface truncate">{contact.full_name}</p>
              <p className="text-body-sm text-on-surface-variant truncate">
                {[contact.title, contact.company].filter(Boolean).join(", ") || "Profil detayı yok"}
              </p>
              <p className="text-[11px] text-outline truncate mt-1">
                {contact.email ?? contact.phone ?? "İletişim bilgisi yok"}
              </p>
            </div>
            <span className="text-[10px] px-2 py-0.5 bg-surface-container-high rounded-full text-on-surface-variant shrink-0">
              {contact.tags[0] ?? contact.status}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}
