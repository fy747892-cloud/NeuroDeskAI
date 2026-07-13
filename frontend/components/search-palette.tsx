"use client";

import { useRouter } from "next/navigation";
import { KeyboardEvent, useEffect, useRef, useState } from "react";
import { SearchResult, semanticSearch } from "@/lib/api";
import { groupResults, highlightMatch, resultHref, SOURCE_TYPE_META } from "@/lib/search-utils";
import { useSession } from "@/lib/session";

const OPEN_EVENT = "neurodesk:open-search";

export function SearchPalette() {
  const { tokens } = useSession();
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
    <div className="paletteOverlay" onClick={() => setOpen(false)}>
      <div className="paletteBox" onClick={(event) => event.stopPropagation()}>
        <div className="paletteHead">
          <span className="material-symbols-outlined" aria-hidden="true">
            search
          </span>
          <input
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={handleKeyNav}
            placeholder="Görüşme, görev, kişi veya e-posta ara..."
            ref={inputRef}
            value={query}
          />
          <kbd>ESC</kbd>
        </div>

        <div className="paletteResults">
          {!query.trim() ? (
            <p className="emptyState">Aramaya başlamak için yazmaya başla.</p>
          ) : null}
          {query.trim() && isSearching ? <p className="emptyState">Aranıyor...</p> : null}
          {query.trim() && !isSearching && results.length === 0 ? (
            <p className="emptyState">Sonuç bulunamadı.</p>
          ) : null}
          {grouped.map(([sourceType, items]) => {
            const meta = SOURCE_TYPE_META[sourceType] ?? { label: sourceType, icon: "search" };
            return (
              <div className="paletteGroup" key={sourceType}>
                <div className="paletteGroupHead">
                  <span>{meta.label}</span>
                  <span>{items.length} eşleşme</span>
                </div>
                {items.slice(0, 4).map((result) => {
                  flatIndex += 1;
                  const isActive = flatIndex === activeIndex;
                  return (
                    <button
                      className={isActive ? "paletteItem active" : "paletteItem"}
                      key={`${result.source_type}-${result.source_id}`}
                      onClick={() => openResult(result)}
                      onMouseEnter={() => setActiveIndex(flatIndex)}
                      type="button"
                    >
                      <span className="material-symbols-outlined" aria-hidden="true">
                        {meta.icon}
                      </span>
                      <div>
                        <p className="paletteItemTitle">{result.title}</p>
                        <p className="paletteItemSnippet">{highlightMatch(result.snippet, query)}</p>
                      </div>
                      <span className="paletteScore">%{Math.round(result.score * 100)}</span>
                    </button>
                  );
                })}
              </div>
            );
          })}
        </div>

        <div className="paletteFooter">
          <span>
            <kbd>↵</kbd> Aç
          </span>
          <span>
            <kbd>↑↓</kbd> Gezin
          </span>
          <span>
            <kbd>Esc</kbd> Kapat
          </span>
          <span className="paletteFooterRight">
            <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 14 }}>
              bolt
            </span>
            NeuroDesk AI Core ile aranıyor
          </span>
        </div>
      </div>
    </div>
  );
}

export function openSearchPalette() {
  window.dispatchEvent(new Event(OPEN_EVENT));
}
