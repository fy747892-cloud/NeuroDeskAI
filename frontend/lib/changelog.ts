export type ChangelogEntry = {
  version: string;
  date: string;
  items: { tr: string; en: string }[];
};

export const CHANGELOG: ChangelogEntry[] = [
  {
    version: "2026.07.31",
    date: "2026-07-31",
    items: [
      {
        tr: "İki adımlı doğrulama (2FA) ve kurtarma kodları eklendi.",
        en: "Added two-factor authentication (2FA) with recovery codes.",
      },
      {
        tr: "Google ile giriş desteği eklendi.",
        en: "Added Sign in with Google.",
      },
      {
        tr: "Hesabını silme ve verilerini JSON olarak indirme eklendi.",
        en: "Added self-service account deletion and JSON data export.",
      },
      {
        tr: "Aktif oturumları görüntüleme ve uzaktan sonlandırma eklendi.",
        en: "Added active session viewing and remote sign-out.",
      },
      {
        tr: "Bildirimler (toast), sayfa geçiş çubuğu, iskelet yüklenme durumları ve hata takibi eklendi.",
        en: "Added toast notifications, a route progress bar, skeleton loading states, and error tracking.",
      },
      {
        tr: "Site geneline sayfa başlıkları, paylaşım kartları, favicon ve güvenlik başlıkları eklendi.",
        en: "Added page titles, share cards, favicons, and security headers site-wide.",
      },
    ],
  },
];

export const LATEST_CHANGELOG_VERSION = CHANGELOG[0]?.version ?? "";
