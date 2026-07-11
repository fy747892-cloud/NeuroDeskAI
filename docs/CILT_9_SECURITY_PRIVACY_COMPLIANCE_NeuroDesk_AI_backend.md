# CILT 9 - Security, Privacy & Compliance Documentation: NeuroDesk AI

Surum: 1.0  
Tarih: 09 Temmuz 2026  
Dil: Turkce  
Dokuman turu: Guvenlik, Gizlilik ve Uyumluluk Mimari Dokumani, Cilt 9  
Kapsam: Security by Design, Privacy by Design, kimlik dogrulama, yetkilendirme, multi-tenant izolasyon, veri guvenligi, AI guvenligi, KVKK/GDPR teknik gereksinimleri, audit, incident response, enterprise security, SOC 2 ve ISO 27001 hazirligi

> Not: Bu dokuman hukuki danismanlik degildir. KVKK, GDPR, SOC 2, ISO 27001 ve benzeri basliklar urun gereksinimi, teknik uyumluluk ve guvenlik mimarisi perspektifiyle ele alinmistir. Nihai hukuki metinler, acik riza formlari, aydinlatma metinleri, veri isleme sozlesmeleri ve kurum politikalari icin uzman hukuk danismanligi alinmalidir.

> Kod uretim notu: Bu cilt uygulama kodu, migration, frontend, backend veya mobil implementasyon icermez. Amac, NeuroDesk AI icin guvenlik, gizlilik ve uyumluluk mimarisini tanimlamaktir.

## Icindekiler

