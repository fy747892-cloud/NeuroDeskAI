# CILT 7 — Mobile Application Architecture Documentation: NeuroDesk AI

Sürüm: 1.0
Tarih: 09 Temmuz 2026
Dil: Türkçe
Doküman türü: Mobil Mimari ve Geliştirme Dokümanı, Cilt 7
Kapsam: Flutter mimarisi, offline-first strateji, senkronizasyon, push/local bildirim, AI Chat mobil deneyimi, görüşme sonrası akış, güvenlik, erişilebilirlik, çoklu platform (telefon/tablet/foldable/desktop) ve yayınlama stratejisi

> Not: Bu doküman mobil mimari ve ürün tasarım çerçevesidir; nihai piksel-hassas ekran tasarımının veya mağaza inceleme sürecinin yerine geçmez.

> Süreklilik notu: Bu doküman CILT_1_PRD, CILT_2_SOFTWARE_ARCHITECTURE (özellikle §14 Mobil Uygulama Mimarisi), CILT_4_BACKEND_DESIGN (§27 API Endpoint Kataloğu), CILT_5_AI_ENGINE_DOCUMENTATION ve CILT_6_WEB_APPLICATION_FRONTEND_ARCHITECTURE'ın devamıdır. Mobil, web ile aynı backend API sözleşmelerini (Cilt 4 §27) tüketir — mobile özel endpoint yoktur. Cilt 2 §14'te sabitlenmiş kararlar (Clean Architecture: Presentation/Domain/Data katmanları, Repository pattern, Use case pattern, MVVM, Firebase Cloud Messaging, secure storage, deep link, düşük frekanslı background sync, iOS/Android telefon görüşmesi kayıt kısıtları) bu ciltte değiştirilmemiş, somutlaştırılmıştır: MVVM'in "ViewModel" karşılığı Riverpod provider'larıdır. Cilt 6'nın "Sonraki Cilt İçin Hazırlık Notları" bölümünde belirtildiği gibi, Design Token isimlendirmesi (Cilt 6 §7-10) mobilde aynı adlarla korunmuş, AI Chat/AI Approval Center bilgi mimarisi (Sources, Confidence, Onayla/Reddet/Düzenle) birebir taşınmış ve Calls modülü, iOS/Android'in otomatik görüşme kaydına izin vermemesi nedeniyle manuel metin/ses dosyası yükleme odaklı tasarlanmıştır.
>
> Kapsam genişletme notu: Kullanıcı promptunda istenen Hive + Isar + SQLite üçlüsü, tek bir birincil yerel veritabanı etrafında netleştirilmiştir (Bölüm 12); Desktop Flutter ve Foldable cihaz desteği, Cilt 2 §14'te tanımlanmamış yeni platform hedefleridir ve bu ciltte MVP dışı/ileri faz olarak işaretlenmiştir (Bölüm 46-47). Ses tabanlı arama/dikte (Bölüm 33-34), Cilt 5 §17-18'de MVP dışı bırakılan sunucu tarafı görüşme transkripsiyon (STT) hattından farklıdır — cihaz üzerindeki işletim sistemi dikte API'sini kullanan, yalnızca metin girişini hızlandıran ayrı ve daha hafif bir yetenektir; bu ayrım Bölüm 34'te açıkça belirtilmiştir.

## İçindekiler

