"use client";

import { useEffect, useState } from "react";
import { getInitials } from "@/lib/format";

export function Avatar({
  name,
  avatarUrl,
  className = "w-10 h-10 text-sm",
}: {
  name: string;
  avatarUrl?: string | null;
  className?: string;
}) {
  const [errored, setErrored] = useState(false);

  // A new avatar URL (re-upload, different user) deserves a fresh attempt
  // instead of staying stuck on a previous failure.
  useEffect(() => {
    setErrored(false);
  }, [avatarUrl]);

  if (avatarUrl && !errored) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={avatarUrl}
        alt={name}
        onError={() => setErrored(true)}
        className={`rounded-full object-cover shrink-0 ${className}`}
      />
    );
  }

  return (
    <div
      className={`rounded-full bg-primary-container/20 flex items-center justify-center text-primary font-bold shrink-0 ${className}`}
    >
      {getInitials(name)}
    </div>
  );
}
