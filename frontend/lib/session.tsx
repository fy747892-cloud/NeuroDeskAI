"use client";

import {
  createContext,
  ReactNode,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { CurrentUser, getCurrentUser, logout, refreshAccessToken, TokenResponse } from "@/lib/api";

type SessionTokens = {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
};

type SessionState = {
  tokens: SessionTokens | null;
  user: CurrentUser | null;
  isAuthenticated: boolean;
  isInitializing: boolean;
  setAuthenticatedSession: (tokens: TokenResponse) => Promise<void>;
  refreshUser: () => Promise<void>;
  signOut: () => Promise<void>;
};

const SessionContext = createContext<SessionState | null>(null);

const REFRESH_TOKEN_KEY = "neurodesk-refresh-token";
const REFRESH_SKEW_MS = 60_000;

function decodeAccessTokenExpiry(accessToken: string): number | null {
  try {
    const payload = accessToken.split(".")[1];
    const decoded = JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/"))) as {
      exp?: number;
    };
    return typeof decoded.exp === "number" ? decoded.exp * 1000 : null;
  } catch {
    return null;
  }
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const [tokens, setTokens] = useState<SessionTokens | null>(null);
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isInitializing, setInitializing] = useState(true);
  const refreshTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  function persistTokens(nextTokens: TokenResponse) {
    const normalizedTokens: SessionTokens = {
      accessToken: nextTokens.access_token,
      refreshToken: nextTokens.refresh_token,
      tokenType: nextTokens.token_type,
    };
    setTokens(normalizedTokens);
    window.localStorage.setItem(REFRESH_TOKEN_KEY, normalizedTokens.refreshToken);
    scheduleRefresh(normalizedTokens);
    return normalizedTokens;
  }

  function clearSession() {
    if (refreshTimer.current) {
      clearTimeout(refreshTimer.current);
      refreshTimer.current = null;
    }
    setTokens(null);
    setUser(null);
    window.localStorage.removeItem(REFRESH_TOKEN_KEY);
  }

  function scheduleRefresh(currentTokens: SessionTokens) {
    if (refreshTimer.current) {
      clearTimeout(refreshTimer.current);
    }
    const expiryMs = decodeAccessTokenExpiry(currentTokens.accessToken);
    const delay = expiryMs ? Math.max(expiryMs - Date.now() - REFRESH_SKEW_MS, 5_000) : 10 * 60_000;

    refreshTimer.current = setTimeout(async () => {
      try {
        const nextTokens = await refreshAccessToken(currentTokens.refreshToken);
        persistTokens(nextTokens);
      } catch {
        clearSession();
      }
    }, delay);
  }

  useEffect(() => {
    const storedRefreshToken = window.localStorage.getItem(REFRESH_TOKEN_KEY);
    if (!storedRefreshToken) {
      setInitializing(false);
      return;
    }

    (async () => {
      try {
        const nextTokens = await refreshAccessToken(storedRefreshToken);
        const normalizedTokens = persistTokens(nextTokens);
        setUser(await getCurrentUser(normalizedTokens.accessToken));
      } catch {
        clearSession();
      } finally {
        setInitializing(false);
      }
    })();

    return () => {
      if (refreshTimer.current) {
        clearTimeout(refreshTimer.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function setAuthenticatedSession(nextTokens: TokenResponse) {
    const normalizedTokens = persistTokens(nextTokens);
    setUser(await getCurrentUser(normalizedTokens.accessToken));
  }

  async function refreshUser() {
    if (!tokens?.accessToken) return;
    setUser(await getCurrentUser(tokens.accessToken));
  }

  async function signOut() {
    const refreshToken = tokens?.refreshToken;
    clearSession();
    if (refreshToken) {
      await logout(refreshToken);
    }
  }

  const value = useMemo<SessionState>(
    () => ({
      tokens,
      user,
      isAuthenticated: Boolean(tokens && user),
      isInitializing,
      setAuthenticatedSession,
      refreshUser,
      signOut,
    }),
    [tokens, user, isInitializing],
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
