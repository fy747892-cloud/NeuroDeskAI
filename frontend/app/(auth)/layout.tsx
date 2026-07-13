export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="authPage">
      <section className="authBrand">
        <div className="authBlob b1" aria-hidden="true" />
        <div className="authBlob b2" aria-hidden="true" />
        <div className="authBlob b3" aria-hidden="true" />

        <div className="authBrandTop">
          <div className="authBrandLogo">
            <div className="brandMark">N</div>
            <span>NeuroDesk AI</span>
          </div>
        </div>

        <div className="authBrandMid">
          <h1>
            İşinizi yöneten
            <br />
            <span>yapay zeka ortağınız.</span>
          </h1>
          <p>
            Görüşmeler, görevler, randevular ve CRM&apos;i tek panelde birleştirir; AI önerir, siz
            onaylarsınız.
          </p>
          <ul className="authFeatureList">
            <li style={{ animationDelay: "0.15s" }}>
              <span className="material-symbols-outlined" aria-hidden="true">
                auto_awesome
              </span>
              AI destekli görüşme özetleri ve öneriler
            </li>
            <li style={{ animationDelay: "0.3s" }}>
              <span className="material-symbols-outlined" aria-hidden="true">
                task_alt
              </span>
              Otomatik görev, randevu ve fırsat çıkarımı
            </li>
            <li style={{ animationDelay: "0.45s" }}>
              <span className="material-symbols-outlined" aria-hidden="true">
                shield
              </span>
              Her AI aksiyonu insan onayından geçer
            </li>
          </ul>
        </div>

        <p className="authBrandFooter">© 2026 NeuroDesk AI</p>
      </section>

      <section className="authFormSide">{children}</section>
    </main>
  );
}
