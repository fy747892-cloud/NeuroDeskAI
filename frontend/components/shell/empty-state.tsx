export function EmptyState({
  icon,
  title,
  subtitle,
  size = "sm",
  action,
}: {
  icon: string;
  title: string;
  subtitle?: string;
  size?: "sm" | "lg";
  action?: { label: string; onClick: () => void };
}) {
  if (size === "lg") {
    return (
      <div className="flex flex-col items-center justify-center text-center py-xl px-lg border-2 border-dashed border-outline-variant/30 rounded-2xl">
        <span className="material-symbols-outlined text-outline-variant text-[44px] mb-md">{icon}</span>
        <p className="font-headline-md text-headline-md text-on-surface-variant">{title}</p>
        {subtitle ? (
          <p className="font-body-md text-on-surface-variant/70 mt-2 max-w-sm">{subtitle}</p>
        ) : null}
        {action ? (
          <button
            type="button"
            onClick={action.onClick}
            className="mt-lg text-primary text-[13px] font-bold hover:underline"
          >
            {action.label}
          </button>
        ) : null}
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center text-center py-lg px-md gap-1">
      <span className="material-symbols-outlined text-outline-variant text-[26px]">{icon}</span>
      <p className="text-body-sm text-on-surface-variant">{title}</p>
      {subtitle ? <p className="text-[11px] text-on-surface-variant/70">{subtitle}</p> : null}
      {action ? (
        <button
          type="button"
          onClick={action.onClick}
          className="mt-1 text-primary text-[11px] font-bold hover:underline"
        >
          {action.label}
        </button>
      ) : null}
    </div>
  );
}
