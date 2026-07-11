"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";
import { authenticate, AuthMode } from "@/lib/api";
import { useSession } from "@/lib/session";

type AuthFormProps = {
  mode: AuthMode;
};

export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const { setAuthenticatedSession } = useSession();
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

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
      setMessage("Lutfen gecerli email, sifre ve ad soyad bilgisi girin.");
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
      await setAuthenticatedSession(tokens);
      router.push("/");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Kimlik dogrulama basarisiz.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="authForm" onSubmit={handleSubmit}>
      {isRegister ? (
        <label>
          Ad soyad
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
        Sifre
        <input
          autoComplete={isRegister ? "new-password" : "current-password"}
          minLength={8}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="En az 8 karakter"
          type="password"
          value={password}
        />
      </label>

      <button disabled={isSubmitting || !canSubmit} type="submit">
        {isSubmitting ? "Isleniyor..." : isRegister ? "Hesap olustur" : "Giris yap"}
      </button>

      {message ? <p className="formMessage">{message}</p> : null}

      <p className="authSwitch">
        {isRegister ? "Zaten hesabin var mi?" : "Hesabin yok mu?"}{" "}
        <a href={isRegister ? "/giris" : "/kayit"}>{isRegister ? "Giris yap" : "Kayit ol"}</a>
      </p>
    </form>
  );
}
