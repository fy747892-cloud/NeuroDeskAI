"use client";

import { useRouter } from "next/navigation";
import { KeyboardEvent, useEffect, useRef, useState } from "react";
import { SearchResult, semanticSearch } from "@/lib/api";
import { groupResults, highlightMatch, resultHref, SOURCE_TYPE_META } from "@/lib/search-utils";
import { useSession } from "@/lib/session";
import { useLanguage } from "@/lib/i18n/context";
import { EmptyState } from "@/components/shell/empty-state";

const OPEN_EVENT = "neurodesk:open-search";

export function SearchPalette() {
  const { tokens } = useSession();
  const { t } = useLanguage();
  const router = useRouter();
  const [isOpen, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setSearching] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    function handleKeydown(event: globalThis.KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((value) => !value);
      } else if (event.key === "Escape") {
        setOpen(false);
      }
    }
    function handleOpenEvent() {
      setOpen(true);
    }

    window.addEventListener("keydown", handleKeydown);
    window.addEventListener(OPEN_EVENT, handleOpenEvent);
    return () => {
      window.removeEventListener("keydown", handleKeydown);
      window.removeEventListener(OPEN_EVENT, handleOpenEvent);
    };
  }, []);

  useEffect(() => {
    if (isOpen) {
      requestAnimationFrame(() => inputRef.current?.focus());
    } else {
      setQuery("");
      setResults([]);
      setActiveIndex(0);
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen || !tokens?.accessToken || !query.trim()) {
      setResults([]);
      return;
    }

    const handle = setTimeout(async () => {
      setSearching(true);
      try {
        const nextResults = await semanticSearch(tokens.accessToken as string, query.trim(), 20);
        setResults(nextResults);
        setActiveIndex(0);
      } catch {
        setResults([]);
      } finally {
        setSearching(false);
      }
    }, 300);

    return () => clearTimeout(handle);
  }, [query, isOpen, tokens?.accessToken]);

  function openResult(result: SearchResult) {
    router.push(resultHref(result));
    setOpen(false);
  }

  function handleKeyNav(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((index) => Math.min(index + 1, results.length - 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((index) => Math.max(index - 1, 0));
    } else if (event.key === "Enter" && results[activeIndex]) {
      event.preventDefault();
      openResult(results[activeIndex]);
    }
  }

  if (!isOpen) {
    return null;
  }

  const grouped = groupResults(results);
  let flatIndex = -1;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-gutter bg-black/20 blur-bg"
      onClick={() => setOpen(false)}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={t("shell.search.placeholder")}
        className="w-full max-w-2xl bg-surface-container-lowest rounded-xl shadow-2xl overflow-hidden flex flex-col border border-outline-variant/30"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="p-lg flex items-center gap-4 border-b border-outline-variant/20 bg-surface-bright">
          <span className="material-symbols-outlined text-primary text-2xl">search</span>
          <input
            className="flex-1 bg-transparent border-none outline-none focus:ring-0 font-body-lg text-body-lg text-on-surface placeholder-on-surface-variant/80"
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={handleKeyNav}
            placeholder={t("shell.search.placeholder")}
            ref={inputRef}
            value={query}
          />
          <div className="flex items-center gap-2 px-2 py-1 bg-surface-container rounded border border-outline-variant/30">
            <span className="text-[10px] font-bold text-outline uppercase tracking-wider">ESC</span>
          </div>
        </div>

        <div className="flex-1 max-h-[60vh] overflow-y-auto custom-scrollbar pb-lg">
          {!query.trim() ? (
            <p className="px-lg py-xl text-body-md text-on-surface-variant text-center">
              {t("shell.search.startTyping")}
            </p>
          ) : null}
          {query.trim() && isSearching ? (
            <p className="px-lg py-xl text-body-md text-on-surface-variant text-center">
              {t("shell.search.searching")}
            </p>
          ) : null}
          {query.trim() && !isSearching && results.length === 0 ? (
            <EmptyState icon="search_off" title={t("shell.search.noResults")} />
          ) : null}
          {grouped.map(([sourceType, items]) => {
            const meta = SOURCE_TYPE_META[sourceType] ?? { label: sourceType, icon: "search" };
            return (
              <div className="mt-lg px-lg" key={sourceType}>
                <div className="flex items-center justify-between mb-sm">
                  <span className="font-label-sm text-label-sm text-outline uppercase tracking-widest">
                    {meta.label}
                  </span>
                  <span className="text-body-sm text-primary">
                    {t("shell.search.matches", { count: items.length })}
                  </span>
                </div>
                <div className="space-y-base">
                  {items.slice(0, 4).map((result) => {
                    flatIndex += 1;
                    const isActive = flatIndex === activeIndex;
                    return (
                      <button
                        className={
                          "group w-full flex items-center gap-4 p-md rounded-lg cursor-pointer transition-colors active:scale-[0.98] border text-left " +
                          (isActive
                            ? "bg-primary-container/10 border-primary/20"
                            : "border-transparent hover:bg-primary-container/5 hover:border-primary/10")
                        }
                        key={`${result.source_type}-${result.source_id}`}
                        onClick={() => openResult(result)}
                        onMouseEnter={() => setActiveIndex(flatIndex)}
                        type="button"
                      >
                        <div className="w-9 h-9 rounded-full bg-surface-container-highest flex items-center justify-center text-primary shrink-0">
                          <span className="material-symbols-outlined text-[18px]">{meta.icon}</span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-label-md text-label-md text-on-surface truncate">
                            {result.title}
                          </p>
                          <p className="text-body-sm text-on-surface-variant truncate">
                            {highlightMatch(result.snippet, query)}
                          </p>
                        </div>
                        <span className="text-[11px] text-primary font-bold shrink-0">
                          %{Math.round(result.score * 100)}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>

        <div className="p-md px-lg bg-surface-container-low border-t border-outline-variant/20 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <kbd className="px-1.5 py-0.5 rounded bg-surface-container-lowest border border-outline-variant/30 text-[10px] font-bold shadow-sm">
                ↵
              </kbd>
              <span className="text-body-sm text-on-surface-variant">{t("shell.search.open")}</span>
            </div>
            <div className="flex items-center gap-2">
              <kbd className="px-1.5 py-0.5 rounded bg-surface-container-lowest border border-outline-variant/30 text-[10px] font-bold shadow-sm">
                ↑↓
              </kbd>
              <span className="text-body-sm text-on-surface-variant">{t("shell.search.navigate")}</span>
            </div>
            <div className="flex items-center gap-2">
              <kbd className="px-1.5 py-0.5 rounded bg-surface-container-lowest border border-outline-variant/30 text-[10px] font-bold shadow-sm">
                Esc
              </kbd>
              <span className="text-body-sm text-on-surface-variant">{t("shell.search.closeHint")}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-body-sm text-on-surface-variant italic">{t("shell.search.poweredBy")}</span>
            <span className="material-symbols-outlined text-primary text-sm animate-pulse">bolt</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export function openSearchPalette() {
  window.dispatchEvent(new Event(OPEN_EVENT));
}
