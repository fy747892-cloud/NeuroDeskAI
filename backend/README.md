# NeuroDeskAI-Backend

FastAPI tabanlı modular monolith backend. Bu doküman, web/mobile frontend ekibinin (Sprint 13-14) backend'i hızlıca ayağa kaldırıp entegre olabilmesi için hazırlanmıştır.

**Durum**: CILT_11 sprint planındaki tüm backend sprintleri (Sprint 1-12, 15-19) tamamlandı ve doğrulandı. Sprint 13-14 (bu frontend işi) ve Sprint 20+ (Admin Panel, Security Hardening vb.) henüz kapsama alınmadı.

Ürün ve teknik tasarım dokümanları `NeuroDeskAI_docs/` altındadır (CILT 1-15) — API'nin "neden böyle" tasarlandığını anlamak için referans, ama günlük entegrasyon için bu README ve `/docs` (Swagger) yeterli olmalı.

---

## 1. Backend şu anda ne yapıyor?

Modular monolith — her domain kendi `app/modules/<domain>/` klasöründe (models → repository → service → schemas), HTTP yüzeyi `app/api/v1/<domain>.py`'de. Tüm endpoint'ler `/api/v1` altında.

| Domain | Ne işe yarar | Router |
|---|---|---|
| **Auth** | Kayıt, login, JWT access + rotating refresh token, logout/logout-all | `/auth` |
| **Users / Organizations** | Profil, tenant/organization/üyelik yönetimi, rol atama | `/users`, `/organizations` |
| **Conversations / Calls** | Görüşme kayıtları, metin tabanlı call transkripti | `/conversations`, `/calls` |
| **AI Analysis / Approvals** | Görüşme özetleme, görev/randevu önerisi çıkarımı (mock LLM), öneri onay/red akışı | `/ai/analysis`, `/ai/approvals` |
| **Tasks / Appointments** | Görev ve randevu CRUD, hatırlatmalar, randevu çakışma kontrolü | `/tasks`, `/appointments` |
| **Calendar** | Google Calendar bağlantı **iskeleti** (gerçek OAuth yok, bkz. §5) | `/calendar` |
| **Notifications** | Hatırlatma oluşturma, manuel "due" tetikleyici | `/notifications` |
| **Dashboard** | Tek endpoint'te özet görünüm (açık görevler, yaklaşan randevular, bekleyen AI önerileri) | `/dashboard` |
| **Contacts (CRM)** | Kişi/not/timeline, görüşmeyle ilişkilendirme | `/contacts` |
| **AI Chat** | RAG benzeri soru-cevap (mock LLM + anahtar kelime tabanlı retrieval) | `/ai/chat` |
| **Search** | Semantic search (gerçek pgvector, mock embedding) | `/search` |
| **Email (Gmail/Outlook)** | OAuth bağlantı **iskeleti** (mock, bkz. §5), mesaj metadata senkronu | `/email` |
| **Files** | Dosya yükleme (gerçek MinIO/S3 presigned URL), metin çıkarımı, malware scan (mock), özet | `/files` |
| **Analytics** | Kullanım metrikleri, AI maliyet takibi, günlük aggregation | `/analytics` |
| **Billing** | Plan/abonelik/kullanım kotası iskeleti (gerçek ödeme yok) | `/billing` |
| **Audit Log** | Kritik işlemlerin denetim kaydı (salt okunur) | `/audit-logs` |

Tam endpoint listesi ve request/response şemaları için backend ayaktayken **`http://localhost:8000/docs`** (Swagger UI, interaktif "Try it out" ile).

---

## 2. Hızlı başlangıç

