"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { Contact, createContact, listContacts } from "@/lib/api";
import { useSession } from "@/lib/session";

export function ContactsView() {
  const { tokens } = useSession();
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [isCreating, setCreating] = useState(false);
  const [newContact, setNewContact] = useState({
    company: "",
    email: "",
    fullName: "",
    phone: "",
    title: "",
  });

  async function loadContacts(nextSearch = search) {
    if (!tokens?.accessToken) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      setContacts(await listContacts(tokens.accessToken, { search: nextSearch.trim() || undefined }));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Kisiler alinamadi.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadContacts("");
  }, [tokens?.accessToken]);

  const summary = useMemo(() => {
    return {
      total: contacts.length,
      active: contacts.filter((contact) => contact.status === "active").length,
      companies: new Set(contacts.map((contact) => contact.company).filter(Boolean)).size,
      tagged: contacts.filter((contact) => contact.tags.length > 0).length,
    };
  }, [contacts]);

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    loadContacts(search);
  }

  async function handleCreateContact(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !newContact.fullName.trim()) {
      return;
    }

    setCreating(true);
    setError(null);
    setNotice(null);
    try {
      const createdContact = await createContact(tokens.accessToken, {
        full_name: newContact.fullName.trim(),
        email: newContact.email.trim() || null,
        phone: newContact.phone.trim() || null,
        company: newContact.company.trim() || null,
        title: newContact.title.trim() || null,
      });
      setContacts((currentContacts) => [createdContact, ...currentContacts]);
      setNewContact({ company: "", email: "", fullName: "", phone: "", title: "" });
      setNotice("Kisi olusturuldu.");
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Kisi olusturulamadi.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <section className="moduleSurface">
      {error ? <p className="notice">{error}</p> : null}
      {notice ? <p className="notice success">{notice}</p> : null}

      <div className="moduleGrid">
        <SummaryCard label="Toplam" value={summary.total} />
        <SummaryCard label="Aktif" value={summary.active} />
        <SummaryCard label="Sirket" value={summary.companies} />
        <SummaryCard label="Etiketli" value={summary.tagged} />
      </div>

      <div className="panel">
        <div className="panelHeader">
          <h2>Yeni kisi</h2>
          <span className="tag">CRM</span>
        </div>
        <form className="createForm" onSubmit={handleCreateContact}>
          <label>
            Ad soyad
            <input
              onChange={(event) =>
                setNewContact((contact) => ({ ...contact, fullName: event.target.value }))
              }
              placeholder="Ayse Demir"
              value={newContact.fullName}
            />
          </label>
          <label>
            Email
            <input
              onChange={(event) =>
                setNewContact((contact) => ({ ...contact, email: event.target.value }))
              }
              placeholder="ayse@example.com"
              type="email"
              value={newContact.email}
            />
          </label>
          <label>
            Telefon
            <input
              onChange={(event) =>
                setNewContact((contact) => ({ ...contact, phone: event.target.value }))
              }
              placeholder="+90..."
              value={newContact.phone}
            />
          </label>
          <label>
            Sirket
            <input
              onChange={(event) =>
                setNewContact((contact) => ({ ...contact, company: event.target.value }))
              }
              placeholder="Kurum"
              value={newContact.company}
            />
          </label>
          <label>
            Unvan
            <input
              onChange={(event) =>
                setNewContact((contact) => ({ ...contact, title: event.target.value }))
              }
              placeholder="Doktor"
              value={newContact.title}
            />
          </label>
          <button disabled={isCreating || !newContact.fullName.trim()} type="submit">
            {isCreating ? "Olusturuluyor" : "Olustur"}
          </button>
        </form>
      </div>

      <div className="panel">
        <div className="panelHeader">
          <h2>Kisi listesi</h2>
          <form className="inlineSearch" onSubmit={handleSearch}>
            <input
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Ara"
              value={search}
            />
            <button disabled={isLoading} type="submit">
              {isLoading ? "Araniyor" : "Ara"}
            </button>
          </form>
        </div>

        <div className="dataList">
          {isLoading ? <p className="emptyState">Kisiler yukleniyor.</p> : null}
          {!isLoading && contacts.length === 0 ? (
            <p className="emptyState">Kisi kaydi bulunmuyor.</p>
          ) : null}
          {contacts.map((contact) => (
            <article className="dataRow" key={contact.id}>
              <div>
                <div className="rowTitle">
                  <h3>{contact.full_name}</h3>
                  <span>{contact.status}</span>
                </div>
                <p>{[contact.title, contact.company].filter(Boolean).join(" - ") || "Profil detayi yok."}</p>
                <small>{contact.email ?? contact.phone ?? "Iletisim bilgisi yok"}</small>
              </div>
              <div className="rowActions">
                <span className="statusPill">{contact.tags[0] ?? "CRM"}</span>
              </div>
            </article>
          ))}
        </div>
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