1. [Executive Summary](#1-executive-summary)
2. [Mobile Vision](#2-mobile-vision)
3. [Mobile Architecture](#3-mobile-architecture)
4. [Clean Architecture](#4-clean-architecture)
5. [Feature Based Folder Structure](#5-feature-based-folder-structure)
6. [Dependency Injection](#6-dependency-injection)
7. [State Management (Riverpod)](#7-state-management-riverpod)
8. [Navigation (GoRouter)](#8-navigation-gorouter)
9. [Authentication Flow](#9-authentication-flow)
10. [Secure Session Management](#10-secure-session-management)
11. [Offline First Strategy](#11-offline-first-strategy)
12. [Local Database](#12-local-database)
13. [Sync Engine](#13-sync-engine)
14. [Conflict Resolution](#14-conflict-resolution)
15. [Background Synchronization](#15-background-synchronization)
16. [Push Notification Architecture](#16-push-notification-architecture)
17. [Local Notification Strategy](#17-local-notification-strategy)
18. [AI Assistant Mobile Experience](#18-ai-assistant-mobile-experience)
19. [AI Chat Mobile UI](#19-ai-chat-mobile-ui)
20. [Dashboard](#20-dashboard)
21. [Calls Module](#21-calls-module)
22. [Conversations Module](#22-conversations-module)
23. [Tasks Module](#23-tasks-module)
24. [Calendar Module](#24-calendar-module)
25. [Appointments Module](#25-appointments-module)
26. [Email Module](#26-email-module)
27. [Contacts / CRM Module](#27-contacts--crm-module)
28. [Files Module](#28-files-module)
29. [AI Approval Center](#29-ai-approval-center)
30. [Notifications Center](#30-notifications-center)
31. [Analytics](#31-analytics)
32. [Search](#32-search)
33. [Voice Search](#33-voice-search)
34. [Speech-to-Text UX](#34-speech-to-text-ux)
35. [Permissions Management](#35-permissions-management)
36. [Camera Integration](#36-camera-integration)
37. [File Picker](#37-file-picker)
38. [Deep Links](#38-deep-links)
39. [Universal Links](#39-universal-links)
40. [Biometric Login](#40-biometric-login)
41. [Secure Storage](#41-secure-storage)
42. [Encryption](#42-encryption)
43. [Accessibility](#43-accessibility)
44. [Dark Mode](#44-dark-mode)
45. [Responsive Layout](#45-responsive-layout)
46. [Tablet UI](#46-tablet-ui)
47. [Foldable Devices](#47-foldable-devices)
48. [Performance Optimization](#48-performance-optimization)
49. [Battery Optimization](#49-battery-optimization)
50. [Memory Management](#50-memory-management)
51. [Error Handling](#51-error-handling)
52. [Logging](#52-logging)
53. [Crash Reporting](#53-crash-reporting)
54. [Mobile Analytics](#54-mobile-analytics)
55. [Feature Flags](#55-feature-flags)
56. [Remote Config](#56-remote-config)
57. [Localization](#57-localization)
58. [Testing Strategy](#58-testing-strategy)
59. [CI/CD Mobile](#59-cicd-mobile)
60. [Store Release Strategy](#60-store-release-strategy)
61. [Enterprise MDM Support](#61-enterprise-mdm-support)
62. [Future Mobile Features](#62-future-mobile-features)
63. [Uygulama Rehberi](#63-uygulama-rehberi)
64. [Modül Kataloğu](#modül-kataloğu)
65. [Sonraki Cilt İçin Hazırlık Notları](#sonraki-cilt-için-hazırlık-notları)
66. [Sonraki Adım](#sonraki-adım)

# 1. Executive Summary

NeuroDesk AI mobil uygulaması, saha kullanıcılarının (satış temsilcisi, emlak danışmanı, freelancer — Cilt 1 §7 Personalar) günlük iş akışını cepten yönetmesini sağlayan, offline-first ve AI destekli bir Flutter uygulamasıdır. Mimari, Cilt 2 §14'te belirlenen Clean Architecture + MVVM temelini Riverpod, GoRouter, Freezed ve Isar ile somutlaştırır. Uygulamanın MVP kapsamı web ile aynı çekirdek değeri taşır (Cilt 1 §11.2): görüşme metni girme, AI özet/görev/randevu önerisi, onay merkezi, takvim, görevler, kişiler, basit AI Chat, bildirimler — ancak mobile özgü üç yetenek eklenir: push bildirim odaklı anlık farkındalık, sınırlı offline çalışma ve biyometrik hızlı erişim (ileri faz).

Mimarinin en kritik kısıtı, iOS ve Android'in üçüncü taraf uygulamaların telefon görüşmelerini otomatik kaydetmesine izin vermemesidir (Cilt 2 §14); bu nedenle mobil "Calls" deneyimi bir kayıt uygulaması değil, kullanıcının bilinçli olarak metin girdiği veya ses dosyası yüklediği bir AI analiz giriş noktasıdır.

# 2. Mobile Vision

Mobil vizyon, "cepte ikinci beyin" fikrinin en yoğun kullanılan yüzeyi olmaktır: kullanıcı bir görüşmeden çıktığında, bir toplantıya beş dakika kala, ya da metroda internetsizken bile temel işlerini (görev ekleme, not alma, takvime bakma) kesintisiz yapabilmelidir. AI, mobilde bir "sohbet penceresi" olmaktan çok, bildirimler ve Onay Merkezi (Bölüm 29) aracılığıyla kullanıcıyı bulan proaktif bir asistan olarak konumlanır — kullanıcı her zaman uygulamayı açıp sormak zorunda değildir.

# 3. Mobile Architecture

Mobil uygulama, backend ile web'in kullandığı aynı REST API'yi (Cilt 4 §27) ve aynı WebSocket kanalını (Cilt 2 §30, Cilt 6 §21/§37) tüketir. Mimari üç ana eksende kurulur: **Clean Architecture** (Bölüm 4, katman ayrımı), **Offline-first veri akışı** (Bölüm 11-15, yerel veritabanı önce, ağ senkron ikinci), **Riverpod tabanlı reaktif state** (Bölüm 7, UI her zaman tek bir doğruluk kaynağını — local DB + provider state'i — yansıtır, doğrudan API yanıtını değil).

```
UI (Widgets) → Riverpod Providers (ViewModel) → Use Cases (Domain) → Repository (Domain arayüzü)
                                                                          ↓
                                                        Repository Impl (Data) → Local (Isar) + Remote (Dio)
```

# 4. Clean Architecture

| Katman | İçerik | Sorumluluk |
|---|---|---|
| Presentation | Widget'lar, sayfalar, Riverpod `Notifier`/`AsyncNotifier` sınıfları | UI durumu, kullanıcı etkileşimi, navigasyon tetikleme |
| Domain | Entity (Freezed ile immutable), Use Case, Repository arayüzü (soyut) | İş kuralları, platformdan bağımsız saf Dart |
| Data | Repository implementasyonu, DTO (json_serializable), Local/Remote DataSource | API/DB erişimi, DTO↔Entity dönüşümü |

Kural: Domain katmanı hiçbir Flutter/Dio/Isar importu içermez — bu, iş mantığının test edilebilirliğini ve ileride farklı bir UI katmanına (örn. Desktop, Bölüm 47) taşınabilirliğini garanti eder. Presentation katmanı Repository'yi asla doğrudan çağırmaz, her zaman Use Case üzerinden geçer (Cilt 2 §14 "Use case pattern" ile birebir).

# 5. Feature Based Folder Structure

```
lib/
  core/            # DI, router, theme, network client, error types
  shared/          # ortak widget'lar (Design System, Cilt 6 §6-10 tokenlarının Flutter karşılığı)
  features/
    auth/
      presentation/  domain/  data/
    dashboard/
    calls/
    conversations/
    tasks/
    calendar/
    appointments/
    contacts/
    ai_chat/
    ai_approval/
    notifications/
    settings/
```

Her `features/<modül>` klasörü kendi `presentation/domain/data` üçlüsünü taşır (Bölüm 4); modüller arası paylaşım yalnızca `shared/` ve `core/` üzerinden yapılır, modüller birbirini doğrudan import etmez (bağımlılık döngüsünü önlemek için).

# 6. Dependency Injection

Riverpod, hem state management hem DI çözümü olarak kullanılır (ayrı bir `get_it` gibi DI kütüphanesine ihtiyaç yoktur — Riverpod `Provider`ları zaten bir bağımlılık grafiği kurar). Repository ve Use Case'ler `Provider` olarak tanımlanır, test ortamında `ProviderScope(overrides: [...])` ile mock'lanır. Bu, Bölüm 58 Testing Strategy'nin temel mekanizmasıdır.

# 7. State Management (Riverpod)

| State türü | Riverpod yapısı | Örnek |
|---|---|---|
| Sunucu + yerel veri (liste/detay) | `AsyncNotifier` / `StreamNotifier` | Görev listesi (Isar stream'i dinler) |
| Basit UI state | `NotifierProvider` | Aktif sekme, filtre seçimi |
| Türetilmiş/hesaplanan state | `Provider` (computed) | Okunmamış bildirim sayısı |
| Kimlik/oturum | `NotifierProvider` (global) | Auth durumu, aktif tenant |

Riverpod, MVVM'in "ViewModel" rolünü üstlenir (Cilt 2 §14 MVVM kararıyla uyumlu): her `Notifier`, ilgili Use Case'leri çağırır, sonucu UI-hazır bir state'e dönüştürür. Widget'lar yalnızca `ref.watch` ile bu state'i okur, iş mantığı içermez.

# 8. Navigation (GoRouter)

Route yapısı, web'deki route gruplarının (Cilt 6 §15) mobil karşılığıdır: `/auth/*` (kimliksiz), `/app/*` (kimlikli, alt tab bar ile), `/app/settings/*`. GoRouter'ın `redirect` mekanizması, Protected Routes (Cilt 6 §17'nin mobil karşılığı) için kullanılır: geçerli oturum yoksa `/auth/login`'e yönlendirir. Deep link (Bölüm 38) ve push bildirim tıklamaları (Bölüm 16) aynı GoRouter route tablosu üzerinden çözümlenir — bildirimden gelen navigasyon ile uygulama içi navigasyon aynı path şemasını kullanır.

Alt tab bar: Dashboard, AI Chat, Onay Merkezi (rozet ile), Görevler/Takvim (birleşik veya sekmeli), Daha Fazla (Kişiler, Analitik, Ayarlar).

# 9. Authentication Flow

Mobil giriş akışı web ile aynı endpoint'leri kullanır (`/api/v1/auth/login`, `/register`, `/oauth/*`, Cilt 4 §27.1) ve aynı ekran sırasını izler (Login → Register → Forgot Password, Cilt 6 §16). Mobile ek olarak: (1) ilk kurulumdan sonra Biometric Login (Bölüm 40) hızlı giriş seçeneği sunar, (2) OAuth akışları (Google/Microsoft) uygulama içi tarayıcı (`flutter_web_auth` benzeri) ile açılır, native WebView değil — bu, sağlayıcıların güvenlik politikalarıyla uyumluluğu sağlar.

# 10. Secure Session Management

Access/refresh token rotasyonu backend ile aynı sözleşmeyi kullanır (Cilt 2 §17, Cilt 4 §16 Authentication Tasarımı). Mobile'a özgü ek kontroller: **Session Timeout** — uygulama arka planda belirli bir süre (örn. 15 dakika, kurumsal politika ile yapılandırılabilir) kaldıysa ön plana dönüşte PIN/biyometrik tekrar istenir (Bölüm 40); **Token Rotation** — refresh token her kullanımda rotasyona uğrar, eski refresh token tekrar kullanılırsa (token theft belirtisi) tüm oturumlar backend tarafından iptal edilir (Cilt 2 §17 ile uyumlu). Token'lar asla düz metin olarak saklanmaz (Bölüm 41).

# 11. Offline First Strategy

Offline-first, Cilt 2 §14'te "sınırlı destek" olarak işaretlenmiştir; bu cilt bu sınırı senaryo bazında netleştirir: **okuma her zaman offline çalışır** (son senkronize veri Isar'dan gösterilir), **yazma offline kuyruğa alınır** (bağlantı gelince gönderilir), **AI analiz istekleri offline'da başlatılamaz** (sunucu işlemi gerektirir) ama istek kuyruğa alınıp bağlantı gelince otomatik gönderilir.

| Senaryo | Offline davranış |
|---|---|
| Görev oluşturma | Yerel Isar'a `pending_sync=true` ile anında yazılır, UI hemen günceli gösterir, arka planda sync kuyruğuna eklenir (Bölüm 13) |
| Not alma (kişi/görüşme notu) | Aynı desen: yerel yaz, kuyruğa al |
| Takvim görüntüleme | Son senkronize edilen etkinlikler Isar'dan salt okunur gösterilir; "X dakika önce senkronize edildi" etiketiyle |
| AI isteği (görüşme analizi tetikleme) | İstek yerel kuyruğa (`ai_request_outbox`) yazılır, "bağlantı gelince gönderilecek" durumuyla gösterilir; sonuç bağlantı gelip backend işleyince push bildirimle döner |
| Bağlantı gelince senkronizasyon | Bölüm 13 Sync Engine devreye girer, kuyruktaki tüm işlemler sırayla gönderilir |
| Çakışma | Bölüm 14 Conflict Resolution |

# 12. Local Database

Kullanıcı promptunda değerlendirilen üç seçenek (Hive, Isar, SQLite) şu şekilde netleştirilir: **Isar birincil yerel veritabanıdır** — NoSQL, sorgulanabilir, reaktif (`watch()` ile stream), Riverpod `StreamNotifier` ile doğal entegre olur ve offline sync kuyruğu gibi karmaşık sorgu ihtiyaçlarını (Bölüm 13) karşılar. **Hive**, yalnızca çok basit anahtar-değer verileri (tema tercihi, feature flag cache, son senkronizasyon zaman damgası) için, Isar'ın şema yükü gerektirmeyen yerlerde kullanılır. **SQLite** doğrudan kullanılmaz; yalnızca ileride zorunlu üçüncü taraf bir kütüphane SQLite gerektirirse (örn. belirli bir takvim senkron paketi) izole şekilde değerlendirilir — varsayılan mimaride yer almaz.

Isar şemaları, Domain Entity'lerin (Freezed) yerel-kalıcı karşılığıdır (Data katmanında ayrı bir Isar Collection sınıfı olarak tanımlanır, Entity'ye map'lenir); Entity Isar'a bağımlı değildir (Bölüm 4 katman kuralı).

# 13. Sync Engine

Sync Engine, offline kuyruğundaki (`*_outbox` Isar koleksiyonları) işlemleri backend ile uzlaştıran arka plan servisidir. Akış: (1) bağlantı geri geldiğinde (`connectivity_plus` benzeri bir dinleyici) veya periyodik arka plan tetikleyicide (Bölüm 15) tetiklenir, (2) outbox'taki işlemler oluşturulma sırasına göre (FIFO) gönderilir, (3) her işlem başarılı olursa outbox'tan silinir ve ilgili Isar kaydı `pending_sync=false` işaretlenir, (4) başarısız olursa exponential backoff ile yeniden denenir (Cilt 5 §8 retry mantığıyla tutarlı prensip), (5) sunucudan gelen güncel veri (diğer cihazlardan/web'den yapılan değişiklikler dahil) aynı senkronizasyon turunda çekilip Isar'a yazılır (iki yönlü senkron).

# 14. Conflict Resolution

Çakışma, aynı kaydın hem yerelde offline değiştirilip hem sunucuda (web veya başka bir cihazdan) değiştirilmiş olması durumudur. Strateji: **son yazan kazanır (last-write-wins), zaman damgası bazlı**, kritik alanlarda (görev durumu, AI onay durumu) ise **sunucu kazanır** — çünkü AI Approval Center (Bölüm 29) gibi akışlarda sunucu, onayın tekilliğini garanti eden otoritedir (Cilt 5 §51 "expired approval uygulanamaz" kuralıyla tutarlı). Çakışma tespit edildiğinde ve kullanıcı verisi kaybolma riski varsa (örn. hem yerelde hem sunucuda farklı görev başlığı), kullanıcıya sessizce üzerine yazılmaz; bir "senkronizasyon uyarısı" (Bölüm 30 Notifications Center'da) gösterilir ve kullanıcı tercihini seçebilir.

# 15. Background Synchronization

Platform kısıtları (Cilt 2 §14 "platform kısıtlarına uyumlu, düşük frekanslı") nedeniyle arka plan sync, iOS'ta `BGTaskScheduler` (Background Fetch), Android'de `WorkManager`/Background Isolate ile, işletim sisteminin belirlediği aralıklarla (garantili anlık değil, fırsatçı) çalışır. Arka plan senkron, yalnızca küçük/kritik veriyi (bekleyen bildirim sayısı, outbox boyutu) günceller; ağır AI işlemleri arka planda tetiklenmez, yalnızca push bildirimle sonuç alınır (Bölüm 16).

# 16. Push Notification Architecture

Firebase Cloud Messaging (FCM) tüm platformlarda (iOS APNs FCM üzerinden) tek bir bildirim altyapısı sağlar (Cilt 2 §14 ile birebir). Her bildirim türü, GoRouter (Bölüm 8) üzerinden ilgili ekrana deep link taşıyan bir `data` payload'ı içerir.

| Bildirim türü | Tetikleyici | Deep link hedefi | Kullanıcı akışı |
|---|---|---|---|
| AI önerisi | `ai_action_approvals` yeni pending kayıt | `/app/approvals/{id}` | Bildirime dokun → Approval Card açılır → onayla/reddet/düzenle (Bölüm 29) |
| Yaklaşan toplantı | Takvim etkinliği hatırlatma zamanı (Cilt 1 §25) | `/app/calendar/event/{id}` | Etkinlik detayına gider, "yol tarifi/katılımcılar" görünür |
| Görev hatırlatma | Görev `due_date` yaklaşımı | `/app/tasks/{id}` | Görev detayı, hızlı "tamamlandı" aksiyonu |
| Mail analizi tamamlandı | `email_summary` job tamamlandı (Future/ikinci aşama) | `/app/conversations/{id}?type=email` | Analiz sonucu paneli |
| Görüşme analizi tamamlandı | `conversation_summary`/`task_extraction` job tamamlandı | `/app/conversations/{id}` | Görüşme Sonrası Deneyim (Bölüm 18.1) başlar |
| Takvim çakışması | `check-conflicts` sonucu çakışma tespiti | `/app/calendar?highlight={id}` | Çakışan etkinlikler vurgulu gösterilir |
| Abonelik bildirimi | Plan/kota durumu (Future, Cilt 6 §40) | `/app/settings/billing` | Bilgilendirme, aksiyon opsiyonel |
| Sistem bildirimi | Bakım, güvenlik uyarısı | `/app/notifications` | Bildirim merkezinde genel duyuru |

Bildirim izni (Bölüm 35), ilk açılışta değil, kullanıcının ilk anlamlı aksiyonundan sonra (örn. ilk görev oluşturduktan sonra) "bağlamsal izin isteme" deseniyle sorulur — bu, izin kabul oranını artıran bilinen bir mobil UX pratiğidir.

# 17. Local Notification Strategy

Local notification (cihaz üzerinde, sunucu olmadan zamanlanmış), özellikle offline senaryolarda (Bölüm 11) veya kesin zamanlı hatırlatmalarda (Cilt 1 §25 "15 dakika önce" gibi) FCM'in gecikme riskine karşı yedek olarak kullanılır: bir görev/randevu için hatırlatma zamanı geldiğinde, eğer FCM bildirimi ulaşmamışsa (cihaz offline olabilir), önceden Isar'a yazılmış hatırlatma zamanına göre planlanmış local notification tetiklenir. İki mekanizma çakışmayı önlemek için aynı `reminder_id` ile idempotent çalışır (biri tetiklenince diğeri iptal edilir).

# 18. AI Assistant Mobile Experience

## 18.1 Görüşme Sonrası Deneyim Akışı

Mobil, AI'ın değerinin en somut hissedildiği yerdir: kullanıcı bir görüşmeyi bitirdiğinde, uygulamayı açmadan bile sürecin işlediğini bildirimlerle takip eder.

| Adım | Ne olur | İlgili bölüm |
|---|---|---|
| 1. Görüşme bitti | Kullanıcı görüşme metnini girer veya ses dosyası yükler (Bölüm 21) | Calls Module |
| 2. AI analiz başladı | İstek `POST /calls/{id}/analyze` ile gönderilir, ekranda "AI analiz ediyor" durumu; kullanıcı uygulamadan çıkabilir | Cilt 5 §4 AI Pipeline |
| 3. Bildirim geldi | Analiz tamamlanınca push bildirim (Bölüm 16, "Görüşme analizi tamamlandı") | Push Notification Architecture |
| 4. Görev önerisi | Bildirime dokununca Conversation Detail açılır, `task_extraction` sonuçları görünür | Conversations Module (22) |
| 5. Randevu önerisi | Aynı ekranda `appointment_extraction` sonucu, çakışma kontrolü ile birlikte | Calendar Module (24) |
| 6. Mail taslağı | (İkinci aşama/Future) `email_action_extraction` sonucu varsa taslak önizlemesi | Email Module (26) |
| 7. Kullanıcı onayı | Tüm öneriler tek tek veya Onay Merkezi'nden (Bölüm 29) toplu incelenir; onayla/reddet/düzenle | AI Approval Center |
| 8. Takvim güncellendi | Onaylanan randevu, backend'de gerçek etkinliğe dönüşür, mobil takvim (Bölüm 24) bir sonraki sync'te (WebSocket ile anlık) güncellenir | Calendar Module, Sync Engine |

Bu akış boyunca hiçbir adım kullanıcı onayı olmadan (adım 7) kalıcı bir aksiyona dönüşmez — Cilt 5 §51 kuralının mobil deneyimdeki birebir yansımasıdır.

## 18.2 Proaktif Asistan Davranışı

Mobilde AI, yalnızca kullanıcı sorduğunda değil, Dashboard (Bölüm 20) ve bildirimler aracılığıyla proaktif olarak öne çıkar. Ancak "proaktiflik" hiçbir zaman sessiz otomasyon anlamına gelmez (Bölüm 18.1 madde 7); yalnızca kullanıcının dikkatini doğru zamanda doğru bilgiye yönlendirmektir.

# 19. AI Chat Mobile UI

| Alan | Detay |
|---|---|
| Amaç | Cilt 6 §23'teki AI Chat'in mobil, tek elle kullanılabilir karşılığı |
| Klasör yapısı | `features/ai_chat/{presentation,domain,data}` |
| State | `AsyncNotifier<ChatSessionState>` (mesaj listesi + streaming durumu) |
| Repository | `AiChatRepository` (Domain arayüz) → `AiChatRepositoryImpl` (Data) |
| Service | `AiChatRemoteDataSource` (Dio + WebSocket/SSE stream) |
| API | POST /api/v1/ai/chat, GET /ai/chat/sessions, GET /ai/chat/sessions/{id}, POST /ai/feedback (Cilt 4 §27.4) |
| Offline davranışı | Geçmiş sohbetler Isar'dan offline okunabilir; yeni mesaj gönderme offline'da devre dışı, net bir "bağlantı gerekli" durumu gösterilir (AI çağrısı sunucu gerektirir, Bölüm 11) |
| Cache | Son N oturum Isar'da tutulur, eskiler yalnızca istenince sunucudan çekilir |
| Loading | Streaming yanıt sırasında yazıyor animasyonu (Typing Animation) |
| Error | Bölüm 51 genel deseni + "tekrar dene" balonu |
| Retry | Kullanıcı tetikli, otomatik retry yok (AI maliyeti nedeniyle) |
| Permission | Mikrofon (Bölüm 33 Voice Input için) |
| UI/UX | Conversation List (üstte yatay kaydırmalı geçmiş özet çipleri veya ayrı sekme), Prompt Suggestions (Cilt 5 §47 örnek sorular), Voice Input (mikrofon ikonu, Bölüm 33-34), Streaming Response + Typing Animation, Source Chip'ler (Cilt 6 §23 ile aynı bileşen dili), Confidence Badge, Feedback (👍/👎), History (oturum listesi), Memory (Short Term Memory göstergesi gerekmez, kullanıcıya görünmez çalışır) |
| Navigation | `/app/chat`, `/app/chat/{sessionId}` |

Mobil AI Chat, masaüstünden farklı olarak varsayılan olarak **tam ekran** çalışır (yan panel yerine Sources bir alt sheet olarak açılır, Cilt 6 §54 Drawers desenine paralel).

# 20. Dashboard

| Alan | Detay |
|---|---|
| Amaç | Cilt 6 §24'ün mobil karşılığı — günlük özet tek ekranda |
| Klasör yapısı | `features/dashboard/*` |
| State | `AsyncNotifier<DashboardState>`, alt widget'lar bağımsız `Provider`larla beslenir (bir kart hatası diğerlerini etkilemez) |
| Repository/Service | `DashboardRepository` → REST (Cilt 4 §27.11) + Isar cache-first okuma |
| API | GET /dashboard, /dashboard/daily-summary, /dashboard/upcoming, /dashboard/pending-actions, /dashboard/ai-suggestions |
| Offline davranışı | Son senkronize dashboard verisi Isar'dan gösterilir, üstte "X dakika önce güncellendi" |
| Cache | 5 dakikalık TTL, pull-to-refresh ile manuel yenileme |
| Loading | Kart bazlı skeleton (Cilt 6 §49 desenine paralel) |
| Error/Retry | Kart bazlı, sessiz retry + manuel "tekrar dene" |
| Permission | Yok (temel okuma) |
| UI/UX | Dikey kaydırmalı kart listesi (web'deki grid yerine, tek kolon mobil öncelik), üstte AI Günlük Özet kartı |
| Navigation | `/app/dashboard` (alt tab bar ana sekmesi) |

# 21. Calls Module

| Alan | Detay |
|---|---|
| Amaç | Görüşme metni girme veya ses dosyası yükleyerek AI analizi başlatma |
| Klasör yapısı | `features/calls/*` |
| State | `NotifierProvider<CallDraftState>` (form durumu) + `AsyncNotifier<CallListState>` |
| Repository/Service | `CallRepository`, upload için `FileUploadService` (Bölüm 28 ile paylaşımlı) |
| API | POST /api/v1/calls/text, POST /calls/{id}/analyze, GET /conversations (Cilt 4 §27.3) |
| Offline davranışı | Metin taslağı Isar'a offline kaydedilir (`pending_sync`), bağlantı gelince gönderilir; ses dosyası offline'da yerel depoda bekletilir, büyük dosya olduğundan yalnızca Wi-Fi'de otomatik yükleme opsiyonu sunulur |
| Cache | Görüşme listesi Isar'da, son 90 gün varsayılan pencere |
| Loading/Error/Retry | Yükleme ilerleme çubuğu; analiz hatası Bölüm 51 deseni + tekrar dene |
| Permission | Dosya erişimi (ses dosyası seçimi), **mikrofon değil** — MVP'de canlı kayıt yoktur |
| UI/UX | "Yeni Görüşme" büyük CTA, metin girme veya dosya seçme seçenekleri; **hiçbir otomatik arama kaydı özelliği yoktur** ve arayüzde bu açıkça iletilir (yasal/platform kısıtı, giriş notu ve Cilt 2 §14) |
| Navigation | `/app/calls`, `/app/calls/new` |

# 22. Conversations Module

| Alan | Detay |
|---|---|
| Amaç | Görüşme detayı + AI analiz sonuçları (Cilt 6 §26 mobil karşılığı) |
| Klasör yapısı | `features/conversations/*` |
| State | `AsyncNotifier<ConversationDetailState>` |
| API | GET /conversations/{id}, /calls/{id}/analysis |
| Offline davranışı | Son görüntülenen detaylar Isar'dan okunur |
| UI/UX | Transkript katlanabilir (Accordion → mobilde ExpansionTile), AI önerileri kart listesi, her kart doğrudan Onay Merkezi eylemlerine bağlı |
| Navigation | `/app/conversations/{id}` |

# 23. Tasks Module

| Alan | Detay |
|---|---|
| Amaç | Görev listesi ve detayı (Cilt 6 §27) |
| Klasör yapısı | `features/tasks/*` |
| State | `AsyncNotifier<TaskListState>` (Isar `watch()` ile reaktif), filtre `NotifierProvider` |
| API | GET /tasks, /tasks/overdue, POST /tasks/{id}/complete, POST /tasks (Cilt 4 §27.5) |
| Offline davranışı | Tam offline CRUD: oluşturma/tamamlama offline çalışır, outbox'a yazılır (Bölüm 11 tablosu) |
| Cache | Isar birincil kaynak; liste UI'ı doğrudan Isar stream'inden beslenir, API yalnızca senkron kaynağıdır |
| Loading/Error/Retry | Anlık (Isar'dan okuma gecikmesizdir); sync hatası ayrı, sessiz arka plan göstergesiyle |
| Permission | Yok |
| UI/UX | Swipe-to-complete, swipe-to-snooze; pull-to-refresh senkron tetikler |
| Navigation | `/app/tasks`, `/app/tasks/{id}` |

# 24. Calendar Module

| Alan | Detay |
|---|---|
| Amaç | Cilt 6 §28'in mobil karşılığı |
| API | GET /calendar/events, POST /appointments/check-conflicts |
| Offline davranışı | Son senkronize etkinlikler görüntülenir; yeni etkinlik oluşturma offline'da kuyruğa alınır ancak çakışma kontrolü sunucu gerektirdiğinden yalnızca bağlantı gelince kesinleşir, offline'da "geçici, çakışma kontrol edilecek" etiketiyle gösterilir |
| UI/UX | Mobilde varsayılan görünüm Agenda/Day (Month görünümü küçük ekranda ikincil, Cilt 6 §28'in mobil daralması); Week/Month yatay kaydırmalı |
| Navigation | `/app/calendar` |

# 25. Appointments Module

| Alan | Detay |
|---|---|
| Amaç | Randevu listesi/formu (Cilt 6 §29 mobil karşılığı) |
| API | GET/POST /appointments, PATCH/DELETE /appointments/{id} |
| Offline davranışı | Bölüm 24 ile aynı prensip |
| UI/UX | Form tek ekran, adım adım değil (kısa form ilkesi, Cilt 6 §4 UX Principles) |
| Navigation | `/app/appointments` |

# 26. Email Module

Cilt 1 ve Cilt 6 ile tutarlı şekilde **MVP dışı/ikinci aşama**; mobilde iskelet route + "yakında" boş durumu (Cilt 6 §48 Empty States deseniyle aynı dil) olarak planlanır, feature flag (Bölüm 55) arkasında.

# 27. Contacts / CRM Module

| Alan | Detay |
|---|---|
| Amaç | Cilt 6 §31'in mobil karşılığı |
| API | GET/POST /contacts, /contacts/{id}, /contacts/{id}/timeline, /contacts/{id}/notes |
| Offline davranışı | Kişi listesi ve son görüntülenen kişi detayları Isar'da; not ekleme offline çalışır (outbox) |
| Cache | Sık erişilen (son 30 gün içinde açılan) kişiler önceliklendirilerek Isar'da tutulur, tümü değil (depolama optimizasyonu) |
| UI/UX | Sekmeler yerine mobilde dikey bölümler (Timeline, Görevler, AI Hafızası) tek sayfada kaydırmalı; arama üstte sabit |
| Navigation | `/app/contacts`, `/app/contacts/{id}` |

# 28. Files Module

| Alan | Detay |
|---|---|
| Amaç | Dosya yükleme/görüntüleme (Cilt 6 §33 mobil karşılığı) |
| API | POST /files/upload-url, /files/complete-upload, GET /files |
| Offline davranışı | Yükleme kuyruğa alınır (özellikle büyük dosyalarda Wi-Fi bekleme opsiyonu, Bölüm 49 Battery/Data tasarrufu) |
| UI/UX | Kamera (Bölüm 36) veya dosya seçici (Bölüm 37) ile ekleme |
| Navigation | `/app/files` |

# 29. AI Approval Center

| Alan | Detay |
|---|---|
| Amaç | Cilt 6 §36'nın mobil karşılığı — mobilin en sık ziyaret edilen ekranlarından biri (push bildirimlerin çoğu buraya yönlendirir) |
| Klasör yapısı | `features/ai_approval/*` |
| State | `AsyncNotifier<ApprovalListState>`, aksiyon başına `AsyncValue` (kart bazlı yükleme) |
| Repository/Service | `AiApprovalRepository` |
| API | POST /ai/actions/{id}/approve, /reject, PATCH /ai/actions/{id} (Cilt 4 §27.4) |
| Offline davranışı | Onay/red **offline'da yapılamaz** (geri alınamaz bir sunucu-otorite aksiyonu, Bölüm 14 kararıyla tutarlı); offline'da kartlar salt okunur gösterilir, aksiyon butonları "bağlantı gerekli" ile devre dışı |
| Cache | Bekleyen öneriler Isar'da tutulur (okuma offline çalışsın diye), ama mutasyon her zaman online |
| Loading | Kart üzerinde inline spinner (Cilt 6 §36 ile birebir aynı UX dili) |
| Error | Toast + kart durumu değişmez |
| Retry | Kullanıcı tetikli |
| Permission | Yok (kullanıcının kendi önerileri) |
| UI/UX | Alt tab bar'da rozet sayaçlı sabit sekme; swipe-to-approve / swipe-to-reject jestleri + her zaman erişilebilir buton alternatifi (jest tek başına yeterli etkileşim yolu olmamalı, Bölüm 43 Accessibility) |
| Navigation | `/app/approvals`, `/app/approvals/{id}` |

Düzenleme akışı (Cilt 6 §36 "Düzenle" ile birebir) mobilde tam ekran bir form olarak açılır, modal değil (küçük ekranda form + klavye için yer kazanmak amacıyla).

# 30. Notifications Center

| Alan | Detay |
|---|---|
| Amaç | Cilt 6 §37'nin mobil karşılığı, kalıcı bildirim geçmişi |
| API | GET /notifications, PATCH /notifications/{id}/read |
| Offline davranışı | Isar'dan okunur, okundu işaretleme offline çalışır (outbox) |
| UI/UX | Tam ekran liste (drawer değil, mobilde ayrı sekme/sayfa), tipe göre ikonlanmış, dokununca Bölüm 16 tablosundaki ilgili deep link'e gider |
| Navigation | `/app/notifications` |

# 31. Analytics

Cilt 6 §34 ile aynı MVP durumu (Should/kısmi); mobilde basitleştirilmiş, yalnızca özet metrik kartları (grafik etkileşimi masaüstü kadar zengin değildir, Recharts'ın mobil-uyumlu sade varyantı kullanılır). `/app/analytics`.

# 32. Search

| Alan | Detay |
|---|---|
| Amaç | Cilt 6 §22'nin mobil karşılığı |
| API | GET /search, POST /search/semantic |
| Offline davranışı | Yalnızca yerel Isar içeriği üzerinde temel metin araması offline çalışır; semantic search her zaman online |
| UI/UX | Alt tab bar'daki arama ikonu tam ekran arama sayfası açar (masaüstündeki command palette yerine, dokunmatik için daha uygun) |
| Navigation | `/app/search` |

# 33. Voice Search

Ses ile arama, cihazın **yerel işletim sistemi konuşma tanıma API'sini** (iOS Speech framework / Android `SpeechRecognizer`) kullanarak, kullanıcının söylediğini metne çevirip Arama (Bölüm 32) veya AI Chat (Bölüm 19) girişine dolduran bir kolaylık özelliğidir — Bölüm 34'te netleştirildiği gibi bu, Cilt 5'teki sunucu tarafı görüşme transkripsiyon hattından tamamen ayrıdır. Mikrofon izni (Bölüm 35) yalnızca bu özellik tetiklendiğinde istenir.

# 34. Speech-to-Text UX

Mikrofon ikonuna basılı tutma → dinleme animasyonu → gerçek zamanlı kısmi metin gösterimi (cihaz API'sinin desteklediği ölçüde) → bırakınca metin girişe yazılır, kullanıcı gönder/düzenle. Bu akış AI Chat (Bölüm 19 Voice Input) ve Arama'da (Bölüm 32) aynı bileşenle tekrar kullanılır. **Netleştirme**: bu özellik görüşme kaydı/transkripsiyonu değildir, yalnızca kullanıcının kendi anlık dikte girişidir; Cilt 5 §17-18'deki STT pipeline hâlâ MVP dışıdır ve Calls Module'de (Bölüm 21) kullanılmaz.

# 35. Permissions Management

| İzin | Ne zaman istenir | Kullanım alanı |
|---|---|---|
| Bildirim | İlk anlamlı aksiyondan sonra (Bölüm 16) | Push bildirimler |
| Dosya erişimi | Calls/Files modülünde dosya seçerken | Ses dosyası, belge yükleme |
| Mikrofon | Voice Search/Chat ilk kullanımda | Bölüm 33-34 |
| Takvim (isteğe bağlı, cihaz takvimiyle iki yönlü senkron ileri faz) | İlgili ayar açıldığında | Bölüm 62 Future |

İzin reddedilirse özellik devre dışı kalır ama uygulama genel işlevini kaybetmez (graceful degradation); Ayarlar'dan (Cilt 6 §38 mobil karşılığı) izin durumu tekrar gözden geçirilebilir ve sistem izin ekranına yönlendirilir.

# 36. Camera Integration

Kamera, belge/kartvizit fotoğrafı çekmek için Files Module (Bölüm 28) ve Contacts Module'e (Bölüm 27, kartvizitten kişi oluşturma — ileri faz) entegre edilir. MVP'de yalnızca "fotoğraf çek → dosya olarak ekle" akışı vardır; OCR/otomatik kişi çıkarımı Cilt 5 §22 OCR Pipeline'ın MVP dışı olması nedeniyle ileri fazdır.

# 37. File Picker

Platform native dosya seçici (iOS Files / Android Storage Access Framework) kullanılır; seçilen dosya Bölüm 28 Files Module akışına (upload URL → yükleme → finalize) girer. Büyük ses dosyalarında (Calls Module, Bölüm 21) format/boyut client-side ön kontrolü yapılır.

# 38. Deep Links

Deep link şeması (`neurodesk://...` custom scheme, iç navigasyon ve push bildirim payload'ları için) Bölüm 16 tablosundaki hedeflerle birebir örtüşür (Cilt 2 §14 "Deep link: randevu, görev, bildirim ve kişi kartı açma" ile uyumlu, bu ciltte AI Approval ve Conversation Detail eklenerek genişletilmiştir).

# 39. Universal Links

Universal Links (iOS) / App Links (Android), `https://app.neurodesk.ai/...` gibi gerçek web URL'lerinin doğrudan uygulamayı açmasını sağlar — örn. e-postayla paylaşılan bir görev/randevu bağlantısı, uygulama kuruluysa mobilde, değilse web'de (Cilt 6) açılır. Aynı path şeması hem web (Cilt 6 §15) hem mobil (Bölüm 8) route yapısında paralel tutulur ki bu geçiş sorunsuz çalışsın.

# 40. Biometric Login

Cilt 2 §14'te "ileri faz" olarak işaretlenmiştir; bu cilt mimarisini tanımlar ama MVP kapsamına dahil etmez. Biyometrik giriş (Face ID/Touch ID/Android Biometric), yalnızca bir kez yapılmış e-posta/şifre veya OAuth girişinin ardından, cihazın güvenli donanımında (Keychain/Keystore) saklanan bir token'ı açmak için kullanılır — biyometrik veri asla backend'e gönderilmez, yalnızca cihaz üzerinde doğrulanır. Başarısız biyometrik deneme sonrası PIN/şifre alternatifi her zaman sunulur.

# 41. Secure Storage

Access/refresh token, biyometrik ile korunan yerel anahtar ve hassas kullanıcı tercihleri, platformun güvenli deposunda (iOS Keychain, Android Keystore — `flutter_secure_storage` benzeri bir soyutlama üzerinden) saklanır; Isar (Bölüm 12) genel uygulama verisi için kullanılır ama token gibi sırlar için kullanılmaz. Bu ayrım, Isar veritabanı şifrelemesi (Bölüm 42) ile token güvenliğinin birbirinden bağımsız katmanlar olmasını sağlar.

# 42. Encryption

**Encrypted Local DB**: Isar, AES tabanlı veritabanı şifrelemesiyle (encryption-at-rest) açılır; şifreleme anahtarı Secure Storage'da (Bölüm 41) tutulur, kod içine gömülmez. **Certificate Pinning**: Dio HTTP client, backend API sertifikasını pinler (man-in-the-middle önleme); pin uyuşmazlığında istek reddedilir ve kullanıcıya güvenlik uyarısı gösterilir — bu, Cilt 2 §32 Security Architecture'ın mobile özgü uzantısıdır. Ağ üzerindeki tüm trafik TLS ile şifrelidir (Cilt 2 §32 ile uyumlu).

# 43. Accessibility

Flutter'ın `Semantics` widget'ları tüm etkileşimli bileşenlerde kullanılır; dinamik tip boyutu (sistem font ölçeği) desteklenir, sabit piksel boyutlu metin kullanılmaz. Onay Merkezi'ndeki swipe jestleri (Bölüm 29) her zaman buton alternatifiyle birlikte sunulur — TalkBack/VoiceOver kullanıcıları jestlere bağımlı kalmaz. Renk kontrastı ve confidence göstergesi kuralları Cilt 6 §13 ile birebir aynıdır (renk + ikon + metin).

# 44. Dark Mode

Tema token sistemi Cilt 6 §7-10'daki isimlendirmeyi birebir kullanır (Flutter `ThemeExtension` ile uygulanır); sistem teması takip edilir, kullanıcı override edebilir (Ayarlar, Bölüm 27 mobil Settings). AI confidence renkleri (Cilt 6 §9) dark modda ayrıca kalibre edilmiş halleriyle kullanılır.

# 45. Responsive Layout

Flutter'ın `LayoutBuilder`/`MediaQuery` ile genişlik bazlı adaptif düzen: telefon (tek kolon, alt tab bar), tablet (Bölüm 46, iki panel — liste + detay yan yana), foldable (Bölüm 47, katlanma durumuna duyarlı). Bu, Cilt 6 §12 Responsive Design'ın mobil-native karşılığıdır; kırılım noktaları piksel yerine mantıksal genişlik sınıflarıyla (compact/medium/expanded, Material 3 window size class'larına paralel) tanımlanır.

# 46. Tablet UI

Tablet'te (expanded genişlik sınıfı) liste ekranları (Tasks, Contacts, Conversations) iki panelli görünüme geçer: sol panelde liste, sağ panelde seçili öğenin detayı — bu, telefonun tam ekran push-navigasyon modelinden farklıdır ve web'in (Cilt 6) çok kolonlu düzenine daha yakındır. Alt tab bar, tablette yan sabit rail navigasyona (`NavigationRail`) dönüşür. MVP kapsamı: temel modüllerde (Tasks, Contacts, Dashboard) tablet optimizasyonu "Should"; tüm modüllerin tablet-özel ince ayarı ileri fazdır.

# 47. Foldable Devices

Foldable cihaz desteği (katlanma sırasında layout'un iki ekran bölgesine ayrılması, `flutter_displaymode`/`WindowManager` API'leri) Cilt 2 §14'te tanımlanmamış, bu ciltte eklenen bir platform hedefidir ve **MVP dışı/ileri faz** olarak işaretlenir. Mimari olarak Bölüm 45'teki adaptif düzen sistemi zaten foldable'ı bir "expanded/dual-pane" durumu olarak ele alacak şekilde tasarlandığından, foldable desteği ayrı bir mimari değil, mevcut responsive sistemin ek bir test/kalibrasyon yüzeyidir.

# 48. Performance Optimization

Hedefler: soğuk başlatma < 2sn, liste kaydırmada 60fps. Teknikler: Isar sorgularının sayfalanması (büyük listelerde `limit/offset`), görsel önbellekleme (`cached_network_image` benzeri), widget rebuild'lerini `Riverpod.select` ile minimize etme (yalnızca değişen alt state dinlenir), büyük listelerde `ListView.builder` (lazy render). AI Chat streaming (Bölüm 19) yanıtı parça parça render eder, tüm yanıtı bekletmez.

# 49. Battery Optimization

Arka plan senkron (Bölüm 15) işletim sisteminin enerji tasarrufu kısıtlarına uygun, düşük frekanslı çalışır; WebSocket bağlantısı (bildirimler için) uygulama ön plandayken açık tutulur, arka planda kapatılıp push bildirime devredilir (sürekli arka plan soket bağlantısı pil tüketimini artırır). Büyük dosya yüklemeleri (Bölüm 21, 28) varsayılan olarak yalnızca Wi-Fi'de otomatik başlar, mobil veride kullanıcı onayı istenir.

# 50. Memory Management

Isar sorguları stream bazlı tüketilir (tüm sonuç kümesi belleğe alınmaz), büyük transkript/mesaj listelerinde sanallaştırma (Bölüm 48) kullanılır. Görsel/dosya önbelleği için boyut ve süre sınırı tanımlanır (LRU eviction), sınırsız büyümez.

# 51. Error Handling

Hata katmanları Cilt 6 §20 ile paralel yapıdadır: alan bazlı form hatası (Bölüm 52 web karşılığı, Flutter'da `flutter_form_builder`/Riverpod form state ile), sayfa bazlı hata widget'ı (network hatası, boş/hata durumu ayrımı), global toast/snackbar (kritik olmayan hatalar). Offline'da başarısız olan işlemler "hata" değil "senkronizasyona alındı" olarak gösterilir (Bölüm 11) — kullanıcıyı gereksiz yere endişelendirmemek için bu ayrım önemlidir.

# 52. Logging

Yapılandırılmış loglama (seviye: debug/info/warn/error), prod'da yalnızca warn/error uzak sisteme (Crashlytics'e ek breadcrumb olarak, Bölüm 53) gönderilir; hassas veri (token, transkript içeriği, kişisel bilgi) asla loglanmaz (Cilt 5 §71 AI Security ilkesiyle tutarlı). Debug build'de daha ayrıntılı yerel log konsolu aktif tutulur.

# 53. Crash Reporting

Firebase Crashlytics, çökme ve yakalanmamış hataları raporlar; her rapora tenant/kullanıcı kimliği değil, anonim/pseudonymous bir cihaz/oturum kimliği eklenir (KVKK/GDPR uyumluluğu, Cilt 5 §58 ile tutarlı prensip). Kritik akışlarda (Bölüm 18.1, Bölüm 29) özel breadcrumb'lar (adım adım iz) eklenir ki bir çökme öncesi tam kullanıcı yolu görülebilsin.

# 54. Mobile Analytics

Firebase Analytics, ürün kullanım metriklerini (Cilt 1 §44 Başarı Metrikleri'nin mobil kırılımı: ekran görüntüleme, AI öneri kabul oranı, Onay Merkezi kullanım sıklığı) toplar. Analytics event'leri, kişisel/hassas veri (görüşme içeriği, mail body) taşımaz — yalnızca davranışsal, anonimleştirilmiş event isimleri ve sayısal metrikler.

# 55. Feature Flags

Cilt 6 §43 ile aynı mekanizmanın mobil karşılığı: MVP dışı modüller (Email, Billing, Roller/İzinler, Biometric Login MVP açılana kadar) Remote Config (Bölüm 56) tabanlı flag'lerle kapatılır/açılır; store'a yeni sürüm göndermeden kademeli açılış yapılabilir.

# 56. Remote Config

Firebase Remote Config, feature flag değerlerini ve bazı davranışsal parametreleri (örn. session timeout süresi, sync sıklığı aralığı) uygulama güncellemesi gerektirmeden ayarlamak için kullanılır. Remote Config değerleri her zaman güvenli varsayılanlarla (fail-safe defaults) gelir; sunucudan değer çekilemezse uygulama en kısıtlayıcı/güvenli davranışa düşer.

# 57. Localization

Cilt 6 §57 ile birebir aynı ilke: MVP'de Türkçe tek dil, tüm metinler anahtar bazlı i18n üzerinden okunur (`flutter_localizations` + ARB dosyaları), hardcoded string yok. Tarih/saat biçimlendirmesi cihaz yerel ayarına değil, uygulama içi seçili dile göre yapılır (tutarlılık için).

# 58. Testing Strategy

| Seviye | Araç | Kapsam |
|---|---|---|
| Unit Test | `flutter_test` + Riverpod test yardımcıları | Use Case'ler, Repository mantığı, mapper'lar |
| Widget Test | `flutter_test` | Tekil widget'lar, form doğrulama |
| Golden Test | `golden_toolkit` benzeri | Design System bileşenleri (Cilt 6 §14 karşılığı), light/dark tema görsel regresyon |
| Integration Test | `integration_test` | Kritik yollar: giriş, görev oluşturma (offline dahil), AI onaylama, push bildirimden deep link |
| Performance Test | Flutter DevTools + manuel profil | Liste kaydırma fps, soğuk başlatma süresi (Bölüm 48 hedefleriyle) |
| Offline Test | Integration test + network koşullu simülasyon (`connectivity_plus` mock) | Bölüm 11 senaryo tablosunun tamamı |
| Push Notification Test | Manuel + FCM test konsolu | Bölüm 16 tablosundaki her bildirim türü → doğru deep link |
| Accessibility Test | `flutter_test` semantics assertion + manuel VoiceOver/TalkBack | Bölüm 43 kriterleri |

AI Approval Center (Bölüm 29) ve Görüşme Sonrası Deneyim (Bölüm 18.1), en yüksek iş etkisine sahip akışlar olduğundan Integration Test kapsamında önceliklidir (Cilt 6 §61 ile aynı önceliklendirme mantığı).

# 59. CI/CD Mobile

CI pipeline (Cilt 2 §42 CI/CD Mimarisi'nin mobil uzantısı): her PR'da unit/widget/golden test + statik analiz (`flutter analyze`); `main`'e merge'de otomatik build (iOS/Android) + internal test kanalına (TestFlight/Play Internal Testing) dağıtım; sürüm etiketlemede store release pipeline'ı (Bölüm 60) tetiklenir. Codesigning sırları (Apple sertifikası, Android keystore) CI secret store'da tutulur, repoya asla commit edilmez.

# 60. Store Release Strategy

Aşamalı yayın: (1) internal test (ekip), (2) kapalı beta (TestFlight/Play beta, seçili gerçek kullanıcılar), (3) kademeli üretim yayını (Play Store'da %10→%50→%100 staged rollout; App Store'da benzer phased release), (4) her aşamada Crashlytics (Bölüm 53) ve Analytics (Bölüm 54) izlenerek anormal çökme/hata oranında yayın durdurulabilir. Zorunlu güncelleme mekanizması (kritik güvenlik yaması gibi durumlar için) Remote Config (Bölüm 56) üzerinden minimum sürüm kontrolüyle uygulanır.

# 61. Enterprise MDM Support

Kurumsal müşteriler için (Cilt 1 §14, Cilt 6 §65 ile hizalı) Mobile Device Management desteği: uygulamanın MDM üzerinden (Intune, Jamf gibi) dağıtılabilmesi, App Config (yapılandırma push'u — örn. varsayılan tenant, SSO ayarları) desteği, kurumsal politika ile zorunlu PIN/biyometrik ve ekran görüntüsü engelleme (Screen Capture Protection, hassas ekranlarda — AI Chat, Onay Merkezi, Kişi Hafızası — kurumsal politika açıkken aktif). Bu bölüm MVP dışıdır, Enterprise fazına aittir.

# 62. Future Mobile Features

Değerlendirme havuzu: cihaz takvimiyle iki yönlü senkron, kartvizit OCR ile otomatik kişi oluşturma (Bölüm 36, Cilt 5 §22 OCR bağımlılığı), widget/ana ekran kısayolları (bugünkü görevler widget'ı), Apple Watch/Wear OS bildirim uzantısı, offline AI (cihaz üzerinde küçük model ile temel özetleme — büyük ölçüde araştırma aşaması, taahhüt değil).

# 63. Uygulama Rehberi

Mobil kod üretimine başlanacağında izlenmesi önerilen sıra:

1. Proje iskeleti: Feature Based Folder Structure (Bölüm 5), Riverpod + GoRouter + Dio + Isar kurulumu (Bölüm 6-8, 12).
2. Design token'ların Flutter `ThemeExtension` olarak taşınması (Bölüm 44), Cilt 6 Design System bileşenlerinin Flutter widget karşılıklarının (`shared/widgets`) oluşturulması.
3. Authentication akışı (Bölüm 9-10) uçtan uca — Secure Storage (Bölüm 41) dahil.
4. Isar şemaları + Sync Engine + Offline outbox mekanizması (Bölüm 12-15) — bu, sonraki tüm modüllerin üzerine kurulacağı temel.
5. Tasks Module (Bölüm 23) — tam offline CRUD'un ilk referans implementasyonu olarak.
6. Calls + Conversations Module (Bölüm 21-22) — Görüşme Sonrası Deneyim akışının (Bölüm 18.1) iskeleti.
7. AI Approval Center (Bölüm 29) — push bildirim entegrasyonuyla (Bölüm 16) birlikte, bu akışın MVP'nin kritik yolu olması nedeniyle erken tamamlanmalı.
8. Calendar/Appointments, Contacts (Bölüm 24-25, 27).
9. AI Chat Mobile UI (Bölüm 19) — RAG backend'i hazır olduğunda; önce Bölüm 18.2'deki proaktif/bildirim tabanlı AI deneyimine öncelik verilebilir.
10. Crash reporting, analytics, remote config (Bölüm 53-56) özellik geliştirmeyle paralel, sona bırakılmadan kurulur.
11. Tablet/Foldable/Desktop (Bölüm 46-47) ve Biometric Login (Bölüm 40) gibi ileri faz/MVP dışı öğeler, temel telefon deneyimi stabil olduktan sonra ele alınır.

# Modül Kataloğu

| Modül | Rota | MVP | Offline desteği |
|---|---|---|---|
| Auth (Login/Register/Forgot Password) | /auth/* | Must | Kısmi (yalnızca oturum kontrolü) |
| Dashboard | /app/dashboard | Must | Okuma |
| AI Chat | /app/chat | Must (basit) | Okuma (geçmiş) |
| Calls | /app/calls | Must | Yazma (outbox) |
| Conversations | /app/conversations/{id} | Must | Okuma |
| Tasks | /app/tasks | Must | Tam (okuma+yazma) |
| Calendar | /app/calendar | Must | Okuma + kısıtlı yazma |
| Appointments | /app/appointments | Must | Okuma + kısıtlı yazma |
| Contacts/CRM | /app/contacts | Must | Okuma + not yazma |
| AI Approval Center | /app/approvals | Must | Yalnızca okuma (mutasyon online) |
| Notifications Center | /app/notifications | Must | Okuma + okundu işaretleme |
| Search | /app/search | Must (temel) | Yerel arama |
| Files | /app/files | Should | Yükleme kuyruğu |
| Analytics | /app/analytics | Should | Okuma (cache) |
| Voice Search | (bileşen, Chat/Search içinde) | Should | Hayır (cihaz API'si online gerekmez ama sonuç işleme online) |
| Email | /app/emails | Future (iskelet) | — |
| Biometric Login | (Auth eklentisi) | Future | — |
| Tablet UI optimizasyonu | (tüm modüller) | Should (temel modüllerde) | — |
| Foldable / Desktop Flutter | (platform) | Future | — |
| Enterprise MDM | (platform) | Future | — |

# Sonraki Cilt İçin Hazırlık Notları

Orijinal 15 cilt planında Cilt 8, 100 ekranlık bir UI/UX kataloğu olarak tanımlanmıştı; bu kapsamın büyük kısmı artık Cilt 6 (Sayfa Kataloğu) ve Cilt 7 (Modül Kataloğu) tarafından zaten karşılanmış durumdadır. Bu nedenle sıradaki cildin **Cilt 8 — Security** (orijinal plandaki Cilt 9) olarak devam etmesi önerilir: bu ciltte dağınık halde duran güvenlik kararları (Cilt 2 §32, Cilt 5 §54-58 ve §71, Cilt 6 §60, Cilt 7 Bölüm 40-42/61) tek bir uçtan uca güvenlik/uyumluluk dokümanında (JWT/OAuth detayları, KVKK/GDPR uygulama checklist'i, pentest/SOC2 hazırlığı) birleştirilip derinleştirilebilir. Tercih ürün sahibine aittir; istenirse orijinal sıradaki UI/UX kataloğu da ayrıca (yalnızca eksik kalan admin/ileri faz ekranlar için) hazırlanabilir.

# Sonraki Adım

Bir sonraki doküman için önerilen başlık **Cilt 8 — Security Documentation**'dır (JWT/OAuth/AES/RBAC/ABAC derinliği, KVKK/GDPR uygulama checklist'i, rate limiting/audit/SIEM, ISO 27001/SOC2 hazırlığı — orijinal 15 cilt planındaki Cilt 9 kapsamı). Ürün sahibi farklı bir sıra tercih ederse (örn. Database/Backend'e dönüp uygulamaya başlamak, ya da DevOps/Sprint Planı ciltlerine geçmek), bu doküman seti buna göre esnek şekilde devam ettirilebilir.