```bash
cp .env.example .env   # JWT_SECRET, MINIO_* değerlerini kendi ortamınıza göre ayarlayın (default'lar local dev için çalışır)
docker compose up -d db redis minio
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Health check: `GET /health` → `{"status": "ok"}`

> `minio` container'ı yalnızca `/files/*` endpoint'lerini kullanacaksanız gerekli. Onun dışındaki her şey için `docker compose up -d db redis` yeterli.

CORS `.env`'deki `CORS_ORIGINS` (virgülle ayrılmış, default `http://localhost:3000`) tarafından kontrol edilir — frontend'in gerçek origin'ini oraya eklemeniz gerekebilir.

---

## 3. Kimlik doğrulama (frontend için en kritik kısım)

### Akış

1. `POST /api/v1/auth/register` `{email, password, display_name}` → `{access_token, refresh_token, token_type}`. Kayıt anında otomatik olarak: kişisel bir tenant + organization oluşturulur, kullanıcı o organization'ın **Owner**'ı olur, **Free plan**'a abone edilir.
2. `POST /api/v1/auth/login` `{email, password}` → aynı token çifti.
3. Korumalı her endpoint'e `Authorization: Bearer <access_token>` header'ı ile istek atılır.
4. `access_token` kısa ömürlüdür (`ACCESS_TOKEN_EXPIRE_MINUTES`, default 15dk). Süresi dolunca `POST /api/v1/auth/refresh` `{refresh_token}` ile yenisi alınır — refresh token'lar **rotating**'dir (her kullanımda yenisi verilir, eskisi geçersiz olur; aynı refresh token iki kez kullanılırsa güvenlik önlemi olarak kullanıcının tüm oturumları iptal edilir).
5. `POST /api/v1/auth/logout` (mevcut refresh token'ı iptal eder) / `POST /api/v1/auth/logout-all` (kullanıcının tüm oturumlarını iptal eder).

### Roller ve izinler

4 rol var: **Owner, Admin, Member, Viewer** (organization bazlı, `GET /api/v1/organizations/members` ile görülür, `PATCH /api/v1/organizations/members/{id}/role` ile değiştirilir — yalnızca Owner/Admin).

Her endpoint belirli bir `Permission`'a bağlıdır (örn. `tasks.manage`, `billing.manage`). Yetkisiz bir istek **403** döner. Genel örüntü: Viewer sadece okuma yapabilir; Member kendi kapsamındaki verileri yönetebilir; yalnızca Owner/Admin faturalama, analytics tetikleme, org ayarları gibi "yönetimsel" işlemleri yapabilir. Frontend'in rol bazlı UI'ı `GET /api/v1/users/me` + `GET /api/v1/organizations/members` üzerinden kullanıcının rolünü öğrenip buna göre kurması gerekir — backend tarafında sabit bir "benim iznim ne" endpoint'i yok, 403 alınca ilgili aksiyonun gizlenmesi/disable edilmesi frontend sorumluluğu.

---

## 4. Hata formatı

Tüm hatalar tek tip JSON döner:

```json
{ "error_code": "not_found", "message": "Task not found." }
```

| HTTP | `error_code` | Anlamı |
|---|---|---|
| 400 | `app_error` | Genel iş kuralı hatası |
| 401 | `auth_error` | Token geçersiz/süresi dolmuş |
| 403 | `forbidden` | Rol/izin yetersiz |
| 404 | `not_found` | Kayıt bulunamadı |
| 409 | `conflict` | Çakışma (örn. aynı e-posta ile tekrar kayıt, randevu çakışması) |
| 422 | `validation_error` | İş kuralı validasyonu (örn. dosya tipi/boyutu, geçersiz durum geçişi) — Pydantic şema hatalarından ayrı, onlar FastAPI'nin kendi 422 formatını kullanır |
| 429 | `rate_limited` | Kısa pencereli anti-abuse limiti (Redis, örn. login denemesi, dosya yükleme) |
| 429 | `quota_exceeded` | Plan bazlı günlük AI kullanım kotası doldu (bkz. §7 Billing) |
| 502 | `provider_error` | Mock/harici sağlayıcı çağrısı başarısız oldu (bkz. §5) |

---

## 5. Önemli: Neyin gerçek, neyin mock olduğu

Frontend UI tasarlarken bunu bilmek kritik — bazı entegrasyonlar gerçek harici hesap/kimlik bilgisi gerektirmediği için **gerçek** çalışır, bazıları henüz gerçek sağlayıcıya bağlı değildir:

| Özellik | Durum | Frontend için anlamı |
|---|---|---|
| Dosya yükleme (Files) | **Gerçek** — MinIO/S3 presigned URL | `POST /files/upload-url` gerçek bir presigned URL döner, dosya gerçekten oraya `PUT` edilmeli |
| Metin çıkarımı (PDF/DOCX/TXT/EML) | **Gerçek** | Yüklenen dosyadan gerçek metin çıkar |
| Semantic search embedding | **Gerçek vektör indeksi**, mock embedding modeli | Arama gerçek pgvector üzerinde çalışır ama embedding gerçek bir LLM'den gelmiyor |
| Google/Outlook OAuth (Email, Calendar) | **Mock** | `POST /email/gmail/connect` gerçek bir Google authorize URL şeklinde bir link döner ama gerçek Google'a gitmez; `callback`'e herhangi bir `code` gönderilebilir (gerçek doğrulama yok). Frontend gerçek bir OAuth popup akışı kurmamalı — şimdilik "connect" butonu backend'in döndürdüğü URL'i gösterebilir/loglayabilir, gerçek yönlendirme Sprint kapsamında değil |
| AI özet/görev çıkarımı, AI Chat cevapları | **Mock LLM** | Gerçek bir dil modeline bağlı değil, sabit/deterministik mantıkla üretilmiş cevaplar döner. Metinde `"[mock-fail]"` geçerse hata senaryosu (502 `provider_error`) tetiklenir — hata durumlarını test etmek isterseniz bu string'i kullanın |
| Malware scan (Files) | **Mock hook** | `"[mock-fail]"` içeren dosya "infected" işaretlenir, gerçek AV motoru yok |
| Ödeme/fatura (Billing) | **Yok** | Sadece plan/kota iskeleti var, gerçek ödeme sağlayıcısı/webhook yok |
| Bildirim gönderimi (email) | **Mock** | Gerçek SMTP yok |
| Zamanlanmış görevler (reminder, reindex, analytics aggregation, email sync) | **Manuel tetikleme** | Backend'de gerçek bir cron/scheduler yok. `POST /notifications/process-due`, `POST /search/reindex`, `POST /analytics/aggregate`, `POST /email/accounts/{id}/sync` gibi endpoint'ler **elle** (veya ileride bir cron job'la) tetiklenmesi gereken "tick" endpoint'leridir. Frontend bunları arka planda kullanıcı beklemeden otomatik çağırmamalı; bunlar operasyonel/admin aksiyonlarıdır |

---

## 6. Genel davranış kalıpları (frontend'in bilmesi gereken)

- **Tenant/Organization**: Her kullanıcı bir tenant + organization'a bağlı. MVP'de "personal tenant" — kayıt olan kişi kendi tenant'ının tek üyesi ve Owner'ı. Organizasyona başka üye davet etme akışı henüz yok.
- **Soft delete**: Silinen kayıtlar (task, appointment, conversation, contact, file, vb.) fiziksel olarak silinmez, `status`/`is_deleted` alanı güncellenir ve listelerden düşer. `DELETE` çağrıları `204 No Content` döner.
- **Tarih/saat**: Tüm timestamp'ler UTC, ISO 8601 (`2026-07-11T12:00:00Z`) formatında.
- **Sayfalama yok**: Şu anki liste endpoint'lerinin (tasks, contacts, appointments, vb.) çoğunda sayfalama yok — tüm sonuçlar tek seferde döner. Büyük veri setlerinde bu ileride eklenecek, şimdilik frontend client-side sayfalama/sanal liste düşünebilir.
- **Signed URL'ler kısa ömürlü**: Files modülündeki upload/download URL'leri ~15 dakika geçerli, süresi dolarsa yeniden istenmeli.
- **AI action approval akışı**: AI bir görev/randevu önerdiğinde önce `ai_action_approvals` kaydı oluşur (`GET /ai/approvals`), kullanıcı `POST /ai/approvals/{id}/approve` ile onaylayınca **ayrı bir çağrı** (`POST /tasks/from-approval` veya `POST /appointments/from-approval`) ile gerçek kayıt materyalize edilir. Onay tek başına task/appointment oluşturmaz — frontend bu iki adımı ayrı UI aksiyonu olarak kurmalı.

---

## 7. Billing / kota davranışı

Her tenant kayıt anında **Free plan**'a otomatik abone olur (günlük 5 AI isteği — chat + conversation analysis ortak sayaçtan düşer). Kota dolunca AI istekleri `429 quota_exceeded` döner. Frontend bu hatayı yakalayıp kullanıcıya "günlük AI kullanım limitine ulaşıldı, planınızı yükseltin" gibi bir mesaj gösterip `GET /billing/usage` ile kalan/limit bilgisini sunabilir, `PATCH /billing/subscription` ile plan değişikliği tetikleyebilir (yalnızca Owner/Admin).

---

## 8. Test ve API keşfi

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

---

## 9. Yeni migration üretme (backend değişikliği yapılırsa)

```bash
uv run alembic revision --autogenerate -m "kısa açıklama"
uv run alembic upgrade head
```

---

## 10. Proje yapısı

```
app/core     — config, security (JWT/Argon2), error handling, rate limiting, permissions
app/db       — async SQLAlchemy session/engine, ORM base + mixin'ler, Redis/S3 bağlantıları
app/modules  — domain modülleri (models, repository, service, schemas — her klasör bir domain)
app/api/v1   — HTTP router'ları (bu dosyalar §1'deki tabloyla birebir eşleşir)
alembic/     — migration'lar
NeuroDeskAI_docs/ — CILT 1-15 tasarım dokümanları (arka plan/gerekçe için)
```

Daha fazla mimari detay için: `NeuroDeskAI_docs/CILT_4_BACKEND_DESIGN_NeuroDesk_AI.md`.
