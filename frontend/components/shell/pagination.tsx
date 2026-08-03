"use client";

import { useLanguage } from "@/lib/i18n/context";

export function Pagination({
  page,
  totalPages,
  onPageChange,
  disabled = false,
}: {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  disabled?: boolean;
}) {
  const { t } = useLanguage();

  if (totalPages <= 1) {
    return null;
  }

  return (
    <div className="flex items-center justify-center gap-md py-md">
      <button
        type="button"
        disabled={disabled || page <= 1}
        onClick={() => onPageChange(page - 1)}
        className="w-9 h-9 flex items-center justify-center rounded-full text-on-surface-variant hover:bg-surface-container-high disabled:opacity-40 disabled:hover:bg-transparent transition-colors"
        aria-label={t("common.previousPage")}
      >
        <span className="material-symbols-outlined text-[20px]">chevron_left</span>
      </button>
      <span className="text-body-sm text-on-surface-variant">
        {t("common.pageOf", { page, totalPages })}
      </span>
      <button
        type="button"
        disabled={disabled || page >= totalPages}
        onClick={() => onPageChange(page + 1)}
        className="w-9 h-9 flex items-center justify-center rounded-full text-on-surface-variant hover:bg-surface-container-high disabled:opacity-40 disabled:hover:bg-transparent transition-colors"
        aria-label={t("common.nextPage")}
      >
        <span className="material-symbols-outlined text-[20px]">chevron_right</span>
      </button>
    </div>
  );
}
