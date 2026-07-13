import type { Route } from "next";
import type { ReactNode } from "react";
import type { SearchResult } from "@/lib/api";

export const SOURCE_TYPE_META: Record<string, { label: string; icon: string }> = {
  contact: { label: "Kişiler", icon: "person" },
  conversation: { label: "Görüşmeler", icon: "forum" },
  task: { label: "Görevler", icon: "task_alt" },
  appointment: { label: "Randevular", icon: "event" },
  email_message: { label: "E-postalar", icon: "mail" },
};

export function resultHref(result: SearchResult): Route {
  switch (result.source_type) {
    case "contact":
      return `/kisiler/${result.source_id}` as Route;
    case "conversation":
      return "/gorusmeler" as Route;
    case "task":
      return "/gorevler" as Route;
    case "appointment":
      return "/takvim" as Route;
    case "email_message":
      return "/mailler" as Route;
    default:
      return "/arama" as Route;
  }
}

export function groupResults(results: SearchResult[]): [string, SearchResult[]][] {
  const groups = new Map<string, SearchResult[]>();
  for (const result of results) {
    const list = groups.get(result.source_type) ?? [];
    list.push(result);
    groups.set(result.source_type, list);
  }
  return Array.from(groups.entries());
}

export function highlightMatch(text: string, query: string): ReactNode {
  const trimmed = query.trim();
  if (!trimmed) {
    return text;
  }
  const index = text.toLowerCase().indexOf(trimmed.toLowerCase());
  if (index === -1) {
    return text;
  }
  return (
    <>
      {text.slice(0, index)}
      <mark>{text.slice(index, index + trimmed.length)}</mark>
      {text.slice(index + trimmed.length)}
    </>
  );
}
