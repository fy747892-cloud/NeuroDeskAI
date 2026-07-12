import { AuthForm } from "@/components/auth-form";

export default function RegisterPage() {
  return (
    <section className="authCard">
      <p className="eyebrow">NeuroDeskAI</p>
      <h1>Kayıt ol</h1>
      <p className="authLead">Yeni çalışma alanı kullanıcısını oluştur.</p>
      <AuthForm mode="register" />
    </section>
  );
}
