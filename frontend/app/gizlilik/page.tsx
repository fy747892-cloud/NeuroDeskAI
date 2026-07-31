import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Gizlilik Politikası",
  description: "NeuroDesk AI gizlilik politikası ve Google kullanıcı verisi kullanım açıklaması.",
};

export default function PrivacyPolicyPage() {
  return (
    <main className="mx-auto min-h-screen max-w-3xl bg-background px-6 py-16 text-on-surface">
      <h1 className="font-[Geist] text-headline-lg text-on-background">
        Gizlilik Politikası
      </h1>
      <p className="mt-2 text-body-sm text-outline">Son güncelleme: 28 Temmuz 2026</p>

      <section className="mt-10 space-y-4 text-body-lg leading-relaxed">
        <p>
          NeuroDesk AI (&ldquo;uygulama&rdquo;, &ldquo;biz&rdquo;), kullanıcılarının görev, takvim,
          müşteri ilişkileri ve e-posta yönetimini tek bir yapay zeka destekli çalışma alanında
          toplayan bir üretkenlik uygulamasıdır. Bu sayfa, uygulamayı kullanırken hangi verilerin
          toplandığını, nasıl kullanıldığını ve nasıl kontrol edebileceğinizi açıklar.
        </p>
      </section>

      <section className="mt-10 space-y-3">
        <h2 className="text-headline-md text-on-background">Google/Gmail hesabınızı bağladığınızda</h2>
        <p className="text-body-lg leading-relaxed">
          Gmail hesabınızı bağlamayı seçtiğinizde, uygulama yalnızca Google&apos;ın{" "}
          <code className="rounded bg-surface-container px-1.5 py-0.5 text-body-sm">
            gmail.metadata
          </code>{" "}
          iznini talep eder. Bu izinle:
        </p>
        <ul className="list-disc space-y-2 pl-6 text-body-lg leading-relaxed">
          <li>Yalnızca mesaj başlıkları (gönderen, konu) ve kısa bir önizleme metni okunur.</li>
          <li>
            E-postalarınızın tam içeriği, gövdesi veya ekleri <strong>hiçbir zaman</strong> okunmaz
            ya da depolanmaz.
          </li>
          <li>Uygulama sizin adınıza e-posta gönderemez, silemez veya düzenleyemez.</li>
        </ul>
        <p className="text-body-lg leading-relaxed">
          Bu sınırlı veri, yalnızca gelen kutunuzu uygulama içinde görüntülemeniz ve yapay zeka
          asistanının (talebiniz üzerine) mesajlarınızı özetlemesi/önceliklendirmesi amacıyla
          kullanılır.
        </p>
      </section>

      <section className="mt-10 space-y-3">
        <h2 className="text-headline-md text-on-background">Yapay zeka işleme</h2>
        <p className="text-body-lg leading-relaxed">
          Yapay zeka asistanı özelliklerini (sohbet, özetleme, önceliklendirme) kullandığınızda,
          ilgili metin verisi bu isteği yanıtlamak amacıyla üçüncü taraf bir yapay zeka
          sağlayıcısına (OpenAI) iletilir. Bu veri, sağlayıcı tarafından genel amaçlı modelleri
          eğitmek için kullanılmaz.
        </p>
      </section>

      <section className="mt-10 space-y-3">
        <h2 className="text-headline-md text-on-background">Google kullanıcı verisi politikasına uyum</h2>
        <p className="text-body-lg leading-relaxed">
          NeuroDesk AI&apos;ın Google API&apos;lerinden aldığı ve kullandığı bilgilerin işlenmesi,
          Google API Hizmetleri Kullanıcı Verisi Politikası&apos;na (Limited Use şartları dahil)
          uygundur. Buna göre:
        </p>
        <ul className="list-disc space-y-2 pl-6 text-body-lg leading-relaxed">
          <li>Google hesap verileriniz reklam amacıyla kullanılmaz veya satılmaz.</li>
          <li>
            Verileriniz, açık onayınız, yasal bir zorunluluk ya da talep ettiğiniz özelliği sunmak
            dışında üçüncü taraflarla paylaşılmaz.
          </li>
          <li>İnsanlar tarafından okunması yalnızca sizin desteğiniz talep etmeniz halinde ve güvenlik/uyum amaçlı istisnalarda söz konusudur.</li>
        </ul>
      </section>

      <section className="mt-10 space-y-3">
        <h2 className="text-headline-md text-on-background">Saklama ve silme</h2>
        <p className="text-body-lg leading-relaxed">
          Erişim jetonlarınız (access/refresh token) veritabanında şifrelenmiş olarak saklanır.
          Ayarlar sayfasından Gmail veya Outlook bağlantınızı istediğiniz zaman kesebilirsiniz;
          bağlantı kesildiğinde ilgili jetonlar ve senkronize edilmiş mesaj kayıtları sistemden
          silinir. Hesabınızın tamamen silinmesini talep etmek için bizimle iletişime geçebilirsiniz.
        </p>
      </section>

      <section className="mt-10 space-y-3">
        <h2 className="text-headline-md text-on-background">Diğer bağlantılar (Outlook)</h2>
        <p className="text-body-lg leading-relaxed">
          Outlook/Microsoft hesabınızı bağladığınızda da aynı prensip geçerlidir: yalnızca mesaj
          başlıkları ve kısa önizleme okunur, tam içerik alınmaz.
        </p>
      </section>

      <section className="mt-10 space-y-3">
        <h2 className="text-headline-md text-on-background">Çocukların gizliliği</h2>
        <p className="text-body-lg leading-relaxed">
          NeuroDesk AI, 13 yaşın altındaki kullanıcılara yönelik değildir ve bu yaş grubundan
          bilerek veri toplamaz.
        </p>
      </section>

      <section className="mt-10 space-y-3">
        <h2 className="text-headline-md text-on-background">Bu politikadaki değişiklikler</h2>
        <p className="text-body-lg leading-relaxed">
          Bu sayfa güncellendiğinde en üstteki tarih değiştirilir. Önemli değişikliklerde
          uygulama içinden ayrıca bilgilendirme yapılır.
        </p>
      </section>

      <section className="mt-10 space-y-3">
        <h2 className="text-headline-md text-on-background">İletişim</h2>
        <p className="text-body-lg leading-relaxed">
          Gizlilik ile ilgili sorularınız veya hesap/veri silme talepleriniz için:{" "}
          <a href="mailto:bahaturk39@gmail.com" className="text-primary underline">
            bahaturk39@gmail.com
          </a>
        </p>
      </section>
    </main>
  );
}
