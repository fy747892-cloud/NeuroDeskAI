"use client";

import { createContext, ReactNode, useContext, useMemo, useState } from "react";
import { CurrentUser, getCurrentUser, logout, TokenResponse } from "@/lib/api";

type SessionTokens = {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
};

type SessionState = {
  tokens: SessionTokens | null;
  user: CurrentUser | null;
  isAuthenticated: boolean;
  setAuthenticatedSession: (tokens: TokenResponse) => Promise<void>;
  signOut: () => Promise<void>;
};

const SessionContext = createContext<SessionState | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [tokens, setTokens] = useState<SessionTokens | null>(null);
  const [user, setUser] = useState<CurrentUser | null>(null);

  async function setAuthenticatedSession(nextTokens: TokenResponse) {
    const normalizedTokens = {
      accessToken: nextTokens.access_token,
      refreshToken: nextTokens.refresh_token,
      tokenType: nextTokens.token_type,
    };
    const currentUser = await getCurrentUser(normalizedTokens.accessToken);
    setTokens(normalizedTokens);
    setUser(currentUser);
  }

  async function signOut() {
    const refreshToken = tokens?.refreshToken;
    setTokens(null);
    setUser(null);
    if (refreshToken) {
      await logout(refreshToken);
    }
  }

  const value = useMemo<SessionState>(
    () => ({
      tokens,
      user,
      isAuthenticated: Boolean(tokens && user),
      setAuthenticatedSession,
      signOut,
    }),
    [tokens, user],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const context = useContext(SessionContext);
  if (context === null) {
    throw new Error("useSession must be used inside SessionProvider.");
  }
  return context;
}
