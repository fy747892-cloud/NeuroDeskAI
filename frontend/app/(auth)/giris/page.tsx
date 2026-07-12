import { AuthForm } from "@/components/auth-form";

export default function LoginPage() {
  return (
    <section className="authCard">
      <p className="eyebrow">NeuroDeskAI</p>
      <h1>Giriş yap</h1>
      <p className="authLead">Operasyon paneline devam etmek için hesabına gir.</p>
      <AuthForm mode="login" />
    </section>
  );
}
