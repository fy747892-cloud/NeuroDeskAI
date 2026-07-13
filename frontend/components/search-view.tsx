"use client";

import Link from "next/link";
import { FormEvent, useMemo, useState } from "react";
import { reindexSearch, ReindexSummary, SearchResult, semanticSearch } from "@/lib/api";
import { groupResults, highlightMatch, resultHref, SOURCE_TYPE_META } from "@/lib/search-utils";
import { useSession } from "@/lib/session";

export function SearchView() {
  const { tokens } = useSession();
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(10);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [summary, setSummary] = useState<ReindexSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [isSearching, setSearching] = useState(false);
  const [isReindexing, setReindexing] = useState(false);

  const grouped = useMemo(() => {
    return results.reduce<Record<string, number>>((groups, result) => {
      groups[result.source_type] = (groups[result.source_type] ?? 0) + 1;
      return groups;
    }, {});
  }, [results]);

  const groupedResults = useMemo(() => groupResults(results), [results]);

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tokens?.accessToken || !query.trim()) {
      return;
    }

    setSearching(true);
    setError(null);
    setNotice(null);
    try {
      const nextResults = await semanticSearch(tokens.accessToken, query.trim(), limit);
      setResults(nextResults);
      setNotice(`${nextResults.length} sonuc bulundu.`);
    } catch (searchError) {
      setError(searchError instanceof Error ? searchError.message : "Arama tamamlanamadi.");
    } finally {
      setSearching(false);
    }
  }

  async function handleReindex() {
    if (!tokens?.accessToken) {
      return;
    }

    setReindexing(true);
    setError(null);
    setNotice(null);
    try {
      const nextSummary = await reindexSearch(tokens.accessToken);
      setSummary(nextSummary);
      setNotice("Arama indeksi güncellendi.");
    } catch (reindexError) {
      setError(reindexError instanceof Error ? reindexError.message : "Re-index tamamlanamadi.");
    } finally {
      setReindexing(false);
    }
  }

  return (
    <section className="moduleSurface">
      {error ? <p className="notice">{error}</p> : null}
      {notice ? <p className="notice success">{notice}</p> : null}

      <div className="moduleGrid">
        <SummaryCard label="Sonuc" value={results.length} />
        <SummaryCard label="Conversation" value={grouped.conversation ?? 0} />
        <SummaryCard label="Task" value={grouped.task ?? 0} />
        <SummaryCard label="Contact" value={grouped.contact ?? 0} />
      </div>

      <section className="panel">
        <div className="panelHeader">
          <h2>Semantic Search</h2>
          <button disabled={isReindexing} onClick={handleReindex} type="button">
            {isReindexing ? "Indexleniyor" : "Re-index"}
          </button>
        </div>

        <form className="searchForm" onSubmit={handleSearch}>
          <label>
            Sorgu
            <input
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Geciken randevu takipleri"
              value={query}
            />
          </label>
          <label>
            Limit
            <select
              onChange={(event) => setLimit(Number(event.target.value))}
              value={limit}
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
          </label>
          <button disabled={isSearching || !query.trim()} type="submit">
            {isSearching ? "Aranıyor" : "Ara"}
          </button>
        </form>

        {summary ? (
          <div className="indexSummary">
            <span>Islenen {summary.processed}</span>
            <span>Yeni {summary.created}</span>
            <span>Guncel {summary.updated}</span>
            <span>Atlanan {summary.skipped}</span>
          </div>
        ) : null}
      </section>

      <section className="panel">
        <div className="panelHeader">
          <h2>Sonuclar</h2>
          <span className="tag">Tenant scoped</span>
        </div>
        {results.length === 0 ? <p className="emptyState">Arama sonucu yok.</p> : null}
        {groupedResults.map(([sourceType, items]) => {
          const meta = SOURCE_TYPE_META[sourceType] ?? { label: formatSourceType(sourceType), icon: "search" };
          return (
            <div key={sourceType} style={{ marginBottom: 20 }}>
              <p className="extractLabel">
                {meta.label} · {items.length}
              </p>
              <div className="dataList">
                {items.map((result) => (
                  <Link
                    className="dataRow"
                    href={resultHref(result)}
                    key={`${result.source_type}-${result.source_id}`}
                    style={{ display: "grid" }}
                  >
                    <div>
                      <div className="rowTitle">
                        <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 16 }}>
                          {meta.icon}
                        </span>
                        <h3>{result.title}</h3>
                      </div>
                      <p>{highlightMatch(result.snippet, query)}</p>
                    </div>
                    <div className="rowActions">
                      <span className="scorePill">{Math.round(result.score * 100)}</span>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          );
        })}
      </section>
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

function formatSourceType(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
