"use client";

import { usePathname, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";

export function RouteProgressBar() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [progress, setProgress] = useState(0);
  const [isVisible, setVisible] = useState(false);
  const trickleTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const finishTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isNavigating = useRef(false);

  useEffect(() => {
    function clearTimers() {
      if (trickleTimer.current) clearInterval(trickleTimer.current);
      if (finishTimer.current) clearTimeout(finishTimer.current);
    }

    function startProgress() {
      if (isNavigating.current) return;
      isNavigating.current = true;
      clearTimers();
      setVisible(true);
      setProgress(15);
      trickleTimer.current = setInterval(() => {
        setProgress((current) => (current < 80 ? current + (80 - current) * 0.1 : current));
      }, 200);
    }

    function handleClick(event: MouseEvent) {
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const anchor = (event.target as HTMLElement)?.closest?.("a[href]") as HTMLAnchorElement | null;
      if (!anchor) return;
      const href = anchor.getAttribute("href");
      if (!href || !href.startsWith("/") || href.startsWith("//") || anchor.target === "_blank") return;
      if (href === window.location.pathname + window.location.search) return;
      startProgress();
    }

    document.addEventListener("click", handleClick, true);
    return () => {
      document.removeEventListener("click", handleClick, true);
      clearTimers();
    };
  }, []);

  useEffect(() => {
    if (!isNavigating.current) return;
    isNavigating.current = false;
    if (trickleTimer.current) clearInterval(trickleTimer.current);
    setProgress(100);
    finishTimer.current = setTimeout(() => {
      setVisible(false);
      setProgress(0);
    }, 250);
    return () => {
      if (finishTimer.current) clearTimeout(finishTimer.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname, searchParams]);

  if (!isVisible) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-[300] h-[3px] bg-transparent pointer-events-none">
      <div
        className="h-full bg-primary transition-all duration-200 ease-out shadow-[0_0_8px_rgba(53,37,205,0.6)]"
        style={{ width: `${progress}%` }}
      />
    </div>
  );
}
