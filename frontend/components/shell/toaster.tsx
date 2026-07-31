"use client";

import { useToast, type ToastVariant } from "@/lib/toast";

const VARIANT_STYLES: Record<ToastVariant, { icon: string; className: string }> = {
  success: { icon: "check_circle", className: "border-primary/30 text-primary" },
  error: { icon: "error", className: "border-error/30 text-error" },
  info: { icon: "info", className: "border-outline-variant text-on-surface" },
};

export function Toaster() {
  const { toasts, dismissToast } = useToast();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-md right-md sm:bottom-xl sm:right-xl z-[200] flex flex-col gap-2 w-[calc(100vw-2rem)] max-w-sm">
      {toasts.map((toast) => {
        const style = VARIANT_STYLES[toast.variant];
        return (
          <div
            key={toast.id}
            role="status"
            className={`flex items-start gap-3 bg-surface-container-lowest border rounded-xl shadow-xl p-md ${style.className}`}
          >
            <span className="material-symbols-outlined text-[20px] shrink-0" style={{ fontVariationSettings: "'FILL' 1" }}>
              {style.icon}
            </span>
            <p className="flex-1 text-body-sm text-on-surface leading-snug">{toast.message}</p>
            {toast.action ? (
              <button
                type="button"
                onClick={() => {
                  toast.action?.onClick();
                  dismissToast(toast.id);
                }}
                className="text-primary text-[13px] font-bold hover:underline shrink-0"
              >
                {toast.action.label}
              </button>
            ) : null}
            <button
              type="button"
              onClick={() => dismissToast(toast.id)}
              className="text-on-surface-variant hover:text-on-surface shrink-0"
              aria-label="Kapat"
            >
              <span className="material-symbols-outlined text-[16px]">close</span>
            </button>
          </div>
        );
      })}
    </div>
  );
}
