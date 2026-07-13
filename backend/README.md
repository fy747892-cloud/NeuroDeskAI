<div style="text-align: center;">

# NeuroDesk AI — Backend

**Telefon görüşmesi, e-posta, takvim, görev ve müşteri ilişkilerini tek bir AI destekli iş asistanında birleştiren backend.**

![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%2B%20pgvector-4169E1?logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%20async-D71F00)
![Status](https://img.shields.io/badge/status-active-success)

</div>

---

## İçindekiler

1. [Genel Bakış](#genel-bakış)
2. [Öne Çıkan Özellikler](#öne-çıkan-özellikler)
3. [Mimari](#mimari)
4. [Hızlı Başlangıç](#hızlı-başlangıç)
5. [Kimlik Doğrulama ve Yetkilendirme](#kimlik-doğrulama-ve-yetkilendirme)
6. [Yapılandırma](#yapılandırma)
7. [Hata Formatı](#hata-formatı)
8. [Gerçek ve Mock Entegrasyonlar](#gerçek-ve-mock-entegrasyonlar)
9. [Davranış Kalıpları](#davranış-kalıpları)
10. [Test, Lint ve Tip Kontrolü](#test-lint-ve-tip-kontrolü)
11. [Proje Yapısı](#proje-yapısı)
12. [Dokümantasyon](#dokümantasyon)

---

## Genel Bakış

**NeuroDesk AI**, satış ekipleri, freelancerlar, emlak danışmanları, sigorta acenteleri, avukatlar ve KOBİ'ler için tasarlanmış; telefon görüşmelerini, e-postaları, takvimi, görevleri ve müşteri geçmişini tek bir çalışma hafızasında birleştiren AI destekli bir iş asistanıdır.

Ürünün temel ilkesi nettir:

> **AI önerir, kullanıcı onaylar, sistem uygular.** AI hiçbir zaman kullanıcı onayı olmadan mail göndermez, takvime yazmaz veya gerçek bir kayıt oluşturmaz.

Backend, FastAPI üzerine kurulu bir **modular monolith**'tir — her iş alanı (`tasks`, `contacts`, `deals`, `ai`, ...) kendi izole modülünde yaşar, ortak altyapı (`auth`, `tenant`, `permissions`) tüm modüller tarafından paylaşılır.

Bu doküman, **frontend/mobile ekibinin backend'i hızlıca ayağa kaldırıp entegre olabilmesi** için hazırlanmıştır. Ürünün "neden böyle tasarlandığına" dair daha derin gerekçeler için `NeuroDeskAI_docs/` altındaki CILT 1-15 tasarım dokümanlarına bakabilirsiniz — günlük entegrasyon için bu README ve canlı Swagger (`/docs`) yeterlidir.

---

## Öne Çıkan Özellikler

| Alan | Ne yapar |
| --- | --- |
| **AI Action Center** | Görüşmelerden çıkarılan görev, randevu ve satış fırsatı önerileri; onay/red akışıyla insan kontrolünde gerçek kayda dönüşür |
| **Akıllı Arama** | Görev, randevu, görüşme, kişi ve e-posta gövdesi üzerinde gerçek pgvector tabanlı semantik arama |
| **Müşteri Hafızası** | Bir kişi için son görüşme, son e-posta, son konu, açık görevler, sıradaki randevu ve açık satış fırsatlarının tek ekranda sentezi |
| **Günlük/Haftalık AI Özeti** | Toplantı, görüşme, bekleyen mail ve açık fırsat sayıları — sayılar deterministik SQL'den, doğal dil özeti AI'dan |
| **Görüşme Sonrası Özet** | Her görüşme için otomatik AI özeti |
| **Öncelik Motoru** | Görev ve randevuları öncelik, son tarih, kişi bağlantısı ve aciliyet ifadesine (TR+EN) göre tek kuyrukta sıralar |
| **AI Chat** | Kendi verisi üzerinde doğal dilde soru-cevap, kaynak gösterimi ve güven skoru |
| **Sesli Asistan** | Sesli komuttan yazıya (gerçek Whisper STT), niyet çıkarımı, yazıdan sese (gerçek TTS) |
| **AI Analitik** | Kullanım metrikleri ve gerçek model/token bazlı AI maliyet takibi |
| **Satış Pipeline'ı (CRM)** | Müşteri kartı + fırsat/teklif/fatura aşamalarını tek `Deal.stage` alanında yöneten pipeline, AI destekli fırsat çıkarımı |

Bu on özelliğin tamamı test edilmiş, uçtan uca çalışan gerçek bir backend karşılığına sahiptir (bkz. [Gerçek ve Mock Entegrasyonlar](#gerçek-ve-mock-entegrasyonlar) — hangi parçaların gerçek dış servise, hangilerinin mock'a bağlı olduğu için).

### Modül haritası

| Domain | Ne işe yarar | Router |
| --- | --- | --- |
| Auth | Kayıt, login, JWT access + rotating refresh token, logout/logout-all | `/auth` |
| Users / Organizations | Profil, tenant/organization/üyelik yönetimi, rol atama | `/users`, `/organizations` |
| Conversations / Calls | Görüşme kayıtları, metin tabanlı call transkripti | `/conversations`, `/calls` |
| AI Analysis / Approvals | Görüşme özetleme, görev/randevu/deal önerisi çıkarımı, onay/red akışı | `/ai/analysis`, `/ai/approvals` |
| Tasks / Appointments | Görev ve randevu CRUD, hatırlatmalar, çakışma kontrolü, kişiye bağlama | `/tasks`, `/appointments` |
| Priority | Görev/randevu öncelik kuyruğu | `/priority` |
| Calendar | Google Calendar bağlantı iskeleti (mock) | `/calendar` |
| Notifications | Hatırlatma oluşturma, manuel tetikleyici | `/notifications` |
| Dashboard | Özet görünüm + günlük/haftalık AI özeti | `/dashboard` |
| Contacts (CRM) | Kişi/not/timeline, müşteri hafızası | `/contacts` |
| Deals | Satış fırsatı / teklif / fatura pipeline'ı | `/deals` |
| AI Chat | Doğal dil soru-cevap | `/ai/chat` |
| Search | Semantic search (gerçek pgvector) | `/search` |
| Voice | Sesli komut yorumlama (gerçek STT/TTS) | `/voice` |
| Email (Gmail/Outlook) | OAuth bağlantı iskeleti (mock), mesaj metadata + gövde senkronu | `/email` |
| Files | Dosya yükleme (gerçek MinIO/S3), metin çıkarımı, malware scan (mock) | `/files` |
| Analytics | Kullanım metrikleri, AI maliyet takibi | `/analytics` |
| Billing | Plan/abonelik/kullanım kotası (gerçek ödeme yok) | `/billing` |
| Audit Log | Kritik işlemlerin denetim kaydı | `/audit-logs` |

Tam endpoint listesi ve request/response şemaları için backend ayaktayken **`http://localhost:8000/docs`** (Swagger UI, interaktif "Try it out" ile).

---

## Mimari

- **Katmanlı modül yapısı**: her domain `models → repository → service → schemas` sırasıyla `app/modules/<domain>/` altında, HTTP yüzeyi `app/api/v1/<domain>.py`'de.
- **Çok kiracılı (multi-tenant)**: her kayıt `tenant_id` + `organization_id` ile izole edilir; sorgular her zaman bu ikiliyle filtrelenir.
- **Rol bazlı yetkilendirme**: Owner / Admin / Member / Viewer, her kaynak için ayrı `Permission` çifti (`*.read` / `*.manage`).
- **AI onay akışı**: her AI önerisi önce `ai_action_approvals` tablosuna düşer; gerçek kayda dönüşmesi ayrı, açık bir kullanıcı aksiyonu gerektirir.
- **Gerçek/mock sağlayıcı ayrımı**: dış servise bağımlı her özellik (LLM, STT/TTS, OAuth, e-posta gönderimi, malware tarama) `Mock*Provider` / `OpenAICompatible*Provider` gibi değiştirilebilir sağlayıcı sınıfları arkasında durur — hangisinin aktif olduğu `.env` ile kontrol edilir, endpoint sözleşmesi değişmez.

---

## Hızlı Başlangıç

```bash
cp .env.example .env   # JWT_SECRET, MINIO_* değerlerini kendi ortamınıza göre ayarlayın (default'lar local dev için çalışır)
docker compose up -d db redis minio
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

| Kaynak | Adres |
| --- | --- |
| API | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/docs` |
| Health check | `GET /health` → `{"status": "ok"}` |

> `minio` container'ı yalnızca `/files/*` endpoint'lerini kullanacaksanız gerekli. Onun dışındaki her şey için `docker compose up -d db redis` yeterli. `db` imajı `pgvector/pgvector:pg16` — semantic search bu uzantıyı gerektirir.

CORS, `.env`'deki `CORS_ORIGINS` (virgülle ayrılmış, default `http://localhost:3000`) tarafından kontrol edilir — frontend'in gerçek origin'ini oraya eklemeniz gerekebilir.

---

## Kimlik Doğrulama ve Yetkilendirme

### Akış

1. `POST /api/v1/auth/register` `{email, password, display_name}` → `{access_token, refresh_token, token_type}`. Kayıt anında otomatik olarak: kişisel bir tenant + organization oluşturulur, kullanıcı o organization'ın **Owner**'ı olur, **Free plan**'a abone edilir.
2. `POST /api/v1/auth/login` `{email, password}` → aynı token çifti.
3. Korumalı her endpoint'e `Authorization: Bearer <access_token>` header'ı ile istek atılır.
4. `access_token` kısa ömürlüdür (`ACCESS_TOKEN_EXPIRE_MINUTES`, default 15 dk). Süresi dolunca `POST /api/v1/auth/refresh` `{refresh_token}` ile yenisi alınır — refresh token'lar **rotating**'dir (her kullanımda yenisi verilir, eskisi geçersiz olur; aynı refresh token iki kez kullanılırsa güvenlik önlemi olarak kullanıcının tüm oturumları iptal edilir).
5. `POST /api/v1/auth/logout` (mevcut refresh token'ı iptal eder) / `POST /api/v1/auth/logout-all` (tüm oturumları iptal eder).

### Roller ve izinler

4 rol vardır: **Owner, Admin, Member, Viewer** (organization bazlı, `GET /api/v1/organizations/members` ile görülür, `PATCH /api/v1/organizations/members/{id}/role` ile değiştirilir — yalnızca Owner/Admin).

Her endpoint belirli bir `Permission`'a bağlıdır (örn. `tasks.manage`, `deals.manage`, `billing.manage`). Yetkisiz bir istek **403** döner. Genel örüntü: Viewer sadece okuma yapabilir; Member kendi kapsamındaki verileri yönetebilir; yalnızca Owner/Admin faturalama, analytics tetikleme, org ayarları gibi yönetimsel işlemleri yapabilir. Backend'de sabit bir "benim iznim ne" endpoint'i yoktur — frontend, kullanıcının rolünü `GET /api/v1/users/me` + `GET /api/v1/organizations/members` üzerinden öğrenip UI'ı buna göre kurmalı, 403 alınca ilgili aksiyonu gizlemeli/devre dışı bırakmalıdır.

---

## Yapılandırma

Tüm AI özellikleri (`AI Analysis`, `AI Chat`, `Search` embedding, `Voice` STT/TTS, `Dashboard` günlük özet cümlesi, `Files` belge özeti) **tek bir sağlayıcı ayarı** üzerinden mock veya gerçek bir OpenAI-uyumlu API'ye bağlanır:

```bash
LLM_PROVIDER=mock          # "mock" (default) veya "openai"
LLM_API_KEY=               # openai için zorunlu
LLM_BASE_URL=https://api.openai.com/v1
LLM_ANALYSIS_MODEL=gpt-4o-mini
LLM_CHAT_MODEL=gpt-4o-mini
LLM_EMBEDDING_MODEL=text-embedding-3-small
LLM_STT_MODEL=whisper-1
LLM_TTS_MODEL=tts-1
LLM_TTS_VOICE=alloy
LLM_TIMEOUT_SECONDS=30
```

`LLM_PROVIDER=openai` yapıldığında tüm bu endpoint'ler gerçek API çağrısı yapar (retry/backoff dahil), her çağrının maliyeti `analytics` modülüne gerçek fiyat üzerinden loglanır ve günlük AI kotasından düşer — **response şeması/endpoint sözleşmesi değişmez**, frontend'in hiçbir şey değiştirmesi gerekmez.

Diğer önemli ortam değişkenleri (`JWT_SECRET`, `TOKEN_ENCRYPTION_KEY`, `MINIO_*`, `CORS_ORIGINS`, ...) için `.env.example` referanstır.

---

## Hata Formatı

Tüm hatalar tek tip JSON döner:

```json
{ "error_code": "not_found", "message": "Task not found." }
```

| HTTP | `error_code` | Anlamı |
| --- | --- | --- |
| 400 | `app_error` | Genel iş kuralı hatası |
| 401 | `auth_error` | Token geçersiz/süresi dolmuş |
| 403 | `forbidden` | Rol/izin yetersiz |
| 404 | `not_found` | Kayıt bulunamadı |
| 409 | `conflict` | Çakışma (örn. aynı e-posta ile tekrar kayıt, randevu çakışması, bir AI onayının ikinci kez materyalize edilmeye çalışılması) |
| 422 | `validation_error` | İş kuralı validasyonu — Pydantic şema hatalarından ayrı, onlar FastAPI'nin kendi 422 formatını kullanır |
| 429 | `rate_limited` | Kısa pencereli anti-abuse limiti (Redis; login denemesi, dosya yükleme, mail sync) |
| 429 | `quota_exceeded` | Plan bazlı günlük AI kullanım kotası doldu (bkz. [Billing / Kota Davranışı](#billing--kota-davranışı)) |
| 502 | `provider_error` | Mock/harici sağlayıcı çağrısı başarısız oldu |

---

## Gerçek ve Mock Entegrasyonlar

Frontend UI tasarlarken bunu bilmek kritiktir — bazı entegrasyonlar gerçek harici hesap/kimlik bilgisi gerektirmediği için **gerçek** çalışır, bazıları henüz gerçek sağlayıcıya bağlı değildir:

| Özellik | Durum | Frontend için anlamı |
| --- | --- | --- |
| Dosya yükleme (Files) | **Gerçek** — MinIO/S3 presigned URL | `POST /files/upload-url` gerçek bir presigned URL döner, dosya gerçekten oraya `PUT` edilmeli |
| Metin çıkarımı (PDF/DOCX/TXT/EML) | **Gerçek** | Yüklenen dosyadan gerçek metin çıkar |
| Semantic search (vektör indeksi) | **Gerçek pgvector** | Görev/randevu/görüşme/kişi/e-posta gövdesi üzerinde gerçek cosine-similarity araması çalışır |
| AI özet, görev/randevu/deal çıkarımı, AI Chat, embedding, STT/TTS, günlük özet cümlesi | **Mock (default) veya gerçek LLM** | Bkz. [Yapılandırma](#yapılandırma). Default kurulumda deterministik/sabit içerik döner; `"[mock-fail]"` içeren metin 502 `provider_error` tetikler (hata senaryosu test etmek için kullanılabilir) |
| Google/Outlook OAuth (Email, Calendar) | **Mock** | `POST /email/gmail/connect` gerçek bir Google authorize URL şeklinde bir link döner ama gerçek Google'a gitmez; `callback`'e herhangi bir `code` gönderilebilir. Frontend gerçek bir OAuth popup akışı kurmamalı |
| Malware scan (Files) | **Mock hook** | `"[mock-fail]"` içeren dosya "infected" işaretlenir, gerçek AV motoru yok |
| Ödeme/fatura (Billing) | **Yok** | Sadece plan/kota iskeleti var, gerçek ödeme sağlayıcısı/webhook yok |
| Bildirim gönderimi (email) | **Mock** | Gerçek SMTP yok |
| Zamanlanmış görevler (reminder, reindex, analytics aggregation, email sync) | **Manuel tetikleme** | Gerçek bir cron/scheduler yok. `POST /notifications/process-due`, `POST /search/reindex`, `POST /analytics/aggregate`, `POST /email/accounts/{id}/sync` — elle (veya ileride bir cron job'la) tetiklenmesi gereken "tick" endpoint'leridir, frontend bunları kullanıcı beklemeden otomatik çağırmamalı |

---

## Davranış Kalıpları

- **Tenant/Organization**: Her kullanıcı bir tenant + organization'a bağlı. MVP'de "personal tenant" — kayıt olan kişi kendi tenant'ının tek üyesi ve Owner'ı. Organizasyona başka üye davet etme akışı henüz yok.
- **Soft delete**: Silinen kayıtlar (task, appointment, conversation, contact, deal, file, vb.) fiziksel olarak silinmez, `is_deleted`/`status` alanı güncellenir ve listelerden düşer. `DELETE` çağrıları `204 No Content` döner.
- **Tarih/saat**: Tüm timestamp'ler UTC, ISO 8601 (`2026-07-11T12:00:00Z`) formatında.
- **Sayfalama yok**: Liste endpoint'lerinin (tasks, contacts, appointments, deals, vb.) çoğunda sayfalama yok — tüm sonuçlar tek seferde döner. Şimdilik frontend client-side sayfalama/sanal liste düşünebilir.
- **Signed URL'ler kısa ömürlü**: Files modülündeki upload/download URL'leri ~15 dakika geçerli, süresi dolarsa yeniden istenmeli.
- **AI action approval akışı**: AI bir görev/randevu/satış fırsatı önerdiğinde önce `ai_action_approvals` kaydı oluşur (`GET /ai/approvals`, `action_type` alanı `"task"` / `"appointment"` / `"deal"` olabilir), kullanıcı `POST /ai/approvals/{id}/approve` ile onaylayınca **ayrı bir çağrı** (`POST /tasks/from-approval`, `POST /appointments/from-approval` veya `POST /deals/from-approval`) ile gerçek kayıt materyalize edilir. Onay tek başına gerçek kayıt oluşturmaz.
- **Müşteri Hafızası / Günlük Özet / Öncelik Kuyruğu yeni tablo eklemez**: `GET /contacts/{id}/memory`, `GET /dashboard/digest`, `GET /priority/queue` — üçü de mevcut veriler üzerinden anlık hesaplanan salt-okunur kompozisyonlardır, ayrı bir "kaydet" aksiyonu yoktur.

### Billing / Kota Davranışı

Her tenant kayıt anında **Free plan**'a otomatik abone olur (günlük 5 AI isteği — chat, conversation analysis ve voice ortak sayaçtan düşer). Kota dolunca AI istekleri `429 quota_exceeded` döner. Frontend bu hatayı yakalayıp kullanıcıya "günlük AI kullanım limitine ulaşıldı, planınızı yükseltin" gibi bir mesaj gösterip `GET /billing/usage` ile kalan/limit bilgisini sunabilir, `PATCH /billing/subscription` ile plan değişikliği tetikleyebilir (yalnızca Owner/Admin).

---

## Test, Lint ve Tip Kontrolü

```bash
docker compose up -d db redis minio
docker compose exec db createdb -U neurodesk neurodesk_test   # ilk seferde
uv run pytest
```

```bash
uv run ruff check .
uv run mypy app
```

Repo kökündeki `bruno/` klasörü auth akışını denemek için hazır bir [Bruno](https://www.usebruno.com/) collection'ı içerir (Register, Login, Refresh, Logout, Users/Me). **Local** environment'ı seçip Register/Login çalıştırınca token'lar otomatik environment'a yazılır, sonraki istekler bunu kullanır.

En pratik keşif yolu yine de `http://localhost:8000/docs` — her endpoint için gerçek request/response şemasını görüp doğrudan tarayıcıdan deneyebilirsiniz.

### Yeni migration üretme

```bash
uv run alembic revision --autogenerate -m "kısa açıklama"
uv run alembic upgrade head
```

---

## Proje Yapısı

```
app/core     — config, security (JWT/Argon2), error handling, rate limiting, permissions, LLM retry/crypto
app/db       — async SQLAlchemy session/engine, ORM base + mixin'ler, Redis/S3 bağlantıları
app/modules  — domain modülleri (models, repository, service, schemas, provider — her klasör bir domain):
               auth, users, organizations, audit, conversations, ai, ai_chat, tasks, appointments,
               priority, calendar, notifications, dashboard, contacts, deals, search, voice, email,
               files, analytics, billing
app/api/v1   — HTTP router'ları (yukarıdaki modül haritasıyla birebir eşleşir)
alembic/     — migration'lar
NeuroDeskAI_docs/ — CILT 1-15 tasarım dokümanları (arka plan/gerekçe için)
```

---

## Dokümantasyon

- Canlı API referansı: `http://localhost:8000/docs` (Swagger UI)
- Mimari gerekçe ve derinlemesine tasarım: `NeuroDeskAI_docs/CILT_4_BACKEND_DESIGN_NeuroDesk_AI.md`
- Ürün vizyonu ve kapsam: `NeuroDeskAI_docs/CILT_1_PRD_NeuroDesk_AI.md`