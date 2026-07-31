export const UNDO_WINDOW_MS = 5000;

/**
 * Runs `action` after `delayMs` unless `cancel()` is called first — the
 * building block for "X deleted [Undo]" flows: the caller updates local
 * state optimistically, then defers the actual API call so an Undo click
 * can cancel it before it ever happens (no server-side restore needed).
 */
export function deferredExecute(action: () => void | Promise<void>, delayMs: number = UNDO_WINDOW_MS): { cancel: () => void } {
  const timer = setTimeout(() => {
    void action();
  }, delayMs);
  return {
    cancel: () => clearTimeout(timer),
  };
}
