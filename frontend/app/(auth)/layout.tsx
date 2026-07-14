export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="min-h-screen flex bg-background">
      <section className="hidden lg:flex lg:w-1/2 relative overflow-hidden flex-col justify-between bg-gradient-to-br from-primary to-secondary text-on-primary p-12">
        <div className="absolute -right-24 -top-24 w-96 h-96 rounded-full bg-white/10 blur-3xl" />
        <div className="absolute -left-16 bottom-0 w-72 h-72 rounded-full bg-white/10 blur-3xl" />

        <div className="relative z-10 flex items-center gap-2">
          <div className="w-9 h-9 rounded-lg bg-white/20 flex items-center justify-center font-bold">N</div>
          <span className="font-headline-md text-headline-md font-bold">NeuroDesk AI</span>
        </div>

        <div className="relative z-10 max-w-md">
          <h1 className="font-headline-lg text-headline-lg leading-tight mb-4">
            İşinizi yöneten
            <br />
            yapay zeka ortağınız.
          </h1>
          <p className="text-body-lg opacity-90 mb-xl">
            Görüşmeler, görevler, randevular ve CRM&apos;i tek panelde birleştirir; AI önerir, siz onaylarsınız.
          </p>
          <ul className="space-y-4">
            <li className="flex items-center gap-3">
              <span className="material-symbols-outlined">auto_awesome</span>
              AI destekli görüşme özetleri ve öneriler
            </li>
            <li className="flex items-center gap-3">
              <span className="material-symbols-outlined">task_alt</span>
              Otomatik görev, randevu ve fırsat çıkarımı
            </li>
            <li className="flex items-center gap-3">
              <span className="material-symbols-outlined">shield</span>
              Her AI aksiyonu insan onayından geçer
            </li>
          </ul>
        </div>

        <p className="relative z-10 text-body-sm opacity-70">© 2026 NeuroDesk AI</p>
      </section>

      <section className="flex-1 flex items-center justify-center p-xl">
        <div className="w-full max-w-md">{children}</div>
      </section>
    </main>
  );
}
