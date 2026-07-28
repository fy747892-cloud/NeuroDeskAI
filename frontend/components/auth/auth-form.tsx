"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { authenticate, AuthMode } from "@/lib/api";
import { useSession } from "@/lib/session";
import { useLanguage } from "@/lib/i18n/context";

type AuthFormProps = {
  mode: AuthMode;
};

const REMEMBERED_EMAIL_KEY = "neurodesk-remembered-email";

export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const { setAuthenticatedSession } = useSession();
  const { t } = useLanguage();
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const isRegister = mode === "register";

  useEffect(() => {
    if (isRegister || typeof window === "undefined") return;
    const rememberedEmail = window.localStorage.getItem(REMEMBERED_EMAIL_KEY);
    if (rememberedEmail) {
      setEmail(rememberedEmail);
      setRememberMe(true);
    }
  }, [isRegister]);

  const canSubmit = useMemo(() => {
    if (!email.trim() || password.length < 8) return false;
    if (isRegister && !displayName.trim()) return false;
    return true;
  }, [displayName, email, isRegister, password]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) {
      setMessage(t("auth.validationMessage"));
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
      if (!isRegister && typeof window !== "undefined") {
        if (rememberMe) {
          window.localStorage.setItem(REMEMBERED_EMAIL_KEY, email.trim());
        } else {
          window.localStorage.removeItem(REMEMBERED_EMAIL_KEY);
        }
      }
      await setAuthenticatedSession(tokens);
      router.push("/");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : t("auth.authFailed"));
    } finally {
      setSubmitting(false);
    }
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
        <label className="flex items-center gap-2 text-body-sm text-on-surface-variant cursor-pointer">
          <input checked={rememberMe} onChange={(e) => setRememberMe(e.target.checked)} type="checkbox" />
          {t("auth.rememberMe")}
        </label>
      ) : null}

      <button
        type="submit"
        disabled={isSubmitting || !canSubmit}
        className="w-full flex items-center justify-center gap-2 py-3 bg-primary text-on-primary rounded-lg font-label-md hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-60"
      >
        <span className="material-symbols-outlined text-[18px]">
          {isSubmitting ? "hourglass_empty" : isRegister ? "person_add" : "login"}
        </span>
        {isSubmitting ? t("auth.submitting") : isRegister ? t("auth.registerSubmit") : t("auth.loginSubmit")}
      </button>

      {message ? <p className="text-error text-body-sm">{message}</p> : null}

      <p className="text-body-sm text-on-surface-variant text-center">
        {isRegister ? t("auth.alreadyHaveAccount") : t("auth.noAccount")}{" "}
        <a href={isRegister ? "/giris" : "/kayit"} className="text-primary font-bold hover:underline">
          {isRegister ? t("auth.loginSubmit") : t("auth.registerLink")}
        </a>
      </p>

      <p className="text-body-sm text-on-surface-variant text-center">
        <a href="/gizlilik" className="hover:underline">
          Gizlilik Politikası
        </a>
      </p>
    </form>
  );
}