1. [Yonetici Ozeti](#1-yonetici-ozeti)
2. [Guvenlik Vizyonu](#2-guvenlik-vizyonu)
3. [Guvenlik Ilkeleri](#3-guvenlik-ilkeleri)
4. [Security by Design Yaklasimi](#4-security-by-design-yaklasimi)
5. [Privacy by Design Yaklasimi](#5-privacy-by-design-yaklasimi)
6. [Zero Trust Yaklasimi](#6-zero-trust-yaklasimi)
7. [Tehdit Modelleme Yaklasimi](#7-tehdit-modelleme-yaklasimi)
8. [Risk Siniflandirmasi](#8-risk-siniflandirmasi)
9. [Veri Siniflandirmasi](#9-veri-siniflandirmasi)
10. [Hassas Veri Envanteri](#10-hassas-veri-envanteri)
11. [Kisisel Veri Envanteri](#11-kisisel-veri-envanteri)
12. [Kimlik Dogrulama Guvenligi](#12-kimlik-dogrulama-guvenligi)
13. [JWT Guvenligi](#13-jwt-guvenligi)
14. [Refresh Token Guvenligi](#14-refresh-token-guvenligi)
15. [OAuth Guvenligi](#15-oauth-guvenligi)
16. [Sifre Guvenligi](#16-sifre-guvenligi)
17. [MFA / 2FA Stratejisi](#17-mfa--2fa-stratejisi)
18. [Oturum Guvenligi](#18-oturum-guvenligi)
19. [Cihaz Guvenligi](#19-cihaz-guvenligi)
20. [Yetkilendirme Guvenligi](#20-yetkilendirme-guvenligi)
21. [RBAC Tasarimi](#21-rbac-tasarimi)
22. [ABAC Stratejisi](#22-abac-stratejisi)
23. [Multi-Tenant Veri Izolasyonu](#23-multi-tenant-veri-izolasyonu)
24. [Tenant Escape Onleme](#24-tenant-escape-onleme)
25. [API Guvenligi](#25-api-guvenligi)
26. [Rate Limiting](#26-rate-limiting)
27. [Brute Force Korumasi](#27-brute-force-korumasi)
28. [Bot ve Abuse Prevention](#28-bot-ve-abuse-prevention)
29. [Input Validation Guvenligi](#29-input-validation-guvenligi)
30. [File Upload Guvenligi](#30-file-upload-guvenligi)
31. [Webhook Guvenligi](#31-webhook-guvenligi)
32. [Entegrasyon Guvenligi](#32-entegrasyon-guvenligi)
33. [OAuth Token Saklama Guvenligi](#33-oauth-token-saklama-guvenligi)
34. [Secret Management](#34-secret-management)
35. [Encryption at Rest](#35-encryption-at-rest)
36. [Encryption in Transit](#36-encryption-in-transit)
37. [Field-Level Encryption](#37-field-level-encryption)
38. [Key Management](#38-key-management)
39. [Backup Encryption](#39-backup-encryption)
40. [Log Guvenligi](#40-log-guvenligi)
41. [Audit Log Guvenligi](#41-audit-log-guvenligi)
42. [Admin Panel Guvenligi](#42-admin-panel-guvenligi)
43. [Super Admin Guvenligi](#43-super-admin-guvenligi)
44. [AI Guvenligi](#44-ai-guvenligi)
45. [Prompt Injection Korumasi](#45-prompt-injection-korumasi)
46. [AI Data Leakage Prevention](#46-ai-data-leakage-prevention)
47. [AI Action Approval Guvenligi](#47-ai-action-approval-guvenligi)
48. [AI Provider Guvenligi](#48-ai-provider-guvenligi)
49. [AI Prompt Logging Politikasi](#49-ai-prompt-logging-politikasi)
50. [AI Moderation ve Safety Katmani](#50-ai-moderation-ve-safety-katmani)
51. [Telefon Gorusmesi Guvenligi](#51-telefon-gorusmesi-guvenligi)
52. [E-posta Guvenligi](#52-e-posta-guvenligi)
53. [Takvim Guvenligi](#53-takvim-guvenligi)
54. [WhatsApp / Mesajlasma Entegrasyonu Guvenligi](#54-whatsapp--mesajlasma-entegrasyonu-guvenligi)
55. [Dosya ve Belge Guvenligi](#55-dosya-ve-belge-guvenligi)
56. [Bildirim Guvenligi](#56-bildirim-guvenligi)
57. [Mobil Uygulama Guvenligi](#57-mobil-uygulama-guvenligi)
58. [Web Uygulama Guvenligi](#58-web-uygulama-guvenligi)
59. [Backend Guvenligi](#59-backend-guvenligi)
60. [Database Guvenligi](#60-database-guvenligi)
61. [Cloud Security](#61-cloud-security)
62. [Network Security](#62-network-security)
63. [Container Security](#63-container-security)
64. [CI/CD Security](#64-cicd-security)
65. [Dependency Security](#65-dependency-security)
66. [Supply Chain Security](#66-supply-chain-security)
67. [Monitoring ve SIEM](#67-monitoring-ve-siem)
68. [Security Alerts](#68-security-alerts)
69. [Incident Response](#69-incident-response)
70. [Vulnerability Management](#70-vulnerability-management)
71. [Penetration Testing](#71-penetration-testing)
72. [Security Testing Strategy](#72-security-testing-strategy)
73. [OWASP Top 10 Kontrolleri](#73-owasp-top-10-kontrolleri)
74. [OWASP API Security Kontrolleri](#74-owasp-api-security-kontrolleri)
75. [OWASP LLM Top 10 Kontrolleri](#75-owasp-llm-top-10-kontrolleri)
76. [KVKK Uyumluluk Gereksinimleri](#76-kvkk-uyumluluk-gereksinimleri)
77. [GDPR Uyumluluk Gereksinimleri](#77-gdpr-uyumluluk-gereksinimleri)
78. [Acik Riza Yonetimi](#78-acik-riza-yonetimi)
79. [Aydinlatma Metni Gereksinimleri](#79-aydinlatma-metni-gereksinimleri)
80. [Veri Isleme Amaclari](#80-veri-isleme-amaclari)
81. [Veri Minimizasyonu](#81-veri-minimizasyonu)
82. [Veri Saklama Politikasi](#82-veri-saklama-politikasi)
83. [Veri Silme Politikasi](#83-veri-silme-politikasi)
84. [Veri Disa Aktarma Politikasi](#84-veri-disa-aktarma-politikasi)
85. [Veri Anonimlestirme](#85-veri-anonimlestirme)
86. [Veri Maskeleme](#86-veri-maskeleme)
87. [Data Processing Agreement Gereksinimleri](#87-data-processing-agreement-gereksinimleri)
88. [Enterprise Security](#88-enterprise-security)
89. [SSO Gereksinimleri](#89-sso-gereksinimleri)
90. [SAML / OIDC Gereksinimleri](#90-saml--oidc-gereksinimleri)
91. [SCIM Provisioning](#91-scim-provisioning)
92. [Audit Export](#92-audit-export)
93. [Customer Managed Keys](#93-customer-managed-keys)
94. [Dedicated Tenant Security](#94-dedicated-tenant-security)
95. [Private Deployment Security](#95-private-deployment-security)
96. [SOC 2 Hazirligi](#96-soc-2-hazirligi)
97. [ISO 27001 Hazirligi](#97-iso-27001-hazirligi)
98. [Guvenlik Politikalari](#98-guvenlik-politikalari)
99. [Guvenlik Kabul Kriterleri](#99-guvenlik-kabul-kriterleri)
100. [Risk Matrisi](#100-risk-matrisi)
101. [Codex Icin Guvenlik Gelistirme Talimatlari](#101-codex-icin-guvenlik-gelistirme-talimatlari)
102. [Codex Icin Sonraki Ciltlere Hazirlik Notlari](#102-codex-icin-sonraki-ciltlere-hazirlik-notlari)

# 1. Yonetici Ozeti

NeuroDesk AI; telefon gorusmeleri, e-postalar, takvim etkinlikleri, belgeler, notlar, resmi mesajlasma entegrasyonlari ve AI analiz sonuclari gibi son derece hassas verilerle calisir. Bu nedenle guvenlik ve gizlilik urune sonradan eklenecek bir "kontrol listesi" degil, mimarinin temel tasarim girdisidir. Urunun basarisi, kullanicinin is iletisimini ne kadar iyi anladigi kadar, bu iletisimi ne kadar guvenli isledigi ve kullanicinin kontrolunu ne kadar korudugu ile de olculmelidir.

Bu cilt, NeuroDesk AI icin guvenlik vizyonunu, tehdit modelini, veri siniflandirmasini, kimlik dogrulama ve yetkilendirme stratejisini, multi-tenant izolasyonu, AI guvenligini, KVKK/GDPR teknik gereksinimlerini ve enterprise guvenlik yeteneklerini tanimlar. MVP icin amac, temel saldiri yuzeylerini kapatmak, tenant izolasyonunu test edilebilir hale getirmek, hassas veri loglamasini engellemek, OAuth/token saklama risklerini azaltmak ve AI'nin kullanici onayi olmadan aksiyon almamasini garanti etmektir. Enterprise fazda SSO, SCIM, SIEM export, CMK, dedicated tenant, custom retention ve private deployment gibi gereksinimler devreye girer.

# 2. Guvenlik Vizyonu

NeuroDesk AI'nin guvenlik vizyonu "guvenilir AI calisma asistani" olmaktir. Sistem, kullanicinin is hayatina dair en ozel sinyalleri isler: kiminle ne konustugu, hangi musteriyle hangi konu uzerinde calistigi, hangi randevuya katildigi, hangi maili aldigi ve AI'nin bunlardan ne sonuc cikardigi. Bu veriler yalnizca teknik olarak degil, ticari ve itibari olarak da kritiktir.

Vizyonun ana eksenleri:

- Kullanici kontrolu: Veri kaynaklari kullanici acik onayi olmadan baglanmaz, analiz edilmez veya aksiyona donusturulmez.
- Tenant izolasyonu: Bir organizasyonun verisi baska bir organizasyon tarafindan gorulemez.
- Guvenli varsayilanlar: Public bucket, uzun omurlu token, genis OAuth scope, hassas log gibi riskli varsayilanlar kabul edilmez.
- Izlenebilirlik: Kritik islemler audit log ile geriye donuk incelenebilir.
- AI sorumlulugu: AI onerir, kullanici onaylar; AI kendi basina mail gondermez, takvim etkinligi olusturmaz veya gorev atamaz.

# 3. Guvenlik Ilkeleri

| Ilke | NeuroDesk AI yorumu | MVP gereksinimi | Enterprise genisleme |
|---|---|---|---|
| Least Privilege | Kullanici, servis, worker ve entegrasyonlar yalnizca ihtiyac duydugu yetkiye sahip olur. | Minimum OAuth scope, endpoint bazli RBAC | Just-in-time admin, privileged access workflow |
| Defense in Depth | Auth, authorization, validation, encryption, audit ve monitoring birlikte calisir. | API middleware + tenant guard + audit | WAF, SIEM, DLP, CASB entegrasyonu |
| Zero Trust | Hicbir istek varsayilan olarak guvenilir degildir. | Her istekte kimlik, tenant ve yetki kontrolu | Device posture, IP risk score, conditional access |
| Privacy by Design | Gizlilik mimari kararlarin parcasi olur. | Consent, retention, export/delete | Custom retention, data residency |
| Security by Default | Varsayilan ayarlar guvenlidir. | Public olmayan storage, secure token config | Organization policy enforcement |
| Human-in-the-Loop | AI aksiyonlari onay gerektirir. | Mail/takvim/gorev onay kapisi | Approval workflow, policy-based approvals |
| Tenant Isolation | Tenant baglami her katmanda zorunludur. | tenant_id guard ve testler | Dedicated DB/schema/cluster |
| Auditability | Kritik islemler kanitlanabilir olur. | Append-only audit log | SIEM export, immutable archive |
| Data Minimization | Gereksiz veri toplanmaz. | Minimum scope ve kisa saklama | Tenant bazli retention policy |
| Explicit Consent | Hassas kaynaklar acik izin ister. | Consent registry | Consent versioning ve enterprise raporlama |

# 4. Security by Design Yaklasimi

Security by Design, guvenlik kontrollerinin tasarim asamasinda karara baglanmasidir. NeuroDesk AI'da yeni bir modul tasarlanirken su sorular cevaplanmadan implementasyon baslamamalidir:

- Bu modul hangi veri siniflarini isliyor?
- Tenant baglami nereden geliyor ve nasil dogrulaniyor?
- Hangi kullanici rolleri hangi islemi yapabilir?
- Kritik islem audit log'a yaziliyor mu?
- Hassas veri log, metric, trace veya AI prompt icine siziyor mu?
- Hatali durumda kullaniciya ne kadar bilgi donuluyor?
- Bu modul icin abuse/rate limit ihtiyaci var mi?

MVP'de her backend endpoint icin authentication default zorunlu olmalidir; public endpointler ayrica gerekcelendirilmelidir. Her yeni veri modeli, veri sinifi ve retention karari olmadan kabul edilmemelidir. Her AI ozelligi icin prompt injection, data leakage ve unauthorized action riskleri tasarim incelemesinde ele alinmalidir.

# 5. Privacy by Design Yaklasimi

Privacy by Design, veri gizliliginin "sonradan yazilan politika" degil, urun davranisi olmasidir. NeuroDesk AI kullanici verisini sadece belirli, acik ve mesru amaclar icin islemelidir. Kullanici telefon, mail, takvim veya belge entegrasyonunu baglamadan once hangi verinin hangi amacla islenecegini anlamalidir.

Temel kararlar:

- Varsayilan olarak entegrasyon kapali gelir.
- Mail gonderme, takvim yazma ve ucuncu taraf AI'ye veri gonderme ayri riza gerektirir.
- Kullanicinin veri export ve veri silme talebi urun icinden baslatilabilir olmalidir.
- AI memory ozelligi acik ve yonetilebilir olmalidir; kullanici memory item silebilmelidir.
- Analytics ve product telemetry PII minimizasyonu ile tasarlanmalidir.

# 6. Zero Trust Yaklasimi

Zero Trust, sistem icinden gelen isteklerin de otomatik olarak guvenilir kabul edilmemesidir. NeuroDesk AI'da API, worker, admin panel, webhook ve entegrasyon callback'leri ayni prensiple dogrulanir: kimlik, yetki, tenant, kaynak sahibi ve islem baglami kontrol edilir.

Zero Trust kontrolleri:

- API istekleri: access token, token_type, tenant_id, role ve permission kontrolu.
- Worker isleri: job payload icindeki tenant_id server-side uretilmeli ve job calisirken tekrar dogrulanmalidir.
- Cache ve vector search: cache key ve retrieval filtresi tenant-aware olmalidir.
- Object storage: path prefix tenant ve resource owner bilgisiyle izole edilmelidir.
- Admin islemleri: step-up auth, MFA ve audit gerektirmelidir.

# 7. Tehdit Modelleme Yaklasimi

Tehdit modelleme STRIDE ve veri akisi bazli yapilmalidir. Her kritik akis icin varliklar, saldirgan profilleri, trust boundary, olasi tehditler ve azaltma kontrolleri belirlenir.

| Akis | Trust boundary | Temel tehditler | Ana kontroller |
|---|---|---|---|
| Login | Kullanici cihazi -> API | Brute force, credential stuffing, session hijack | Rate limit, MFA, password hash, audit |
| OAuth | NeuroDesk -> Google/Microsoft | Token theft, scope abuse, redirect hijack | PKCE, state, allowlist, encrypted token |
| Mail sync | Provider -> Worker -> DB | Mail body leak, over-collection | Scope minimization, consent, masking |
| AI analyze | Worker -> AI provider | Prompt injection, sensitive disclosure | Prompt firewall, minimization, redaction |
| Semantic search | API -> Vector DB | Cross-tenant retrieval | tenant_id filter, test, query guard |
| File upload | Client -> Storage -> Worker | Malware, oversized file, exfiltration | Allowlist, scanning, signed URL |
| Admin action | Admin panel -> API | Privilege abuse, account takeover | RBAC, MFA, audit, break-glass policy |

# 8. Risk Siniflandirmasi

Riskler etki ve olasilik matrisine gore siniflandirilir. Etki, kullanici verisi, tenant izolasyonu, servis surekliligi, yasal uyum, maliyet ve marka itibari uzerinden degerlendirilir.

| Seviye | Etki tanimi | Ornek |
|---|---|---|
| Low | Sinirli operasyonel etki, hassas veri yok | Tek kullanicinin basarisiz bildirim tercihi |
| Medium | Bir ozellik veya sinirli veri etkilenir | Tek kullanicinin hatali AI ozeti |
| High | Hassas veri, yetki, servis veya kurumsal musteri etkilenir | OAuth token leak, admin yetki hatasi |
| Critical | Cross-tenant veri sizintisi, genis veri ihlali, sistem kompromizasyonu | Tenant escape, production DB leak |

Critical riskler MVP'de ertelenemez. High riskler icin MVP'de en az azaltici kontrol ve izleme bulunmalidir. Medium riskler backlog'a alinabilir ancak kabul gerekcesi yazilmalidir.

# 9. Veri Siniflandirmasi

| Veri sinifi | Ornekler | Saklama yeri | Sifreleme | Erisim kisiti | Loglanabilir mi? | AI provider'a gonderilebilir mi? | Saklama ve silme |
|---|---|---|---|---|---|---|---|
| Public Data | Pazarlama sayfalari, yardim dokumanlari | CDN, public web | TLS yeterli | Herkese acik | Evet | Evet, gerekirse | Versiyonlu saklanir |
| Internal Data | Sistem loglari, metrikler, feature flag | Log store, monitoring | At rest + transit | Sadece ekip | PII yoksa evet | Hayir | 30-180 gun |
| Confidential Data | Kullanici profili, organizasyon, gorev, randevu | PostgreSQL | At rest + transit | Owner/Admin/ilgili kullanici | Maskeli | Riza ve amac varsa | Kullanici/tenant policy |
| Sensitive Personal Data | Mail body, transkript, takvim detaylari, notlar, belgeler | PostgreSQL, object storage, vector DB | At rest, transit, gerekirse field-level | En kucuk yetki | Hayir veya maskeli | Minimize/redact + riza | Kisa/orta sure, silinebilir |
| Highly Sensitive Data | OAuth token, refresh token, sifre hash, API key, encryption metadata | Vault/KMS/DB encrypted alan | Strong encryption + key rotation | Sistem servisi ve yetkili admin | Asla | Hayir | Expiry/revoke/hard delete |

# 10. Hassas Veri Envanteri

| Veri tipi | PII | Sifrelenmeli | Maskelenmeli | Loglanabilir | AI islemine gidebilir | Kullanici silebilir | Audit gerekir |
|---|---|---|---|---|---|---|---|
| Kullanici adi/e-posta/telefon | Evet | Evet | Evet | Maskeli | Profil baglami gerekiyorsa sinirli | Evet | Degisiklikte evet |
| Firma/organizasyon bilgisi | Evet olabilir | Evet | Gerektikce | Maskeli | Evet, tenant baglami ile | Yetkiye bagli | Evet |
| Kisi rehberi verisi | Evet | Evet | Evet | Hayir | Riza ile minimum | Evet | Evet |
| Telefon metadata/ses/transkript | Evet | Evet | Evet | Hayir | Riza ve redaction ile | Evet | Evet |
| Konusmaci ayrimi | Evet olabilir | Evet | Evet | Hayir | Evet, analiz icin | Evet | Evet |
| Mail subject/body/attachment | Evet | Evet | Evet | Hayir | Riza, scope ve redaction ile | Evet | Evet |
| Takvim basligi/aciklama/katilimci | Evet | Evet | Evet | Hayir | Riza ile | Evet | Evet |
| Gorev/randevu aciklamasi | Evet olabilir | Evet | Gerektikce | Maskeli | Evet | Evet | Degisiklikte |
| Kullanici notlari/belgeler | Evet olabilir | Evet | Evet | Hayir | Riza ile | Evet | Evet |
| AI ozetleri/entities/memory/chat | Evet olabilir | Evet | Evet | Hayir | AI sonucu oldugu icin ozellikle korunur | Evet | Evet |
| Embedding vektorleri | Dolayli PII | Evet | N/A | Hayir | Retrieval icin kullanilir | Evet | Evet |
| OAuth/refresh/API token | Cok hassas | Evet | Tam maske | Asla | Hayir | Revoke | Evet |
| IP/device/payment metadata | Evet olabilir | Evet | Evet | Maskeli | Hayir | Policy'ye bagli | Evet |

# 11. Kisisel Veri Envanteri

Kisisel veri envanteri, hangi verinin hangi amacla, hangi hukuki/sozlesmesel zeminde, hangi sureyle, hangi sistemlerde ve hangi taraflarla islendigini izler. NeuroDesk AI icin envanter dinamik tutulmalidir; yeni entegrasyon veya AI ozelligi eklendiginde veri envanteri guncellenmeden production'a cikilmamalidir.

Temel envanter alanlari:

- Veri kategorisi ve veri tipi
- Veri sahibi: kullanici, tenant calisani, musteri, gorusme taraflari
- Isleme amaci
- Saklama sistemi: DB, object storage, vector DB, log store, backup
- Ucuncu taraf aktarimi: AI provider, mail provider, calendar provider
- Saklama suresi
- Silme/anonimlestirme yontemi
- Riza veya sozlesme baglami
- Sorumlu ekip

# 12. Kimlik Dogrulama Guvenligi

Desteklenecek giris yontemleri e-posta + sifre, Google OAuth, Microsoft OAuth, Apple OAuth, enterprise fazda SSO ve ileri fazda MFA/2FA'dir. E-posta + sifre akisi MVP'de guvenli hash, e-posta dogrulama, progressive delay ve rate limit ile korunmalidir. OAuth login akislari authorization code + PKCE ile uygulanmalidir.

Login guvenlik kontrolleri:

- Failed login denemeleri IP, kullanici ve tenant bazli izlenir.
- Kullanici enumeration onlenir; hata mesajlari "kimlik bilgileri gecersiz" seviyesinde tutulur.
- Yeni cihaz veya supheli lokasyon girisleri kullaniciya bildirilir.
- Session ve refresh token listesi kullanici tarafindan gorulup kapatilabilir.
- Admin ve enterprise hesaplarda MFA zorunlu hale getirilebilir.

# 13. JWT Guvenligi

Access token kisa omurlu olmalidir; onerilen sure 10-30 dakikadir. JWT icinde hassas veri tutulmaz. Token claim'leri user_id, tenant_id, organization_id, roles, permissions versiyonu, token_type, issued_at ve expiration ile sinirli kalmalidir.

Algoritma secimi:

- MVP'de HS256 kullanilabilir, ancak secret KMS/Vault uzerinden yonetilmeli ve rotasyon planlanmalidir.
- Enterprise ve cok servisli mimaride RS256/JWKS daha uygundur; dogrulama yapan servisler private key'e erismeden public key ile verify eder.
- `alg=none`, zayif algoritma downgrade veya kid header injection riskleri test edilmelidir.

# 14. Refresh Token Guvenligi

Refresh token uzun omurlu olabilir ancak rotation zorunludur. Her refresh kullaniminda eski token gecersiz hale gelir ve yeni token uretilir. Eski token tekrar kullanilirsa reuse detection tetiklenmeli ve ilgili oturum ailesi revoke edilmelidir.

Kontroller:

- Refresh token DB'de duz metin saklanmaz; hashlenir veya field-level encrypted saklanir.
- Token, device/session kaydi ile iliskilendirilir.
- Logout, password change, MFA change ve entegrasyon revoke durumunda tokenlar gecersizlestirilir.
- Supheli reuse olaylari audit log'a ve security alert'e duser.

# 15. OAuth Guvenligi

Google, Microsoft, Apple, Gmail, Outlook, Google Calendar ve Outlook Calendar entegrasyonlarinda authorization code flow + PKCE kullanilmalidir. `state` parametresi zorunludur ve CSRF/replay riskini azaltmak icin kisa omurlu, tek kullanimlik ve server-side dogrulanir olmalidir.

OAuth kurallari:

- Redirect URI allowlist ile sinirlandirilir.
- Scope minimization uygulanir; mail okuma ve mail gonderme ayrilir.
- Calendar read ve write izinleri ayrilir.
- Tokenlar encrypted saklanir ve loglanmaz.
- Kullanici entegrasyonu istedigi zaman kaldirabilir.
- Consent, scope, provider, granted_at ve revoked_at audit kaydina yazilir.

# 16. Sifre Guvenligi

Sifreler asla plain text tutulmaz veya loglanmaz. Onerilen hash algoritmasi Argon2id'dir; alternatif olarak guvenli parametrelerle bcrypt kullanilabilir. Parametreler ortam kapasitesine gore benchmark ile secilmeli ve zaman icinde guncellenmelidir.

Politika:

- Minimum 12 karakter onerilir.
- Yaygin ve sizmis sifre kontrolu yapilmalidir.
- Password reset token kisa omurlu ve tek kullanimlik olmalidir.
- Reset akisi email enumeration yaratmamalidir.
- Enterprise fazda sifre gecmisi, zorunlu rotasyon yerine risk bazli politika ile degerlendirilmelidir.

# 17. MFA / 2FA Stratejisi

MVP'de MFA opsiyonel olabilir; admin ve super admin hesaplari icin erken fazda zorunlu hale getirilmesi onerilir. Enterprise'da MFA enforcement organizasyon politikasi olarak uygulanmalidir.

Desteklenecek yontemler:

- TOTP authenticator app
- WebAuthn/FIDO2, enterprise ve guvenlik olgunlugu icin
- Recovery code
- SSO provider MFA'sina guvenme, SAML/OIDC enterprise senaryolarinda

SMS tabanli MFA phishing ve SIM swap riskleri nedeniyle birincil yontem olmamalidir.

# 18. Oturum Guvenligi

Oturumlar kullanici, cihaz, IP ve user agent baglami ile izlenmelidir. Kullanici aktif oturumlarini gorebilmeli ve kapatabilmelidir. Supheli oturum davranisinda step-up auth veya revoke uygulanabilir.

Web icin token saklama karari uygulama mimarisine gore verilmelidir:

- HttpOnly Secure SameSite cookie XSS'e karsi avantaj saglar, ancak CSRF korumasi gerektirir.
- Memory + refresh akisi XSS etkisini azaltmak icin dikkatli uygulanmalidir.
- LocalStorage hassas token icin tercih edilmemelidir.

# 19. Cihaz Guvenligi

Cihaz bilgisi risk skoru icin kullanilabilir ancak fingerprinting gizlilik riskleri nedeniyle minimizasyonla uygulanmalidir. Mobil uygulamada tokenlar platform secure storage uzerinde saklanmalidir. Jailbreak/root tespiti enterprise policy icin opsiyonel kontrol olabilir; MVP'de kullaniciyi kilitlemek yerine risk sinyali olarak degerlendirilmelidir.

# 20. Yetkilendirme Guvenligi

Yetkilendirme kimlik dogrulamadan bagimsiz ve her istekte uygulanir. API endpoint'leri sadece "login oldu mu?" kontroluyle yetinmemeli; role, permission, tenant, resource owner ve data classification kontrolu yapmalidir.

Kurallar:

- Frontend'den gelen role veya tenant bilgisine guvenilmez.
- Server-side context, token ve DB iliskileriyle dogrulanir.
- Resource-level authorization zorunludur.
- Admin yetkileri en kucuk kapsamla verilir.

# 21. RBAC Tasarimi

| Rol | Yetki kapsami | Gorebilecegi veriler | Kritik kisitlar | Audit |
|---|---|---|---|---|
| Owner | Organizasyon tam yonetim | Tenant geneli | Super admin degildir | Evet |
| Admin | Kullanici/entegrasyon/ayar yonetimi | Yetkili tenant verisi | Billing/silme sinirlanabilir | Evet |
| Manager | Takim ve operasyon takibi | Takim kaynaklari | Sistem ayari yok | Evet |
| Member | Kendi calisma verisi | Kendi kaynaklari | Baska kullanici verisi yok | Degisiklikte |
| Viewer | Salt okunur | Paylasilan kaynaklar | Export/silme yok | Okuma audit opsiyonel |
| Billing Admin | Fatura/abonelik | Payment metadata | Icerik verisi yok | Evet |
| Support Admin | Destek islemleri | Minimum maskeli veri | Onay ve audit zorunlu | Evet |
| Super Admin | Platform yonetimi | Gerekirse tenantlar arasi | Break-glass, MFA, gerekce | Zorunlu |

Ornek permission set: `users.read`, `users.create`, `users.update`, `users.delete`, `organizations.manage`, `roles.manage`, `calls.read`, `calls.delete`, `emails.read`, `emails.analyze`, `emails.send`, `calendars.read`, `calendars.write`, `ai.analyze`, `ai.chat`, `ai.approve_action`, `tasks.manage`, `appointments.manage`, `contacts.manage`, `billing.manage`, `audit.read`, `admin.access`.

# 22. ABAC Stratejisi

ABAC, RBAC'in yetersiz kaldigi durumlarda attribute bazli karar verir. MVP'de RBAC + resource ownership yeterli olabilir; enterprise ve risk bazli erisimde ABAC devreye alinmalidir.

ABAC attribute'lari:

- `tenant_id`, `organization_id`, `team_id`, `user_id`, `resource_owner_id`
- `resource_sensitivity`, `data_classification`
- `device_trust_level`, `ip_risk_score`, `location_risk`
- `plan_type`, `enterprise_policy`
- `consent_status`, `integration_scope`

# 23. Multi-Tenant Veri Izolasyonu

MVP yaklasimi shared database + shared schema + `tenant_id` izolasyonudur. Bu model basit ve maliyet etkin olsa da tenant guard ve test zorunlulugunu artirir.

Kurallar:

- Tenant'a ait her tabloda `tenant_id` bulunmalidir.
- Sorgular tenant-scoped repository uzerinden calismalidir.
- `tenant_id` frontend parametresinden degil server-side auth context'ten belirlenir.
- Background job, cache, object storage ve vector search tenant-aware olmalidir.
- Cross-tenant admin erisimi sadece super admin ve gerekceli audit ile mumkundur.

# 24. Tenant Escape Onleme

Tenant escape riskleri:

- Eksik `tenant_id` filtresi
- Yanlis join
- Cache key icinde tenant yoklugu
- Vector search filtresiz calisma
- Object storage path izolasyonu eksikligi
- Background job tenant context kaybi
- Admin panelde genel sorgu hatasi

Azaltma kontrolleri:

- Tenant-aware repository ve middleware
- Query guard ve test helper
- Row Level Security degerlendirmesi
- Tenant-aware cache key standardi
- Vector search icin zorunlu tenant filter
- Object storage path: `tenant/{tenant_id}/...`
- Cross-tenant regression test suite

# 25. API Guvenligi

API default olarak authenticated olmalidir. Public endpointler register, login, password reset, OAuth callback, health check ve webhook gibi sinirli alanlarda kalmalidir.

Kontroller:

- HTTPS zorunlu
- Request validation ve response filtering
- RBAC + ABAC + tenant context
- Rate limit, pagination limit, request size limit
- CORS allowlist
- CSRF korumasi, cookie tabanli auth varsa
- Idempotency key, kritik write islemleri icin
- Error hardening: stack trace ve internal detay donmez

# 26. Rate Limiting

Rate limit IP, kullanici, tenant, endpoint, API key, plan ve AI kota bazinda uygulanmalidir. Edge katmani kaba bot/DDoS azaltma yapar; uygulama katmani is kuralina uygun ince taneli limit uygular.

Siki limit gereken endpointler: login, register, forgot password, reset password, OAuth callback, AI analyze, AI chat, file upload, email sync, calendar sync, webhook ve payment endpointleri.

# 27. Brute Force Korumasi

Brute force ve credential stuffing'e karsi progressive delay, IP/kullanici bazli limit, yaygin sifre kontrolu, e-posta dogrulama, supheli giris bildirimi ve gerekirse CAPTCHA uygulanir. Hesap kilitleme dikkatli tasarlanmalidir; saldirganin kurban hesaplari kilitlemesine izin vermemek icin progressive delay genellikle daha guvenlidir.

# 28. Bot ve Abuse Prevention

Abuse prevention yalnizca login icin degil, AI maliyeti ve veri export gibi pahali akislarda da gereklidir. AI chat ve analyze endpointleri tenant ve plan kotasina baglanmalidir. Anormal token tuketimi, cok sayida export talebi, webhook retry patlamasi ve file upload spike olaylari security alert uretmelidir.

# 29. Input Validation Guvenligi

Tum inputlar schema bazli dogrulanir. Serbest metin alanlari AI'ye gonderilmeden once boyut, format ve risk sinyalleri acisindan kontrol edilir. SQL/NoSQL injection, path traversal, SSRF, XSS ve command injection riskleri icin validation, escaping ve parameterized query zorunludur.

# 30. File Upload Guvenligi

Dosya yukleme hassas bir saldiri yuzeyidir. Allowlist MIME/extension, maksimum boyut, virus/malware scanning, content sniffing, file name normalization, signed URL ve private bucket zorunlu olmalidir. Dosyalar web root altinda tutulmamalidir. AI belge analizi icin dosya icerigi minimize edilmeli ve kullanici riza durumu kontrol edilmelidir.

# 31. Webhook Guvenligi

Webhook endpointleri signature validation olmadan veri kabul etmemelidir. Her provider icin HMAC veya provider-specific imza dogrulamasi, timestamp tolerance, replay prevention ve idempotency key uygulanmalidir. Payment webhook'lari ayrica event source verification ve audit gerektirir.

# 32. Entegrasyon Guvenligi

Gmail, Outlook, Calendar, mesajlasma ve diger entegrasyonlar scope minimization, consent, token encryption ve revocation kurallariyla yonetilir. Entegrasyon hatalari kullaniciya kontrollu mesajla doner; provider token veya raw response loglanmaz. Provider izinleri degistiginde yeniden riza gerekebilir.

# 33. OAuth Token Saklama Guvenligi

OAuth access ve refresh tokenlari highly sensitive data olarak siniflandirilir. Tokenlar field-level encrypted veya dedicated secret store uzerinde saklanmalidir. Token metadata'si ayrica tutulabilir ancak token degeri asla log, trace, analytics veya hata mesajina girmemelidir.

Token revoke akislari:

- Kullanici entegrasyonu kaldirir.
- Sifre veya MFA degisikligi risk sinyali uretir.
- Provider refresh token invalid doner.
- Security incident nedeniyle toplu revoke gerekir.

# 34. Secret Management

Secret'lar repo, image, client bundle veya log icinde bulunamaz. Development ve production secret'lari ayrilir. Production secret'lari Vault/KMS/managed secret manager ile yonetilir. Rotasyon periyodik ve olay bazli yapilir. `.env.example` yalnizca placeholder icerir.

# 35. Encryption at Rest

PostgreSQL, Redis persistence, object storage, backup ve log store at rest encryption kullanmalidir. Managed servislerde provider encryption varsayilanlari yeterli gorulmemeli; anahtar yonetimi, rotasyon ve access policy dokumante edilmelidir. Highly sensitive alanlar icin field-level encryption ayrica uygulanir.

# 36. Encryption in Transit

Tum dis trafik HTTPS/TLS uzerinden akar. Internal servis iletisiminde en azindan private network kullanilir; Kubernetes/enterprise fazda mTLS veya service mesh degerlendirilir. Provider API cagrilari TLS dogrulamasi kapatilmadan yapilir. Webhook callback URL'leri HTTPS olmak zorundadir.

# 37. Field-Level Encryption

OAuth token, refresh token, AI provider key, hassas entegrasyon credential'i, belirli belge metadata'lari ve enterprise musteri talebine gore mail/transkript alanlari field-level encrypted olabilir. Bu yontem DB leak etkisini azaltir ancak query ve indexing kabiliyetini sinirlar; bu nedenle alan bazli karar verilir.

# 38. Key Management

Anahtarlar KMS/Vault tarafindan uretilir, saklanir ve rotasyona tabi tutulur. Uygulama anahtari mumkunse memory'de kisa sure tutar; kalici config'e yazmaz. CMK enterprise fazda musteriye ozel anahtar yonetimi saglar. Anahtar erisimi audit log'a duser.

# 39. Backup Encryption

Backup'lar production verisinin kopyasidir ve ayni hassasiyetle korunur. Backup encryption, erisim kontrolu, retention, restore audit ve silme yayilimi gereklidir. Backup restore sonrasi silinmis kullanici verisinin geri gelmemesi icin tombstone veya post-restore deletion replay proseduru tanimlanmalidir.

# 40. Log Guvenligi

Loglar operasyon icin gereklidir ancak hassas veri sizintisinin yaygin kaynagidir. Loglarda sifre, token, mail body, transkript, belge icerigi, AI prompt raw data ve kisi listesi bulunmamalidir. Request ID, actor ID, tenant ID, endpoint, status, latency ve error code yeterlidir. PII gerekiyorsa maskelenir.

# 41. Audit Log Guvenligi

Audit log append-only olmalidir. Kritik alanlar: `actor_id`, `tenant_id`, `action`, `entity_type`, `entity_id`, `timestamp`, `ip_address` maskeli, `user_agent`, `request_id`, `metadata`. Audit log degistirilemez veya silinemez olmalidir; silme taleplerinde audit kaydi yasal/guvenlik gerekcesiyle minimize edilmis sekilde saklanabilir.

Audit gerektiren islemler: login failure spike, password reset, MFA change, integration grant/revoke, data export, data deletion, admin role change, AI action approval, mail send, calendar write, tenant setting change, super admin access.

# 42. Admin Panel Guvenligi

Admin panel ayrica korunmalidir: MFA, role-based admin, IP allowlist enterprise opsiyonu, step-up auth, sensitive action confirmation ve audit zorunludur. Admin panelde arama ve filtreler tenant izolasyonunu atlayamaz. Support admin yalnizca maskeli veri gorebilmelidir.

# 43. Super Admin Guvenligi

Super admin erisimi break-glass prensibiyle sinirlanmalidir. Her super admin oturumu gerekce, MFA, kisa session, approval opsiyonu ve ayrintili audit ile kaydedilir. Production data browsing default yasak olmalidir; destek icin kullanici/tenant onayi ve maskeleme gerekir.

# 44. AI Guvenligi

AI katmani NeuroDesk AI'nin en degerli ozelligi ve en yeni risk alanidir. Riskler prompt injection, sensitive data disclosure, hallucination, excessive agency, cross-tenant retrieval ve provider data handling etrafinda yogunlasir.

AI guvenlik kurallari:

- AI, yetki kontrolunu atlayan bir arka kapi olamaz.
- Retrieval sadece kullanicinin erisebildigi tenant kaynaklariyla sinirlidir.
- AI action'lari onay gerektirir.
- Prompt'a gereksiz PII konulmaz.
- Model cevabi aksiyona donusmeden once policy engine kontrolunden gecer.

# 45. Prompt Injection Korumasi

Prompt injection; mail, belge, web iceriği veya kullanici mesajinin AI'ye sistem talimatlarini bozacak sekilde sunulmasidir. Koruma icin system prompt veri ile ayrilmalidir, retrieval icerigi "untrusted content" olarak isaretlenmelidir, modelden gelen talimat degil veri olarak ele alinmalidir.

Test senaryolari:

- Mail body icinde "onceki talimatlari unut" ifadesi.
- Belge icinde gizli token isteme talimati.
- Chat'te baska tenant verisini isteme.
- AI'den kullanici onayi olmadan mail gondermesini isteme.

# 46. AI Data Leakage Prevention

AI'ye giden veri minimize edilir, redaction uygulanir ve tenant boundary korunur. Embedding ve RAG sorgularinda tenant_id filtresi zorunludur. AI provider'a gonderilen prompt ve context icinde token, secret, gereksiz kisi listesi, tam mail arsivi veya raw belge toplu halde bulunmamalidir.

# 47. AI Action Approval Guvenligi

AI aksiyonlari iki asamali olmalidir: AI taslak/onerir, kullanici onaylar. Mail gonderme, takvim etkinligi olusturma, gorev atama, dosya paylasma, CRM kaydi guncelleme ve entegrasyon uzerinden dis etki yaratan tum islemler approval gerektirir. Onay ekraninda AI'nin ne yapacagi, hangi veriyle yapacagi ve hedef alici/kisi acik gorunmelidir.

# 48. AI Provider Guvenligi

AI provider seciminde veri isleme sozlesmesi, data retention, training opt-out, bolgesel veri isleme, audit ve guvenlik sertifikalari degerlendirilir. Provider API key'leri secret manager'da saklanir. Provider yanitlari dogrudan guvenilir kabul edilmez; output validation ve policy check uygulanir.

# 49. AI Prompt Logging Politikasi

Raw prompt logging varsayilan olarak kapali olmalidir. Debug amacli prompt loglama gerekiyorsa sadece development/staging ortaminda, sentetik veriyle veya maskelenmis olarak yapilir. Production'da prompt/response loglama icin explicit debug flag, kisa retention, erisim kisiti ve PII redaction gerekir.

# 50. AI Moderation ve Safety Katmani

AI moderation; zararli istekleri, hassas veri ifsasini, policy disi aksiyonu ve yuksek riskli cevabi siniflandirir. NeuroDesk AI is odakli bir asistan oldugu icin moderation yalnizca genel icerik guvenligi degil, is verisi gizliligi ve yetki ihlali uzerine de kurulmalidir.

# 51. Telefon Gorusmesi Guvenligi

Telefon gorusmesi verisi cok hassastir. Metadata, ses dosyasi, transkript, konusmaci ayrimi, ozet ve cikarilan gorevler ayri veri tipleri olarak korunur. Gorusme kaydi ve isleme icin ilgili taraf bilgilendirmesi ve riza gereksinimleri hukuki danismanlikla netlestirilmelidir.

Teknik kontroller:

- Ses dosyalari private storage'da encrypted tutulur.
- Transkriptler tenant scoped ve silinebilir olur.
- STT/AI provider'a veri gonderimi riza ve minimizasyonla yapilir.
- Gorusme ozetleri ve extracted entities hassas veri kabul edilir.

# 52. E-posta Guvenligi

E-posta icerigi, konu, ekler ve alicilar hassas veri kabul edilir. Gmail/Outlook entegrasyonunda okuma ve gonderme scope'lari ayrilmalidir. AI e-postadan gorev veya randevu cikarabilir; ancak mail gonderemez veya yanitlayamaz, kullanici onayi gerekir.

Mail body raw hali loglanmaz. Attachment analizi file upload guvenligi ve belge guvenligi kontrollerine tabidir.

# 53. Takvim Guvenligi

Takvim basligi, aciklama, katilimcilar ve lokasyon PII ve ticari sir icerebilir. Calendar read ve write izinleri ayrilir. AI etkinlik onerisi sunar; kullanici onayi olmadan etkinlik olusturulmaz, guncellenmez veya silinmez. Katilimci listeleri maskelenmis loglanir veya loglanmaz.

# 54. WhatsApp / Mesajlasma Entegrasyonu Guvenligi

Mesajlasma entegrasyonlari yalnizca resmi API ve izinli kanallar uzerinden dusunulmelidir. Resmi olmayan scraping veya istemci otomasyonu guvenlik, gizlilik ve platform politikasi riski tasir. Mesaj icerikleri mail body ile ayni hassasiyette ele alinir; riza, minimizasyon ve provider sozlesmesi gerekir.

# 55. Dosya ve Belge Guvenligi

Belgeler is sozlesmeleri, teklif, fatura, kimlik, musteri verisi veya ticari sir icerebilir. Dosya icindeki metin AI analizine gonderilmeden once boyut, veri sinifi, riza ve tenant kontrolu yapilmalidir. Belgeler private bucket, signed URL, malware scan ve retention policy ile korunur.

# 56. Bildirim Guvenligi

Push, e-posta veya SMS bildirimlerinde hassas icerik minimum tutulur. Bildirim metni "Yeni gorev olustu" gibi genel ifade icermeli; mail body, transkript, musteri adi veya gizli detay lockscreen'de gorunmemelidir. Kullanici bildirim tercihlerini yonetebilmelidir.

# 57. Mobil Uygulama Guvenligi

Mobil uygulamada tokenlar secure storage'da tutulur. Deep link ve OAuth callback dogrulanir. Certificate pinning enterprise veya yuksek riskli deployment'larda degerlendirilebilir. Offline cache hassas veri icerecekse encrypted local storage ve clear-on-logout gerekir.

# 58. Web Uygulama Guvenligi

Web uygulamasi XSS, CSRF, clickjacking, token theft ve supply chain risklerine karsi korunur. CSP, secure cookie, dependency scanning, output encoding, trusted types degerlendirmesi, route-level authorization ve frontend'de hassas veri maskeleme gereklidir. Frontend yetki kontrolu UX icindir; asil kontrol backend'dedir.

# 59. Backend Guvenligi

Backend security middleware zinciri auth, tenant context, RBAC/ABAC, request validation, rate limit, audit ve error hardening adimlarini icermelidir. Repository katmani tenant-scoped olmalidir. Background worker'lar da API kadar guvenlik kontrolune tabidir.

# 60. Database Guvenligi

PostgreSQL private network'te, managed HA ve encrypted at rest ile calismalidir. DB kullanicilari least privilege ile ayrilir: app read/write, migration, analytics, readonly gibi roller. Production DB'ye dogrudan erisim sinirli, auditli ve gerekceli olmalidir. Pgvector/semantic search tenant filtresi olmadan calismamalidir.

# 61. Cloud Security

Cloud hesaplari MFA, least privilege IAM, environment separation, private networking, encrypted storage, security group hardening ve audit log ile korunur. Production ve staging ayrilmali; production verisi local ortama indirilmemelidir. Cloud access break-glass ve review surecine tabi olmalidir.

# 62. Network Security

Public yuzey Load Balancer/CDN/WAF ile sinirli tutulur. API ve worker private subnet'te calisir. Data katmani internete acik olmaz. Egress kurallari provider API'leri ve gerekli servislerle sinirlanir. Enterprise fazda VPN/private link ve IP allowlist degerlendirilir.

# 63. Container Security

Container image'lari minimal base image, non-root user, pinned dependency, image scanning ve immutable tag ile uretilir. Secret image icine gomulmez. Runtime'da read-only filesystem, seccomp/apparmor ve capability drop degerlendirilir. `latest` tag production'da kullanilmaz.

# 64. CI/CD Security

CI/CD pipeline secret scanning, dependency scanning, SAST, test, image scan ve manual approval adimlarini icermelidir. Production deploy yetkisi sinirli olmalidir. CI secret'lari pull request from fork gibi riskli baglamlarda aciga cikmamalidir. Artifact integrity ve commit SHA izlenebilirligi korunur.

# 65. Dependency Security

Node, Python ve Flutter paketleri vulnerability scan ile izlenir. Lockfile kullanilir. Kritik CVE'ler icin SLA tanimlanir: Critical 24-72 saat, High 7 gun, Medium sprint icinde. Kullanilmayan paketler kaldirilir. AI/ML SDK'lari ozellikle provider token handling acisindan incelenir.

# 66. Supply Chain Security

Supply chain riski kod, dependency, container image, CI action, third-party provider ve browser package kaynakli olabilir. Pinning, signature verification, trusted registry, GitHub branch protection, code review ve secret scanning zorunludur. Enterprise fazda SLSA/SBOM uretimi degerlendirilir.

# 67. Monitoring ve SIEM

Security monitoring login anomaly, token reuse, cross-tenant access attempt, high AI cost, large export, admin action, webhook signature failure, file malware detection ve provider error spike olaylarini izlemelidir. Enterprise musteriler icin SIEM export JSON/CEF veya webhook tabanli sunulabilir.

# 68. Security Alerts

Alert seviyeleri Low, Medium, High, Critical olarak ayrilir. Critical alert ornekleri: cross-tenant data access attempt, OAuth token leak suspicion, admin account compromise, production DB access anomaly, large data export anomaly, AI cost abuse spike, webhook signature bypass attempt.

Her critical alert'in sahibi, runbook'u ve escalation kanali olmalidir.

# 69. Incident Response

Incident response asamalari:

1. Detection: Alert, kullanici bildirimi veya provider uyarisi.
2. Triage: Kapsam, etki, veri sinifi ve tenant sayisi belirlenir.
3. Containment: Token revoke, hesap kilitleme, entegrasyon durdurma, deploy rollback.
4. Eradication: Kok neden giderilir.
5. Recovery: Sistem guvenli sekilde normale doner.
6. Communication: Ic ve dis iletisim yapilir; yasal bildirim gerekliligi hukukla degerlendirilir.
7. Postmortem: Aksiyon maddeleri ve kontrol iyilestirmeleri yazilir.

# 70. Vulnerability Management

Vulnerability management sureci asset inventory, scan, triage, risk rating, remediation, verification ve reporting adimlarini icerir. Kritik aciklar icin hotfix akisi bulunmalidir. False positive kararlar gerekceli kaydedilir. Third-party provider aciklari vendor risk surecine baglanir.

# 71. Penetration Testing

Penetrasyon testi MVP sonrasi, enterprise satis oncesi ve buyuk mimari degisikliklerde yapilmalidir. Kapsam: web, API, auth, tenant isolation, OAuth, file upload, webhook, admin panel, AI prompt injection, vector search ve cloud misconfiguration. Bulgular severity, exploitability ve veri etkisine gore onceliklendirilir.

# 72. Security Testing Strategy

| Test tipi | Amaç | Ne zaman |
|---|---|---|
| SAST | Kod guvenlik analizi | Her PR |
| DAST | Calisan uygulama testi | Staging |
| Dependency scan | Paket CVE kontrolu | Her PR ve planli |
| Container scan | Image guvenligi | Build asamasi |
| Secret scan | Repo/CI secret sizintisi | Her push |
| API security test | Auth, RBAC, tenant, rate limit | PR ve regression |
| AI security test | Prompt injection, data leakage, unauthorized action | AI ozelligi PR'lari |
| Mobile test | Token storage, local cache, deep link | Release oncesi |
| Cloud review | IAM, network, storage, backup | Production oncesi |

# 73. OWASP Top 10 Kontrolleri

| Risk | NeuroDesk AI ornegi | Kontrol | Test |
|---|---|---|---|
| Broken Access Control | Baska kullanicinin gorusmesini okuma | Resource + tenant authz | Cross-tenant test |
| Cryptographic Failures | OAuth token duz metin | Field encryption | DB dump review |
| Injection | Search/filter injection | Parameterized query, validation | Fuzz test |
| Insecure Design | AI onaysiz mail gonderir | Approval gate | Abuse test |
| Security Misconfiguration | Public bucket | IaC policy, review | Cloud scan |
| Vulnerable Components | Eski SDK | Dependency scan | CVE pipeline |
| Auth Failures | Zayif reset token | Short-lived one-time token | Auth test |
| Integrity Failures | CI artifact manipulation | Signed artifact, branch protection | Pipeline review |
| Logging Failures | Admin action loglanmaz | Audit coverage | Audit test |
| SSRF | URL fetch ozelligi | URL allowlist, metadata block | SSRF test |

# 74. OWASP API Security Kontrolleri

| Risk | Senaryo | Onleme | Test |
|---|---|---|---|
| BOLA | `/calls/{id}` ile baska tenant | Resource ownership check | IDOR test |
| Broken Authentication | Refresh reuse | Rotation + reuse detection | Token replay |
| BOPLA | Fazla property doner | Response DTO filtering | Contract test |
| Resource Consumption | AI chat maliyet patlamasi | Quota + rate limit | Load/abuse |
| Function Auth | Member admin endpoint cagirir | Permission middleware | Role test |
| Sensitive Flows | Toplu export abuse | Approval/rate/audit | Abuse scenario |
| SSRF | Webhook test URL fetch | Allowlist | SSRF payload |
| Misconfiguration | CORS wildcard | Allowlist | Security header test |
| Inventory | Eski API v1 acik | API inventory | Route scan |
| Unsafe APIs | Provider response'a guven | Validation + timeout | Provider mock |

# 75. OWASP LLM Top 10 Kontrolleri

| Risk | NeuroDesk AI karsiligi | Etki | Azaltma | Test |
|---|---|---|---|---|
| Prompt Injection | Mail icindeki kotu talimat | Veri sizintisi/yanlis aksiyon | Untrusted context, policy gate | Injection corpus |
| Insecure Output Handling | Model SQL/HTML uretir | XSS/injection | Output validation | Output fuzz |
| Training Data Poisoning | Bilgi kaynagi kirlenir | Yanlis cevap | Source trust, approval | Poison test |
| Model DoS | Uzun prompt/token spike | Maliyet/kesinti | Token limit, quota | Load test |
| Supply Chain | Riskli AI SDK | Token leak | SDK review | Dependency scan |
| Sensitive Disclosure | PII cevaba sizar | Gizlilik ihlali | Redaction, permission | Leakage test |
| Insecure Plugin Design | Tool yetki asimi | Yetkisiz aksiyon | Tool permission | Tool abuse |
| Excessive Agency | AI takvim/mail yapar | Is etkisi | Human approval | Action test |
| Overreliance | Hallucination karari | Yanlis is karari | Confidence, citations | Eval set |
| Model Theft | API key/model abuse | Maliyet/IP | Rate limit, secret mgmt | Abuse test |

# 76. KVKK Uyumluluk Gereksinimleri

Bu bolum hukuki danismanlik degildir. KVKK uyumu icin nihai degerlendirme hukuk danismani ile yapilmalidir. Teknik perspektiften NeuroDesk AI; kisisel veri isleme amaclarini acik tanimlamali, acik riza gerektiren kaynaklari ayirmali, aydinlatma metni gereksinimlerini urun akisi icinde desteklemeli, veri minimizasyonu ve saklama politikalarini uygulamalidir.

KVKK teknik gereksinimleri:

- Telefon gorusmesi, mail, takvim, contact ve belge isleme icin acik izin.
- Yurtdisina veri aktarimi riskinin AI/provider seciminde degerlendirilmesi.
- Kullanici haklari icin export, silme, duzeltme ve itiraz surecleri.
- Ucuncu taraf saglayici envanteri.
- Veri isleme kayitlari ve audit.

# 77. GDPR Uyumluluk Gereksinimleri

GDPR teknik gereksinimleri lawful basis, consent, legitimate interest degerlendirmesi, data subject rights, DPIA, DPA, subprocessor management, data residency, international transfer, breach notification ve records of processing activities etrafinda ele alinmalidir.

NeuroDesk AI icin DPIA onerilir; cunku sistem buyuk olcude iletisim verisi, otomatik analiz, AI profiling benzeri cikarimlar ve ucuncu taraf provider aktarimi icerebilir.

# 78. Acik Riza Yonetimi

Riza turleri: Terms of Service, Privacy Policy, AI analysis consent, telefon gorusmesi isleme, ses dosyasi isleme, mail erisim, takvim erisim, contact access, document analysis, third-party AI provider, marketing communication ve product analytics.

Consent kaydi alanlari: `user_id`, `tenant_id`, `consent_type`, `consent_version`, `granted`, `granted_at`, `revoked_at`, `source`, maskeli IP, `user_agent`, `policy_version`, `metadata`.

Riza geri cekildiginde ilgili veri isleme durmalidir.

# 79. Aydinlatma Metni Gereksinimleri

Aydinlatma metni kullanicinin hangi verisinin, hangi amacla, hangi sureyle, hangi ucuncu taraflarla ve hangi haklarla islendigini anlasilir sekilde aciklamalidir. Uygulama teknik olarak policy version takibi yapmali ve onemli degisikliklerde yeniden onay akisini desteklemelidir.

# 80. Veri Isleme Amaclari

Veri isleme amaclari urun fonksiyonlariyla sinirli olmalidir: gorusme transkripsiyonu, ozetleme, gorev/randevu cikarimi, mail/takvim analizi, hatirlatma, AI chat, semantic search, musteri hafizasi, guvenlik/audit ve faturalandirma. Amac disi kullanim yeni riza ve politika guncellemesi gerektirir.

# 81. Veri Minimizasyonu

Minimum scope, minimum retention, minimum prompt context ve minimum log ilkeleri uygulanir. Ornegin mail entegrasyonu tum mailbox'i indislemek yerine kullanici tarafindan secilen tarih araligi, label veya is hesabi kapsamiyla sinirlanabilir. AI prompt'u icin tum belge yerine ilgili parca gonderilir.

# 82. Veri Saklama Politikasi

| Veri | Varsayilan saklama | Kullanici silebilir | Enterprise policy | Not |
|---|---|---|---|---|
| Ses dosyasi | 30-90 gun | Evet | Evet | Kisa saklama onerilir |
| Transkript | Kullanici silene/policy'ye kadar | Evet | Evet | Hassas veri |
| Mail icerigi | Minimum gerekli sure | Evet | Evet | Analiz sonucu saklama opsiyonu |
| AI analizleri | Policy'ye kadar | Evet | Evet | Memory ayrica yonetilir |
| Audit log | 1-7 yil, ihtiyaca gore | Sinirli | Evet | Minimize edilmis tutulur |
| Notification log | 30-180 gun | Kismen | Evet | Hassas icerik icermemeli |
| Refresh token | Expiry + kisa guvenlik suresi | Revoke | Evet | Hash/encrypted |
| Backup | Backup retention kadar | Dolayli | Evet | Restore proseduru onemli |

# 83. Veri Silme Politikasi

Kullanici silme talebi dogrulanir, grace period uygulanabilir, entegrasyon tokenlari revoke edilir, object storage dosyalari silinir, vector embeddings silinir, AI memory ve analiz kayitlari silinir veya anonimlestirilir. Yasal saklama gereken audit/fatura verileri minimum ve maskeli tutulabilir.

# 84. Veri Disa Aktarma Politikasi

Export request kullanici tarafindan baslatilir. Sistem background job ile export uretir, signed URL ile sinirli sure indirilebilir hale getirir ve islemi audit log'a yazar. Export kapsaminda profil, gorev, randevu, gorusme metadata, transkript, AI ozetleri, kisiler, notlar, dosya metadata ve consent kayitlari bulunabilir.

# 85. Veri Anonimlestirme

Anonimlestirme geri dondurulemez olmalidir. Analytics ve product improvement icin kullanilan verilerde user_id, e-posta, telefon, musteri adi ve serbest metin PII kaldirilmalidir. Embedding anonimlestirmesi zordur; bu nedenle embedding'ler kisisel veri gibi ele alinmali veya silinmelidir.

# 86. Veri Maskeleme

Maskeleme log, admin panel, support ekranlari, audit export ve bildirimlerde uygulanir. Ornekler: e-posta `a***@domain.com`, telefon `+90 *** *** 12 34`, token `tok_****last4`. Maskeleme, erisim kontrolunun yerine gecmez; ek koruma katmanidir.

# 87. Data Processing Agreement Gereksinimleri

DPA; veri sorumlusu/veri isleyen rolleri, subprocessor listesi, veri isleme amaclari, guvenlik tedbirleri, veri iadesi/silme, incident bildirimi, uluslararasi aktarim ve audit haklarini kapsamalidir. Bu dokuman teknik gereksinimleri tanimlar; sozlesme dili hukuk ekibiyle hazirlanmalidir.

# 88. Enterprise Security

Enterprise ozellikleri: SSO, SAML/OIDC, SCIM, MFA enforcement, role-based admin, advanced audit, audit export, SIEM integration, dedicated tenant, dedicated database, dedicated encryption keys, CMK, custom retention, data residency, private deployment, IP allowlist, device posture, legal hold, DLP integration ve security questionnaire support.

# 89. SSO Gereksinimleri

SSO Azure AD/Microsoft Entra ID, Google Workspace, Okta, OneLogin ve benzeri IdP'leri desteklemelidir. Domain verification, forced SSO, JIT provisioning, role/group mapping, break-glass admin ve audit zorunludur.

# 90. SAML / OIDC Gereksinimleri

SAML icin metadata validation, signature validation, ACS URL allowlist, NameID/attribute mapping ve certificate rotation gerekir. OIDC icin discovery document, issuer/audience validation, nonce/state, PKCE ve JWKS cache kurallari uygulanir.

# 91. SCIM Provisioning

SCIM user provisioning, deprovisioning, group sync, role assignment ve suspended user handling saglar. Kullanici deprovision edildiginde oturumlar kapatilmali, tokenlar revoke edilmeli ve erisim aninda kesilmelidir.

# 92. Audit Export

Enterprise musteriler audit log'lari SIEM'e aktarabilmelidir. Export formatlari JSON, webhook, S3-compatible bucket veya syslog/CEF olabilir. Export edilen veriler maskeli ve tenant-scoped olmalidir. Export islemi de auditlenir.

# 93. Customer Managed Keys

CMK, musterinin kendi encryption key'ini yonetebilmesini saglar. CMK devre disi kalirsa ilgili tenant verisine erisim durabilir; bu nedenle operasyonel etkiler acik dokumante edilmelidir. Key rotation, revoke ve audit desteklenmelidir.

# 94. Dedicated Tenant Security

Dedicated tenant; buyuk musteriler icin ayrilmis database, schema, namespace, bucket veya cluster anlamina gelebilir. Hedef, blast radius'u azaltmak ve musteriye ozel compliance gereksinimlerini karsilamaktir. MVP icin gerekli degildir.

# 95. Private Deployment Security

Private deployment musteri VPC'si, private cloud veya on-prem benzeri ortamlarda calismayi ifade eder. Bu modelde secrets, logging, update, support access, telemetry ve incident response sorumluluklari sozlesmede netlesmelidir.

# 96. SOC 2 Hazirligi

SOC 2 hazirligi Trust Services Criteria ekseninde ele alinir:

- Security: access control, change management, vulnerability management, incident response, monitoring.
- Availability: backup, DR, uptime tracking, capacity planning.
- Confidentiality: data classification, encryption, secure deletion.
- Privacy: consent, data subject rights, retention, policy versioning.

Gerekli politika seti: Access Control, Information Security, Incident Response, Change Management, Vendor Management, Data Retention, Backup, Risk Management, Acceptable Use ve Business Continuity.

# 97. ISO 27001 Hazirligi

ISO 27001 icin ISMS kapsami, risk assessment, risk treatment plan, asset inventory, access control, cryptography, operations security, communications security, supplier relationships, incident management, business continuity ve compliance controls hazirlanmalidir. Bu cilt tam sertifikasyon paketi degil, teknik hazirlik cercevesidir.

# 98. Guvenlik Politikalari

Hazirlanmasi gereken politikalar:

- Information Security Policy: Genel guvenlik yonetimi.
- Access Control Policy: Hesap, rol, yetki ve review kurallari.
- Password Policy: Sifre ve reset gereksinimleri.
- Acceptable Use Policy: Sistem kullanim sinirlari.
- Incident Response Policy: Olay yonetimi.
- Data Retention Policy: Veri saklama ve silme.
- Data Classification Policy: Veri siniflari.
- Encryption Policy: Sifreleme ve key management.
- Backup Policy: Backup/restore.
- Vendor Management Policy: Ucuncu taraf riskleri.
- Vulnerability Management Policy: Acik yonetimi.
- Change Management Policy: Degisiklik kontrolu.
- Secure Development Policy: Guvenli gelistirme.
- AI Usage Policy: AI kullanim ve riza kurallari.
- Privacy Policy, Cookie Policy, Subprocessor Policy, Business Continuity Policy, Disaster Recovery Policy.

# 99. Guvenlik Kabul Kriterleri

MVP:

- Sifreler guvenli hashlenir.
- Access token kisa omurludur.
- Refresh token rotation ve reuse detection calisir.
- OAuth tokenlar encrypted saklanir.
- Tenant isolation testleri gecer.
- AI kullanici onayi olmadan aksiyon alamaz.
- Hassas veriler loglanmaz.
- Audit log kritik islemleri kaydeder.
- Public bucket kullanilmaz.
- Login, AI ve upload endpointlerinde rate limiting vardir.
- Consent kayitlari tutulur.
- Kullanici entegrasyonu kaldirabilir.
- Data export/delete talepleri desteklenir.
- Production secret'lar repo'da bulunmaz.

Enterprise:

- SSO, MFA enforcement, SCIM, SIEM export desteklenir.
- Audit export calisir.
- IP allowlist ve custom retention desteklenir.
- Dedicated tenant ve CMK opsiyonlari dokumante edilir.
- Security questionnaire icin standart cevap seti hazirdir.

# 100. Risk Matrisi

| ID | Risk | Aciklama | Etki | Olasilik | Seviye | Azaltma | Sorumlu | MVP |
|---|---|---|---|---|---|---|---|---|
| R-001 | Cross-tenant data leakage | Tenant verisi baska tenant'a sizar | Critical | Medium | Critical | Tenant guard, tests, RLS | Backend | Evet |
| R-002 | OAuth token leak | Provider tokeni ele gecirilir | Critical | Medium | Critical | Encryption, masking, revoke | Backend/Sec | Evet |
| R-003 | Refresh token reuse | Calinan refresh token kullanilir | High | Medium | High | Rotation, reuse detection | Backend | Evet |
| R-004 | Password brute force | Hesap ele gecirme denemesi | High | High | High | Rate limit, MFA | Backend | Evet |
| R-005 | Prompt injection | AI talimatlari manipule edilir | High | High | High | Prompt guard, tests | AI | Evet |
| R-006 | AI unauthorized action | AI onaysiz mail/takvim yapar | Critical | Medium | Critical | Approval gate | AI/Backend | Evet |
| R-007 | AI sensitive data leakage | Model PII ifsa eder | Critical | Medium | Critical | Redaction, authz | AI/Sec | Evet |
| R-008 | Vector search tenant leak | Retrieval tenant filtresiz calisir | Critical | Medium | Critical | Tenant filter, test | AI/Backend | Evet |
| R-009 | Mail body leak | Mail icerigi log/provider'da sizar | High | Medium | High | No raw logs, minimization | Backend | Evet |
| R-010 | Transcription leak | Ses/transkript sizar | High | Medium | High | Encryption, consent | Backend/AI | Evet |
| R-011 | Public storage bucket | Dosyalar public olur | Critical | Low | High | IaC policy, scan | DevOps | Evet |
| R-012 | File upload malware | Kotucul dosya yuklenir | High | Medium | High | Allowlist, scanning | Backend | Evet |
| R-013 | Webhook forgery | Sahte provider event'i | High | Medium | High | Signature validation | Backend | Evet |
| R-014 | Admin compromise | Admin hesabi ele gecirilir | Critical | Medium | Critical | MFA, audit, least privilege | Sec/Ops | Evet |
| R-015 | Excessive permission | Kullanici gereksiz yetkili | High | Medium | High | RBAC review | Backend | Evet |
| R-016 | Missing audit log | Kritik islem izlenemez | High | Medium | High | Audit coverage tests | Backend | Evet |
| R-017 | Backup leak | Backup verisi sizar | Critical | Low | High | Encryption, access control | DevOps | Evet |
| R-018 | Secret in repository | API key commit edilir | Critical | Medium | Critical | Secret scan | DevOps | Evet |
| R-019 | CI/CD compromise | Pipeline ile prod ele gecirilir | Critical | Low | High | Branch protection, OIDC | DevOps | Evet |
| R-020 | Dependency vulnerability | Paket acigi exploit edilir | High | High | High | Dependency scan | DevOps | Evet |
| R-021 | Container vulnerability | Image acigi | High | Medium | High | Image scan, minimal base | DevOps | Evet |
| R-022 | Payment webhook spoofing | Sahte odeme event'i | High | Medium | High | Signature + idempotency | Backend | Evet |
| R-023 | Data deletion failure | Silme talebi tam uygulanmaz | High | Medium | High | Deletion workflow | Backend/Privacy | Evet |
| R-024 | Consent missing | Rizasiz veri islenir | Critical | Medium | Critical | Consent gate | Product/Backend | Evet |
| R-025 | KVKK/GDPR non-compliance | Yasal/itibar riski | Critical | Medium | Critical | DPA, policies, audit | Legal/Sec | Evet |
| R-026 | Provider outage | AI/mail provider kesilir | Medium | High | Medium | Retry, fallback | DevOps/AI | Hayir |
| R-027 | AI cost abuse | Token maliyeti patlar | High | Medium | High | Quota, alerts | AI/Ops | Evet |
| R-028 | DDoS | Servis erisilemez | High | Medium | High | WAF/CDN/rate limit | DevOps | Evet |
| R-029 | Insider threat | Yetkili kisi veri kotuye kullanir | Critical | Low | High | Least privilege, audit | Sec/Ops | Evet |
| R-030 | Misconfigured CORS | Web veri sizintisi | High | Medium | High | Allowlist, tests | Frontend/Backend | Evet |
| R-031 | XSS token theft | Token calinir | High | Medium | High | CSP, HttpOnly, encoding | Frontend | Evet |

# 101. Codex Icin Guvenlik Gelistirme Talimatlari

Codex ileride NeuroDesk AI icin kod uretirken su kurallara uymalidir:

1. Security by default yaklasimi kullanilmalidir.
2. Hicbir secret kod icine yazilmamalidir.
3. `.env.example` icinde gercek secret bulunmamalidir.
4. Password hash icin Argon2id veya guvenli alternatif kullanilmalidir.
5. JWT access token kisa omurlu olmalidir.
6. Refresh token rotation uygulanmalidir.
7. OAuth tokenlar encrypted saklanmalidir.
8. Her tenant verisi `tenant_id` ile filtrelenmelidir.
9. Repository katmani tenant scoped olmalidir.
10. Vector search `tenant_id` filtresi olmadan calismamalidir.
11. AI action approval modeli zorunlu uygulanmalidir.
12. AI kullanici onayi olmadan mail gonderemez.
13. AI kullanici onayi olmadan takvim etkinligi olusturamaz.
14. AI kullanici onayi olmadan gorev atayamaz.
15. Hassas veri loglanmamalidir.
16. API hata mesajlari internal detay sizdirmamalidir.
17. File upload allowlist ile sinirlandirilmalidir.
18. Object storage bucket public olmamalidir.
19. Webhook endpointleri signature dogrulamalidir.
20. Rate limiting login, AI ve upload endpointlerinde uygulanmalidir.
21. Admin endpointleri ekstra yetki kontrolu yapmalidir.
22. Audit log kritik islemlerde zorunlu olmalidir.
23. Consent kontrolu yapilmadan telefon, mail veya takvim verisi islenmemelidir.
24. Kullanici veri silme ve export talepleri desteklenmelidir.
25. Sensitive data masking utility hazirlanmalidir.
26. Security testleri yazilmalidir.
27. Cross-tenant access testleri zorunludur.
28. Prompt injection testleri AI modulu icin eklenmelidir.
29. CI pipeline'da secret scanning ve dependency scanning olmalidir.
30. Kod uretirken OWASP kontrolleri dikkate alinmalidir.

# 102. Codex Icin Sonraki Ciltlere Hazirlik Notlari

Bir sonraki dokumanda Cilt 10 - DevOps & Deployment Documentation hazirlanacaktir. Cilt 10; Docker, Docker Compose, Kubernetes, CI/CD, GitHub Actions, environment strategy, cloud deployment, monitoring, logging, backup, disaster recovery, staging-production ayrimi, infrastructure as code, scaling, observability ve release yonetimi detaylarini icermelidir.

Not: Bu repository'de Cilt 8 zaten DevOps, Cloud & Infrastructure Architecture kapsaminda genis bir mimari cerceve sunmustur. Cilt 10 hazirlanirken Cilt 8 ile celismemeli; daha cok uygulama/kurulum runbook'u, deployment checklist'i, pipeline uygulama ayrintilari ve operasyonel el kitabi olarak konumlandirilmalidir.
