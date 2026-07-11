import { AuthForm } from "@/components/auth-form";

export default function RegisterPage() {
  return (
    <section className="authCard">
      <p className="eyebrow">NeuroDeskAI</p>
      <h1>Kayit ol</h1>
      <p className="authLead">Yeni calisma alani kullanicisini olustur.</p>
      <AuthForm mode="register" />
    </section>
  );
}
