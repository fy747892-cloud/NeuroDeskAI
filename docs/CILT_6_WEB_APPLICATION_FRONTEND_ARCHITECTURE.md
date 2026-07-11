# CILT 6 — Web Application & Frontend Architecture Documentation: NeuroDesk AI

Sürüm: 1.0
Tarih: 09 Temmuz 2026
Dil: Türkçe
Doküman türü: Frontend Mimari ve Tasarım Dokümanı, Cilt 6
Kapsam: Frontend mimarisi, design system, sayfa/modül tasarımları, state/API katmanı, AI Chat ve AI Approval Center arayüzleri, admin panel, erişilebilirlik ve test stratejisi

> Not: Bu doküman frontend mimarisi ve ürün tasarım çerçevesidir; görsel kimlik/marka çalışmasının veya nihai piksel-hassas tasarımın yerine geçmez. Nihai renk/tipografi/ikon seti bir marka çalışmasıyla netleştirilmelidir.

> Süreklilik notu: Bu doküman CILT_1_PRD, CILT_2_SOFTWARE_ARCHITECTURE, CILT_3_DATABASE_DESIGN, CILT_4_BACKEND_DESIGN ve CILT_5_AI_ENGINE_DOCUMENTATION dokümanlarının devamıdır. Frontend teknoloji kararları (Next.js App Router, TypeScript, TanStack Query, Zustand, şema tabanlı form doğrulama) Cilt 2 §13 Frontend Web Mimarisi ile birebir uyumludur; bu ciltte Zod (şema doğrulama) ve Axios (typed API client'ın altındaki HTTP katmanı) olarak somutlaştırılmıştır. Tüm API çağrıları Cilt 4 §27 API Endpoint Kataloğu'ndaki gerçek endpoint yollarını referans alır; bu ciltte hiçbir yeni endpoint icat edilmemiş, yalnızca mevcut endpoint'lerin UI'da nasıl kullanılacağı tanımlanmıştır. AI Chat ve AI Approval Center arayüzleri Cilt 5 §47 (AI Chat), §51 (AI Action Approval) ve §52 (Confidence Score) ile birebir uyumludur.
>
> Sıra notu: Orijinal 15 cilt planında Cilt 5 sonunda "sıradaki cilt Mobile (Flutter)" olarak işaretlenmişti. Ürün sahibinin tercihiyle sıra değiştirilmiş, Web Application (orijinal plandaki Cilt 7) bu ciltte Cilt 6 olarak öne alınmıştır. Mobile (Flutter), bir sonraki ciltte işlenecektir. Bu, herhangi bir teknik karışıklığa yol açmaz; Cilt 2 §13 (Web) ve §14 (Mobil) mimarileri zaten birbirinden bağımsız tanımlanmıştır.

## İçindekiler

1. [Executive Summary](#1-executive-summary)
2. [Frontend Vision](#2-frontend-vision)
3. [Design Philosophy](#3-design-philosophy)
4. [UX Principles](#4-ux-principles)
5. [UI Principles](#5-ui-principles)
6. [Design System](#6-design-system)
7. [Theme System](#7-theme-system)
8. [Typography](#8-typography)
9. [Color Tokens](#9-color-tokens)
10. [Icon System](#10-icon-system)
11. [Layout System](#11-layout-system)
12. [Responsive Design](#12-responsive-design)
13. [Accessibility](#13-accessibility)
14. [Component Library](#14-component-library)
15. [Routing](#15-routing)
16. [Authentication Flow](#16-authentication-flow)
17. [Protected Routes](#17-protected-routes)
18. [API Layer](#18-api-layer)
19. [State Management](#19-state-management)
20. [Error Handling](#20-error-handling)
21. [Notifications](#21-notifications)
22. [Global Search](#22-global-search)
23. [AI Chat Interface](#23-ai-chat-interface)
24. [Dashboard](#24-dashboard)
25. [Calls Module](#25-calls-module)
26. [Conversations Module](#26-conversations-module)
27. [Tasks Module](#27-tasks-module)
28. [Calendar Module](#28-calendar-module)
29. [Appointment Module](#29-appointment-module)
30. [Email Module](#30-email-module)
31. [Contacts CRM Module](#31-contacts-crm-module)
32. [Timeline Module](#32-timeline-module)
33. [Document Module](#33-document-module)
34. [Analytics Module](#34-analytics-module)
35. [AI Suggestions](#35-ai-suggestions)
36. [AI Approval Center](#36-ai-approval-center)
37. [Notification Center](#37-notification-center)
38. [User Settings](#38-user-settings)
39. [Organization Settings](#39-organization-settings)
40. [Billing](#40-billing)
41. [Admin Panel](#41-admin-panel)
42. [Super Admin](#42-super-admin)
43. [Feature Flags](#43-feature-flags)
44. [File Upload UI](#44-file-upload-ui)
45. [Data Export](#45-data-export)
46. [GDPR Screens](#46-gdpr-screens)
47. [Loading States](#47-loading-states)
48. [Empty States](#48-empty-states)
49. [Skeleton Screens](#49-skeleton-screens)
50. [Charts](#50-charts)
51. [Tables](#51-tables)
52. [Forms](#52-forms)
53. [Modals](#53-modals)
54. [Drawers](#54-drawers)
55. [Toasts](#55-toasts)
56. [Keyboard Shortcuts](#56-keyboard-shortcuts)
57. [Internationalization](#57-internationalization)
58. [Offline Support](#58-offline-support)
59. [Performance](#59-performance)
60. [Security](#60-security)
61. [Testing Strategy](#61-testing-strategy)
62. [Storybook](#62-storybook)
63. [Component Documentation](#63-component-documentation)
64. [Future UI](#64-future-ui)
65. [Enterprise Features](#65-enterprise-features)
66. [Uygulama Rehberi](#66-uygulama-rehberi)
67. [Sayfa Kataloğu](#sayfa-kataloğu)
68. [Sonraki Cilt İçin Hazırlık Notları](#sonraki-cilt-için-hazırlık-notları)
69. [Sonraki Adım](#sonraki-adım)

# 1. Executive Summary

NeuroDesk AI web uygulaması, ürünün birincil çalışma yüzeyidir: Cilt 1'de tanımlanan tüm modülleri (görüşme, görev, randevu/takvim, mail, kişi/CRM, AI Chat, dashboard) masaüstü öncelikli, tablet ve mobil web'de kullanılabilir tek bir Next.js uygulamasında birleştirir. Frontend, Cilt 4'te tanımlanan backend API sözleşmelerini birebir tüketir; hiçbir iş kuralı (yetki, onay, veri doğrulama) yalnızca frontend'de uygulanmaz — UI, backend'in zaten uyguladığı kuralları kullanıcı deneyimi için yansıtır (Cilt 2 §13 "Role-based UI rendering backend yetkilendirmesinin yerine geçmemeli" ilkesiyle birebir).

Bu cildin stratejik önceliği, MVP kapsamındaki (Cilt 1 §11.2) modüllerin üretim kalitesinde tasarlanması; Billing, gelişmiş Admin, Roller/İzinler gibi ileri faz modüllerinin ise iskelet düzeyinde (route + boş state) planlanmasıdır. AI Chat ve AI Approval Center, ürünün farklılaşan değerini taşıdığı için (Cilt 1 §9 Değer Önerisi) en yüksek tasarım özeniyle ele alınmıştır.

# 2. Frontend Vision

Frontend vizyonu, kullanıcının "AI'a güvenerek hız kazanma" ile "her aksiyonu kontrol altında tutma" ihtiyaçları arasında sürtünmesiz bir denge kurmaktır. Arayüz, AI çıktılarını asla "gerçek" gibi sunmaz; her zaman öneri, kaynak ve güven düzeyiyle birlikte gösterir (Cilt 5 §54 AI Safety ile birebir). Vizyonun ikinci ayağı, dağınık modüllerin (görüşme, mail, takvim, görev, kişi) tek bir tutarlı gezinme ve tasarım dili altında hissedilmesidir — kullanıcı "beş ayrı araç" değil "tek bir çalışma masası" kullandığını hissetmelidir.

# 3. Design Philosophy

- Netlik, süsten önce gelir: yoğun bilgi (görüşme özeti, AI önerisi, timeline) her zaman taranabilir hiyerarşiyle sunulur.
- Güven görünür kılınır: AI çıktısı olan her yüzeyde kaynak ve confidence göstergesi bulunur (Cilt 5 §51-52).
- Geri alınabilirlik: kritik olmayan hiçbir aksiyon "emin misiniz" diyaloğu gerektirmez, ama AI onayları (Bölüm 36) her zaman açık bir onay adımından geçer.
- Tutarlılık, yaratıcılıktan önce gelir: her modül aynı Design System bileşenlerini (Bölüm 6, 14) kullanır, modül bazlı özel bileşen icadı istisnadır.

# 4. UX Principles

1. Kullanıcı hiçbir zaman "AI ne yaptı, ben ne yaptım" konusunda kafası karışık kalmamalı.
2. Her liste ekranı (görevler, randevular, kişiler) filtre, arama ve boş durum içermeli.
3. Kritik bilgi (geciken görev, düşük confidence'lı öneri) görsel önceliklendirmeyle (renk, konum) öne çıkarılmalı, ama alarm yorgunluğu yaratacak kadar abartılmamalı.
4. Form akışları (görev/randevu oluşturma) 3 adımdan fazla sürmemeli; AI önerisinden gelen veriler önceden doldurulmuş (pre-filled) olmalı.
5. Mobil web'de hiçbir kritik aksiyon (AI onaylama, görev tamamlama) yalnızca masaüstünde çalışacak şekilde tasarlanmamalı.

# 5. UI Principles

- 8px grid sistemi tüm spacing kararlarının temelidir.
- Etkileşimli her bileşen (buton, kart, satır) hover/focus/active/disabled durumlarının tümünü tanımlar.
- Birincil aksiyon (CTA) her ekranda görsel olarak tektir; ikincil aksiyonlar daha düşük vurguyla gösterilir.
- Renk tek başına anlam taşımaz (erişilebilirlik, Bölüm 13); durum göstergeleri her zaman ikon veya metinle desteklenir.

# 6. Design System

Design System, Shadcn UI bileşen setinin NeuroDesk AI marka tokenlarıyla (Bölüm 7-10) özelleştirilmiş halidir. Shadcn UI'ın tercih edilme nedeni, kaynak kodun projeye kopyalanması (headless + Radix UI tabanlı) sayesinde tam kontrol ve Tailwind CSS ile doğal entegrasyondur — harici bir component kütüphanesine "kara kutu" bağımlılık oluşturulmaz. Design System üç katmandan oluşur: **Token katmanı** (Bölüm 7-10, ham değerler), **Primitive katmanı** (Bölüm 14, Button/Input/Card gibi temel bileşenler), **Pattern katmanı** (AI Suggestion Card, Approval Card gibi ürüne özgü bileşik bileşenler, Bölüm 14.2).

# 7. Theme System

Dark Mode zorunlu bir gereksinimdir (proje kapsamı). Tema, CSS custom property tabanlı token sistemiyle uygulanır; her renk tokenı (Bölüm 9) hem light hem dark değerine sahiptir, bileşenler hardcoded renk kullanmaz. Tema tercihi: sistem tercihi (varsayılan) → kullanıcı override (User Settings, Bölüm 38) → local storage'da kalıcı. Tema geçişi anlık olur, sayfa yenilenmesi gerekmez.

# 8. Typography

| Rol | Kullanım | Not |
|---|---|---|
| Display | Dashboard büyük sayılar, boş durum başlıkları | Sade, tek ağırlık |
| Heading (H1-H4) | Sayfa/bölüm başlıkları | Kademeli ölçek (1.25 oranı) |
| Body | Genel metin, form etiketleri | Türkçe karakter desteği (ğ, ş, ı, ö, ü, ç) zorunlu test kriteri |
| Caption | Zaman damgası, meta bilgi, confidence etiketi | Düşük kontrast, ikincil bilgi için |
| Mono | Kod/ID gösterimi (approval_id, job_id) admin ekranlarında | Yalnızca admin/debug yüzeylerinde |

Nihai font ailesi marka çalışmasıyla belirlenecektir; bu doküman yalnızca rol/ölçek sistemini tanımlar.

# 9. Color Tokens

Renk tokenları semantik isimlendirilir (`primary`, `success`, `warning`, `destructive`, `muted`), ham hex değer component kodunda kullanılmaz. AI'a özgü ek semantik tokenlar tanımlanır: `ai-suggestion` (AI önerisi vurgusu), `ai-confidence-high/medium/low` (Cilt 5 §52 confidence eşikleriyle hizalı üç kademeli renk), `ai-pending` (onay bekleyen durum). Bu tokenlar hem light hem dark temada WCAG AA kontrast oranını (Bölüm 13) sağlayacak şekilde ayrı ayrı kalibre edilir.

# 10. Icon System

İkon seti tutarlı bir tek kaynaktan (outline stil, 24px grid) seçilir. AI'a özgü aksiyonlar (öner, onayla, reddet, düzenle) için sabit ikon eşlemesi tanımlanır ve tüm modüllerde (Approval Center, AI Chat, Dashboard) aynı ikon kullanılır — kullanıcı "onay" ikonunu bir kez öğrenir, her yerde tanır.

# 11. Layout System

Üç ana layout: **Auth Layout** (ortalanmış kart, minimal gezinme — Login/Register/Forgot Password), **App Layout** (sol sabit sidebar + üst bar + içerik alanı + sağ opsiyonel panel — AI Chat ve Approval Center gibi ekranlarda sağ panel kullanılır), **Admin Layout** (App Layout'un admin'e özgü sidebar varyantı, Cilt 2 §15 "iki seviyeli admin" ayrımını yansıtır: platform admin ve organizasyon admin farklı sidebar setleriyle çalışır).

Sidebar birincil gezinme: Dashboard, AI Chat, Görüşmeler, Görevler, Takvim, Kişiler/CRM, Mailler (MVP dışıysa gizli/flag'li), Onay Merkezi (rozet ile bekleyen sayı), Analitik, Ayarlar.

# 12. Responsive Design

| Kırılım | Genişlik | Davranış |
|---|---|---|
| Desktop | ≥1280px | Tam sidebar, çok kolonlu layout, sağ panel açık |
| Laptop | 1024-1279px | Sidebar daraltılabilir (icon-only), sağ panel isteğe bağlı kapanır |
| Tablet | 768-1023px | Sidebar drawer'a döner, tablo görünümleri kart görünümüne düşebilir |
| Mobil Web | <768px | Alt tab bar navigasyon, tek kolon, modaller tam ekran drawer'a döner |

Tasarım desktop öncelikli üretilir (proje kapsamı gereği) ancak her bileşen mobil web'de de fonksiyonel kalmalıdır; "mobil web'de devre dışı" bir özellik yoktur, yalnızca yoğunluk azaltılır.

# 13. Accessibility

- WCAG 2.1 AA hedeflenir: kontrast oranları (metin 4.5:1, büyük metin 3:1), klavye ile tam gezinebilirlik, görünür focus ring.
- Tüm etkileşimli bileşenler ARIA rolleriyle işaretlenir; özellikle Approval Card (Bölüm 36) ve AI Chat mesaj listesi (Bölüm 23) `aria-live` bölgeleriyle ekran okuyucuya yeni içerik geldiğini bildirir.
- Renk körlüğü: confidence göstergesi (Bölüm 9) renk + ikon + metin etiketiyle birlikte sunulur, yalnızca renkle anlam taşınmaz.
- Form hataları (Bölüm 52) alanla `aria-describedby` ile ilişkilendirilir, yalnızca renkle değil metinle de gösterilir.
- Bu bölüm Cilt 1 §16 Non-Functional Requirements'taki erişilebilirlik maddesiyle uyumludur.

# 14. Component Library

## 14.1 Primitive Bileşenler (Shadcn UI tabanlı)

| Bileşen | Varyantlar | Not |
|---|---|---|
| Button | primary, secondary, ghost, destructive, icon | Loading durumu spinner ile |
| Input | text, password, search, with-icon | Zod hata mesajıyla entegre |
| Textarea | resizable, auto-grow | AI Chat prompt kutusunda auto-grow |
| Select / Dropdown | single, multi, searchable | Kişi/etiket seçiminde searchable |
| Tooltip | hover, focus-triggered | Confidence açıklaması için kullanılır |
| Popover | click-triggered | Hızlı filtre panelleri |
| Dialog (Modal) | Bölüm 53 | Onay/red işlemleri için |
| Alert | info, warning, destructive, success | Sistem/AI hata mesajları |
| Badge | status, count | Onay merkezi rozet sayacı |
| Avatar | user, contact, org | Fallback: baş harfler |
| Card | default, interactive | AI Suggestion Card'ın temel taşıyıcısı |
| Accordion | Sıkça sorulan/detay gizleme | Görüşme detayında ham transkript gizleme |
| Tabs | Sayfa içi bölüm geçişleri | Kişi detayında Timeline/Görevler/Notlar sekmeleri |
| Table | Bölüm 51 | |
| Pagination | offset, cursor | Liste ekranlarında |
| Calendar | Bölüm 28 | FullCalendar entegrasyonu |
| Timeline | Bölüm 32 | |

## 14.2 Ürüne Özgü Pattern Bileşenler

| Bileşen | Amaç | İlgili modül |
|---|---|---|
| AI Suggestion Card | AI'ın ürettiği öneriyi kaynak + confidence ile göstermek | Dashboard, Approval Center (Bölüm 35-36) |
| Notification Card | Bildirim listesi öğesi | Notification Center (Bölüm 37) |
| Approval Card | Onay/red/düzenle aksiyonlu AI önerisi kartı | AI Approval Center (Bölüm 36) |
| Confidence Badge | Düşük/orta/yüksek güven göstergesi | Her AI çıktısı yüzeyi |
| Source Chip | RAG kaynağına tıklanabilir referans | AI Chat (Bölüm 23) |
| Contact Mini Card | Kişi hover/inline önizlemesi | CRM, Timeline (Bölüm 31-32) |

# 15. Routing

Next.js App Router, route grupları ile organize edilir: `(auth)` — Login/Register/Forgot Password, `(app)` — kimlik doğrulanmış tüm ana modüller, `(admin)` — admin/super admin ekranları. Her route grubu kendi layout'unu (Bölüm 11) taşır. Dinamik route'lar (`/contacts/[contactId]`, `/tasks/[taskId]`, `/conversations/[conversationId]`) backend'deki path parametreleriyle (Cilt 4 §27) birebir eşleşir.

# 16. Authentication Flow

## 16.1 Login

| Alan | Detay |
|---|---|
| Amaç | Kullanıcının e-posta/şifre veya OAuth ile oturum açması |
| Wireframe | Ortalanmış kart: logo, e-posta, şifre, "Google ile giriş" butonu, "şifremi unuttum" linki, "kayıt ol" linki |
| Bileşenler | Input(e-posta), Input(şifre), Button(primary), Button(oauth) |
| API bağlantıları | POST /api/v1/auth/login, GET /api/v1/auth/oauth/google/start |
| Loading | Buton spinner, form disabled |
| Error | 401 → "e-posta veya şifre hatalı" (Alert, alan bazlı değil genel — kullanıcı numarasını sızdırmamak için) |
| Permission | Public |
| Responsive | Mobilde kart tam genişlik, logo küçülür |
| Accessibility | Form `aria-label`, hata Alert `role=alert` |

## 16.2 Register

| Alan | Detay |
|---|---|
| Amaç | Yeni hesap oluşturma |
| Wireframe | Login ile aynı düzen + ad/soyad alanı + KVKK/kullanım şartları onay kutusu |
| Bileşenler | Input × 4, Checkbox(rıza), Button |
| API bağlantıları | POST /api/v1/auth/register, POST /api/v1/auth/email/verify (kayıt sonrası) |
| Loading/Error | Login ile aynı desen; şifre gücü göstergesi client-side, zorunluluk backend'de |
| Permission | Public |
| Responsive/Accessibility | Login ile aynı |

## 16.3 Forgot Password

| Alan | Detay |
|---|---|
| Amaç | Şifre sıfırlama akışı başlatma ve tamamlama |
| Wireframe | İki adım: e-posta girme ekranı → "bağlantı gönderildi" onay ekranı → (e-posta linkinden) yeni şifre belirleme ekranı |
| Bileşenler | Input, Button, Alert(info) |
| API bağlantıları | POST /api/v1/auth/password-reset/request, POST /api/v1/auth/password-reset/confirm |
| Loading/Error | Standart; e-posta bulunamasa bile "eğer kayıtlıysa bağlantı gönderildi" mesajı (enumeration koruması) |
| Permission | Public / Public token (confirm adımı) |

# 17. Protected Routes

`(app)` ve `(admin)` route grupları middleware seviyesinde korunur: geçerli access token yoksa `(auth)`'a yönlendirilir. Rol bazlı sayfa erişimi (örn. Admin Panel yalnızca `admin` rolüne) route middleware'de kontrol edilir, ancak bu yalnızca UX kısayoludur — gerçek yetki kontrolü her zaman backend'de tekrar doğrulanır (Cilt 2 §17 Authorization ile birebir, "Role-based UI rendering yetkilendirmenin yerine geçmez" ilkesi). Token yenileme (`/api/v1/auth/refresh`) sessiz arka plan mekanizmasıyla, kullanıcı deneyimini kesmeden yapılır.

# 18. API Layer

API katmanı iki alt katmandan oluşur: **HTTP katmanı** (Axios instance; base URL, `Authorization` header enjeksiyonu, 401'de otomatik refresh-and-retry, request ID üretimi Cilt 2 §16 Gateway ile uyumlu) ve **Query katmanı** (TanStack Query; her domain için ayrı query key namespace — `['tasks']`, `['contacts', contactId]`, `['ai', 'chat', sessionId]`). API çağrıları tip güvenli sarmalayıcı fonksiyonlarla yapılır (`getTasks()`, `approveAiAction(id)`), bileşenler Axios'u doğrudan çağırmaz. Her wrapper, Cilt 4 §27'deki tam endpoint yolunu ve response şemasını referans alır; backend şeması değiştiğinde yalnızca bu katman güncellenir.

Mutation'lar (görev oluşturma, AI onaylama) TanStack Query mutation + ilgili query key invalidation ile yönetilir; optimistic update yalnızca düşük riskli aksiyonlarda (bildirim okundu işaretleme) kullanılır, AI onay/red gibi geri alınamaz aksiyonlarda optimistic update kullanılmaz (Bölüm 36).

# 19. State Management

| Durum türü | Araç | Örnek |
|---|---|---|
| Server state (API'den gelen veri) | TanStack Query | Görev listesi, AI sonuçları |
| Global UI state | Zustand | Sidebar açık/kapalı, tema, aktif tenant |
| Form state | React Hook Form + Zod | Tüm formlar |
| URL state | Next.js searchParams | Filtreler, sayfalama, aktif sekme |
| Ephemeral local state | React useState | Modal açık/kapalı, hover |

Zustand store'ları küçük ve modüler tutulur (tek bir dev store yerine `useUiStore`, `useTenantStore` gibi ayrık store'lar); sunucu verisi asla Zustand'da tutulmaz (Cilt 2 §13 "State management: Zustand küçük UI state için, server state için TanStack Query" ilkesiyle birebir).

# 20. Error Handling

Hata seviyeleri: (1) alan bazlı form hatası (Zod + React Hook Form, Bölüm 52), (2) sayfa/modül bazlı Error Boundary (Next.js `error.tsx`, Cilt 2 §13 "Error boundary: sayfa ve modül bazlı"), (3) global toast hatası (beklenmeyen 500'ler, Bölüm 55). Backend'in standart hata formatı (Cilt 4 §20 Error Handling Standardı) frontend'de tek bir merkezi error mapper ile kullanıcı diline çevrilir; ham backend hata kodu asla doğrudan kullanıcıya gösterilmez.

AI'a özgü hata durumu: bir analiz job'ı `failed` olursa (Cilt 5 §69 AI Failure Recovery), ilgili ekranda (Görüşme Detayı, Bölüm 26) "AI analizi şu an tamamlanamadı, tekrar deneyin" durumu gösterilir; bu bir Error Boundary değil, modül içi bir Empty/Error State'tir (Bölüm 48).

# 21. Notifications

Bildirimler iki kanaldan gelir: gerçek zamanlı (WebSocket, Bölüm 37) ve poll edilen (TanStack Query periyodik refetch, WebSocket bağlantısı yoksa fallback). Uygulama içi bildirim, tarayıcı push bildirimi (Cilt 1 §25) ve toast (Bölüm 55) birbirinden ayrı katmanlardır: toast anlık geçici olayları, bildirim merkezi kalıcı geçmişi temsil eder.

# 22. Global Search

| Alan | Detay |
|---|---|
| Amaç | Görüşme, kişi, görev, randevu genelinde hızlı arama |
| Wireframe | Üst barda komut paleti tetikleyici (kısayol, Bölüm 56), açıldığında ortalanmış arama kutusu + kategorize sonuç listesi |
| Bileşenler | Dialog(command palette), Input, sonuç grupları (kişi/görev/görüşme) |
| API bağlantıları | GET /api/v1/search, POST /api/v1/search/semantic (MVP'de temel, Cilt 5 §41) |
| Loading | Debounce edilmiş, satır içi skeleton (Bölüm 49) |
| Error | Sessiz başarısızlık + "sonuç getirilemedi" küçük not, ekranı bloklamaz |
| Permission | Kullanıcının erişebildiği kayıtlarla sınırlı (tenant/rol filtreli, backend tarafından) |
| Responsive | Mobilde tam ekran arama sayfasına döner |
| Accessibility | Klavye ile tam gezinme (yukarı/aşağı ok, Enter), `role=listbox` |

# 23. AI Chat Interface

Kurumsal, ChatGPT benzeri ama kaynak-şeffaf bir sohbet ekranı.

| Alan | Detay |
|---|---|
| Amaç | Kullanıcının doğal dilde geçmiş iletişimini sorgulaması (Cilt 5 §47) |
| Wireframe | Sol dar sidebar (Conversation List + "yeni sohbet"), orta mesaj akışı, mesaj altında Prompt Suggestions (ilk açılışta), sağda opsiyonel Sources paneli |
| Bileşenler | Sidebar, ConversationListItem, ChatMessage(user/assistant), SourceChip, ConfidenceBadge, FeedbackButtons(👍/👎), Textarea(auto-grow), PromptSuggestionChip |
| API bağlantıları | POST /api/v1/ai/chat, GET /api/v1/ai/chat/sessions, GET /api/v1/ai/chat/sessions/{id}, POST /api/v1/ai/feedback |
| Loading | Assistant mesajı streaming/typing göstergesi (üç nokta animasyonu) |
| Error | Provider hatası → "şu an cevap veremiyorum" assistant balonu + tekrar dene butonu (Cilt 5 §69 ile uyumlu) |
| Permission | Yalnızca kullanıcının kendi tenant/yetki kapsamındaki kayıtlar RAG'e girer (backend garantisi, Cilt 5 §44) |
| Responsive | Mobilde Sidebar drawer'a, Sources paneli alt sheet'e döner |
| Accessibility | Yeni mesaj `aria-live=polite` bölgesinde duyurulur |

Alt bileşenlerin davranışı:

- **Sidebar / Conversation List**: geçmiş sohbet oturumları (`/ai/chat/sessions`), en son aktif olan üstte.
- **Prompt Suggestions**: Cilt 5 §47 örnek sorularından ("Bugün ne yapmam gerekiyor?", "Ali ile en son ne konuştum?" vb.) türetilen tıklanabilir öneri çipleri, yalnızca boş/yeni sohbette gösterilir.
- **Sources / References**: her assistant yanıtının altında, Cilt 5 §43 RAG Pipeline'ının `sources` alanından gelen tıklanabilir referanslar (Source Chip); tıklanınca ilgili görüşme/mail/görev detayına gider.
- **AI Confidence**: yanıt geneli için tek bir Confidence Badge; düşük güvende ek bir "bu cevaptan emin değilim" notu.
- **Feedback**: her assistant mesajının altında 👍/👎; 👎 seçilirse kısa serbest metin alanı açılır (Cilt 5 §63 AI Feedback System'in UI karşılığı).
- **Memory**: sohbet geçmişi oturum bazlı saklanır (Short Term Memory, Cilt 5 §32); uzun oturumlarda eski mesajlar "daha fazla göster" ile katlanır, tamamı backend'de saklı kalır.

# 24. Dashboard

| Alan | Detay |
|---|---|
| Amaç | Günlük çalışma özeti — AI önerileri, görevler, randevular, mailler tek bakışta |
| Wireframe | Üstte "AI Günlük Özet" banner'ı, altında grid: Bugünkü Görevler / Yaklaşan Randevular / Bekleyen AI Önerileri / Son Görüşmeler / Son Mailler kartları, en altta Performans grafikleri (Bölüm 50) |
| Bileşenler | SummaryBanner, TaskListCard, AppointmentListCard, AiSuggestionCard × n, RecentConversationCard, RecentEmailCard, PerformanceChart |
| API bağlantıları | GET /api/v1/dashboard, /dashboard/daily-summary, /dashboard/upcoming, /dashboard/pending-actions, /dashboard/ai-suggestions |
| Loading | Her kart bağımsız skeleton (Bölüm 49), tek bir global spinner kullanılmaz |
| Error | Kart bazlı hata (bir widget başarısız olursa diğerleri etkilenmez) |
| Permission | Kullanıcı bazlı; Team/Enterprise'da ekip dashboard'u için ayrı yetki (Cilt 1 §8.7) |
| Responsive | Grid mobilde tek kolona düşer, banner özetlenir |
| Accessibility | Kartlar `region` landmark'ları ile ayrılır |

"AI Günlük Özet" banner'ı, Cilt 5 §47'deki "Bugün ne yapmam gerekiyor?" sorusunun önceden hesaplanmış, tıklama gerektirmeyen halidir — kullanıcı AI Chat'i açmadan aynı bilgiyi görür; AI Chat, bunun serbest-sorgu genişletilmiş halidir.

# 25. Calls Module

| Alan | Detay |
|---|---|
| Amaç | Görüşme metni yükleme/listeleme |
| Wireframe | Liste görünümü (tarih, kişi, durum) + "yeni görüşme" butonu → metin giriş modalı/sayfası |
| Bileşenler | Table (Bölüm 51), Button, Textarea(metin girişi), Dropzone (ses dosyası, Future) |
| API bağlantıları | GET/POST /api/v1/conversations, POST /api/v1/calls/text, POST /api/v1/calls/{id}/analyze |
| Loading | Liste skeleton; analiz tetiklendikten sonra satırda "analiz ediliyor" durumu (polling veya WebSocket) |
| Error | Analiz job hatası satırda "tekrar dene" aksiyonu ile |
| Permission | Tenant + kullanıcı kapsamlı (Team planında ekip görünürlüğü, Cilt 1 §21) |
| Responsive | Liste mobilde kart listesine döner |
| Accessibility | Tablo `scope` header'ları, durum ikonla + metinle |

# 26. Conversations Module

| Alan | Detay |
|---|---|
| Amaç | Tek bir görüşmenin transkripti + AI analiz sonuçları |
| Wireframe | İki kolon: solda transkript (Accordion ile katlanabilir), sağda AI Analiz paneli (özet, çıkarılan görevler/randevular önerileri, confidence) |
| Bileşenler | Accordion(transkript), AiSuggestionCard × n, ConfidenceBadge, Button(onayla/reddet — Approval Card'a yönlendirir) |
| API bağlantıları | GET /api/v1/conversations/{id}, GET /api/v1/calls/{id}/analysis |
| Loading | Analiz tamamlanana kadar sağ panelde progress göstergesi |
| Error | Analiz başarısızsa Bölüm 20'deki modül içi hata deseni |
| Permission | Kayıt sahibi/tenant kapsamlı |
| Responsive | Mobilde sağ panel transkript altına akar (tek kolon) |
| Accessibility | Transkript konuşmacı etiketleri screen reader'a okunur şekilde işaretlenir |

# 27. Tasks Module

## 27.1 Tasks (Liste)

| Alan | Detay |
|---|---|
| Amaç | Tüm görevlerin listelenmesi, filtrelenmesi |
| Wireframe | Filtre çubuğu (durum, öncelik, kaynak) + Table/Kanban geçişi |
| Bileşenler | Table (Bölüm 51), FilterBar, Badge(öncelik), Checkbox(tamamlandı) |
| API bağlantıları | GET /api/v1/tasks, GET /api/v1/tasks/overdue, POST /api/v1/tasks/{id}/complete |
| Loading | Table skeleton (Bölüm 49) |
| Error | Toast + retry (Bölüm 55) |
| Permission | Kullanıcı/ekip kapsamlı |
| Responsive | Kanban mobilde gizlenir, yalnızca liste |
| Accessibility | Checkbox'lar `aria-label` ile görev başlığına bağlı |

## 27.2 Task Detail

| Alan | Detay |
|---|---|
| Amaç | Görev detayı, düzenleme, hatırlatma ekleme |
| Wireframe | Başlık/açıklama/öncelik/son tarih formu + bağlı kaynak (görüşme/mail) linki + hatırlatma listesi |
| Bileşenler | Form (Bölüm 52), Badge, ContactMiniCard(varsa ilişkili kişi), Button |
| API bağlantıları | GET/PATCH /api/v1/tasks/{id}, POST /api/v1/tasks/{id}/reminders |
| Loading/Error | Standart form deseni (Bölüm 52) |
| Permission | Görev sahibi veya yetkili yönetici |
| Responsive | Form tek kolona düşer |
| Accessibility | Form etiketleri `for`/`id` eşleşmeli |

# 28. Calendar Module

Google Calendar benzeri görünüm, FullCalendar kütüphanesi üzerine kurulu.

| Alan | Detay |
|---|---|
| Amaç | Randevu/etkinlik görselleştirme ve yönetimi |
| Wireframe | Üstte görünüm seçici (Day/Week/Month/Agenda), ana alan takvim grid'i, Conflict View overlay'i (çakışan etkinlikler yan yana vurgulanır) |
| Bileşenler | Calendar(FullCalendar wrapper), ViewSwitcher, EventCard, ConflictBadge |
| API bağlantıları | GET /api/v1/calendar/events, POST /api/v1/appointments/check-conflicts, GET /api/v1/calendar/accounts |
| Loading | Görünüm değişiminde skeleton grid |
| Error | Sync hatası üst barda kalıcı Alert (Cilt 4 §32 Calendar Backend Akışı ile ilişkili) |
| Permission | Bağlı takvim hesabına göre; salt okunur paylaşılan takvimler ayrı ikonla işaretlenir |
| Responsive | Mobilde varsayılan görünüm Agenda'ya döner (grid yerine liste) |
| Accessibility | Klavye ile gün/hafta gezinme (ok tuşları), etkinlik detayına Enter ile giriş |

# 29. Appointment Module

| Alan | Detay |
|---|---|
| Amaç | Randevu listesi ve manuel/AI önerili randevu oluşturma |
| Wireframe | Liste (Calendar Module'den bağımsız, tablo görünümü) + "yeni randevu" formu |
| Bileşenler | Table, Form, ConflictBadge |
| API bağlantıları | GET/POST /api/v1/appointments, PATCH/DELETE /api/v1/appointments/{id} |
| Loading/Error | Standart liste/form desenleri |
| Permission | Kullanıcı/ekip kapsamlı |
| Responsive | Liste → kart |
| Accessibility | Standart tablo/form kuralları |

# 30. Email Module

Cilt 1'de mail entegrasyonu MVP'de opsiyonel ikinci aşama, Cilt 4'te ilgili endpoint'ler `Future` olarak işaretlidir. Bu modül bu ciltte **iskelet düzeyinde** tasarlanır: hesap bağlama ekranı (Gmail/Outlook OAuth), mail listesi, mail detayında AI özet paneli (Conversations Module ile aynı desen, `source_type=email`). MVP'de route mevcuttur ancak "yakında" boş durumuyla (Bölüm 48) gösterilebilir; backend hazır olduğunda aktifleştirilir.

# 31. Contacts CRM Module

| Alan | Detay |
|---|---|
| Amaç | Kişi/firma kartı, ilişki hafızası, geçmiş etkileşimler |
| Wireframe | Liste (kişi/şirket sekmeli) + Kişi Detayı: üstte kimlik kartı, sekmeler: Timeline (Bölüm 32) / Görevler / Mailler / Belgeler / AI Hafızası |
| Bileşenler | Table, Tabs, ContactMiniCard, Timeline, AiSuggestionCard(AI Hafızası özeti) |
| API bağlantıları | GET/POST /api/v1/contacts, GET /api/v1/contacts/{id}, GET /api/v1/contacts/{id}/timeline, POST /api/v1/contacts/{id}/notes |
| Loading | Kişi kartı + sekme içerikleri bağımsız skeleton |
| Error | Sekme bazlı hata (bir sekme başarısız olsa diğerleri çalışır) |
| Permission | Team planında paylaşımlı görünürlük (Cilt 1 §21), aksi halde kullanıcıya özel |
| Responsive | Sekmeler mobilde yatay kaydırmalı |
| Accessibility | Tabs `role=tablist`/`tab`/`tabpanel` |

**AI Hafızası** sekmesi, Cilt 5 §28 Contact Memory'nin doğrudan UI karşılığıdır: `ai_memory_summaries` içeriği okunabilir özet olarak, kaynak etkileşimlere (`ai_memory_links`) tıklanabilir referanslarla gösterilir — AI Chat'teki Source Chip deseniyle aynı bileşen tekrar kullanılır (Bölüm 6 "tutarlılık" ilkesi).

# 32. Timeline Module

Timeline, Contact Detail (Bölüm 31) içinde kullanılan, kronolojik olarak sıralı, tipine göre ikonlanmış (görüşme/mail/görev/randevu/not) bir olay akışıdır. Her timeline öğesi tıklanınca ilgili kaynağın detayına gider. Timeline sonsuz kaydırma (infinite scroll) ile yüklenir, TanStack Query'nin `useInfiniteQuery`'si kullanılır.

# 33. Document Module

Cilt 1'de belge/dosya işlevi "olsa iyi olur" ve orta vadeli kapsamda değerlendirilmiştir.

| Alan | Detay |
|---|---|
| Amaç | Dosya yükleme, listeleme, (ileri fazda) AI analiz sonucu görüntüleme |
| Wireframe | Dropzone + dosya listesi (ikon, ad, boyut, yüklenme tarihi) |
| Bileşenler | Dropzone, FileListItem, PDF Preview (React PDF ile, yalnızca PDF için) |
| API bağlantıları | POST /api/v1/files/upload-url, POST /api/v1/files/complete-upload, GET /api/v1/files, POST /api/v1/files/{id}/analyze (Future) |
| Loading | Yükleme ilerleme çubuğu |
| Error | Boyut/tip limiti aşımı client-side önceden engellenir, sunucu hatası toast ile |
| Permission | Kaynağa bağlı (kişi/görüşme dosyası ise o kaydın yetkisiyle) |
| Responsive | Dropzone mobilde dosya seçici butonuna döner |
| Accessibility | Yükleme durumu `aria-live` ile duyurulur |

# 34. Analytics Module

| Alan | Detay |
|---|---|
| Amaç | Haftalık/aylık performans ve AI kullanım metrikleri (Cilt 1 §34, §44) |
| Wireframe | Üstte dönem seçici, altta metrik kartları + grafikler (Bölüm 50); "Reports" burada bir alt-sekme olarak (dönemsel özet PDF/CSV export) yer alır |
| Bileşenler | DateRangePicker, MetricCard, LineChart/BarChart(Recharts), ExportButton |
| API bağlantıları | GET /api/v1/analytics/overview, /tasks, /calls, /appointments, /ai (MVP'de "Should", tam kapsam ileri faz) |
| Loading | Grafik alanı skeleton |
| Error | Grafik bazlı hata, metrik kartları etkilenmez |
| Permission | Team/Enterprise'da ekip metrikleri ayrı yetki gerektirir (`/analytics/team`, Future) |
| Responsive | Grafikler mobilde dikey istiflenir, yatay kaydırma ile detay |
| Accessibility | Grafiklerin altında veri tablosu alternatifi (screen reader için) |

# 35. AI Suggestions

"AI Suggestions" ayrı bir sayfa değil, AI Suggestion Card bileşeninin (Bölüm 14.2) Dashboard (Bölüm 24), Conversation Detail (Bölüm 26) ve Contact Detail (Bölüm 31) gibi birden çok yüzeyde tekrar kullanılan halidir. Kart her zaman şu üçlüyü taşır: öneri içeriği, kaynak referansı, confidence göstergesi + üç aksiyon butonu (onayla/reddet/düzenle) — tıklanınca Bölüm 36'daki tam Approval akışına girer.

# 36. AI Approval Center

Ürünün güven mekanizmasının (Cilt 2 §21, Cilt 5 §51) tek merkezi arayüzü.

| Alan | Detay |
|---|---|
| Amaç | AI tarafından önerilen tüm görev/randevu/mail taslağı/hatırlatmaların tek yerden onaylanması |
| Wireframe | Sol filtre (tür: görev/randevu/mail/hatırlatma, durum: bekleyen/onaylanan/reddedilen), sağ liste: her öğe bir Approval Card |
| Bileşenler | Approval Card (kaynak özeti + confidence + `suggested_payload` önizlemesi + Onayla/Reddet/Düzenle butonları), FilterSidebar, EditDialog(düzenle akışı için) |
| API bağlantıları | GET pending liste (dashboard `/pending-actions` veya ayrık liste endpoint'i), POST /api/v1/ai/actions/{approval_id}/approve, POST /api/v1/ai/actions/{approval_id}/reject, PATCH /api/v1/ai/actions/{approval_id} |
| Loading | Liste skeleton; aksiyon sırasında kart üzerinde inline spinner (kart kaybolmaz, sonuç gelince duruma göre listeden çıkar) |
| Error | Aksiyon başarısızsa kart durumu değişmez, toast ile hata gösterilir — kullanıcı tekrar deneyebilir (optimistic update kullanılmaz, Bölüm 18) |
| Permission | Yalnızca önerinin sahibi (veya Team planında yetkili yönetici) onaylayabilir |
| Responsive | Sol filtre mobilde üstte katlanır sheet'e döner |
| Accessibility | Her Approval Card `role=article`, aksiyon butonları net `aria-label` (örn. "Ahmet için görevi onayla") |

**Düzenle akışı**: kullanıcı "Düzenle" seçtiğinde `suggested_payload` alanları önceden doldurulmuş bir form (EditDialog) açılır; kaydedince `approved_payload` ile PATCH edilir ve aynı istek onayı da işaretler (Cilt 5 §51 madde 8 ile birebir — düzenleme ayrı bir adım değil, onayın bir varyantıdır).

**Süresi dolmuş öneriler**: `expired` durumundaki kartlar salt okunur gösterilir, aksiyon butonları devre dışıdır, "kaynak veri değişmiş olabilir, yeniden analiz edin" notu ile (Cilt 5 §51 kuralıyla birebir).

# 37. Notification Center

| Alan | Detay |
|---|---|
| Amaç | Kalıcı bildirim geçmişi |
| Wireframe | Üst bardan açılan panel/drawer, kronolojik liste, okunmamışlar vurgulu |
| Bileşenler | Drawer, NotificationCard, Badge(sayaç) |
| API bağlantıları | GET /api/v1/notifications, PATCH /api/v1/notifications/{id}/read, GET/PATCH /api/v1/notifications/preferences |
| Loading | Liste skeleton |
| Error | Sessiz retry, toast yok (arka plan özelliği) |
| Permission | Kullanıcıya özel |
| Responsive | Mobilde tam ekran panel |
| Accessibility | Yeni bildirim geldiğinde `aria-live=polite` sayaç güncellemesi |

Gerçek zamanlı güncelleme Socket.io Client ile sağlanır (Cilt 2 §30 WebSocket/Realtime Mimarisi, Cilt 2 §27 event listesindeki bildirim olaylarıyla uyumlu); bağlantı koptuğunda TanStack Query periyodik polling'e düşer (graceful degradation).

# 38. User Settings

| Alan | Detay |
|---|---|
| Amaç | Profil, tercihler, cihaz/oturum yönetimi, bağlı veri kaynakları, tema |
| Wireframe | Sol alt-sekme menüsü (Profil / Güvenlik / Bildirimler / Entegrasyonlar / Gizlilik) + sağda ilgili form |
| Bileşenler | Form, Toggle(tema, bildirim tercihleri), SessionListItem, IntegrationCard |
| API bağlantıları | GET/PATCH /api/v1/users/me, /me/preferences, GET /me/sessions + DELETE, GET/POST/DELETE /api/v1/integrations |
| Loading/Error | Standart form deseni |
| Permission | Kullanıcının kendi ayarları |
| Responsive | Alt-sekme menü mobilde üstte yatay tab'a döner |
| Accessibility | Toggle'lar `role=switch` ile |

"Gizlilik" alt-sekmesi Bölüm 46 GDPR Screens'e, "Entegrasyonlar" Provider bağlama akışına (Cilt 4 §27.13) bağlanır.

# 39. Organization Settings

MVP'de temel organizasyon bilgisi düzenleme (`/organizations/current`); üye listesi ve davet (`/organizations/members`, `/invitations`) Cilt 4'te `Future` işaretlidir, bu ciltte iskelet olarak planlanır. "Roles" ve "Permissions" sayfaları da bu modülün alt-sekmeleridir ve aynı şekilde Future kapsamdadır — MVP'de rol/izin yönetimi UI'ı yoktur, backend'deki sabit rol modeli (Cilt 2 §17) kullanılır.

# 40. Billing

Cilt 4'te billing endpoint'lerinin tamamı `Should`/`Future` işaretlidir; bu modül MVP'de yalnızca "mevcut plan" salt okunur görünümüyle (`GET /billing/plans`, `GET /billing/subscription`) var olur, plan değiştirme/iptal akışları ileri faz olarak iskelet route + "yakında" boş durumuyla planlanır.

# 41. Admin Panel

| Alan | Detay |
|---|---|
| Amaç | Platform/organizasyon admin işlemleri (Cilt 2 §15) |
| Wireframe | Admin Layout (Bölüm 11), MVP'de: sistem sağlığı kartı, feature flag listesi; ileri fazda kullanıcı/organizasyon/tenant listeleri, audit log |
| Bileşenler | Table, MetricCard, Toggle(feature flag) |
| API bağlantıları | GET /api/v1/admin/system-health (Should), GET/PATCH /api/v1/admin/feature-flags (Should), GET /admin/users /organizations /tenants /audit-logs /errors /ai-costs (tümü Future) |
| Loading/Error | Standart liste/kart desenleri |
| Permission | Yalnızca `admin` rolü; route middleware + backend RBAC çift kontrol (Bölüm 17) |
| Responsive | Admin ekranları öncelikle desktop için tasarlanır, mobil web'de salt okunur özet |
| Accessibility | Standart tablo/form kuralları |

"Users", "Roles", "Permissions" sayfaları burada Admin Panel'in alt-rotaları olarak konumlanır (Organization Settings'teki hafif versiyonlarının platform-geneli karşılığı) ve tamamı `Future` kapsamdadır.

# 42. Super Admin

Super Admin, Admin Panel'in platform-geneli (NeuroDesk operasyon ekibi) katmanıdır (Cilt 2 §15 "Platform admin"). MVP'de ayrı bir arayüz yoktur; Admin Panel içinde rol bazlı ek görünürlük olarak planlanır (tüm tenant'ları listeleme, sistem geneli AI maliyet dashboard'u Bölüm 34 ile paylaşımlı). Bağımsız bir Super Admin uygulaması ancak Enterprise ölçekte (Bölüm 65) gerekçelendirilebilir.

# 43. Feature Flags

Feature flag yönetimi (`/admin/feature-flags`) hem bir admin ekranı hem frontend'in kendi mimari aracıdır: MVP dışı modüller (Email, Billing tam akışı, Roller/İzinler) kod olarak var olabilir ama flag ile kapatılabilir. Bu, "Future" olarak işaretli sayfaların iskelet halinde geliştirilip prod'da gizli tutulmasını sağlar — Cilt 4 §41 Deployment ile birlikte kademeli açılışın (Bölüm 7 Prompt Versioning'deki kademeli açılış mantığına benzer) UI karşılığıdır.

# 44. File Upload UI

Dosya yükleme deseni (Document Module Bölüm 33'te kullanılan) iki aşamalıdır: (1) frontend backend'den signed upload URL ister (`/files/upload-url`), (2) dosya doğrudan object storage'a yüklenir (backend'i bypass ederek, Cilt 2 §25 Storage Mimarisi ile uyumlu), (3) `/files/complete-upload` ile finalize edilir. UI bu üç adımı tek bir Dropzone bileşeni arkasında gizler, kullanıcı yalnızca ilerleme çubuğu görür.

# 45. Data Export

Kullanıcı veri dışa aktarma talebi (`POST /api/v1/privacy/export`), User Settings → Gizlilik altında tetiklenir (Bölüm 38, 46). Export asenkron olduğundan UI, talebi "işleniyor" durumuyla gösterir, tamamlandığında bildirim (Bölüm 37) ve indirme bağlantısı sunar (`GET /privacy/export/{request_id}`). Bu akış Cilt 1 §37 "kullanıcı veri taşıma hakkı" gereksinimin doğrudan arayüz karşılığıdır.

# 46. GDPR Screens

| Alan | Detay |
|---|---|
| Amaç | Rıza yönetimi, veri dışa aktarma, hesap/veri silme talebi |
| Wireframe | Rıza listesi (her veri kaynağı için açık/kapalı durum) + "Verilerimi Dışa Aktar" + "Hesabımı Sil" bölümleri |
| Bileşenler | Toggle(rıza), Button(export/delete), Dialog(silme onayı — çift onay: yazı ile teyit) |
| API bağlantıları | GET/POST/PATCH /api/v1/consents, GET/PATCH /api/v1/privacy/settings, POST /api/v1/privacy/delete-request |
| Loading/Error | Standart form deseni |
| Permission | Kullanıcının kendi verisi |
| Responsive | Tek kolon, mobilde de tam işlevsel (kritik yasal akış, kısıtlanmaz) |
| Accessibility | Silme onayı iki aşamalı ve net dille (yanlışlıkla tetiklenmeyi önlemek için) |

Bu ekran, hem Cilt 1 §37 Kullanıcı Onayı ve Rıza Yönetimi hem Cilt 5 §58 KVKK GDPR Compliance'ın doğrudan UI karşılığıdır.

# 47. Loading States

Üç seviye: (1) sayfa geçişi — Next.js `loading.tsx` ile iskelet sayfa, (2) veri yükleme — bileşen bazlı Skeleton (Bölüm 49), (3) aksiyon yükleme — buton/kart içi inline spinner. Global tam ekran spinner yalnızca ilk uygulama yüklemesinde (auth kontrolü sırasında) kullanılır, sayfa içi geçişlerde kullanılmaz (ani "flash" hissini önlemek için).

# 48. Empty States

Her liste/modül için özel boş durum metni ve aksiyonu tanımlanır (jenerik "veri yok" kullanılmaz): örn. Tasks boşsa "Henüz göreviniz yok, ilk görevi ekleyin" + CTA; AI Approval Center boşsa "Bekleyen AI önerisi yok, harika gidiyorsunuz" (olumlu ton — bu ekranda boş durum iyi haberdir). MVP dışı modüller (Email, Billing) için boş durum "yakında" mesajı + varsa bekleme listesi CTA'sı taşır.

# 49. Skeleton Screens

Skeleton'lar gerçek içerik düzenini taklit eder (kart/tablo satır sayısı ve oranları), jenerik gri kutu yerine. Skeleton süresi 300ms altına düşen yüklemelerde gösterilmez (flicker önleme); TanStack Query'nin `isLoading` vs `isFetching` ayrımı bu davranışı yönetir.

# 50. Charts

Recharts kütüphanesi tüm grafiklerde (Dashboard performans grafiği Bölüm 24, Analytics Bölüm 34) tutarlı kullanılır. Grafik renkleri Bölüm 9 Color Tokens'tan türetilir (marka rengi + destekleyici palet), asla grafik kütüphanesinin varsayılan renkleri kullanılmaz. Her grafik, Bölüm 13 gereği bir veri tablosu alternatifiyle eşleştirilir.

# 51. Tables

React Table (TanStack Table) tüm liste ekranlarında (Tasks, Contacts, Conversations, Admin listeleri) ortak bir `DataTable` wrapper'ı üzerinden kullanılır: sıralama, kolon gizleme, sayfalama (backend cursor/offset ile senkron, Cilt 4 §21 Pagination Standardı), satır seçimi (toplu aksiyon için, ileri faz) tek noktadan yönetilir. Mobilde `DataTable`, otomatik olarak kart listesine dönüşen bir responsive mod içerir (Bölüm 12).

# 52. Forms

Tüm formlar React Hook Form + Zod ile inşa edilir: Zod şeması hem client-side doğrulamayı hem TypeScript tip çıkarımını sağlar, backend'in Cilt 4 §22 Validation Standardı ile aynı alan kurallarını (zorunluluk, format, uzunluk) yansıtır — iki katman birbirinden bağımsız yazılmaz, backend şeması "kaynak of truth", frontend şeması onun bir aynasıdır. Hata mesajları alan altında anlık (blur/submit) gösterilir.

# 53. Modals

Dialog (Shadcn/Radix tabanlı) kritik, odaklanma gerektiren, kısa akışlar için kullanılır (AI onay/red teyidi, silme onayı, hızlı görev oluşturma). Modal içinde başka bir modal açılmaz; çok adımlı akışlar (Register gibi) modal yerine ayrı sayfa/adım göstergesi kullanır.

# 54. Drawers

Drawer (yandan/alttan kayan panel), bağlamı kaybetmeden ek bilgi göstermek için kullanılır: Notification Center (Bölüm 37), mobilde Sidebar (Bölüm 11) ve AI Chat Sources paneli (Bölüm 23). Drawer arka plandaki içeriği tamamen kapatmaz (Modal'dan farkı), kullanıcı ana bağlamı görmeye devam eder.

# 55. Toasts

Toast, geçici ve kritik olmayan geri bildirim için kullanılır (kayıt başarılı, bildirim okundu). Kurallar: en fazla 3 toast aynı anda ekranda, 4-6 saniye sonra otomatik kapanır, kritik/geri alınamaz sonuçlar (AI onay hatası gibi) için toast tek başına yeterli değildir — ilgili kart/sayfa durumu da güncellenir (Bölüm 36).

# 56. Keyboard Shortcuts

| Kısayol | Aksiyon |
|---|---|
| Cmd/Ctrl+K | Global Search / Command Palette (Bölüm 22) |
| G sonra D | Dashboard'a git |
| G sonra T | Tasks'a git |
| G sonra C | AI Chat'e git |
| Cmd/Ctrl+Enter | Aktif formu gönder |
| Esc | Modal/Drawer kapat |

Kısayollar yalnızca desktop'ta aktiftir, mobilde devre dışıdır ve bir "kısayollar" yardım modalı (`?` tuşu) ile keşfedilebilir kılınır (Bölüm 13 erişilebilirlik ilkesiyle uyumlu — keşfedilemez gizli özellik olmamalı).

# 57. Internationalization

MVP dili Türkçe'dir (varsayılan ve tek dil); Cilt 2 §13 "i18n: Türkçe varsayılan, ileri fazda İngilizce" ile birebir. Metinler baştan i18n kütüphanesi (anahtar bazlı) üzerinden okunur, hardcoded string kullanılmaz — bu, MVP'de tek dil olsa bile ileri fazdaki İngilizce eklemenin metin değişikliği değil yalnızca çeviri dosyası eklemesi olmasını sağlar.

# 58. Offline Support

Cilt 2 §13'te web için özel bir offline-first gereksinimi tanımlanmamıştır (bu, Mobile mimarisine özgüdür, Cilt 2 §14). Web'de "offline support" sınırlı bir kapsamda ele alınır: TanStack Query'nin cache'i sayesinde son görüntülenen veriler bağlantı kesildiğinde salt okunur olarak görünmeye devam eder; yazma işlemleri (form gönderimi, AI onaylama) bağlantı yokken devre dışı bırakılır ve kullanıcıya net biçimde bildirilir. Tam offline-first senkronizasyon web kapsamı dışıdır.

# 59. Performance

Hedefler: ilk anlamlı boyama (LCP) < 2.5sn, etkileşime hazır olma (TTI) < 3.5sn (iyi ağ koşulunda). Teknikler: route bazlı code splitting (Next.js varsayılanı), ağır bileşenlerin (FullCalendar, Recharts, React PDF) dinamik import ile yalnızca ilgili sayfada yüklenmesi, liste sanallaştırması (uzun Timeline/Chat geçmişinde), resim optimizasyonu (Next.js Image). AI Chat'te streaming yanıt (Bölüm 23), algılanan gecikmeyi (Cilt 5 §27 hedef gecikme) azaltmak için kullanılır.

# 60. Security

Frontend güvenlik sorumlulukları: XSS önleme (React'in varsayılan escaping'i + kullanıcı/AI üretimi metinlerde `dangerouslySetInnerHTML` kullanılmaması), token'ların yalnızca `httpOnly` cookie'de veya güvenli bellek içi saklanması (localStorage'da access token tutulmaz), CSRF koruması (Cilt 2 §32 ile uyumlu), Content Security Policy header'ları. Frontend hiçbir yetki/iş kuralı kararını nihai otorite olarak almaz (Bölüm 17); bu, bir güvenlik açığı değil bilinçli mimari sınırdır.

# 61. Testing Strategy

| Seviye | Araç | Kapsam |
|---|---|---|
| Unit | Vitest/Jest | Utility fonksiyonlar, form şemaları, hook'lar |
| Component | React Testing Library | Primitive ve pattern bileşenler (Bölüm 14) |
| Entegrasyon | React Testing Library + MSW (mock API) | Sayfa akışları (login, görev oluşturma, AI onaylama) |
| E2E | Playwright | Kritik yollar: kayıt→giriş, görüşme yükleme→AI önerisi→onaylama, AI Chat soru-cevap |
| Erişilebilirlik | axe-core (otomatik) + manuel klavye testi | Bölüm 13 kriterleri |

AI Approval Center (Bölüm 36) ve AI Chat (Bölüm 23), en yüksek iş etkisine sahip modüller olduğundan E2E kapsamında öncelikli test edilir.

# 62. Storybook

Tüm Primitive ve Pattern bileşenler (Bölüm 14) Storybook'ta izole olarak geliştirilir/dokümante edilir; her bileşenin light/dark tema, tüm varyant ve durumları (loading/error/empty) story olarak tanımlanır. Storybook, Component Documentation'ın (Bölüm 63) canlı/çalıştırılabilir halidir ve tasarım-geliştirme el sıkışma noktasıdır (tasarımcı burada onay verir).

# 63. Component Documentation

Her bileşen için: amaç, prop tablosu (TypeScript tipinden otomatik türetilir), kullanım örneği, erişilebilirlik notları, hangi modüllerde kullanıldığı (Bölüm 14.2 tablosundaki "İlgili modül" alanına referans). Dokümantasyon kod ile aynı repoda, bileşenin yanında tutulur (ayrı bir wiki'de değil) ki güncel kalması kolaylaşsın.

# 64. Future UI

Bu ciltte mimarisi kesinleştirilmemiş ancak değerlendirme havuzunda olan fikirler: komut paleti üzerinden doğrudan AI aksiyonu tetikleme ("Cmd+K > Ahmet'e hatırlatma oluştur"), Approval Center'da toplu onay (birden çok öneriyi tek tıkla onaylama — Cilt 5 §48 AI Agent sınırlarıyla dikkatli değerlendirilmeli), AI Chat'te sesli giriş, kişiselleştirilebilir dashboard widget düzeni.

# 65. Enterprise Features

Enterprise fazına özgü frontend ihtiyaçları (Cilt 1 §14, Cilt 2 §38 ile hizalı): SSO login akışı (Bölüm 16'ya ek üçüncü seçenek), organizasyon bazlı beyaz etiketleme (logo/renk override — Bölüm 7 Theme System'in tenant bazlı genişlemesi), gelişmiş Admin/Super Admin ekranları (Bölüm 41-42'nin tam kapsamı), SIEM/audit log export arayüzü, SLA durumu gösterge paneli.

# 66. Uygulama Rehberi

Frontend kod üretimine başlanacağında izlenmesi önerilen sıra:

1. Next.js App Router iskeleti, route grupları (Bölüm 15) ve üç layout (Bölüm 11) kurulur.
2. Design token'lar (Bölüm 7-10) Tailwind config'e işlenir, Shadcn UI primitive bileşenleri (Bölüm 14.1) kuruluma dahil edilir.
3. Axios instance + TanStack Query provider + Zustand store iskeleti (Bölüm 18-19) kurulur.
4. Authentication akışı (Bölüm 16-17) uçtan uca yazılır — bundan sonraki her ekran buna bağımlıdır.
5. Dashboard (Bölüm 24) iskelet veriyle (mock/gerçek karışık) oluşturulur; bu, çoğu pattern bileşenin (Bölüm 14.2) ilk kullanıldığı yerdir.
6. Tasks, Calls/Conversations, Calendar/Appointments, Contacts modülleri (Bölüm 25-29, 31) MVP kapsamına göre sırayla yazılır.
7. AI Approval Center (Bölüm 36) — bu, backend'deki `ai_action_approvals` akışının UI karşılığı olduğundan Task/Appointment akışlarından hemen sonra öncelikli yazılmalı.
8. AI Chat (Bölüm 23) — RAG backend'i (Cilt 5) hazır olduğunda entegre edilir; önce basit yapısal sorgular (Cilt 5 §47 tablosundaki ilk satır) ile başlanabilir.
9. Notification Center + WebSocket entegrasyonu (Bölüm 21, 37) eklenir.
10. Future/Should işaretli modüller (Email, Billing, Analytics'in tam kapsamı, Admin'in ileri seviyeleri) feature flag (Bölüm 43) arkasında iskelet olarak eklenir, MVP lansmanını bloklamaz.
11. Storybook (Bölüm 62) ve test altyapısı (Bölüm 61) özellik geliştirmeyle paralel, sona bırakılmadan kurulur.

# Sayfa Kataloğu

| Sayfa | Rota (örnek) | İlgili bölüm | MVP |
|---|---|---|---|
| Login | /login | 16.1 | Must |
| Register | /register | 16.2 | Must |
| Forgot Password | /forgot-password | 16.3 | Must |
| Dashboard | /dashboard | 24 | Must |
| AI Chat | /chat | 23 | Must (basit) |
| Calls | /conversations | 25 | Must |
| Conversation Detail | /conversations/[id] | 26 | Must |
| Tasks | /tasks | 27.1 | Must |
| Task Detail | /tasks/[id] | 27.2 | Must |
| Calendar | /calendar | 28 | Must |
| Appointments | /appointments | 29 | Must |
| Contacts | /contacts | 31 | Must |
| CRM (Kişi Detayı) | /contacts/[id] | 31 | Must |
| Emails | /emails | 30 | Future (iskelet) |
| Analytics | /analytics | 34 | Should |
| Notifications | /notifications (drawer) | 37 | Must |
| AI Approval Center | /approvals | 36 | Must |
| Files | /files | 33 | Should |
| Search | /search (command palette) | 22 | Must |
| Reports | /analytics/reports | 34 | Future |
| Billing | /settings/billing | 40 | Future (iskelet) |
| Organization | /settings/organization | 39 | Must (temel) |
| Users | /admin/users | 41 | Future |
| Roles | /settings/organization/roles | 39 | Future |
| Permissions | /settings/organization/permissions | 39 | Future |
| Settings | /settings | 38 | Must |
| Admin | /admin | 41 | Must (temel) |

# Sonraki Cilt İçin Hazırlık Notları

Cilt 7 (Mobile) hazırlanırken bu cildin şu kararları temel alınmalıdır: Design Token sistemi (Bölüm 7-10) mobilde de aynı isimlendirmeyle (farklı platform implementasyonuyla) kullanılmalı; AI Chat (Bölüm 23) ve AI Approval Center (Bölüm 36) akışları mobilin kendi native bileşenleriyle yeniden üretilecek ama bilgi mimarisi (Sources, Confidence, Onayla/Reddet/Düzenle) birebir korunmalı; Cilt 2 §14'te belirtilen "telefon görüşmesi kısıtları" (iOS/Android otomatik kayıt sınırlamaları) nedeniyle mobilin Calls modülü (Bölüm 25) manuel metin/ses dosyası yükleme odaklı tasarlanmalı, web'deki akıştan farklılaşacağı noktalar Cilt 7'de açıkça işaretlenmelidir.

# Sonraki Adım

Bir sonraki dokümanda Cilt 7 — Mobile (Flutter) hazırlanacaktır. Cilt 7; Flutter mimarisi, Clean Architecture, MVVM, state management, offline mode, push notification, biometric login, tema/widget yapısı ile birlikte bu ciltte tanımlanan AI Chat, AI Approval Center, Dashboard ve Contacts/CRM akışlarının mobil ekran karşılıklarını içermelidir.
