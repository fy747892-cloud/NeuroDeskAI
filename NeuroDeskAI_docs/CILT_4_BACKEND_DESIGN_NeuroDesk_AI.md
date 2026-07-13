# CILT 4 — Backend Design Document: NeuroDesk AI

Sürüm: 1.0  
Tarih: 08 Temmuz 2026  
Doküman türü: Backend Tasarım Dokümanı  
Kapsam: FastAPI backend mimarisi, modular monolith, servis/repository katmanları, API endpoint tasarımı, authentication, authorization, tenant isolation, worker/queue, AI entegrasyonu, güvenlik, test ve backend kod üretim talimatları

> Not: Bu doküman backend tasarım standardıdır. Uygulama kodu, migration dosyası, frontend veya mobil kod içermez. Kod örneği verilmesi gereken yerlerde yalnızca pseudo-code düzeyinde anlatım yapılır. Gerçek backend implementasyonu ayrı aşamada hazırlanmalıdır.

## İçindekiler

1. [Yönetici Özeti](#1-yönetici-özeti)
2. [Backend Vizyonu](#2-backend-vizyonu)
3. [Backend Mimari İlkeleri](#3-backend-mimari-ilkeleri)
4. [Backend Teknoloji Kararları](#4-backend-teknoloji-kararları)
5. [Modular Monolith Yaklaşımı](#5-modular-monolith-yaklaşımı)
6. [Gelecekte Microservice’e Evrim Stratejisi](#6-gelecekte-microservicee-evrim-stratejisi)
7. [Backend Proje Klasör Yapısı](#7-backend-proje-klasör-yapısı)
8. [Domain Modülleri](#8-domain-modülleri)
9. [Layered Architecture](#9-layered-architecture)
10. [Dependency Injection Yaklaşımı](#10-dependency-injection-yaklaşımı)
11. [Configuration ve Environment Management](#11-configuration-ve-environment-management)
12. [Database, SQLAlchemy ve Alembic Standardı](#12-database-sqlalchemy-ve-alembic-standardı)
13. [Repository, Service ve Unit of Work Pattern](#13-repository-service-ve-unit-of-work-pattern)
14. [DTO / Schema Tasarımı](#14-dto--schema-tasarımı)
15. [API Router Tasarımı ve Versioning](#15-api-router-tasarımı-ve-versioning)
16. [Authentication Tasarımı](#16-authentication-tasarımı)
17. [Authorization, RBAC ve Permission Tasarımı](#17-authorization-rbac-ve-permission-tasarımı)
18. [Multi-Tenant Backend Tasarımı](#18-multi-tenant-backend-tasarımı)
19. [Request Lifecycle](#19-request-lifecycle)
20. [Error Handling Standardı](#20-error-handling-standardı)
21. [Response, Pagination, Filtering ve Sorting Standardı](#21-response-pagination-filtering-ve-sorting-standardı)
22. [Validation Standardı](#22-validation-standardı)
23. [Background Job, Queue ve Scheduler Mimarisi](#23-background-job-queue-ve-scheduler-mimarisi)
24. [Event-Driven Backend ve Outbox Pattern](#24-event-driven-backend-ve-outbox-pattern)
25. [Audit Log Backend Tasarımı](#25-audit-log-backend-tasarımı)
26. [Modül Bazlı Backend Tasarımları](#26-modül-bazlı-backend-tasarımları)
27. [API Endpoint Kataloğu](#27-api-endpoint-kataloğu)
28. [AI Backend Tasarımı](#28-ai-backend-tasarımı)
29. [AI Action Approval Backend Akışı](#29-ai-action-approval-backend-akışı)
30. [Call Analysis Backend Akışı](#30-call-analysis-backend-akışı)
31. [Email Analysis Backend Akışı](#31-email-analysis-backend-akışı)
32. [Calendar Backend Akışı](#32-calendar-backend-akışı)
33. [AI Chat ve Semantic Search Backend Akışı](#33-ai-chat-ve-semantic-search-backend-akışı)
34. [Notification Backend Tasarımı](#34-notification-backend-tasarımı)
35. [File Upload ve Object Storage Backend Tasarımı](#35-file-upload-ve-object-storage-backend-tasarımı)
36. [Security Backend Tasarımı](#36-security-backend-tasarımı)
37. [Rate Limiting](#37-rate-limiting)
38. [Logging, Monitoring ve Tracing](#38-logging-monitoring-ve-tracing)
39. [Testing Strategy](#39-testing-strategy)
40. [Performance Strategy](#40-performance-strategy)
41. [Deployment, Docker ve CI/CD Backend Gereksinimleri](#41-deployment-docker-ve-cicd-backend-gereksinimleri)
42. [Backend Riskleri](#42-backend-riskleri)
43. [Backend Kabul Kriterleri](#43-backend-kabul-kriterleri)
44. [Codex İçin Backend Kod Üretim Talimatları](#44-codex-için-backend-kod-üretim-talimatları)
45. [Codex İçin Sonraki Ciltlere Hazırlık Notları](#45-codex-için-sonraki-ciltlere-hazırlık-notları)
46. [Codex İçin Sonraki Adım](#codex-için-sonraki-adım)

# 1. Yönetici Özeti

NeuroDesk AI backend’i, AI destekli kişisel/kurumsal çalışma asistanının güvenli, ölçeklenebilir ve denetlenebilir işlem katmanıdır. Backend; kullanıcı yönetimi, authentication, tenant isolation, görüşme metni analizi, AI önerileri, görev/randevu oluşturma, takvim ve mail entegrasyonları, bildirimler, kişi hafızası, AI Chat, semantic search, audit log ve privacy süreçlerini yönetir.

MVP için önerilen backend mimarisi FastAPI tabanlı modular monolith’tir. Bu yaklaşım, küçük/orta ekip için hızlı geliştirme, kolay transaction yönetimi ve düşük operasyonel karmaşıklık sağlar. Ancak domain modülleri açık sınırlara sahip olmalı; AI analysis, transcription, email sync, calendar sync, notification, embedding ve analytics gibi uzun süren işler ayrı worker süreçleri olarak tasarlanmalıdır.

Backend’in en kritik iş kuralı şudur:

> AI yalnızca öneri üretir. Mail gönderme, takvim etkinliği oluşturma, görev atama, veri silme veya dış sisteme yazma gibi gerçek aksiyonlar ancak kullanıcı onayıyla uygulanır.

Bu nedenle ai_action_approvals modeli backend’in merkezinde yer almalıdır. AI worker öneri üretir, backend öneriyi pending state ile saklar, kullanıcı onaylar veya reddeder, gerçek aksiyon ilgili service tarafından audit log ile uygulanır.

# 2. Backend Vizyonu

Backend vizyonu, NeuroDesk AI’ın ürün değerini hızlı doğrulayan ama enterprise seviyeye kontrollü evrilebilen bir uygulama çekirdeği oluşturmaktır.

Vizyon ilkeleri:

- MVP hızlı çıkarılmalıdır.
- Tenant isolation tüm veri erişiminde zorunlu olmalıdır.
- AI aksiyonları insan onayına bağlı olmalıdır.
- Auth, RBAC, audit, privacy ve rate limiting sonradan eklenen yan parçalar değil temel platform kabiliyetleri olmalıdır.
- Backend modülleri mikroservise ayrılabilecek domain sınırlarıyla tasarlanmalıdır.
- Worker sistemi job status, retry, idempotency ve DLQ ile güvenilir olmalıdır.
- API sözleşmeleri OpenAPI ile net ve test edilebilir olmalıdır.

# 3. Backend Mimari İlkeleri

- Modular monolith, domain modülleriyle uygulanır.
- API layer iş kuralı içermez; service layer çağırır.
- Repository layer yalnızca veri erişiminden sorumludur.
- Service layer iş kurallarını ve transaction akışını yönetir.
- Tenant context request başında çözülür ve tüm katmanlara taşınır.
- Repository sorguları tenant-scoped olmalıdır.
- Sensitive data loglanmaz.
- Tokenlar plain text saklanmaz.
- OAuth refresh token encrypted saklanır.
- Rıza kontrolü yapılmadan telefon, mail veya AI analizi başlatılmaz.
- Background jobs idempotent tasarlanır.
- Audit log kritik aksiyonlarda zorunludur.
- AI provider entegrasyonu adapter üzerinden soyutlanır.

# 4. Backend Teknoloji Kararları

| Alan | Teknoloji | Gerekçe |
|---|---|---|
| Dil | Python 3.12+ | AI ekosistemi, hızlı geliştirme, tip desteği |
| Web framework | FastAPI | OpenAPI, dependency injection, async desteği |
| Schema | Pydantic v2 | Request/response validation |
| ORM | SQLAlchemy 2.x | Olgun ORM, transaction yönetimi |
| Migration | Alembic | SQLAlchemy uyumlu migration |
| Database | PostgreSQL | Transaction, JSONB, pgvector, relational model |
| Cache/Queue | Redis | MVP için cache, rate limit, queue broker |
| Worker | Celery veya RQ | Background job orchestration |
| Server | Uvicorn, production’da Gunicorn + Uvicorn worker | ASGI çalışma modeli |
| HTTP client | HTTPX | Async provider çağrıları |
| Auth | JWT, OAuth 2.0 | Web/mobil API uyumu |
| Logging | structlog veya standart logging | Structured logs |
| Error tracking | Sentry | Production hata izleme |
| Test | Pytest | Unit/integration/API testleri |
| Quality | Ruff, MyPy | Lint, format, type safety |
| Container | Docker, Docker Compose | Local ve deployment standardı |

AI ve entegrasyon tarafı:

- OpenAI API veya benzeri LLM provider.
- Whisper veya alternatif Speech-to-Text servisleri.
- Google APIs.
- Microsoft Graph.
- Firebase Cloud Messaging.
- SMTP/transactional mail provider.
- SMS provider.
- WhatsApp Business API, yalnızca resmi ve izinli kullanım.
- S3/GCS/Azure Blob/MinIO object storage.

# 5. Modular Monolith Yaklaşımı

MVP için modular monolith seçilmelidir.

Neden:

- Daha hızlı geliştirilir.
- Küçük ekip için operasyonel karmaşıklığı azaltır.
- Domain modülleri ayrı klasörlerde tutulur.
- İleride mikroservise ayrılabilecek sınırlar korunur.
- Transaction yönetimi daha kolaydır.
- İlk ürünün pazara çıkış süresini kısaltır.

Ayrı worker süreci olarak tasarlanacak alanlar:

- AI analysis worker.
- Speech-to-text worker.
- Email sync worker.
- Calendar sync worker.
- Notification worker.
- Scheduled reminder worker.
- Embedding worker.
- Analytics aggregation worker.
- Data export/delete worker.
- Webhook retry worker.

# 6. Gelecekte Microservice’e Evrim Stratejisi

Uzun vadeli hedef event-driven microservice architecture’dır.

Ayrılabilecek servisler:

- Auth Service.
- User Service.
- Organization Service.
- Conversation Service.
- Call Service.
- Email Service.
- Calendar Service.
- Task Service.
- Appointment Service.
- Contact Service.
- Notification Service.
- AI Service.
- Search Service.
- Analytics Service.
- Billing Service.
- Admin Service.

Mikroservise geçiş tetikleyicileri:

- AI job hacmi API performansını etkiliyor.
- Mail/calendar sync ayrı ölçekleme gerektiriyor.
- Enterprise tenant izolasyonu ayrı database gerektiriyor.
- Takımlar domain bazlı sahiplik istiyor.
- Release döngüleri servis bazında ayrışıyor.

Geçiş prensibi:

- Önce domain boundary netleşir.
- Sonra outbox/event sözleşmeleri stabilize edilir.
- Ardından veri sahipliği servis bazında ayrılır.
- En son network boundary ve bağımsız deploy eklenir.

# 7. Backend Proje Klasör Yapısı

Önerilen klasör yapısı:

```text
backend/
├── app/
│   ├── main.py
│   ├── core/
│   ├── db/
│   ├── api/
│   ├── modules/
│   ├── workers/
│   ├── integrations/
│   ├── schemas/
│   ├── shared/
│   └── tests/
├── alembic/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── .env.example
└── README.md
```

Klasör amaçları:

| Klasör/Dosya | Amaç |
|---|---|
| app/main.py | FastAPI uygulama oluşturma, middleware, router mount, lifecycle |
| app/core | Config, security, logging, errors, pagination, tenant context, permissions |
| app/db | DB session, base model, unit of work, migration bağlantıları |
| app/api/v1 | API router dosyaları ve versioned endpoint tanımları |
| app/modules | Domain modülleri ve iş kuralları |
| app/workers | Celery/RQ app ve worker task girişleri |
| app/integrations | Harici provider adapterları |
| app/schemas | Ortak Pydantic schema ve response modelleri |
| app/shared | Ortak utility, value object, constants, domain event base yapıları |
| app/tests | Backend testleri |
| alembic | Migration altyapısı |
| Dockerfile | Backend image tanımı |
| docker-compose.yml | Local development servisleri |
| pyproject.toml | Dependency, lint, type check, test ayarları |
| .env.example | Ortam değişkenleri örneği |
| README.md | Local çalıştırma ve geliştirme talimatları |

core alt bileşenleri:

- config.py: Pydantic settings, environment değişkenleri.
- security.py: JWT, password hash, token helpers.
- logging.py: Structured logging standardı.
- errors.py: Uygulama hata sınıfları ve mapping.
- pagination.py: Ortak pagination model ve helperları.
- rate_limit.py: Rate limit policy adapter.
- tenant.py: Tenant context çözümleme.
- permissions.py: Global permission kontrol helperları.
- constants.py: Ortak sabitler.

# 8. Domain Modülleri

Her domain modülü şu standart yapıya sahip olmalıdır:

```text
modules/{module_name}/
├── models.py
├── schemas.py
├── repository.py
├── service.py
├── dependencies.py
├── permissions.py
├── events.py
├── exceptions.py
├── tasks.py
└── tests/
```

Dosya amaçları:

| Dosya | Amaç |
|---|---|
| models.py | SQLAlchemy ORM modelleri |
| schemas.py | Pydantic request/response modelleri |
| repository.py | Veritabanı erişim katmanı |
| service.py | İş kuralları ve domain logic |
| dependencies.py | FastAPI dependency injection fonksiyonları |
| permissions.py | Modül özel yetki kontrolleri |
| events.py | Domain event tanımları |
| exceptions.py | Modül özel hata sınıfları |
| tasks.py | Background job fonksiyonları |
| tests/ | Unit ve integration testleri |

MVP domain modülleri:

- core.
- db.
- auth.
- users.
- organizations.
- roles.
- conversations.
- calls.
- ai.
- tasks.
- appointments.
- notifications.
- audit.
- files.

Future/skeleton modüller:

- email.
- billing.
- admin.
- analytics.
- enterprise.
- whatsapp_business.

# 9. Layered Architecture

## 9.1 API Layer

Sorumluluklar:

- HTTP request alır.
- Auth dependency çalıştırır.
- Tenant context oluşturur.
- Input validation yapar.
- Service layer çağırır.
- Response döner.

API layer şunları yapmamalıdır:

- Doğrudan SQLAlchemy query yazmamalıdır.
- İş kuralı uygulamamalıdır.
- Harici provider çağrısını doğrudan yapmamalıdır.

## 9.2 Schema Layer

Sorumluluklar:

- Pydantic request modelleri.
- Pydantic response modelleri.
- Pagination schema.
- Error schema.
- Validation rule.
- OpenAPI açıklamaları.

## 9.3 Service Layer

Sorumluluklar:

- İş kurallarını uygular.
- Repository çağırır.
- Domain event üretir.
- Permission kontrolü yapar.
- AI action approval iş kurallarını uygular.
- Transaction boundary için Unit of Work kullanır.

## 9.4 Repository Layer

Sorumluluklar:

- SQLAlchemy query işlemleri.
- Tenant scoped query.
- CRUD operasyonları.
- Filtering/sorting/pagination query inşası.

Repository layer transaction dışı iş kuralı içermez.

## 9.5 Integration Layer

Sorumluluklar:

- Google API.
- Microsoft API.
- OpenAI/LLM API.
- Speech-to-Text API.
- Storage API.
- Notification API.
- Payment API.

Provider adapterları domain service’lere doğrudan provider objesi sızdırmamalıdır.

## 9.6 Worker Layer

Sorumluluklar:

- Background işler.
- AI analiz.
- Mail sync.
- Takvim sync.
- Bildirim gönderimi.
- Embedding üretimi.
- Analytics aggregation.
- Data export/delete.

# 10. Dependency Injection Yaklaşımı

FastAPI dependency injection şu amaçlarla kullanılmalıdır:

- DB session sağlama.
- Current user çözümleme.
- Current tenant çözümleme.
- Permission kontrolü.
- Repository/service instance sağlama.
- Rate limit policy uygulama.
- Request ID ve tracing context taşıma.

Dependency prensipleri:

- Auth dependency endpointlerden önce çalışmalıdır.
- Tenant context olmadan tenant verisi sorgulanmamalıdır.
- Service bağımlılıkları açık olmalıdır.
- Testlerde dependency override kolay olmalıdır.
- Harici provider adapterları interface üzerinden enjekte edilmelidir.

# 11. Configuration ve Environment Management

Configuration Pydantic settings ile yönetilmelidir.

Ortamlar:

- local.
- development.
- staging.
- production.
- test.

Config alanları:

- App name/version/environment.
- Database URL.
- Redis URL.
- JWT secret/public-private key.
- Access/refresh token süreleri.
- OAuth client ayarları.
- AI provider key ve model config.
- Storage bucket.
- Email/SMS provider.
- Sentry DSN.
- CORS allowed origins.
- Rate limit varsayılanları.

Güvenlik:

- Secret değerler repo içine yazılmamalıdır.
- .env yalnızca local development için kullanılmalıdır.
- Production secret manager veya KMS kullanmalıdır.

# 12. Database, SQLAlchemy ve Alembic Standardı

## 12.1 Database Connection Management

- API request başına session açılır ve request sonunda kapatılır.
- Background job kendi session lifecycle’ını yönetir.
- Long-running job tek transaction içinde tüm işi yapmamalıdır.
- Connection pool ayarları ortam bazlı yapılandırılmalıdır.
- Health check endpoint DB bağlantısını doğrulamalıdır.

## 12.2 SQLAlchemy Kullanım Standardı

- SQLAlchemy 2.x typed style tercih edilmelidir.
- Model tanımları domain modüllerinde tutulur.
- Ortak Base model created_at, updated_at, tenant_id gibi alanları standardize edebilir.
- Lazy loading kaynaklı N+1 sorunları için selectin/joined loading bilinçli kullanılmalıdır.
- Repository dışından query yazılmamalıdır.
- Tenant filter repository base seviyesinde enforce edilmelidir.

## 12.3 Alembic Migration Stratejisi

- Migration dosyaları versiyonlanmalıdır.
- Her migration reversible olmalıdır.
- Production migration öncesi backup alınmalıdır.
- Büyük tablo migrationları dikkatli yapılmalıdır.
- Zero-downtime migration prensipleri uygulanmalıdır.
- Kolon ekleme önce nullable yapılmalıdır.
- Backfill ayrı job ile yapılmalıdır.
- Daha sonra not null constraint eklenmelidir.
- Indexler concurrent oluşturulmalıdır.
- Migrationlar CI/CD içinde test edilmelidir.

# 13. Repository, Service ve Unit of Work Pattern

## 13.1 Repository Pattern

Repository sorumlulukları:

- Entity get/list/create/update.
- Tenant-scoped query.
- Pagination.
- Filtering/sorting.
- FK bazlı erişim.

Repository yasakları:

- Harici API çağrısı yapmaz.
- AI provider çağırmaz.
- Kullanıcı onayı gibi iş kurallarını uygulamaz.
- Audit log yazmaz; service layer tetikler.

## 13.2 Service Layer Pattern

Service layer:

- Use case bazlı metodlar içerir.
- Permission kontrolü yapar.
- Repository’leri koordine eder.
- Audit event üretir.
- Outbox event üretir.
- AI action approval durumlarını uygular.

Örnek service use case isimleri:

- register_user.
- create_conversation_from_text.
- request_ai_analysis.
- approve_ai_action.
- create_task_from_approval.
- create_appointment_from_approval.
- schedule_notification.
- export_user_data.
- request_user_deletion.

## 13.3 Unit of Work Pattern

Unit of Work:

- Transaction boundary sağlar.
- Birden fazla repository operasyonunu tek transaction altında yönetir.
- Outbox event kaydını transaction içine dahil eder.
- Commit/rollback davranışını merkezileştirir.

Kullanım ilkesi:

- API request içinde tek business transaction hedeflenir.
- Provider çağrıları mümkünse transaction dışında yapılır.
- Transaction içinde uzun süren AI/provider çağrısı yapılmamalıdır.

# 14. DTO / Schema Tasarımı

Pydantic schema türleri:

- Create request.
- Update request.
- Patch request.
- Detail response.
- List item response.
- Paginated response.
- Internal DTO.
- Error response.

Schema kuralları:

- Request ve response modelleri ayrılmalıdır.
- DB model doğrudan response olarak dönmemelidir.
- Hassas alanlar response’larda maskelenmelidir.
- Pydantic validation iş kuralının yerine geçmemeli; temel input doğrulama için kullanılmalıdır.
- OpenAPI açıklamaları ve örnekleri eklenmelidir.

# 15. API Router Tasarımı ve Versioning

API versioning:

- Tüm endpointler `/api/v1` altında olmalıdır.
- Gelecekte kırıcı değişiklikler `/api/v2` ile ayrılmalıdır.
- OpenAPI title/version environment ve release version ile eşleşmelidir.

Router prensipleri:

- Her domain kendi router dosyasına sahip olmalıdır.
- Router sadece dependency, request, response ve service çağrısı içermelidir.
- Endpoint isimleri resource odaklı olmalıdır.
- Idempotent işlemler için uygun HTTP method kullanılmalıdır.
- Webhook endpointleri ayrı güvenlik middleware veya dependency kullanmalıdır.

# 16. Authentication Tasarımı

## 16.1 Auth Akışları

1. E-posta ve şifre ile kayıt:
   - E-posta normalize edilir.
   - Şifre güvenlik kurallarına göre doğrulanır.
   - password_hash oluşturulur.
   - personal tenant ve default organization oluşturulur.
   - varsayılan rol atanır.
   - e-posta doğrulama tokenı üretilir.

2. E-posta doğrulama:
   - Token hash ile doğrulanır.
   - Süre ve kullanım durumu kontrol edilir.
   - Kullanıcı verified yapılır.

3. Şifre ile giriş:
   - Rate limit kontrol edilir.
   - Kullanıcı ve password_hash doğrulanır.
   - Oturum ve refresh token oluşturulur.
   - Access token döner.

4. JWT access token üretimi:
   - Kısa ömürlü olmalıdır.
   - user_id, tenant_id, roles ve token_type içermelidir.

5. Refresh token üretimi:
   - Uzun ömürlüdür.
   - Hashlenmiş veya şifrelenmiş saklanmalıdır.
   - Cihaz/oturum ile ilişkilidir.

6. Refresh token rotation:
   - Kullanılan refresh token revoke edilir.
   - Yeni refresh token üretilir.
   - Reuse detection güvenlik event’i üretir.

7. Logout:
   - Aktif refresh token revoke edilir.
   - Session kapatılır.

8. Tüm cihazlardan çıkış:
   - Kullanıcının tüm refresh tokenları revoke edilir.
   - Tüm sessionlar kapatılır.

9. Şifre sıfırlama:
   - Token hash saklanır.
   - Süre ve kullanım durumu kontrol edilir.
   - Yeni password_hash üretilir.
   - Tüm oturumları revoke etme önerilir.

10. Google OAuth login:
   - OAuth callback doğrulanır.
   - Provider user id ve email eşlenir.
   - Yeni kullanıcı veya mevcut kullanıcı bağlantısı yapılır.

11. Microsoft OAuth login:
   - Microsoft identity doğrulanır.
   - Kurumsal tenant kısıtları ileri fazda uygulanır.

12. Apple OAuth login:
   - Apple identity token doğrulanır.
   - E-posta gizleme senaryoları dikkate alınır.

13. 2FA:
   - İleri fazdır.
   - TOTP veya WebAuthn değerlendirilebilir.

## 16.2 JWT Claims

JWT içinde tutulabilecek bilgiler:

- sub.
- user_id.
- tenant_id.
- organization_id.
- roles.
- permissions, kısa liste veya permission version.
- token_type.
- issued_at.
- expires_at.

Güvenlik notları:

- Access token kısa ömürlü olmalıdır.
- Refresh token rotation zorunludur.
- Token çalınma durumunda revoke edilebilmelidir.
- Oturum cihaz bilgisiyle ilişkilendirilmelidir.
- Token içine hassas kişisel veri yazılmamalıdır.

# 17. Authorization, RBAC ve Permission Tasarımı

Roller:

- Owner.
- Admin.
- Manager.
- Member.
- Viewer.
- Billing Admin.

Permission örnekleri:

- users.read.
- users.manage.
- conversations.read.
- conversations.create.
- ai.analysis.request.
- ai.action.approve.
- tasks.manage.
- appointments.manage.
- calendar.connect.
- email.connect.
- contacts.manage.
- billing.manage.
- admin.access.

RBAC prensipleri:

- Role permission ilişkileri DB’de tutulur.
- Endpoint dependency gerekli permission’ı kontrol eder.
- Service layer kritik işlemlerde tekrar permission doğrular.
- Frontend role-based UI güvenlik mekanizması sayılmaz.
- Kurumsal kullanıcı yalnızca yetkili olduğu tenant/organization verisini görebilir.

İleri faz:

- ABAC.
- Resource owner check.
- Team scope.
- Data classification based access.

# 18. Multi-Tenant Backend Tasarımı

Tenant context kaynakları:

- JWT içindeki tenant_id.
- Kullanıcının aktif workspace’i.
- Admin impersonation, yalnızca audit ile ileri faz.
- API key tenant mapping, platform fazı.

Tenant kuralları:

- Tüm sorgular tenant_id ile filtrelenmelidir.
- Tenant isolation ihlali kritik güvenlik hatasıdır.
- Repository base class tenant filter uygular.
- Cross-tenant query yalnızca platform admin operasyonlarında, güçlü audit ile yapılabilir.
- AI Chat ve semantic search tenant filtresi olmadan çalışamaz.
- Background job payload tenant_id içermelidir.

Tenant context lifecycle:

1. Auth dependency kullanıcıyı çözer.
2. Tenant dependency tenant_id’yi doğrular.
3. Request state içine tenant_context yazılır.
4. Service ve repository tenant_context alır.
5. Audit log tenant_id ile yazılır.

# 19. Request Lifecycle

Standart request akışı:

1. Request API gateway/load balancer üzerinden gelir.
2. Request ID oluşturulur veya alınır.
3. Logging/tracing context başlar.
4. Rate limit kontrol edilir.
5. Auth dependency çalışır.
6. Tenant context oluşturulur.
7. Pydantic validation yapılır.
8. Permission kontrol edilir.
9. Service use case çağrılır.
10. Repository ve UoW ile DB işlemleri yapılır.
11. Audit/outbox event yazılır.
12. Response standard formatta döner.
13. Log/metrics kaydı tamamlanır.

# 20. Error Handling Standardı

Standart hata kategorileri:

- ValidationError.
- AuthenticationError.
- AuthorizationError.
- PermissionDenied.
- TenantIsolationError.
- ResourceNotFound.
- ConflictError.
- RateLimitExceeded.
- ProviderError.
- AIProviderError.
- JobQueueError.
- StorageError.
- BusinessRuleViolation.

Response alanları:

- success: false.
- error_code.
- message.
- details.
- request_id.
- timestamp.

İlkeler:

- Kullanıcıya teknik stack trace dönülmez.
- Provider hata detayları sanitize edilir.
- Sensitive data hata mesajında yer almaz.
- Her hata request_id ile loglanır.
- Tenant isolation hataları security_event üretir.

# 21. Response, Pagination, Filtering ve Sorting Standardı

Başarılı response:

- success.
- data.
- meta.
- request_id.

Pagination:

- page/page_size veya cursor tabanlı destek.
- Büyük timeline ve activity listelerinde cursor pagination tercih edilir.
- page_size üst limiti olmalıdır.

Filtering:

- status.
- date range.
- source_type.
- contact_id.
- assigned_user_id.
- tag.

Sorting:

- created_at.
- updated_at.
- due_at.
- start_at.
- priority.

Standart:

- Filtering ve sorting whitelist ile sınırlandırılmalıdır.
- Kullanıcıdan gelen field adı doğrudan query’ye yansıtılmamalıdır.

# 22. Validation Standardı

Validation katmanları:

- Pydantic field validation.
- Business validation service layer.
- DB constraint.
- Provider response schema validation.
- AI JSON output validation.

Örnek validasyonlar:

- E-posta formatı.
- Şifre gücü.
- Tarih aralığı start_at < end_at.
- Görev due_at geçmişte ise uyarı.
- AI confidence_score 0-1 arası.
- OAuth scope beklenen minimum scope’u karşılamalı.

# 23. Background Job, Queue ve Scheduler Mimarisi

Background job kullanım alanları:

- AI analiz.
- Speech-to-text.
- Mail sync.
- Calendar sync.
- Bildirim gönderimi.
- Hatırlatma planlama.
- Embedding üretimi.
- Semantic index güncelleme.
- Dosya analizi.
- OCR.
- Analytics aggregation.
- Data export.
- Data deletion.
- Webhook retry.
- Payment webhook processing.

Job status değerleri:

- queued.
- processing.
- completed.
- failed.
- cancelled.
- retrying.
- dead_letter.

Job tasarım ilkeleri:

- Retry policy.
- Exponential backoff.
- Dead letter queue.
- Idempotency.
- Job timeout.
- Job priority.
- Tenant-aware workers.
- Audit logging.
- Error tracking.
- Progress reporting.

Queue ayrımı:

- ai_high_priority.
- ai_default.
- sync_email.
- sync_calendar.
- notifications.
- embeddings.
- privacy_jobs.
- analytics.
- webhooks.

Scheduler:

- scheduled_notifications tarar.
- due reminder job üretir.
- periyodik sync job tetikler.
- analytics aggregation çalıştırır.
- retention cleanup çalıştırır.

# 24. Event-Driven Backend ve Outbox Pattern

Outbox pattern:

1. Service transaction içinde domain state’i günceller.
2. Aynı transaction içinde outbox_events kaydı oluşturur.
3. Outbox worker event’i okur.
4. Message broker’a veya internal handler’a gönderir.
5. Event processed durumuna alınır.

Örnek eventler:

- user.created.
- conversation.created.
- call.uploaded.
- ai.analysis.requested.
- ai.analysis.completed.
- task.suggested.
- task.created.
- appointment.suggested.
- appointment.created.
- notification.scheduled.
- notification.sent.
- contact.updated.
- consent.updated.
- data.deletion.requested.

Prensip:

- MVP’de internal event dispatcher yeterli olabilir.
- İleri fazda RabbitMQ/Kafka entegrasyonuna evrilebilir.
- Event payload tenant_id ve correlation_id içermelidir.

# 25. Audit Log Backend Tasarımı

Audit log gerektiren işlemler:

- Login success/failure.
- Logout.
- Password change.
- Role change.
- Permission change.
- Organization member ekleme/silme.
- Integration bağlama/kaldırma.
- OAuth token yenileme.
- AI action approval.
- Mail gönderme.
- Takvim event oluşturma.
- Veri dışa aktarma.
- Veri silme talebi.
- Dosya silme.
- Admin işlemleri.
- Billing değişiklikleri.

Audit log standardı:

- Append-only olmalıdır.
- actor_id, tenant_id, action, entity_type, entity_id, request_id içermelidir.
- Before/after state hassas veri içeriyorsa maskeleme uygulanmalıdır.
- Audit yazma hatası kritik işlemlerde fail-closed değerlendirilebilir.

# 26. Modül Bazlı Backend Tasarımları

## 26.1 Auth Backend Tasarımı

Amaç:

- Kullanıcı kimlik doğrulaması, oturum ve token lifecycle yönetimi.

Sorumluluklar:

- Register.
- Login.
- Refresh token rotation.
- Logout.
- Password reset.
- OAuth login.
- Session management.

MVP:

- E-posta/şifre auth.
- JWT.
- Refresh token rotation.
- Google OAuth opsiyonel.

Future:

- Microsoft/Apple OAuth.
- MFA.
- Enterprise SSO.

## 26.2 User ve Organization Backend Tasarımı

Amaç:

- Kullanıcı profili, preferences, organization ve membership yönetimi.

MVP:

- Personal tenant.
- Default organization.
- User profile.
- Basic roles.

Future:

- Team management.
- Organization invitations.
- SCIM provisioning.

## 26.3 Conversation / Call Backend Tasarımı

Amaç:

- Görüşme metni, call kaydı, transcription ve AI analysis job akışını yönetmek.

MVP:

- Manuel görüşme metni.
- Conversation + call + transcription kayıtları.
- AI analysis job enqueue.

Future:

- Ses dosyası yükleme.
- STT provider.
- Diarization.

## 26.4 Task Backend Tasarımı

Amaç:

- Manuel ve AI önerili görevleri yönetmek.

MVP:

- CRUD.
- due_at.
- priority.
- status.
- source link.
- reminder.

Future:

- Team assignment.
- Recurring tasks.
- External project tool sync.

## 26.5 Appointment ve Calendar Backend Tasarımı

Amaç:

- Uygulama içi randevu ve harici takvim eventlerini yönetmek.

MVP:

- Appointment CRUD.
- Google Calendar connect.
- Conflict check.
- User approval ile external event create.

Future:

- Outlook Calendar.
- Availability suggestions.
- Two-way sync.

## 26.6 Contact / CRM Backend Tasarımı

Amaç:

- Kişi/firma hafızası, timeline ve ilişkilendirme.

MVP:

- Contact CRUD.
- Timeline.
- Conversation/task/appointment ilişkilendirme.

Future:

- Deduplication.
- Company memory.
- CRM pipeline.

## 26.7 Notification Backend Tasarımı

Amaç:

- Bildirim planlama ve teslimat.

MVP:

- E-posta/push temel bildirim.
- scheduled_notifications.
- delivery log.

Future:

- SMS.
- WhatsApp Business API resmi izinli kanal.
- Template management.

## 26.8 Consent ve Privacy Backend Tasarımı

Amaç:

- Rıza, veri dışa aktarma, veri silme ve privacy ayarlarını yönetmek.

MVP:

- consent_records.
- export request.
- deletion request.
- AI provider consent flag.

Future:

- Custom retention.
- Legal hold.
- Enterprise DPA workflows.

## 26.9 Billing Backend Tasarımı

MVP’de skeleton olabilir.

Sorumluluklar:

- Plan listesi.
- Subscription state.
- Usage quota.
- Payment webhook, ileri faz.

## 26.10 Admin Backend Tasarımı

MVP’de sınırlı platform admin olarak başlayabilir.

Sorumluluklar:

- User/tenant overview.
- System health.
- AI cost logs.
- Feature flags.
- Audit logs.

# 27. API Endpoint Kataloğu

Bu bölüm endpoint tasarımını tanımlar. Her endpoint backend implementasyonunda auth, tenant context, permission, validation, audit ve standart response kurallarına uymalıdır.

## 27.1 Auth Endpointleri

| Method | Endpoint | Amaç | Auth | MVP |
|---|---|---|---|---|
| POST | /api/v1/auth/register | Kullanıcı kaydı | Public | Must |
| POST | /api/v1/auth/login | Şifre ile giriş | Public | Must |
| POST | /api/v1/auth/refresh | Refresh token rotation | Refresh token | Must |
| POST | /api/v1/auth/logout | Oturum kapatma | User | Must |
| POST | /api/v1/auth/logout-all | Tüm cihazlardan çıkış | User | Should |
| POST | /api/v1/auth/password-reset/request | Şifre sıfırlama talebi | Public | Must |
| POST | /api/v1/auth/password-reset/confirm | Yeni şifre belirleme | Public token | Must |
| POST | /api/v1/auth/email/verify | E-posta doğrulama | Public token | Must |
| GET | /api/v1/auth/oauth/google/start | Google OAuth başlatma | Public | Should |
| GET | /api/v1/auth/oauth/google/callback | Google OAuth callback | Public | Should |
| GET | /api/v1/auth/oauth/microsoft/start | Microsoft OAuth başlatma | Public | Future |
| GET | /api/v1/auth/oauth/apple/start | Apple OAuth başlatma | Public | Future |

## 27.2 User / Organization Endpointleri

| Method | Endpoint | Amaç | MVP |
|---|---|---|---|
| GET | /api/v1/users/me | Kendi profilini görüntüleme | Must |
| PATCH | /api/v1/users/me | Profil güncelleme | Must |
| GET | /api/v1/users/me/preferences | Tercihleri görüntüleme | Should |
| PATCH | /api/v1/users/me/preferences | Tercihleri güncelleme | Should |
| GET | /api/v1/users/me/sessions | Aktif oturumlar | Should |
| DELETE | /api/v1/users/me/sessions/{session_id} | Oturum kapatma | Should |
| GET | /api/v1/organizations/current | Aktif organizasyon | Must |
| PATCH | /api/v1/organizations/current | Organizasyon güncelleme | Should |
| GET | /api/v1/organizations/members | Üyeler | Future |
| POST | /api/v1/organizations/invitations | Davet | Future |

## 27.3 Conversation / Call Endpointleri

| Method | Endpoint | Amaç | MVP |
|---|---|---|---|
| GET | /api/v1/conversations | Görüşme listesi | Must |
| POST | /api/v1/conversations | Manuel conversation oluşturma | Must |
| GET | /api/v1/conversations/{conversation_id} | Detay | Must |
| DELETE | /api/v1/conversations/{conversation_id} | Soft delete | Should |
| POST | /api/v1/calls/text | Görüşme metni yükleme | Must |
| POST | /api/v1/calls/audio-upload-url | Ses upload URL | Future |
| POST | /api/v1/calls/{call_id}/transcribe | STT job başlatma | Future |
| POST | /api/v1/calls/{call_id}/analyze | AI analysis job başlatma | Must |
| GET | /api/v1/calls/{call_id}/analysis | Analiz sonuçları | Must |

## 27.4 AI Endpointleri

| Method | Endpoint | Amaç | MVP |
|---|---|---|---|
| POST | /api/v1/ai/analyze | Kaynak analiz job oluşturma | Must |
| GET | /api/v1/ai/jobs/{job_id} | Job status | Must |
| GET | /api/v1/ai/results/{result_id} | AI result detail | Must |
| POST | /api/v1/ai/actions/{approval_id}/approve | AI önerisini onaylama | Must |
| POST | /api/v1/ai/actions/{approval_id}/reject | AI önerisini reddetme | Must |
| PATCH | /api/v1/ai/actions/{approval_id} | AI önerisini düzenleme | Must |
| POST | /api/v1/ai/feedback | Feedback verme | Should |
| POST | /api/v1/ai/chat | AI Chat mesajı | Must |
| GET | /api/v1/ai/chat/sessions | Chat session listesi | Must |
| GET | /api/v1/ai/chat/sessions/{session_id} | Chat geçmişi | Must |

## 27.5 Task Endpointleri

| Method | Endpoint | Amaç | MVP |
|---|---|---|---|
| GET | /api/v1/tasks | Görev listesi | Must |
| POST | /api/v1/tasks | Manuel görev oluşturma | Must |
| GET | /api/v1/tasks/{task_id} | Görev detayı | Must |
| PATCH | /api/v1/tasks/{task_id} | Görev güncelleme | Must |
| DELETE | /api/v1/tasks/{task_id} | Soft delete | Should |
| POST | /api/v1/tasks/{task_id}/complete | Tamamlandı | Must |
| POST | /api/v1/tasks/{task_id}/reminders | Hatırlatma ekleme | Must |
| GET | /api/v1/tasks/overdue | Geciken görevler | Must |

## 27.6 Appointment / Calendar Endpointleri

| Method | Endpoint | Amaç | MVP |
|---|---|---|---|
| GET | /api/v1/appointments | Randevu listesi | Must |
| POST | /api/v1/appointments | Manuel randevu | Must |
| GET | /api/v1/appointments/{appointment_id} | Randevu detayı | Must |
| PATCH | /api/v1/appointments/{appointment_id} | Randevu güncelleme | Must |
| DELETE | /api/v1/appointments/{appointment_id} | Randevu silme | Should |
| POST | /api/v1/appointments/check-conflicts | Çakışma kontrolü | Must |
| GET | /api/v1/calendar/accounts | Bağlı takvim hesapları | Must |
| POST | /api/v1/calendar/google/connect | Google Calendar connect | Must |
| POST | /api/v1/calendar/sync | Takvim sync | Should |
| GET | /api/v1/calendar/events | Takvim eventleri | Must |

## 27.7 Email Endpointleri

| Method | Endpoint | Amaç | MVP |
|---|---|---|---|
| GET | /api/v1/email/accounts | Mail hesapları | Future |
| POST | /api/v1/email/gmail/connect | Gmail bağlama | Future |
| POST | /api/v1/email/outlook/connect | Outlook bağlama | Future |
| POST | /api/v1/email/sync | Mail sync | Future |
| GET | /api/v1/email/messages | Mail listesi | Future |
| POST | /api/v1/email/{email_id}/analyze | Mail analizi | Future |
| POST | /api/v1/email/drafts | Taslak oluşturma | Future |
| POST | /api/v1/email/drafts/{draft_id}/send | Açık onayla gönderme | Future |

## 27.8 Contact Endpointleri

| Method | Endpoint | Amaç | MVP |
|---|---|---|---|
| GET | /api/v1/contacts | Kişi listesi | Must |
| POST | /api/v1/contacts | Kişi oluşturma | Must |
| GET | /api/v1/contacts/{contact_id} | Kişi detayı | Must |
| PATCH | /api/v1/contacts/{contact_id} | Kişi güncelleme | Must |
| DELETE | /api/v1/contacts/{contact_id} | Soft delete | Should |
| GET | /api/v1/contacts/{contact_id}/timeline | Timeline | Must |
| POST | /api/v1/contacts/{contact_id}/notes | Not ekleme | Should |

## 27.9 Notification Endpointleri

| Method | Endpoint | Amaç | MVP |
|---|---|---|---|
| GET | /api/v1/notifications | Bildirim listesi | Must |
| PATCH | /api/v1/notifications/{notification_id}/read | Okundu | Must |
| GET | /api/v1/notifications/preferences | Tercihler | Should |
| PATCH | /api/v1/notifications/preferences | Tercih güncelleme | Should |
| POST | /api/v1/notifications/test | Test bildirimi | Could |

## 27.10 File Endpointleri

| Method | Endpoint | Amaç | MVP |
|---|---|---|---|
| POST | /api/v1/files/upload-url | Signed upload URL | Should |
| POST | /api/v1/files/complete-upload | Upload finalize | Should |
| GET | /api/v1/files | Dosya listesi | Should |
| GET | /api/v1/files/{file_id} | Dosya metadata | Should |
| DELETE | /api/v1/files/{file_id} | Dosya silme | Should |
| POST | /api/v1/files/{file_id}/analyze | Belge analizi | Future |
| GET | /api/v1/files/{file_id}/analysis | Analiz sonuçları | Future |

## 27.11 Search ve Dashboard Endpointleri

| Method | Endpoint | Amaç | MVP |
|---|---|---|---|
| GET | /api/v1/search | Anahtar kelime arama | Must |
| POST | /api/v1/search/semantic | Semantik arama | Should |
| GET | /api/v1/search/recent | Son aramalar | Could |
| GET | /api/v1/dashboard | Ana dashboard | Must |
| GET | /api/v1/dashboard/daily-summary | Günlük özet | Must |
| GET | /api/v1/dashboard/upcoming | Yaklaşan randevular | Must |
| GET | /api/v1/dashboard/pending-actions | Bekleyen AI onayları | Must |
| GET | /api/v1/dashboard/ai-suggestions | AI önerileri | Must |

## 27.12 Analytics Endpointleri

| Method | Endpoint | Amaç | MVP |
|---|---|---|---|
| GET | /api/v1/analytics/overview | Genel metrikler | Should |
| GET | /api/v1/analytics/tasks | Görev metrikleri | Should |
| GET | /api/v1/analytics/calls | Görüşme metrikleri | Should |
| GET | /api/v1/analytics/emails | Mail metrikleri | Future |
| GET | /api/v1/analytics/appointments | Randevu metrikleri | Should |
| GET | /api/v1/analytics/ai | AI kullanım/maliyet | Should |
| GET | /api/v1/analytics/team | Ekip metrikleri | Future |

## 27.13 Integration Endpointleri

| Method | Endpoint | Amaç | MVP |
|---|---|---|---|
| GET | /api/v1/integrations/providers | Provider listesi | Must |
| GET | /api/v1/integrations | Bağlı entegrasyonlar | Must |
| POST | /api/v1/integrations/{provider}/connect | Bağlantı başlatma | Must |
| DELETE | /api/v1/integrations/{integration_id} | Entegrasyon kaldırma | Must |
| POST | /api/v1/integrations/{integration_id}/sync | Manuel sync | Should |
| GET | /api/v1/integrations/{integration_id}/status | Sync/connection durumu | Should |
| POST | /api/v1/integrations/webhooks/{provider} | Provider webhook | Future |

## 27.14 Consent ve Privacy Endpointleri

| Method | Endpoint | Amaç | MVP |
|---|---|---|---|
| GET | /api/v1/consents | Rıza kayıtları | Must |
| POST | /api/v1/consents | Rıza verme | Must |
| PATCH | /api/v1/consents/{consent_id} | Rıza geri çekme | Must |
| GET | /api/v1/privacy/settings | Privacy ayarları | Should |
| PATCH | /api/v1/privacy/settings | Ayar güncelleme | Should |
| POST | /api/v1/privacy/export | Veri export talebi | Must |
| GET | /api/v1/privacy/export/{request_id} | Export durumu | Must |
| POST | /api/v1/privacy/delete-request | Silme talebi | Must |
| GET | /api/v1/privacy/delete-request/{request_id} | Silme durumu | Must |

## 27.15 Billing Endpointleri

| Method | Endpoint | Amaç | MVP |
|---|---|---|---|
| GET | /api/v1/billing/plans | Planlar | Should |
| GET | /api/v1/billing/subscription | Mevcut abonelik | Should |
| POST | /api/v1/billing/subscription | Abonelik başlatma | Future |
| PATCH | /api/v1/billing/subscription | Plan değiştirme | Future |
| DELETE | /api/v1/billing/subscription | İptal | Future |
| GET | /api/v1/billing/invoices | Faturalar | Future |
| GET | /api/v1/billing/usage | Kullanım | Should |
| POST | /api/v1/billing/webhook | Payment webhook | Future |

## 27.16 Admin Endpointleri

| Method | Endpoint | Amaç | MVP |
|---|---|---|---|
| GET | /api/v1/admin/users | Kullanıcı listesi | Future |
| GET | /api/v1/admin/organizations | Organizasyon listesi | Future |
| GET | /api/v1/admin/tenants | Tenant listesi | Future |
| GET | /api/v1/admin/audit-logs | Audit log | Future |
| GET | /api/v1/admin/system-health | Sistem sağlığı | Should |
| GET | /api/v1/admin/feature-flags | Feature flags | Should |
| PATCH | /api/v1/admin/feature-flags/{flag_id} | Flag güncelleme | Future |
| GET | /api/v1/admin/errors | Hata logları | Future |
| GET | /api/v1/admin/ai-costs | AI maliyetleri | Future |

# 28. AI Backend Tasarımı

AI Orchestration Service sorumlulukları:

- AI analysis job oluşturma.
- Prompt template seçme.
- Prompt version belirleme.
- Provider seçme.
- LLM çağrısı yapma.
- JSON response validation.
- Confidence score hesaplama.
- AI çıktısını structured data’ya dönüştürme.
- Kullanıcı onayı gerektiren action approval oluşturma.
- Embedding oluşturma.
- AI logs ve cost logs yazma.
- User feedback kaydetme.

AI analiz türleri:

- conversation_summary.
- task_extraction.
- appointment_extraction.
- entity_extraction.
- deadline_extraction.
- risk_detection.
- priority_scoring.
- email_summary.
- email_action_extraction.
- ai_chat_response.
- semantic_search_context_generation.
- contact_memory_update.

AI provider adapter:

- Provider bağımlılığı interface arkasına alınmalıdır.
- Timeout, retry ve cost logging standart olmalıdır.
- Response schema validation zorunlu olmalıdır.
- Prompt injection ve tool misuse riskleri safety layer ile azaltılmalıdır.
- İlk backend implementasyonunda gerçek provider yerine mock adapter ile başlanabilir.

# 29. AI Action Approval Backend Akışı

AI önerisi oluştuğunda:

1. AI Worker analiz sonucunu üretir.
2. Görev/randevu/mail taslağı gibi aksiyon önerileri çıkarılır.
3. Bu öneriler doğrudan uygulanmaz.
4. ai_action_approvals kaydı oluşturulur.
5. Kullanıcıya “AI önerisi” olarak gösterilir.
6. Kullanıcı onaylarsa ilgili service gerçek aksiyonu uygular.
7. Kullanıcı reddederse öneri rejected olur.
8. Kullanıcı düzenlerse approved_payload üzerinden uygulanır.
9. Tüm süreç audit log’a yazılır.

İş kuralı:

- AI sadece öneri üretir.
- Gerçek iş aksiyonu kullanıcı onayıyla uygulanır.
- Onaylanan payload tekrar validate edilir.
- Approval tenant_id, user_id, source_type ve source_id ile doğrulanır.
- Expired approval uygulanamaz.

# 30. Call Analysis Backend Akışı

Telefon görüşmesi analizi:

1. Kullanıcı görüşme metni veya ses dosyası yükler.
2. Backend rıza kontrolü yapar.
3. Conversation kaydı oluşturur.
4. Call kaydı oluşturur.
5. Ses dosyası varsa object storage’a yüklenir.
6. Transcription job kuyruğa alınır, ses yoksa manuel metin transcription kabul edilir.
7. Transcription tamamlanınca call_transcriptions kaydı oluşur.
8. AI analysis job kuyruğa alınır.
9. AI summary, task, appointment ve entity önerileri üretir.
10. Sonuçlar kullanıcıya gösterilir.
11. Onaylanan task/appointment kayıtları oluşturulur.
12. Bildirimler planlanır.
13. Contact timeline güncellenir.

MVP:

- Manuel metin girişi.
- AI summary/task/appointment extraction.

Future:

- STT.
- Speaker diarization.
- Audio upload.

# 31. Email Analysis Backend Akışı

Mail analizi:

1. Kullanıcı Gmail veya Outlook entegrasyonu bağlar.
2. OAuth token güvenli şekilde saklanır.
3. Mail sync job başlar.
4. Provider’dan mail metadata alınır.
5. Gerekli izin varsa mail body alınır.
6. Mail thread ve email kayıtları oluşturulur.
7. AI analysis job kuyruğa alınır.
8. AI mail özeti, görev, deadline, randevu ve bekleyen cevap tespit eder.
9. Kullanıcı onaylarsa görev/randevu oluşturulur.
10. Mail taslağı önerisi varsa kullanıcı onayıyla draft oluşturulur.
11. Mail gönderimi için ayrıca açık kullanıcı onayı gerekir.

Güvenlik:

- Minimum OAuth scope.
- Token encryption.
- Mail body encryption veya retention.
- Onaysız mail gönderimi kesinlikle engellenir.

# 32. Calendar Backend Akışı

Takvim akışı:

1. Kullanıcı Google Calendar veya Outlook Calendar bağlar.
2. OAuth token güvenli saklanır.
3. Calendar sync job çalışır.
4. Harici takvim eventleri alınır.
5. Uygulama içi calendar_events kayıtları güncellenir.
6. AI önerili randevu oluşturulurken çakışma kontrol edilir.
7. Kullanıcı onaylarsa harici takvimde event oluşturulur.
8. Reminder kayıtları oluşturulur.
9. Notification worker hatırlatmaları gönderir.

MVP:

- Google Calendar.
- Conflict check.
- User-approved event creation.

Future:

- Outlook Calendar.
- Two-way sync.
- Availability suggestions.

# 33. AI Chat ve Semantic Search Backend Akışı

AI Chat:

1. Kullanıcı doğal dilde soru sorar.
2. Backend user/tenant context kontrol eder.
3. Query embedding oluşturulur.
4. Vector database veya pgvector üzerinde tenant-scoped semantic search yapılır.
5. İlgili kaynaklar alınır.
6. RAG context oluşturulur.
7. LLM cevap üretir.
8. Cevap kaynaklarla birlikte döner.
9. Chat message kaydedilir.
10. Kullanıcı feedback verebilir.

Örnek sorular:

- “Ahmet bana en son ne demişti?”
- “Bu hafta kimlere teklif göndermem gerekiyor?”
- “Geçen ay fiyat isteyen ama dönüş yapmadığım müşterileri listele.”
- “Bugün en önemli işlerim neler?”
- “Cuma günü olan toplantılarımı göster.”

Semantic search:

- Kaynak metin chunk’lara bölünür.
- Her chunk için embedding oluşturulur.
- embeddings tablosuna veya vector DB’ye kaydedilir.
- source_type, source_id, tenant_id metadata olarak saklanır.
- Kullanıcı arama yaptığında query embedding oluşturulur.
- Tenant filter zorunlu uygulanır.
- En alakalı sonuçlar skorla döner.
- Kullanıcıya kaynak gösterilir.

Source type örnekleri:

- conversation.
- call_transcription.
- email.
- note.
- document.
- task.
- appointment.
- contact_memory.

# 34. Notification Backend Tasarımı

Bildirim kanalları:

- Push notification.
- E-posta.
- SMS.
- WhatsApp Business API, resmi izinli kullanım varsa.

Bildirim türleri:

- Randevu hatırlatma.
- Görev deadline hatırlatma.
- Geciken görev.
- AI önerisi hazır.
- Mail analizi tamamlandı.
- Görüşme analizi tamamlandı.
- Takvim çakışması.
- Sistem bildirimi.
- Abonelik bildirimi.

Gönderim akışı:

1. scheduled_notification kaydı oluşturulur.
2. Scheduler zamanı gelen kayıtları bulur.
3. Notification worker uygun kanalı seçer.
4. Provider’a gönderim yapar.
5. Delivery sonucu kaydedilir.
6. Başarısızsa retry uygulanır.
7. Kullanıcı bildirim tercihlerine saygı duyulur.

# 35. File Upload ve Object Storage Backend Tasarımı

Dosya yükleme yaklaşımı:

- Büyük dosyalar backend üzerinden doğrudan geçirilmemelidir.
- Backend signed upload URL üretmelidir.
- Kullanıcı dosyayı object storage’a yüklemelidir.
- Upload tamamlanınca backend metadata kaydını finalize etmelidir.
- Dosya tipi ve boyutu kontrol edilmelidir.
- Malware scan ileri fazda eklenmelidir.
- Dosya erişimleri permission ve tenant context ile kontrol edilmelidir.

Desteklenecek dosyalar:

- PDF.
- DOCX.
- TXT.
- MP3.
- WAV.
- M4A.
- EML.
- CSV, ileri faz.
- XLSX, ileri faz.

Güvenlik:

- Signed URL kısa ömürlü olmalıdır.
- Storage key kullanıcıya kalıcı açık verilmemelidir.
- Download da signed URL ile olmalıdır.
- Dosya binary veritabanında tutulmamalıdır.

# 36. Security Backend Tasarımı

Başlıklar:

- HTTPS zorunluluğu.
- JWT access token.
- Refresh token rotation.
- Password hashing.
- OAuth token encryption.
- Field-level encryption.
- KMS kullanımı.
- Secrets management.
- RBAC.
- Tenant isolation.
- Rate limiting.
- Brute force protection.
- CORS.
- CSRF, web cookie tabanlı auth kullanılırsa.
- Secure headers.
- File upload validation.
- Webhook signature verification.
- API key management.
- Audit logging.
- PII masking.
- AI data leakage prevention.
- Sensitive logging yasağı.

Backend güvenlik iş kuralları:

- AI hiçbir zaman kullanıcı onayı olmadan mail gönderemez.
- AI hiçbir zaman kullanıcı onayı olmadan takvim etkinliği oluşturamaz.
- AI hiçbir zaman kullanıcı onayı olmadan görev atayamaz.
- AI hiçbir zaman kullanıcı onayı olmadan veri silemez.
- AI önerileri ai_action_approvals üzerinden onaylanmalıdır.
- Kullanıcı veri kaynağı entegrasyonunu istediği zaman kaldırabilmelidir.
- Kullanıcı verisini dışa aktarabilmelidir.
- Kullanıcı verisini silebilmelidir.
- WhatsApp tarafında yalnızca resmi API ve izinli entegrasyonlar kullanılmalıdır.

# 37. Rate Limiting

Rate limit örnekleri:

| Alan | Limit yaklaşımı |
|---|---|
| Login endpointleri | IP + user/email bazlı sıkı limit |
| Password reset | IP + email bazlı sıkı limit |
| AI analysis | Plan + tenant + user bazlı kota |
| AI Chat | Plan + user bazlı kota |
| File upload | Dosya boyutu + günlük limit |
| Email sync | Provider rate limitlerine uyumlu throttling |
| Calendar sync | Provider rate limitlerine uyumlu throttling |
| Public webhook | Signature + IP/provider bazlı limit |
| Admin endpointleri | Güvenlik odaklı limit |

Rate limit scope:

- IP bazlı.
- User bazlı.
- Tenant bazlı.
- API key bazlı.
- Endpoint bazlı.

# 38. Logging, Monitoring ve Tracing

## 38.1 Logging Standardı

Structured logging kullanılmalıdır.

Log alanları:

- timestamp.
- level.
- service.
- environment.
- request_id.
- trace_id.
- user_id.
- tenant_id.
- organization_id.
- endpoint.
- method.
- status_code.
- duration_ms.
- error_code.
- job_id.
- provider.
- ai_model.
- ai_cost.
- message.

Loglanmaması gerekenler:

- Password.
- Access token.
- Refresh token.
- OAuth token.
- Full mail body.
- Full transcription.
- Payment card data.
- Sensitive personal data.

## 38.2 Monitoring

Metrikler:

- API latency.
- Error rate.
- Queue length.
- Worker success/failure.
- AI provider latency.
- AI cost.
- DB connection pool.
- Notification delivery rate.
- OAuth refresh failure.
- Tenant-level usage.

## 38.3 Tracing

- OpenTelemetry önerilir.
- request_id ve trace_id worker job’lara taşınmalıdır.
- Provider çağrıları trace span olarak izlenmelidir.

# 39. Testing Strategy

## 39.1 Unit Test

- Service layer.
- Repository mock.
- Permission logic.
- Validation logic.
- AI response parser.
- Tenant context helper.

## 39.2 Integration Test

- API endpointler.
- Database işlemleri.
- Auth flow.
- Tenant isolation.
- Background job enqueue.
- Audit log write.

## 39.3 Contract Test

- External provider API wrapper.
- AI provider response schema.
- Webhook payload validation.
- OpenAPI schema compatibility.

## 39.4 Security Test

- Unauthorized access.
- Cross-tenant access.
- Token expiration.
- Permission denial.
- Rate limit.
- Sensitive log absence.

## 39.5 AI Test

- Summary validation.
- Task extraction validation.
- Appointment extraction validation.
- JSON schema validation.
- Low confidence handling.
- Hallucination guard.

## 39.6 E2E API Test

- Register/login.
- Call upload.
- AI analysis.
- Task approval.
- Appointment approval.
- Notification scheduling.
- Dashboard read.

# 40. Performance Strategy

Hedefler:

- Çoğu API endpointi 300-800ms aralığında cevap vermelidir.
- Kullanıcı bazlı görev listesi 500ms altında dönmelidir.
- Randevu listesi 500ms altında dönmelidir.
- Dashboard cache kullanmalıdır.
- AI analizler asenkron çalışmalıdır.
- Semantic search 1-3 saniye hedeflemelidir.
- Büyük transkripsiyonlar chunk/segment yapısıyla saklanmalıdır.
- Mail sync batch mantığıyla çalışmalıdır.
- Analytics pre-aggregated tablolar üzerinden okunmalıdır.

Backend teknikleri:

- Pagination zorunlu.
- Eager loading ölçümle.
- Redis cache.
- Index-aware filtering.
- Worker autoscaling.
- Queue priority.
- Provider timeout.
- Request payload size limit.

# 41. Deployment, Docker ve CI/CD Backend Gereksinimleri

## 41.1 Deployment

Backend servisleri:

- API server.
- Worker containers.
- Scheduler container.
- PostgreSQL.
- Redis.
- Object storage.

Production:

- Gunicorn + Uvicorn worker.
- Health check endpoint.
- Readiness/liveness probes.
- Environment-based config.
- Sentry enabled.
- Structured logs stdout.

## 41.2 Docker

Docker gereksinimleri:

- Minimal production image.
- Non-root user.
- Healthcheck.
- Separate API and worker commands.
- No secrets in image.

## 41.3 CI/CD

Pipeline:

1. Ruff lint.
2. MyPy type check.
3. Unit tests.
4. Integration tests.
5. OpenAPI generation/validation.
6. Docker build.
7. Security scan.
8. Staging deploy.
9. Smoke test.
10. Manual approval production deploy.

# 42. Backend Riskleri

| Risk | Açıklama | Etki | Olasılık | Azaltma stratejisi |
|---|---|---|---|---|
| Tenant isolation hatası | Yanlış sorgu başka tenant verisini döndürebilir | Çok yüksek | Orta | Repository-level tenant enforcement, test, audit, security review |
| AI provider maliyet artışı | AI analiz/chat maliyeti büyüyebilir | Yüksek | Orta | Kota, cost logs, model routing, cache, plan limitleri |
| AI hallucination | Kaynakta olmayan bilgi üretilebilir | Yüksek | Orta | RAG, kaynak gösterme, confidence, human approval |
| AI response JSON parse hatası | LLM beklenen schema dışında dönebilir | Orta | Yüksek | Schema validation, retry, fallback prompt, parser tests |
| OAuth token sızıntısı | Mail/takvim erişimi riski | Çok yüksek | Orta | Field encryption, KMS, token rotation, audit |
| Mail API rate limitleri | Sync gecikir veya başarısız olur | Orta | Yüksek | Backoff, incremental sync, throttling |
| Calendar API rate limitleri | Event yazma/okuma limitlenir | Orta | Orta | Batch, cache, retry, idempotency |
| Speech-to-text doğruluk sorunları | Yanlış transcript yanlış AI önerisi üretir | Orta/Yüksek | Orta | Confidence score, kullanıcı düzeltmesi, STT provider seçimi |
| Background job backlog | AI/sync işleri birikir | Yüksek | Orta | Queue metrics, autoscaling, priority queues |
| Büyük transkripsiyon veri yükü | DB ve AI token maliyeti artar | Yüksek | Orta | Chunking, retention, summarization, async processing |
| File upload güvenlik riski | Zararlı dosya veya yetkisiz erişim | Yüksek | Orta | Signed URL, type/size validation, malware scan future |
| Audit log büyümesi | DB boyutu ve sorgu maliyeti artar | Orta | Yüksek | Partition, archive, retention |
| Notification provider başarısızlığı | Hatırlatmalar gitmez | Orta | Orta | Retry, fallback, delivery log |
| Payment webhook hataları | Abonelik durumu bozulur | Yüksek | Orta | Signature verification, idempotency, DLQ |
| GDPR/KVKK silme süreçleri eksik | Uyum ve güven riski | Çok yüksek | Orta | Privacy service, deletion jobs, audit, legal review |
| Vendor lock-in | Provider değiştirme maliyeti artar | Orta | Orta | Adapter pattern, provider abstraction |

# 43. Backend Kabul Kriterleri

Backend MVP kabul kriterleri:

- Kullanıcı kayıt olabilir.
- Kullanıcı giriş yapabilir.
- JWT ve refresh token çalışır.
- Refresh token rotation çalışır.
- Kullanıcı kendi profilini görebilir.
- Tenant isolation uygulanır.
- Görüşme metni kaydedilebilir.
- Görüşme için AI analiz job oluşturulabilir.
- AI analiz sonucu kaydedilebilir.
- AI görev önerisi oluşturabilir.
- AI randevu önerisi oluşturabilir.
- Kullanıcı AI önerisini onaylayabilir veya reddedebilir.
- Onaylanan görev gerçek task kaydına dönüşür.
- Onaylanan randevu appointment kaydına dönüşür.
- Dashboard verisi döner.
- Bildirim planlanabilir.
- Audit log kritik işlemleri kaydeder.
- API error formatı standarttır.
- OpenAPI dokümantasyonu otomatik oluşur.
- Testler CI içinde çalışır.
- Sensitive data loglanmaz.
- Rıza kontrolü olmadan görüşme/mail/AI analizi yapılmaz.

# 44. Codex İçin Backend Kod Üretim Talimatları

İleride backend kod üretimine geçildiğinde şu talimatlar izlenmelidir:

1. Kod üretimine MVP backend ile başlanmalıdır.
2. İlk üretilecek modüller:
   - core.
   - db.
   - auth.
   - users.
   - organizations.
   - roles.
   - conversations.
   - calls.
   - ai.
   - tasks.
   - appointments.
   - notifications.
   - audit.
3. İlk aşamada email, billing, admin ve enterprise modülleri skeleton olarak kalabilir.
4. FastAPI app ayağa kalkmalıdır.
5. PostgreSQL bağlantısı kurulmalıdır.
6. Alembic migration altyapısı hazırlanmalıdır.
7. JWT auth çalışmalıdır.
8. Refresh token rotation çalışmalıdır.
9. Tenant context dependency yazılmalıdır.
10. Repository ve service pattern uygulanmalıdır.
11. Unit of Work transaction yönetimi için kullanılmalıdır.
12. OpenAPI dokümantasyonu düzgün oluşmalıdır.
13. Docker Compose ile local ortam çalışmalıdır.
14. Pytest ile temel testler hazırlanmalıdır.
15. AI provider gerçek çağrı yerine ilk aşamada mock adapter ile başlayabilir.
16. AI action approval modeli mutlaka uygulanmalıdır.
17. Kullanıcı onayı olmadan hiçbir AI aksiyonu uygulanmamalıdır.
18. Tüm kodlar type hint içermelidir.
19. Ruff ve MyPy standartlarına uygun yazılmalıdır.
20. Sensitive data loglanmamalıdır.
21. README içinde local çalıştırma adımları yazılmalıdır.
22. Tenant isolation testleri ilk günden eklenmelidir.
23. Audit log helper merkezi tasarlanmalıdır.
24. Error response formatı tüm endpointlerde aynı olmalıdır.
25. Background job payload’ları tenant_id ve correlation_id içermelidir.

# 45. Codex İçin Sonraki Ciltlere Hazırlık Notları

Cilt 5 hazırlanırken bu backend tasarımındaki AI modül sınırları, AI Orchestration Service, AI action approval, prompt versioning, provider adapter, response schema validation, semantic search ve AI cost logging detayları temel alınmalıdır.

Cilt 5 ayrıca backend ile AI engine arasındaki sözleşmeleri açıkça tanımlamalıdır:

- AI job input schema.
- AI result output schema.
- Prompt template/version seçimi.
- Function/tool calling sınırları.
- RAG context formatı.
- Embedding lifecycle.
- Feedback ve evaluation verisi.
- Cost ve usage logging.
- Safety guardrails.

# Codex İçin Sonraki Adım

Bir sonraki dokümanda Cilt 5 — AI Engine Documentation hazırlanacaktır. Cilt 5; AI pipeline, prompt engineering, prompt versioning, function calling, RAG, semantic search, embeddings, AI memory, AI action approval, AI güvenliği, AI evaluation, AI cost tracking, hallucination azaltma, kullanıcı feedback sistemi ve AI modüllerinin backend ile entegrasyon detaylarını içermelidir.
