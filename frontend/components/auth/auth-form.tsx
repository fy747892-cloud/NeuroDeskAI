"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { authenticate, AuthMode, exchangeGoogleLoginCode, getGoogleLoginUrl } from "@/lib/api";
import { useSession } from "@/lib/session";
import { useLanguage } from "@/lib/i18n/context";

type AuthFormProps = {
  mode: AuthMode;
};

const REMEMBERED_EMAIL_KEY = "neurodesk-remembered-email";

export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setAuthenticatedSession } = useSession();
  const { t } = useLanguage();
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [needsMfa, setNeedsMfa] = useState(false);
  const [mfaCode, setMfaCode] = useState("");
  const [useRecoveryCode, setUseRecoveryCode] = useState(false);
  const [isGoogleBusy, setGoogleBusy] = useState(false);

  const isRegister = mode === "register";

  useEffect(() => {
    if (isRegister || typeof window === "undefined") return;
    const rememberedEmail = window.localStorage.getItem(REMEMBERED_EMAIL_KEY);
    if (rememberedEmail) {
      setEmail(rememberedEmail);
      setRememberMe(true);
    }
  }, [isRegister]);

  useEffect(() => {
    const loginCode = searchParams.get("login_code");
    const googleError = searchParams.get("google_error");

    if (loginCode) {
      setGoogleBusy(true);
      exchangeGoogleLoginCode(loginCode)
        .then(async (tokens) => {
          await setAuthenticatedSession(tokens);
          router.push("/");
        })
        .catch((error) => {
          setMessage(error instanceof Error ? error.message : t("auth.google.exchangeError"));
          setGoogleBusy(false);
          router.replace(isRegister ? "/kayit" : "/giris");
        });
      return;
    }

    if (googleError) {
      setMessage(
        googleError === "totp_required" ? t("auth.google.totpRequiredError") : t("auth.google.error"),
      );
      router.replace(isRegister ? "/kayit" : "/giris");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  async function handleGoogleLogin() {
    setGoogleBusy(true);
    setMessage(null);
    try {
      const { authorize_url } = await getGoogleLoginUrl();
      window.location.href = authorize_url;
    } catch (error) {
      setMessage(error instanceof Error ? error.message : t("auth.google.error"));
      setGoogleBusy(false);
    }
  }

  const canSubmit = useMemo(() => {
    if (!email.trim() || password.length < 8) return false;
    if (isRegister && !displayName.trim()) return false;
    if (needsMfa && !mfaCode.trim()) return false;
    return true;
  }, [displayName, email, isRegister, mfaCode, needsMfa, password]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) {
      setMessage(t("auth.validationMessage"));
      return;
    }

    setSubmitting(true);
    setMessage(null);

    try {
      const result = await authenticate(mode, {
        email,
        password,
        displayName: displayName.trim() || email.split("@")[0],
        totpCode: needsMfa && !useRecoveryCode ? mfaCode.trim() : undefined,
        recoveryCode: needsMfa && useRecoveryCode ? mfaCode.trim() : undefined,
      });

      if ("mfa_required" in result) {
        if (needsMfa) {
          setMessage(t("auth.mfa.invalidCode"));
        } else {
          setNeedsMfa(true);
        }
        return;
      }

      if (!isRegister && typeof window !== "undefined") {
        if (rememberMe) {
          window.localStorage.setItem(REMEMBERED_EMAIL_KEY, email.trim());
        } else {
          window.localStorage.removeItem(REMEMBERED_EMAIL_KEY);
        }
      }
      await setAuthenticatedSession(result);
      router.push("/");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : t("auth.authFailed"));
    } finally {
      setSubmitting(false);
    }
  }

  if (searchParams.get("login_code")) {
    return (
      <div className="flex flex-col items-center gap-3 py-12 text-center">
        <span className="material-symbols-outlined text-primary text-3xl animate-spin">progress_activity</span>
        <p className="text-body-md text-on-surface-variant">{t("auth.google.signingIn")}</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <h1 className="font-headline-lg text-headline-lg text-on-surface">
          {isRegister ? t("auth.registerTitle") : t("auth.loginTitle")}
        </h1>
        <p className="text-body-md text-on-surface-variant mt-1">
          {isRegister ? t("auth.registerSubtitle") : t("auth.loginSubtitle")}
        </p>
      </div>

      {!needsMfa ? (
        <>
          <button
            type="button"
            disabled={isGoogleBusy}
            onClick={handleGoogleLogin}
            className="w-full flex items-center justify-center gap-2 py-2.5 border border-outline-variant rounded-lg font-label-md text-on-surface hover:bg-surface-container-high active:scale-[0.98] transition-all disabled:opacity-60"
          >
            <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
              <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z" />
              <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.9-2.26 5.36-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z" />
              <path fill="#FBBC05" d="M10.53 28.59A14.5 14.5 0 0 1 9.5 24c0-1.59.27-3.13.76-4.59l-7.98-6.19A23.96 23.96 0 0 0 0 24c0 3.86.92 7.51 2.56 10.78z" />
              <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z" />
            </svg>
            {isGoogleBusy ? t("auth.submitting") : t("auth.google.continueButton")}
          </button>
          <div className="flex items-center gap-3 text-[11px] text-on-surface-variant uppercase tracking-wide">
            <span className="flex-1 h-px bg-outline-variant/40" />
            {t("auth.google.divider")}
            <span className="flex-1 h-px bg-outline-variant/40" />
          </div>
        </>
      ) : null}

      {needsMfa ? (
        <div className="space-y-3">
          <p className="text-body-sm text-on-surface-variant">
            {useRecoveryCode ? t("auth.mfa.recoveryPrompt") : t("auth.mfa.codePrompt")}
          </p>
          <label className="block">
            <span className="text-label-sm font-label-sm text-on-surface-variant mb-1 block">
              {useRecoveryCode ? t("auth.mfa.recoveryCodeLabel") : t("auth.mfa.codeLabel")}
            </span>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">
                {useRecoveryCode ? "vpn_key" : "pin"}
              </span>
              <input
                autoComplete="one-time-code"
                autoFocus
                onChange={(e) => setMfaCode(e.target.value)}
                placeholder={useRecoveryCode ? t("auth.mfa.recoveryCodePlaceholder") : "000000"}
                value={mfaCode}
                className="w-full pl-10 pr-4 py-2.5 bg-surface-container-low border border-outline-variant/30 rounded-lg text-body-md focus:ring-2 focus:ring-primary/20 focus:outline-none tracking-widest"
              />
            </div>
          </label>
          <button
            type="button"
            onClick={() => {
              setUseRecoveryCode((v) => !v);
              setMfaCode("");
              setMessage(null);
            }}
            className="text-body-sm text-primary hover:underline"
          >
            {useRecoveryCode ? t("auth.mfa.useCodeInstead") : t("auth.mfa.useRecoveryInstead")}
          </button>
        </div>
      ) : (
        <>
          {isRegister ? (
            <label className="block">
              <span className="text-label-sm font-label-sm text-on-surface-variant mb-1 block">
                {t("auth.fullName")}
              </span>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">badge</span>
                <input
                  autoComplete="name"
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder={t("auth.fullNamePlaceholder")}
                  value={displayName}
                  className="w-full pl-10 pr-4 py-2.5 bg-surface-container-low border border-outline-variant/30 rounded-lg text-body-md focus:ring-2 focus:ring-primary/20 focus:outline-none"
                />
              </div>
            </label>
          ) : null}

          <label className="block">
            <span className="text-label-sm font-label-sm text-on-surface-variant mb-1 block">{t("common.email")}</span>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">mail</span>
              <input
                autoComplete="email"
                onChange={(e) => setEmail(e.target.value)}
                placeholder={t("auth.emailPlaceholder")}
                type="email"
                value={email}
                className="w-full pl-10 pr-4 py-2.5 bg-surface-container-low border border-outline-variant/30 rounded-lg text-body-md focus:ring-2 focus:ring-primary/20 focus:outline-none"
              />
            </div>
          </label>

          <label className="block">
            <span className="text-label-sm font-label-sm text-on-surface-variant mb-1 block">{t("auth.password")}</span>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">lock</span>
              <input
                autoComplete={isRegister ? "new-password" : "current-password"}
                minLength={8}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={t("auth.passwordPlaceholder")}
                type={showPassword ? "text" : "password"}
                value={password}
                className="w-full pl-10 pr-10 py-2.5 bg-surface-container-low border border-outline-variant/30 rounded-lg text-body-md focus:ring-2 focus:ring-primary/20 focus:outline-none"
              />
              <button
                type="button"
                aria-label={showPassword ? t("auth.hidePassword") : t("auth.showPassword")}
                onClick={() => setShowPassword((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-outline hover:text-primary"
              >
                <span className="material-symbols-outlined text-[18px]">
                  {showPassword ? "visibility_off" : "visibility"}
                </span>
              </button>
            </div>
          </label>

          {!isRegister ? (
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-body-sm text-on-surface-variant cursor-pointer">
                <input checked={rememberMe} onChange={(e) => setRememberMe(e.target.checked)} type="checkbox" />
                {t("auth.rememberMe")}
              </label>
              <a href="/sifremi-unuttum" className="text-body-sm text-primary hover:underline">
                {t("auth.forgotPasswordLink")}
              </a>
            </div>
          ) : null}
        </>
      )}

      <button
        type="submit"
        disabled={isSubmitting || !canSubmit}
        className="w-full flex items-center justify-center gap-2 py-3 bg-primary text-on-primary rounded-lg font-label-md hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-60"
      >
        <span className="material-symbols-outlined text-[18px]">
          {isSubmitting ? "hourglass_empty" : needsMfa ? "verified_user" : isRegister ? "person_add" : "login"}
        </span>
        {isSubmitting
          ? t("auth.submitting")
          : needsMfa
            ? t("auth.mfa.verifyButton")
            : isRegister
              ? t("auth.registerSubmit")
              : t("auth.loginSubmit")}
      </button>

      {message ? <p className="text-error text-body-sm">{message}</p> : null}

      {needsMfa ? (
        <p className="text-body-sm text-center">
          <button
            type="button"
            onClick={() => {
              setNeedsMfa(false);
              setMfaCode("");
              setUseRecoveryCode(false);
              setMessage(null);
            }}
            className="text-primary hover:underline"
          >
            {t("auth.mfa.backToLogin")}
          </button>
        </p>
      ) : (
        <p className="text-body-sm text-on-surface-variant text-center">
          {isRegister ? t("auth.alreadyHaveAccount") : t("auth.noAccount")}{" "}
          <a href={isRegister ? "/giris" : "/kayit"} className="text-primary font-bold hover:underline">
            {isRegister ? t("auth.loginSubmit") : t("auth.registerLink")}
          </a>
        </p>
      )}

      <p className="text-body-sm text-on-surface-variant text-center">
        <a href="/gizlilik" className="hover:underline">
          Gizlilik Politikası
        </a>
      </p>
    </form>
  );
}
