"use client";

import { FormEvent, useMemo, useState } from "react";
import { authenticate, AuthMode } from "@/lib/api";

const STORAGE_KEY = "neurodesk.tokens";

type SavedSession = {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  email: string;
};

export function AuthPanel() {
  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [session, setSession] = useState<SavedSession | null>(() => loadSession());

  const isRegister = mode === "register";
  const canSubmit = useMemo(() => {
    if (!email.trim() || password.length < 8) {
      return false;
    }
    if (isRegister && !displayName.trim()) {
      return false;
    }
    return true;
  }, [displayName, email, isRegister, password]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) {
      setMessage("Email, password and display name fields must be valid.");
      return;
    }

    setSubmitting(true);
    setMessage(null);

    try {
      const tokens = await authenticate(mode, {
        email,
        password,
        displayName: displayName.trim() || email.split("@")[0],
      });
      const nextSession = {
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        tokenType: tokens.token_type,
        email,
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(nextSession));
      setSession(nextSession);
      setPassword("");
      setMessage(isRegister ? "Account created and signed in." : "Signed in successfully.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Authentication failed.");
    } finally {
      setSubmitting(false);
    }
  }

  function handleSignOut() {
    localStorage.removeItem(STORAGE_KEY);
    setSession(null);
    setMessage("Signed out locally.");
  }

  return (
    <section className="authSurface" aria-label="Authentication">
      <div className="panelHeader">
        <h2>Access</h2>
        <div className="segmented" role="tablist" aria-label="Authentication mode">
          <button
            aria-selected={mode === "login"}
            className={mode === "login" ? "selected" : ""}
            onClick={() => setMode("login")}
            type="button"
          >
            Login
          </button>
          <button
            aria-selected={mode === "register"}
            className={mode === "register" ? "selected" : ""}
            onClick={() => setMode("register")}
            type="button"
          >
            Register
          </button>
        </div>
      </div>

      {session ? (
        <div className="sessionBox">
          <span>Active session</span>
          <strong>{session.email}</strong>
          <button type="button" onClick={handleSignOut}>
            Sign out
          </button>
        </div>
      ) : (
        <form className="authForm" onSubmit={handleSubmit}>
          {isRegister ? (
            <label>
              Display name
              <input
                autoComplete="name"
                onChange={(event) => setDisplayName(event.target.value)}
                placeholder="Dr. Ayse Demir"
                value={displayName}
              />
            </label>
          ) : null}

          <label>
            Email
            <input
              autoComplete="email"
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              type="email"
              value={email}
            />
          </label>

          <label>
            Password
            <input
              autoComplete={isRegister ? "new-password" : "current-password"}
              minLength={8}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="At least 8 characters"
              type="password"
              value={password}
            />
          </label>

          <button disabled={isSubmitting || !canSubmit} type="submit">
            {isSubmitting ? "Please wait..." : isRegister ? "Create account" : "Login"}
          </button>
        </form>
      )}

      {message ? <p className="formMessage">{message}</p> : null}
    </section>
  );
}

function loadSession(): SavedSession | null {
  if (typeof window === "undefined") {
    return null;
  }
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as SavedSession;
  } catch {
    localStorage.removeItem(STORAGE_KEY);
    return null;
  }
}
