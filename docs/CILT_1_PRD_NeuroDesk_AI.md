# CILT 1 — Product Requirements Document: NeuroDesk AI

Sürüm: 1.0  
Tarih: 08 Temmuz 2026  
Dil: Türkçe  
Doküman türü: Product Requirements Document, Cilt 1  
Hazırlık amacı: Ürün stratejisi, MVP kapsamı, fonksiyonel gereksinimler, kullanıcı hikayeleri, kabul kriterleri, iş modeli ve yol haritası

> Not: Bu doküman yazılım geliştirme, ürün yönetimi ve yatırımcı değerlendirmesi için hazırlanmış ürün gereksinimleri dokümanıdır. Hukuki danışmanlık niteliği taşımaz. KVKK, GDPR, telekomünikasyon, iş hukuku ve elektronik iletişim mevzuatı için uzman hukuk danışmanlığı alınmalıdır.

## İçindekiler

1. [Yönetici Özeti](#1-yönetici-özeti)
2. [Ürün Vizyonu](#2-ürün-vizyonu)
3. [Problem Tanımı](#3-problem-tanımı)
4. [Çözüm Tanımı](#4-çözüm-tanımı)
5. [Ürün Konumlandırması](#5-ürün-konumlandırması)
6. [Hedef Kullanıcılar](#6-hedef-kullanıcılar)
7. [Kullanıcı Personaları](#7-kullanıcı-personaları)
8. [Kullanım Senaryoları](#8-kullanım-senaryoları)
9. [Değer Önerisi](#9-değer-önerisi)
10. [Ana Özellikler](#10-ana-özellikler)
11. [MVP Kapsamı](#11-mvp-kapsamı)
12. [MVP Dışı Kapsam](#12-mvp-dışı-kapsam)
13. [Orta Vadeli Kapsam](#13-orta-vadeli-kapsam)
14. [Uzun Vadeli Kapsam](#14-uzun-vadeli-kapsam)
15. [Functional Requirements](#15-functional-requirements)
16. [Non-Functional Requirements](#16-non-functional-requirements)
17. [User Stories](#17-user-stories)
18. [Acceptance Criteria](#18-acceptance-criteria)
19. [İş Kuralları](#19-iş-kuralları)
20. [Ürün Modülleri](#20-ürün-modülleri)
21. [Kullanıcı Rolleri](#21-kullanıcı-rolleri)
22. [Yetkilendirme Mantığı](#22-yetkilendirme-mantığı)
23. [Veri Kaynakları](#23-veri-kaynakları)
24. [AI Kullanım Alanları](#24-ai-kullanım-alanları)
25. [Bildirim ve Hatırlatma Gereksinimleri](#25-bildirim-ve-hatırlatma-gereksinimleri)
26. [Takvim Gereksinimleri](#26-takvim-gereksinimleri)
27. [Mail Analizi Gereksinimleri](#27-mail-analizi-gereksinimleri)
28. [Telefon Görüşmesi Analizi Gereksinimleri](#28-telefon-görüşmesi-analizi-gereksinimleri)
29. [WhatsApp / Mesajlaşma Entegrasyonu Notları](#29-whatsapp--mesajlaşma-entegrasyonu-notları)
30. [CRM Benzeri Kişi Hafızası](#30-crm-benzeri-kişi-hafızası)
31. [AI Chat Gereksinimleri](#31-ai-chat-gereksinimleri)
32. [Dashboard Gereksinimleri](#32-dashboard-gereksinimleri)
33. [Arama ve Anlamsal Arama Gereksinimleri](#33-arama-ve-anlamsal-arama-gereksinimleri)
34. [Raporlama ve Analitik Gereksinimleri](#34-raporlama-ve-analitik-gereksinimleri)
35. [Güvenlik ve KVKK/GDPR Gereksinimleri](#35-güvenlik-ve-kvkkgdpr-gereksinimleri)
36. [Veri Saklama Politikası](#36-veri-saklama-politikası)
37. [Kullanıcı Onayı ve Rıza Yönetimi](#37-kullanıcı-onayı-ve-rıza-yönetimi)
38. [Hedef Pazar](#38-hedef-pazar)
39. [Rakip Analizi](#39-rakip-analizi)
40. [SWOT Analizi](#40-swot-analizi)
41. [İş Modeli](#41-iş-modeli)
42. [Gelir Modeli](#42-gelir-modeli)
43. [Paketleme ve Abonelik Planları](#43-paketleme-ve-abonelik-planları)
44. [Başarı Metrikleri](#44-başarı-metrikleri)
45. [Riskler ve Varsayımlar](#45-riskler-ve-varsayımlar)
46. [Ürün Yol Haritası](#46-ürün-yol-haritası)
47. [Sprint Bazlı Ürün Planı](#47-sprint-bazlı-ürün-planı)
48. [Ekibin İhtiyaç Duyacağı Roller](#48-ekibin-ihtiyaç-duyacağı-roller)
49. [Sonuç ve Stratejik Öneriler](#49-sonuç-ve-stratejik-öneriler)
50. [Codex İçin Sonraki Ciltlere Hazırlık Notları](#50-codex-için-sonraki-ciltlere-hazırlık-notları)
51. [Codex İçin Sonraki Adım](#codex-için-sonraki-adım)

# 1. Yönetici Özeti

NeuroDesk AI, bireylerin ve kurumların iş iletişimini anlayan, ilişkilendiren, hatırlatan ve aksiyona dönüştüren AI destekli kişisel/kurumsal çalışma asistanıdır. Ürün; telefon görüşmesi metinleri, e-postalar, takvim etkinlikleri, toplantı notları, belgeler, manuel notlar ve izinli mesajlaşma entegrasyonlarından gelen verileri analiz ederek kullanıcının iş hafızasını yapılandırır.

Ürünün ana amacı, dağınık iletişim verilerini pasif kayıt olmaktan çıkarıp iş sonuçlarına bağlamaktır. Kullanıcı bir müşteriyle konuştuğunda sistem görüşmeyi özetler, görevleri çıkarır, randevu önerir, kişi hafızasına işler ve gelecekte doğal dille sorgulanabilir hale getirir. Örneğin kullanıcı “Geçen ay fiyat isteyen ama dönüş yapmadığım müşterileri göster” dediğinde sistem telefon, mail, not, görev ve takvim verilerini birleştirerek kanıtlı, kaynaklı ve aksiyon önerili cevap sunmalıdır.

İlk ürün, kapsamı bilinçli olarak daraltılmış bir MVP olarak tasarlanmalıdır. MVP; kullanıcı yönetimi, görüşme metni yükleme/girme, AI özet, AI görev ve randevu çıkarımı, uygulama içi takvim, görev listesi, basit hatırlatma, dashboard, kişi kartı, Google Calendar entegrasyonu ve basit AI Chat özelliklerini içermelidir. Gmail entegrasyonu MVP içinde opsiyonel ikinci aşama olarak ele alınabilir.

Ürün pazarı; satış ekipleri, freelancerlar, emlak danışmanları, sigorta acenteleri, avukatlar, muhasebeciler, teknik destek ekipleri, çağrı merkezleri, KOBİ’ler ve kurumsal ekiplerdir. NeuroDesk AI’ın farklılaşma alanı yalnızca toplantı notu üretmesi değil; telefon, mail, takvim, görev ve kişi hafızasını tek bir aksiyon motorunda birleştirmesidir.

Stratejik ürün ilkesi: AI hiçbir zaman kullanıcı onayı olmadan mail göndermez, takvim etkinliği oluşturmaz, dış sistemlere veri yazmaz veya kullanıcı adına kesin aksiyon almaz. AI önerir, kullanıcı onaylar, sistem uygular. Bu yaklaşım güven, KVKK/GDPR uyumu, hatalı AI çıktılarının riskini azaltma ve kurumsal satış kabiliyeti için temel gereksinimdir.

# 2. Ürün Vizyonu

NeuroDesk AI’ın vizyonu, modern profesyoneller için “iletişim hafızası ve aksiyon zekası” katmanı olmaktır. Bugünün iş dünyasında kritik bilgiler telefon görüşmelerinde, e-posta zincirlerinde, takvim davetlerinde, toplantı notlarında, müşteri mesajlarında ve kişisel hatırlatmalarda parçalanmış durumdadır. NeuroDesk AI bu parçaları güvenli, izinli ve anlamlandırılmış bir yapıya dönüştürerek kullanıcının iş hafızasını güçlendirmeyi hedefler.

Vizyon cümlesi:

> NeuroDesk AI, her profesyonelin iş iletişimini anlayan, hatırlayan ve güvenli şekilde aksiyona dönüştüren kişisel AI çalışma asistanı olacaktır.

Ürün uzun vadede yalnızca not alan bir yardımcı değil, kullanıcının iş bağlamını bilen bir ikinci beyin olarak konumlanmalıdır. Kullanıcıya “ne oldu?”, “ne yapmalıyım?”, “kime döneceğim?”, “neyi unuttum?” ve “hangi müşteri riskte?” sorularında ölçülebilir destek vermelidir.

Vizyonun temel ilkeleri:

- Güven ve kullanıcı kontrolü, otomasyondan önce gelir.
- AI çıktıları kaynaklı, açıklanabilir ve düzeltilebilir olmalıdır.
- Ürün iş sonuçlarına bağlanmalıdır: görev tamamlanması, müşteri dönüşü, randevu yönetimi, satış takibi.
- Veri kaynakları izinli ve geri alınabilir bağlantılarla yönetilmelidir.
- KOBİ ve bireysel profesyoneller için basit, kurumsal ekipler için yönetilebilir olmalıdır.

# 3. Problem Tanımı

Profesyonellerin iş iletişimi çok kanallı ve dağınıktır. Bir müşteri telefonla bilgi ister, sonra e-posta atar, sonraki hafta toplantı yapılır, arada not alınır, görev başka bir uygulamaya yazılır ve takip sorumluluğu kişinin hafızasına kalır. Bu yapı ölçeklendikçe bilgi kaybı, geciken dönüşler ve kaçan fırsatlar ortaya çıkar.

Temel problemler:

- Telefon görüşmelerinde konuşulan aksiyonlar unutulur.
- E-postalardaki son tarihler ve yapılacak işler manuel takip edilir.
- Takvim, görev listesi ve müşteri geçmişi kopuktur.
- Kullanıcılar geçmiş iletişimde aradığını anahtar kelimeyle bile bulmakta zorlanır.
- Satış ekipleri fiyat isteyen, teklif bekleyen veya geri dönüş bekleyen müşterileri kaçırır.
- KOBİ’lerde CRM kullanımı ağır veya disiplin gerektirdiği için sürdürülemez.
- Toplantı notu araçları çoğunlukla toplantıya odaklanır; telefon, mail ve kişi hafızasını bütünleştirmez.
- AI araçları aksiyon önerse bile kullanıcı onayı, gizlilik, kaynak gösterme ve iş akışı entegrasyonu çoğu zaman yetersizdir.

Problem maliyetleri:

- Satış fırsatı kaybı.
- Müşteri memnuniyetsizliği.
- İş takip yükünün artması.
- Yönetici görünürlüğünün azalması.
- Çalışanların hatırlama, arama ve manuel kayıt için zaman harcaması.
- Hukuki veya operasyonel olarak kritik tarihlerde gecikme.

# 4. Çözüm Tanımı

NeuroDesk AI, kullanıcının izin verdiği veri kaynaklarından gelen iletişim içeriklerini analiz eder, yapılandırır ve aksiyona dönüştürür. Sistem, görüşme metni veya e-posta gibi serbest metinleri işlenebilir nesnelere çevirir: özet, görev, randevu, kişi/firma bağlantısı, konu etiketi, öncelik, risk ve takip durumu.

Çözüm bileşenleri:

- İletişim yakalama: görüşme metni, e-posta, takvim, not, belge ve resmi mesajlaşma entegrasyonları.
- AI analiz: özet, görev, randevu, son tarih, kişi/firma, konu, duygu/risk ve öncelik çıkarımı.
- İnsan onayı: AI tarafından önerilen aksiyonların kullanıcı tarafından onaylanması.
- Hafıza katmanı: kişi, firma, iletişim timeline’ı, görevler, notlar, belgeler ve geçmiş etkileşimler.
- Aksiyon katmanı: görev oluşturma, randevu kaydetme, hatırlatma planlama, takip listesi üretme.
- Sorgulama katmanı: AI Chat ve anlamsal arama ile geçmiş kayıtlara doğal dil üzerinden erişim.
- Yönetim katmanı: kullanıcı, rol, yetki, cihaz, oturum, veri kaynağı ve rıza yönetimi.

Çözümün temel davranışı:

1. Kullanıcı görüşme metni girer veya veri kaynağı bağlar.
2. Sistem veriyi işler ve AI analizi üretir.
3. AI çıktıları güven puanı ve kaynak referanslarıyla gösterilir.
4. Kullanıcı önerileri onaylar, düzenler veya reddeder.
5. Onaylanan görev/randevu/kişi güncellemeleri sisteme kaydedilir.
6. İlgili kişi/firma hafızası güncellenir.
7. Kullanıcı dashboard ve AI Chat üzerinden bu bilgilere erişir.

# 5. Ürün Konumlandırması

NeuroDesk AI; AI not alma, CRM, görev yönetimi, takvim ve iletişim arşivi kategorilerinin kesişiminde konumlanır. Ürün “arama kaydı uygulaması” veya “toplantı transkripsiyon aracı” olarak değil, “AI destekli iş iletişimi hafızası ve aksiyon asistanı” olarak pazarlanmalıdır.

Konumlandırma cümlesi:

> NeuroDesk AI, telefon, mail, takvim ve notlardan iş aksiyonlarını çıkaran; kişi bazlı hafıza oluşturan; kullanıcı onayıyla görev ve randevu yönetimini kolaylaştıran AI çalışma asistanıdır.

Farklılaşma alanları:

- Telefon görüşmesi, e-posta, takvim ve kişi hafızasını birlikte ele alma.
- Satış, müşteri takibi ve günlük iş planı odaklı aksiyon çıkarımı.
- Kullanıcı onaylı AI çalışma prensibi.
- KOBİ ve profesyonel hizmet sektörleri için CRM’den daha hafif, not alma aracından daha iş odaklı yapı.
- Doğal dilde geçmiş iletişim sorgulama.

Alternatif isim önerileri:

| İsim | Konumlandırma hissi | Not |
|---|---|---|
| NeuroDesk AI | Zeka + çalışma masası | Ana öneri |
| RecallDesk | Hatırlama ve masaüstü iş akışı | Global pazara uygun |
| MemoPilot | Hafıza + asistan | Daha kişisel ton |
| WorkMemory AI | İş hafızası | Açıklayıcı |
| ActionMind | Aksiyon odaklı AI | Satış odaklı |
| ClientBrain | Müşteri hafızası | CRM odaklı |
| FollowUp AI | Takip ve dönüş odaklı | Dar ama güçlü |

# 6. Hedef Kullanıcılar

| Hedef kitle | Problem | Kullanım şekli | Beklenen fayda | Örnek senaryo |
|---|---|---|---|---|
| Satış ekipleri | Fırsat ve takip kaçırma | Görüşme/mail analizi, görev ve takip listesi | Daha yüksek dönüş oranı | Temsilci, fiyat isteyen ama aranmayı bekleyen müşterileri listeler. |
| Freelance çalışanlar | Çok sayıda müşteri ve iş detayı | Kişi hafızası, görev, randevu, AI Chat | İşleri unutmaz, müşteri iletişimi düzenlenir | Freelancer, son konuşmada istenen revizyonları AI Chat ile bulur. |
| Emlak danışmanları | Portföy, alıcı, randevu ve takip karmaşası | Telefon görüşmesi analizi, randevu önerisi, müşteri kartı | Daha hızlı takip ve daha az kaçan randevu | Danışman, hafta sonu ev görmek isteyenleri listeler. |
| Sigorta acenteleri | Yenileme, belge ve müşteri takibi | Hatırlatma, kişi/firma hafızası, mail analizi | Poliçe yenileme kaçmaz | Sistem, yenileme konuşması geçen müşteriyi görev olarak önerir. |
| Avukatlar | Görüşme notu, son tarih ve müvekkil takibi | Özet, son tarih, güvenli kişi hafızası | Kritik tarihler takip edilir | Avukat, duruşma ve evrak teslim tarihlerini çıkarır. |
| Muhasebeciler | Evrak, beyanname ve müşteri dönüşleri | Mail analizi, son tarih, hatırlatma | Gecikme riski azalır | Sistem, belge göndermeyen müşterileri listeler. |
| Danışmanlık firmaları | Toplantı çıktıları ve müşteri aksiyonları | Toplantı/görüşme özeti, görev dağıtımı | Daha iyi proje takibi | Danışman, toplantıdan çıkan aksiyonları ekibe atar. |
| Teknik destek ekipleri | Müşteri taleplerinin dağılması | Görüşme özeti, risk, bekleyen iş | SLA ve memnuniyet artar | Uzman, açık kalan şikayetleri dashboard’da görür. |
| Çağrı merkezi ekipleri | Görüşme kalitesi ve takip | Transkript, konu, risk, raporlama | Kalite ve performans izlenir | Yönetici, riskli konuşmaları raporda inceler. |
| KOBİ’ler | CRM disiplininin düşük olması | Hafif CRM, görev, müşteri timeline | Satış ve operasyon görünürlüğü | İşletme sahibi, kimlere dönüş yapılacağını görür. |
| Kurumsal şirketler | Ekip veri yönetimi ve uyum | Rol bazlı yetki, audit, entegrasyon | Güvenli AI iş akışı | Yönetici yalnızca ekibinin müşteri hafızasını görür. |
| Ajanslar | Müşteri talepleri ve revizyon takibi | Mail/görüşme analizi, görev çıkarımı | Revizyonlar kaçmaz | Ajans, bekleyen müşteri onaylarını listeler. |
| Domain, hosting ve yazılım firmaları | Destek, yenileme ve teklif takibi | Ticket benzeri görev, mail, çağrı notu | Müşteri kaybı azalır | Sistem, yenileme isteyen ama teklif bekleyen müşterileri çıkarır. |

# 7. Kullanıcı Personaları

## 7.1 Persona 1 — Satış Temsilcisi

| Alan | Detay |
|---|---|
| İsim | Mert Kaya |
| Yaş | 29 |
| Meslek | B2B satış temsilcisi |
| Günlük problemi | Çok sayıda müşteriyle görüşür, kime ne teklif verdiğini ve kime döneceğini takip etmekte zorlanır. |
| Uygulamadan beklentisi | Görüşmelerden otomatik görev ve takip tarihi çıkarılması. |
| En çok kullanacağı özellikler | Telefon analizi, görev listesi, kişi hafızası, AI Chat, dashboard. |
| Başarı senaryosu | Mert, “Bu hafta fiyat teklifi bekleyen müşterilerim kimler?” diye sorar ve 12 kişilik kaynaklı liste alır. |

## 7.2 Persona 2 — Emlak Danışmanı

| Alan | Detay |
|---|---|
| İsim | Selin Acar |
| Yaş | 35 |
| Meslek | Emlak danışmanı |
| Günlük problemi | Alıcı, satıcı, portföy, lokasyon ve randevu bilgileri telefon görüşmelerinde dağılır. |
| Uygulamadan beklentisi | Görüşmelerden randevu, bütçe, lokasyon ve müşteri niyetinin çıkarılması. |
| En çok kullanacağı özellikler | Randevu önerisi, kişi kartı, takvim, hatırlatma, anlamsal arama. |
| Başarı senaryosu | Selin, “Cumartesi ev görmek isteyen alıcıları göster” der ve takvim önerileriyle liste alır. |

## 7.3 Persona 3 — Freelancer Yazılımcı

| Alan | Detay |
|---|---|
| İsim | Deniz Ural |
| Yaş | 32 |
| Meslek | Freelancer yazılımcı |
| Günlük problemi | Farklı müşterilerden gelen revizyon, toplantı ve teslim tarihlerini ayrı ayrı takip eder. |
| Uygulamadan beklentisi | Mail ve görüşmelerden görevlerin otomatik çıkarılması. |
| En çok kullanacağı özellikler | Mail analizi, görev yönetimi, AI Chat, kişi/firma hafızası. |
| Başarı senaryosu | Deniz, “Ayşe Hanım son toplantıda hangi revizyonları istemişti?” sorusuna kaynaklı cevap alır. |

## 7.4 Persona 4 — Küçük İşletme Sahibi

| Alan | Detay |
|---|---|
| İsim | Burak Demir |
| Yaş | 41 |
| Meslek | Küçük işletme sahibi |
| Günlük problemi | Satış, tedarik, müşteri ve operasyon işlerini tek başına yönetir. |
| Uygulamadan beklentisi | Günlük yapılacakları ve önemli müşteri dönüşlerini tek ekranda görmek. |
| En çok kullanacağı özellikler | Dashboard, görev, hatırlatma, kişi hafızası, AI Chat. |
| Başarı senaryosu | Burak sabah dashboard’da geciken işleri, bugünkü randevuları ve önemli mailleri görür. |

## 7.5 Persona 5 — Avukat

| Alan | Detay |
|---|---|
| İsim | Ece Arslan |
| Yaş | 38 |
| Meslek | Avukat |
| Günlük problemi | Müvekkil görüşmeleri, belge tarihleri ve duruşma hazırlıkları kritik son tarihler içerir. |
| Uygulamadan beklentisi | Görüşme notlarının güvenli özetlenmesi ve son tarihlerin çıkarılması. |
| En çok kullanacağı özellikler | Güvenli not, son tarih çıkarımı, randevu, kişi hafızası, veri maskeleme. |
| Başarı senaryosu | Ece, müvekkil görüşmesinden evrak teslim tarihi ve duruşma hazırlık görevlerini çıkarır. |

## 7.6 Persona 6 — Sigorta Danışmanı

| Alan | Detay |
|---|---|
| İsim | Hakan Yıldız |
| Yaş | 34 |
| Meslek | Sigorta danışmanı |
| Günlük problemi | Poliçe yenileme, teklif ve belge takibi manuel yapılır. |
| Uygulamadan beklentisi | Yenileme ve teklif takiplerinin otomatik hatırlatılması. |
| En çok kullanacağı özellikler | Görev, hatırlatma, kişi kartı, mail analizi, dashboard. |
| Başarı senaryosu | Hakan, “Bu ay yenileme konuştuğum ama poliçeyi tamamlamadığım müşteriler” listesini alır. |

## 7.7 Persona 7 — Teknik Destek Uzmanı

| Alan | Detay |
|---|---|
| İsim | Cem Öz |
| Yaş | 27 |
| Meslek | Teknik destek uzmanı |
| Günlük problemi | Telefonla alınan sorunlar ve takip sözleri kayıt dışında kalır. |
| Uygulamadan beklentisi | Görüşmelerden sorun, öncelik ve takip görevi çıkarılması. |
| En çok kullanacağı özellikler | Görüşme özeti, risk tespiti, görev, kişi/firma hafızası. |
| Başarı senaryosu | Cem, riskli müşterileri ve bekleyen teknik aksiyonları dashboard’da görür. |

## 7.8 Persona 8 — Kurumsal Ekip Yöneticisi

| Alan | Detay |
|---|---|
| İsim | Aylin Şahin |
| Yaş | 44 |
| Meslek | Satış operasyon yöneticisi |
| Günlük problemi | Ekip aktivitelerini, geciken takipleri ve müşteri risklerini merkezi göremez. |
| Uygulamadan beklentisi | Ekip bazlı görünürlük, yetki kontrolü, raporlama ve audit. |
| En çok kullanacağı özellikler | Raporlama, ekip dashboard’u, rol bazlı erişim, audit log, CRM görünümü. |
| Başarı senaryosu | Aylin, ekipte kimlerin kritik müşterilere dönüş yapmadığını haftalık raporda görür. |

# 8. Kullanım Senaryoları

## 8.1 Telefon Görüşmesinden Görev ve Randevu Çıkarma

Kullanıcı görüşme metnini sisteme yükler veya örnek görüşme metni girer. Sistem konuşmacıları ayırır, müşteri adını tespit eder, özet çıkarır, “Perşembe 14:00’te tekrar görüşelim” gibi ifadelerden randevu önerir ve “teklif gönder” gibi ifadelerden görev çıkarır. Kullanıcı önerileri düzenleyip onaylar.

## 8.2 Günlük İş Planı

Kullanıcı dashboard’a girdiğinde bugünkü toplantılar, geciken görevler, önemli mailler, yaklaşan randevular ve AI önerilerini görür. Sistem kullanıcının geçmiş iletişimine göre “Bugün dönmeniz gereken 5 müşteri var” gibi aksiyonlar önerir.

## 8.3 Mailden Son Tarih ve Görev Çıkarma

Kullanıcı Gmail veya Outlook hesabını bağlar. Sistem izin verilen e-postaları analiz eder, “Cuma’ya kadar iletir misiniz?” gibi ifadelerden son tarih çıkarır, önemli mailleri işaretler, bekleyen cevapları gösterir ve kullanıcı onayıyla görev oluşturur.

## 8.4 Kişi Hafızası

Kullanıcı bir kişi kartını açtığında son görüşmeler, son mailler, geçmiş randevular, açık görevler, konuşulan konular, notlar ve belgeler timeline içinde görünür. Sistem kişiyle ilgili geçmiş bilgileri AI Chat cevaplarında kaynak olarak kullanır.

## 8.5 AI Chat ile Geçmiş Sorgulama

Kullanıcı “Ahmet bana en son ne demişti?” diye sorar. Sistem Ahmet ile ilişkili görüşme, mail, not ve görevleri tarar; son önemli iletişimi özetler; kaynak kayıtları listeler; emin olmadığı noktaları açıkça belirtir.

## 8.6 Satış Takibi

Satış temsilcisi “Geçen ay fiyat isteyen ama dönüş yapmadığım müşterileri göster” diye sorar. Sistem fiyat, teklif, dönüş, bekleme, takip gibi semantik sinyalleri tarar; görev veya mail cevabı olmayan kişileri listeler; hızlı aksiyon önerir.

## 8.7 Kurumsal Ekip Takibi

Yönetici yalnızca yetkili olduğu ekip verilerini görür. Ekip dashboard’unda haftalık görüşme sayısı, çıkarılan görevler, tamamlanan görev oranı, geciken takipler ve müşteri riskleri gösterilir.

# 9. Değer Önerisi

NeuroDesk AI’ın temel değer önerisi, iletişimden aksiyona giden mesafeyi kısaltmasıdır. Ürün kullanıcının hafızasına bağımlı olan iş takip süreçlerini yapılandırır ve görünür hale getirir.

Kullanıcı için değer:

- Unutulan görevleri azaltır.
- Randevu ve son tarihleri görünür kılar.
- Geçmiş iletişimi hızlı buldurur.
- Müşteri bazlı hafıza sağlar.
- Günlük iş önceliklerini sadeleştirir.

Kurum için değer:

- Müşteri takip disiplinini artırır.
- Satış fırsatı kaybını azaltır.
- Ekip performansını ölçülebilir kılar.
- Bilgi kaybını azaltır.
- Kurumsal hafıza oluşturur.

Yatırımcı için değer:

- Büyük ve büyüyen AI productivity pazarına hitap eder.
- B2C, prosumer, SMB ve enterprise katmanlarında genişleme potansiyeli taşır.
- AI kullanım kotası, abonelik ve entegrasyon bazlı gelir modellerine uygundur.
- Veri kaynakları arttıkça ürünün bağlamsal değeri ve switching cost’u yükselir.

# 10. Ana Özellikler

## 10.1 Kullanıcı Yönetimi

- E-posta/şifre ile kayıt.
- Google, Microsoft ve Apple ile giriş.
- Şifre sıfırlama.
- Profil yönetimi.
- Cihaz ve oturum yönetimi.
- Veri kaynaklarını bağlama/kaldırma.
- Rıza ve izin geçmişi görüntüleme.

## 10.2 Telefon Görüşmesi Modülü

- Görüşme metni yükleme veya manuel giriş.
- İleriki fazlarda ses dosyasından metne dönüştürme.
- Konuşmacı ayrımı.
- Görüşme özeti.
- Kişi/firma tespiti.
- Tarih/saat ve randevu tespiti.
- Görev önerisi.
- Etiketleme ve arşivleme.
- Gizlilik ve açık rıza akışı.

## 10.3 AI Analiz Modülü

- Özet çıkarma.
- Görev ve randevu çıkarma.
- Son tarih tespiti.
- Kişi/firma tespiti.
- Konu sınıflandırma.
- Öncelik ve risk puanı.
- Bekleyen iş tespiti.
- AI confidence score.
- Kullanıcı onayı gerektiren aksiyonlar.

## 10.4 Randevu ve Takvim Modülü

- Google Calendar entegrasyonu.
- Outlook Calendar entegrasyonu.
- Manuel randevu.
- AI önerili randevu.
- Çakışma kontrolü.
- Boş zaman önerisi.
- Hatırlatma zamanları.
- Etkinlik güncelleme ve silme.

## 10.5 Görev Yönetimi

- Manuel görev oluşturma.
- AI önerili görev oluşturma.
- Öncelik ve son tarih.
- Hatırlatma.
- Tamamlandı durumu.
- Geciken görevler.
- Kişi/firma, görüşme ve mail bağlantısı.

## 10.6 Mail Analizi

- Gmail bağlantısı.
- Outlook bağlantısı.
- Mail okuma izni.
- Önemli mail tespiti.
- Son tarih, görev, randevu tespiti.
- Mail özeti.
- Bekleyen cevap tespiti.
- AI mail taslağı önerisi, yalnızca kullanıcı onayıyla.

## 10.7 WhatsApp / Mesajlaşma

- Yalnızca resmi API veya izinli entegrasyonlar.
- Kişisel WhatsApp sohbetlerine izinsiz erişim hedeflenmez.
- WhatsApp Business API ve benzeri resmi kanallar değerlendirilir.
- Mesajlardan görev, randevu ve not çıkarma.
- Kullanıcı onayı ve taraf bilgilendirmesi vurgulanır.

## 10.8 Kişi ve Müşteri Hafızası

- Kişi ve firma profili.
- Son görüşmeler, son mailler, bekleyen görevler.
- Geçmiş randevular.
- Konuşulan konular.
- Notlar ve belgeler.
- Timeline görünümü.

## 10.9 AI Chat

- Doğal dilde soru sorma.
- Geçmiş kayıtlar üzerinde arama.
- Kaynaklı ve özetli cevap.
- Kullanıcı izni dışında veri kullanmama.
- Belirsizlik ve düşük güven durumlarını belirtme.

## 10.10 Dashboard

- Günlük özet.
- Bugünkü toplantılar.
- Bekleyen ve geciken görevler.
- Önemli mailler.
- Yaklaşan randevular.
- AI önerileri.
- Haftalık performans.
- Hızlı aksiyonlar.

## 10.11 Bildirim Sistemi

- Push notification.
- E-posta bildirimi.
- SMS bildirimi.
- Resmi API mümkünse WhatsApp bildirimi.
- 1 gün önce, 1 saat önce, 15 dakika önce hatırlatma.
- Özel zamanlı hatırlatmalar.

## 10.12 Analitik ve Raporlama

- Haftalık görüşme sayısı.
- Mail sayısı.
- Oluşturulan/tamamlanan/geciken görevler.
- Randevu sayısı.
- Müşteri dönüş takibi.
- Satış ekipleri için performans raporları.

# 11. MVP Kapsamı

## 11.1 MVP Hedefi

MVP’nin amacı, NeuroDesk AI’ın temel değer hipotezini doğrulamaktır: Kullanıcı serbest iletişim metninden güvenilir şekilde özet, görev, randevu ve kişi hafızası elde ederse ürünü düzenli kullanır mı?

MVP, gerçek telefon kayıt entegrasyonlarını ve tam otomatik mesajlaşma erişimini hedeflememelidir. İlk sürümde kullanıcı görüşme metni yükleyerek veya örnek metin girerek AI değerini deneyimlemelidir.

## 11.2 Olmazsa Olmaz

- Kullanıcı kaydı ve girişi.
- Profil yönetimi.
- Görüşme metni manuel giriş/yükleme.
- AI görüşme özeti.
- AI görev çıkarma.
- AI randevu çıkarma.
- Kullanıcı onayıyla görev kaydetme.
- Kullanıcı onayıyla uygulama içi randevu kaydetme.
- Basit takvim görünümü.
- Görev listesi.
- Temel hatırlatma.
- Dashboard.
- Kişi kartı.
- Basit AI Chat.
- Google Calendar entegrasyonu.
- Web panel.
- Mobil uygulama temel ekranları.
- Açık rıza ve veri silme akışları.

## 11.3 Olsa İyi Olur

- Gmail bağlantısı.
- Mail özeti.
- Bekleyen cevap tespiti.
- AI mail taslağı önerisi.
- Outlook Calendar entegrasyonu.
- Gelişmiş konuşmacı ayrımı.
- Kişi/firma otomatik eşleştirme.
- Temel anlamsal arama.
- Mobil push bildirimleri.

## 11.4 Sonraki Faza Bırakılacak

- Otomatik telefon görüşmesi kaydı.
- Tam ses transkripsiyon altyapısı.
- WhatsApp Business entegrasyonu.
- Kurumsal ekip rolleri ve gelişmiş yetkiler.
- Enterprise SSO.
- Gelişmiş CRM pipeline.
- API marketplace.
- Gelişmiş analitik.
- Çoklu şirket yapısı.

## 11.5 MVP Başarı Kriterleri

- İlk analiz tamamlama oranı: yüzde 70+.
- AI görev önerisi kabul oranı: yüzde 35+.
- AI randevu önerisi kabul oranı: yüzde 25+.
- Haftalık aktif kullanıcı / kayıtlı kullanıcı oranı: yüzde 30+.
- Ortalama AI analiz süresi: 15 saniye altı.
- Kullanıcıların yüzde 50’sinin ilk hafta en az 3 analiz yapması.
- Kullanıcı memnuniyeti: 5 üzerinden 4+.

# 12. MVP Dışı Kapsam

İlk sürümde aşağıdaki özellikler kapsam dışıdır:

- Tam otomatik kişisel WhatsApp okuma.
- Kişisel WhatsApp sohbetlerine izinsiz erişim.
- Gelişmiş CRM pipeline yönetimi.
- ERP entegrasyonu.
- Fatura oluşturma.
- Teklif yönetimi.
- Çoklu şirket yapısı.
- Enterprise SSO.
- SAP entegrasyonu.
- Gelişmiş analitik.
- AI’ın kullanıcı onayı olmadan mail göndermesi.
- AI’ın kullanıcı onayı olmadan takvim etkinliği oluşturması.
- AI’ın kullanıcı onayı olmadan dış sistemlere veri yazması.
- Tam otomatik telefon kayıt entegrasyonları.
- Çağrı merkezi seviyesinde gerçek zamanlı dinleme.
- Model fine-tuning yönetim paneli.

# 13. Orta Vadeli Kapsam

3-12 aylık dönemde hedeflenen ürün genişletmeleri:

- Gmail entegrasyonunun kararlı hale getirilmesi.
- Outlook mail entegrasyonu.
- AI Chat’in kaynaklı cevap ve filtreleme kabiliyetlerinin güçlendirilmesi.
- Kişi ve firma hafızasının timeline, etiket ve ilişki haritasıyla zenginleştirilmesi.
- Mobil uygulama deneyiminin iyileştirilmesi.
- Team planı için ekip görevleri ve paylaşımlı müşteri hafızası.
- CRM benzeri liste ve pipeline görünümü.
- Gelişmiş raporlama.
- WhatsApp Business gibi resmi mesajlaşma entegrasyonlarının değerlendirilmesi.
- Semantic search ve AI Memory katmanının genişletilmesi.
- Admin paneli, rol bazlı erişim ve audit log.

# 14. Uzun Vadeli Kapsam

12 ay ve sonrası için hedeflenen stratejik kapsam:

- Enterprise müşteri yönetimi.
- API Marketplace.
- ERP/CRM entegrasyonları.
- Salesforce, HubSpot, Zoho, Pipedrive entegrasyonları.
- Çoklu dil ve global pazar uyumu.
- Bölgesel veri saklama seçenekleri.
- Kurumsal veri yönetişimi ve DLP entegrasyonları.
- Sektörel dikey paketler: hukuk, emlak, sigorta, danışmanlık, teknik destek.
- Gelişmiş AI ajanları, ancak kullanıcı onayı ve audit ile.
- Gelişmiş çağrı merkezi konuşma zekası.
- On-premise veya private cloud enterprise opsiyonu.

# 15. Functional Requirements

| ID | Başlık | Açıklama | Kullanıcı rolü | Öncelik | Kabul kriteri | Bağımlılıklar |
|---|---|---|---|---|---|---|
| FR-001 | Kullanıcı kayıt olabilmelidir | Kullanıcı e-posta ve şifre ile hesap oluşturur | Tüm kullanıcılar | Must | Geçerli e-posta ve güçlü şifre ile hesap oluşturulur | Authentication |
| FR-002 | Kullanıcı giriş yapabilmelidir | Kullanıcı e-posta/şifre ile oturum açar | Tüm kullanıcılar | Must | Doğru bilgilerle erişim verilir | Authentication |
| FR-003 | Şifre sıfırlama yapılabilmelidir | Kullanıcı e-posta ile sıfırlama bağlantısı alır | Tüm kullanıcılar | Must | Bağlantı süreli token ile çalışır | E-posta servisi |
| FR-004 | Google ile giriş desteklenmelidir | Kullanıcı Google OAuth ile giriş yapar | Tüm kullanıcılar | Should | OAuth başarılıysa oturum açılır | Google OAuth |
| FR-005 | Microsoft ile giriş desteklenmelidir | Kullanıcı Microsoft OAuth ile giriş yapar | Tüm kullanıcılar | Should | OAuth başarılıysa oturum açılır | Microsoft OAuth |
| FR-006 | Apple ile giriş desteklenmelidir | Kullanıcı Apple ID ile giriş yapar | Mobil kullanıcı | Could | Apple doğrulaması sonrası hesap bağlanır | Apple OAuth |
| FR-007 | Profil düzenlenebilmelidir | Ad, soyad, unvan, firma, saat dilimi güncellenir | Tüm kullanıcılar | Must | Değişiklikler kaydedilir ve gösterilir | Kullanıcı profili |
| FR-008 | Cihaz listesi görüntülenebilmelidir | Kullanıcı aktif cihazlarını görür | Tüm kullanıcılar | Should | Aktif oturumlar listelenir | Oturum yönetimi |
| FR-009 | Oturum sonlandırılabilmelidir | Kullanıcı seçili cihazdaki oturumu kapatır | Tüm kullanıcılar | Should | Seçili token geçersiz kılınır | Oturum yönetimi |
| FR-010 | Veri kaynakları yönetilebilmelidir | Kullanıcı bağlı hesapları görür ve kaldırır | Tüm kullanıcılar | Must | Bağlantı kaldırıldığında yeni veri çekilmez | Entegrasyon |
| FR-011 | Rıza metinleri gösterilmelidir | Veri işleme öncesi açık rıza alınır | Tüm kullanıcılar | Must | Rıza verilmeden analiz başlatılmaz | Rıza yönetimi |
| FR-012 | Rıza geçmişi tutulmalıdır | Kullanıcı hangi tarihte neye izin verdiğini görür | Tüm kullanıcılar | Must | Rıza kaydı audit olarak saklanır | Audit |
| FR-013 | Görüşme metni manuel girilebilmelidir | Kullanıcı metin alanına görüşme içeriği girer | Tüm kullanıcılar | Must | Metin kaydedilip analize gönderilir | Görüşme modülü |
| FR-014 | Görüşme metni dosya olarak yüklenebilmelidir | Kullanıcı txt/doc benzeri destekli format yükler | Tüm kullanıcılar | Should | Desteklenen dosya parse edilir | Dosya servisi |
| FR-015 | Görüşme kaydı oluşturulmalıdır | Her analiz için kaynak kayıt oluşur | Tüm kullanıcılar | Must | Kayıt tarih, sahip ve kaynakla görünür | Veri modeli |
| FR-016 | Görüşme özeti oluşturulmalıdır | AI kısa ve detaylı özet üretir | Tüm kullanıcılar | Must | Özet kaynak metinle ilişkili gösterilir | AI analiz |
| FR-017 | Konuşmacı ayrımı yapılmalıdır | Sistem konuşmacı rollerini ayırmaya çalışır | Tüm kullanıcılar | Should | Ayrım güven puanıyla gösterilir | AI analiz |
| FR-018 | Kişi tespiti yapılmalıdır | Görüşmeden kişi adı veya mevcut kişi eşleşmesi çıkarılır | Tüm kullanıcılar | Must | Eşleşme önerisi kullanıcıya gösterilir | Kişi modülü |
| FR-019 | Firma tespiti yapılmalıdır | Görüşmeden firma adı çıkarılır | Tüm kullanıcılar | Should | Firma önerisi kişi kartına bağlanabilir | Firma modülü |
| FR-020 | Tarih/saat tespiti yapılmalıdır | Metindeki zaman ifadeleri normalize edilir | Tüm kullanıcılar | Must | Tarih belirsizse kullanıcıdan netleştirme istenir | AI analiz |
| FR-021 | Randevu önerisi üretilmelidir | AI olası toplantı/arama etkinliği önerir | Tüm kullanıcılar | Must | Öneri kaydedilmeden önce onay bekler | AI + takvim |
| FR-022 | Görev önerisi üretilmelidir | AI yapılacak işleri çıkarır | Tüm kullanıcılar | Must | Görevler düzenlenebilir öneri olarak gösterilir | AI + görev |
| FR-023 | Son tarih önerisi üretilmelidir | Görevler için deadline çıkarılır | Tüm kullanıcılar | Must | Son tarih güven puanıyla gösterilir | AI analiz |
| FR-024 | Öncelik puanı üretilmelidir | AI görev ve iletişim için öncelik tahmin eder | Tüm kullanıcılar | Should | Puan kullanıcı tarafından değiştirilebilir | AI analiz |
| FR-025 | Risk tespiti yapılmalıdır | Memnuniyetsizlik, gecikme veya churn sinyali çıkarılır | Takım kullanıcıları | Should | Risk gerekçesiyle gösterilir | AI analiz |
| FR-026 | AI confidence score gösterilmelidir | Her öneride güven seviyesi bulunur | Tüm kullanıcılar | Must | Düşük güvenli öneriler açıkça işaretlenir | AI analiz |
| FR-027 | Kullanıcı öneriyi onaylayabilmelidir | Öneri onaylanınca ilgili kayıt oluşur | Tüm kullanıcılar | Must | Onay sonrası görev/randevu kaydedilir | Aksiyon servisi |
| FR-028 | Kullanıcı öneriyi düzenleyebilmelidir | Görev/randevu alanları düzenlenir | Tüm kullanıcılar | Must | Düzenlenen değerler kaydedilir | Formlar |
| FR-029 | Kullanıcı öneriyi reddedebilmelidir | Reddedilen öneri kaydedilmez | Tüm kullanıcılar | Must | Reddetme nedeni opsiyonel alınır | AI feedback |
| FR-030 | Görüşmeler etiketlenebilmelidir | Kullanıcı veya AI etiket atar | Tüm kullanıcılar | Should | Etiketle filtreleme yapılır | Etiket servisi |
| FR-031 | Görüşmeler arşivlenebilmelidir | Kullanıcı kayıtları aktif listeden kaldırır | Tüm kullanıcılar | Should | Arşivden geri alınabilir | Arşiv |
| FR-032 | Görev manuel oluşturulabilmelidir | Kullanıcı başlık, açıklama, tarih girer | Tüm kullanıcılar | Must | Görev listeye eklenir | Görev modülü |
| FR-033 | Görev kişi/firma ile ilişkilendirilebilmelidir | Göreve kişi veya firma bağlanır | Tüm kullanıcılar | Must | Kişi kartında görev görünür | Kişi modülü |
| FR-034 | Görev kaynak kayda bağlanmalıdır | AI görevi görüşme/mail ile ilişkilendirir | Tüm kullanıcılar | Must | Görev detayında kaynak görünür | Veri modeli |
| FR-035 | Görev önceliği atanabilmelidir | Düşük, orta, yüksek, kritik öncelik seçilir | Tüm kullanıcılar | Must | Liste önceliğe göre filtrelenir | Görev modülü |
| FR-036 | Görev tamamlandı yapılabilmelidir | Kullanıcı görevi kapatır | Tüm kullanıcılar | Must | Tamamlanma zamanı kaydedilir | Görev modülü |
| FR-037 | Geciken görevler gösterilmelidir | Son tarihi geçmiş açık görevler listelenir | Tüm kullanıcılar | Must | Dashboard’da ayrı görünür | Görev + dashboard |
| FR-038 | Göreve hatırlatma eklenebilmelidir | Kullanıcı özel veya varsayılan zaman seçer | Tüm kullanıcılar | Must | Hatırlatma planlanır | Bildirim |
| FR-039 | Randevu manuel oluşturulabilmelidir | Kullanıcı takvim etkinliği ekler | Tüm kullanıcılar | Must | Etkinlik takvimde görünür | Takvim |
| FR-040 | AI randevusu onayla kaydedilmelidir | Öneri onaylanınca etkinlik oluşur | Tüm kullanıcılar | Must | Onaysız etkinlik oluşmaz | AI + takvim |
| FR-041 | Google Calendar bağlanabilmelidir | Kullanıcı OAuth ile takvim erişimi verir | Tüm kullanıcılar | Must | Bağlantı sonrası etkinlikler okunur | Google Calendar |
| FR-042 | Google Calendar’a etkinlik yazılabilmelidir | Kullanıcı onayıyla harici takvime yazılır | Tüm kullanıcılar | Must | Etkinlik Google Calendar’da oluşur | Google Calendar |
| FR-043 | Outlook Calendar bağlanabilmelidir | Microsoft takvim erişimi sağlanır | Tüm kullanıcılar | Should | Etkinlikler okunur/yazılır | Microsoft Graph |
| FR-044 | Takvim çakışması kontrol edilmelidir | Yeni randevu mevcut etkinliklerle karşılaştırılır | Tüm kullanıcılar | Must | Çakışma varsa uyarı gösterilir | Takvim |
| FR-045 | Boş zaman önerisi yapılmalıdır | Sistem uygun zaman aralıkları önerir | Tüm kullanıcılar | Should | Öneriler kullanıcı saat dilimine göre üretilir | Takvim |
| FR-046 | Etkinlik güncellenebilmelidir | Kullanıcı tarih/saat/başlık değiştirir | Tüm kullanıcılar | Must | Güncelleme yerel ve bağlı takvime yansır | Takvim |
| FR-047 | Etkinlik silinebilmelidir | Kullanıcı etkinliği kaldırır | Tüm kullanıcılar | Must | Silme için doğrulama alınır | Takvim |
| FR-048 | Hatırlatma gönderilmelidir | Sistem planlanan zamanda bildirim yollar | Tüm kullanıcılar | Must | Bildirim teslim durumu kaydedilir | Bildirim |
| FR-049 | Push notification desteklenmelidir | Mobil/web push ile hatırlatma yapılır | Tüm kullanıcılar | Should | İzinli cihazlara gönderilir | Push servis |
| FR-050 | E-posta bildirimi desteklenmelidir | Hatırlatma maili gönderilir | Tüm kullanıcılar | Must | Kullanıcı tercihi varsa mail gider | E-posta |
| FR-051 | SMS bildirimi desteklenmelidir | Kritik hatırlatma için SMS gönderilir | Ücretli kullanıcı | Could | Telefon doğrulaması gerekir | SMS sağlayıcı |
| FR-052 | Gmail bağlantısı yapılabilmelidir | Kullanıcı Gmail okuma izni verir | Tüm kullanıcılar | Should | OAuth sonrası mail meta verisi çekilir | Gmail API |
| FR-053 | Outlook mail bağlantısı yapılabilmelidir | Microsoft mail okuma izni verilir | Tüm kullanıcılar | Should | İzinli mailler okunur | Microsoft Graph |
| FR-054 | Mail özeti oluşturulmalıdır | AI seçili maili özetler | Tüm kullanıcılar | Should | Özet kaynak maille gösterilir | Mail + AI |
| FR-055 | Mailden görev çıkarılmalıdır | AI yapılacak işi önerir | Tüm kullanıcılar | Should | Onayla görev oluşur | Mail + görev |
| FR-056 | Mailden randevu çıkarılmalıdır | AI toplantı önerisini yakalar | Tüm kullanıcılar | Should | Onayla etkinlik oluşur | Mail + takvim |
| FR-057 | Bekleyen cevap tespit edilmelidir | Cevap gerektiren mail işaretlenir | Tüm kullanıcılar | Could | Kullanıcı bekliyor/cevaplandı durumu görebilir | Mail analiz |
| FR-058 | AI mail taslağı önerilmelidir | Sistem cevap taslağı üretir | Tüm kullanıcılar | Could | Taslak kullanıcı onayı olmadan gönderilmez | Mail |
| FR-059 | Kişi kartı oluşturulabilmelidir | Kullanıcı kişi ekler veya AI önerisini onaylar | Tüm kullanıcılar | Must | Kişi listede görünür | Kişi modülü |
| FR-060 | Firma kartı oluşturulabilmelidir | Kullanıcı firma kaydı açar | Tüm kullanıcılar | Should | Firma kişi ve görevlerle ilişkilidir | Firma modülü |
| FR-061 | Kişi timeline’ı gösterilmelidir | Görüşme, mail, not, görev ve randevular sıralanır | Tüm kullanıcılar | Must | Zaman çizelgesi filtrelenebilir | Kişi hafızası |
| FR-062 | Kişiye not eklenebilmelidir | Kullanıcı manuel not girer | Tüm kullanıcılar | Must | Not kişi kartında görünür | Not modülü |
| FR-063 | Belge ilişkilendirilebilmelidir | Dosya veya link kişi/firma kaydına bağlanır | Tüm kullanıcılar | Could | Belge izinli kullanıcıya görünür | Dosya servisi |
| FR-064 | AI Chat soru cevap desteklemelidir | Kullanıcı doğal dilde sorgu yapar | Tüm kullanıcılar | Must | Cevap kaynaklarla döner | AI Chat |
| FR-065 | AI Chat kaynak göstermelidir | Cevap ilgili kayıtlarla ilişkilidir | Tüm kullanıcılar | Must | Kaynak linki veya kayıt referansı görünür | Arama |
| FR-066 | AI Chat yetki sınırlarına uymalıdır | Kullanıcı izinsiz veriyi sorgulayamaz | Tüm kullanıcılar | Must | Yetkisiz veri cevapta kullanılmaz | Yetkilendirme |
| FR-067 | AI Chat belirsizliği belirtmelidir | Düşük güven durumunda kesin konuşmaz | Tüm kullanıcılar | Must | Cevapta güven notu görünür | AI |
| FR-068 | Anahtar kelime arama yapılmalıdır | Kullanıcı kayıtlar içinde metin arar | Tüm kullanıcılar | Must | Sonuçlar filtrelenebilir | Arama |
| FR-069 | Anlamsal arama yapılmalıdır | Kullanıcı anlam bazlı sorgu yapar | Tüm kullanıcılar | Should | Benzer kayıtlar listelenir | Vector search |
| FR-070 | Dashboard günlük özet göstermelidir | Kullanıcı günün işlerini görür | Tüm kullanıcılar | Must | Toplantı, görev, mail, öneri görünür | Dashboard |
| FR-071 | Haftalık performans gösterilmelidir | Kullanıcı aktivite metriklerini görür | Tüm kullanıcılar | Should | Haftalık grafikler görünür | Analitik |
| FR-072 | Ekip raporu oluşturulmalıdır | Yönetici ekip aktivitelerini görür | Yönetici | Could | Rol yetkisiyle erişilir | Team plan |
| FR-073 | Kullanıcı rolü atanabilmelidir | Admin kullanıcıya rol verir | Admin | Should | Rol yetkileri uygulanır | RBAC |
| FR-074 | Ekip oluşturulabilmelidir | Yönetici ekip tanımlar | Yönetici | Should | Üyeler ekibe bağlanır | Organizasyon |
| FR-075 | Yetkili ekip verisi görüntülenmelidir | Yönetici yalnızca kendi ekibini görür | Yönetici | Must | Başka ekip verisi görünmez | RBAC |
| FR-076 | Audit log tutulmalıdır | Kritik aksiyonlar kayıt altına alınır | Admin | Must | Kim, ne, ne zaman bilgisi tutulur | Audit |
| FR-077 | Kullanıcı tüm verilerini indirebilmelidir | Veri taşıma hakkı desteklenir | Tüm kullanıcılar | Must | Export dosyası hazırlanır | Veri yönetimi |
| FR-078 | Kullanıcı tüm verilerini silebilmelidir | Hesap ve kişisel veriler silinir/anomize edilir | Tüm kullanıcılar | Must | Silme talebi işlenir ve raporlanır | Veri yönetimi |
| FR-079 | Hassas veri maskeleme seçilebilmelidir | AI’a gönderilecek alanlar maskelenebilir | Tüm kullanıcılar | Should | Maskelenen veri model isteğinde yer almaz | Privacy |
| FR-080 | AI geri bildirim toplanmalıdır | Kullanıcı çıktıyı doğru/yanlış işaretler | Tüm kullanıcılar | Should | Feedback analiz kalitesine raporlanır | AI kalite |
| FR-081 | Bildirim tercihleri yönetilmelidir | Kullanıcı kanal ve saat tercihlerini seçer | Tüm kullanıcılar | Must | Tercihler bildirim motoruna uygulanır | Bildirim |
| FR-082 | Dil tercihi seçilebilmelidir | Kullanıcı arayüz ve AI cevap dilini seçer | Tüm kullanıcılar | Could | Seçim profilinde saklanır | i18n |
| FR-083 | Veri kaynağı senkronizasyon durumu görünmelidir | Kullanıcı son senkronizasyonu görür | Tüm kullanıcılar | Should | Hata varsa uyarı gösterilir | Entegrasyon |
| FR-084 | Entegrasyon hata yönetimi yapılmalıdır | Token süresi dolduğunda yeniden bağlama istenir | Tüm kullanıcılar | Must | Hata kullanıcıya anlaşılır gösterilir | Entegrasyon |
| FR-085 | AI analiz geçmişi tutulmalıdır | Analiz çıktısının versiyonu saklanır | Tüm kullanıcılar | Should | Önceki analiz görülebilir | AI analiz |

# 16. Non-Functional Requirements

| ID | Başlık | Açıklama | Ölçüm kriteri | Öncelik |
|---|---|---|---|---|
| NFR-001 | Web performansı | Ana dashboard hızlı açılmalıdır | P95 yükleme 2.5 sn altı | Must |
| NFR-002 | API gecikmesi | Kritik API yanıtları hızlı olmalıdır | P95 500 ms altı, AI hariç | Must |
| NFR-003 | AI analiz süresi | Görüşme metni analizi makul sürede tamamlanmalıdır | P95 15 sn altı MVP | Must |
| NFR-004 | AI Chat süresi | Chat cevapları kullanıcıyı bekletmemelidir | P95 10 sn altı | Should |
| NFR-005 | Ölçeklenebilirlik | Sistem kullanıcı ve veri artışına göre yatay ölçeklenmelidir | 10x trafik artışında mimari değişmeden ölçek | Should |
| NFR-006 | Uptime | Servis yüksek erişilebilir olmalıdır | MVP yüzde 99.5, Enterprise yüzde 99.9+ | Must |
| NFR-007 | Veri şifreleme | Kişisel veriler şifreli saklanmalıdır | At-rest AES-256 veya eşdeğeri | Must |
| NFR-008 | Aktarım güvenliği | Tüm trafik güvenli olmalıdır | TLS 1.2+ zorunlu | Must |
| NFR-009 | Parola güvenliği | Parolalar düz metin saklanmamalıdır | Güçlü hash + salt | Must |
| NFR-010 | RBAC | Rol bazlı erişim uygulanmalıdır | Yetkisiz erişim testleri geçer | Must |
| NFR-011 | Audit logging | Kritik aksiyonlar izlenebilir olmalıdır | Audit kaydı yüzde 100 kritik aksiyon | Must |
| NFR-012 | KVKK uyumu | Açık rıza, silme ve aydınlatma süreçleri olmalıdır | Uyum kontrol listesi tamam | Must |
| NFR-013 | GDPR uyumu | Veri taşıma, silme ve işleme amaçları desteklenmelidir | DSR süreçleri tanımlı | Must |
| NFR-014 | Veri minimizasyonu | Gereksiz veri toplanmamalıdır | Her veri alanı için işleme amacı kayıtlı | Must |
| NFR-015 | Hassas veri maskeleme | AI isteği öncesi maskeleme opsiyonu olmalıdır | Seçili alanlar maskelenir | Should |
| NFR-016 | Rate limiting | API kötüye kullanımına karşı sınır uygulanmalıdır | Kullanıcı/IP bazlı limit | Must |
| NFR-017 | AI kota kontrolü | Plan bazlı AI kullanım sınırı olmalıdır | Kota aşımında işlem engellenir/uyarılır | Must |
| NFR-018 | Log gizliliği | Loglarda hassas veri tutulmamalıdır | PII log taraması başarır | Must |
| NFR-019 | Monitoring | Servis sağlığı izlenmelidir | Uyarılar 5 dk içinde tetiklenir | Must |
| NFR-020 | Backup | Veri yedeklenmelidir | Günlük yedek, periyodik geri yükleme testi | Must |
| NFR-021 | Disaster recovery | Kritik veri kaybı sınırlanmalıdır | RPO 24 saat, RTO 8 saat MVP | Should |
| NFR-022 | Mobil uyumluluk | Web panel mobilde kullanılabilir olmalıdır | 360px genişlikte temel akışlar çalışır | Must |
| NFR-023 | Erişilebilirlik | Temel erişilebilirlik sağlanmalıdır | WCAG 2.1 AA hedeflenir | Should |
| NFR-024 | Kullanılabilirlik | İlk analiz akışı kolay olmalıdır | Yeni kullanıcı 5 dk içinde ilk analiz yapar | Must |
| NFR-025 | Çoklu dil altyapısı | İleride dil eklenebilir olmalıdır | Metinler i18n yapısında | Could |
| NFR-026 | Saat dilimi desteği | Takvim ve hatırlatma doğru saat diliminde çalışmalıdır | Profil saat dilimi uygulanır | Must |
| NFR-027 | Veri tutarlılığı | Görev/randevu/kaynak bağlantıları bozulmamalıdır | Referans bütünlüğü korunur | Must |
| NFR-028 | Entegrasyon güvenliği | OAuth tokenları güvenli saklanmalıdır | Tokenlar şifreli ve erişim sınırlı | Must |
| NFR-029 | İzin geri alma | Bağlantı kaldırılınca veri çekimi durmalıdır | Sonraki sync yapılmaz | Must |
| NFR-030 | AI açıklanabilirlik | AI önerileri gerekçe ve kaynakla gösterilmelidir | Önerilerin yüzde 90+ kaynaklı | Must |
| NFR-031 | AI halüsinasyon kontrolü | Kaynaksız kesin bilgi verilmemelidir | Test setinde kaynaksız iddia oranı düşük | Must |
| NFR-032 | Hata mesajları | Hatalar anlaşılır olmalıdır | Kullanıcı dostu mesaj + teknik log | Should |
| NFR-033 | Tarayıcı uyumu | Modern tarayıcılar desteklenmelidir | Chrome, Safari, Edge son 2 majör sürüm | Must |
| NFR-034 | E-posta teslimatı | Sistem mailleri güvenilir gitmelidir | Bounce ve delivery takibi | Should |
| NFR-035 | Bildirim güvenilirliği | Hatırlatmalar zamanında gitmelidir | P95 planlanan zamandan 2 dk sapma | Should |
| NFR-036 | Veri izolasyonu | Tenant verileri karışmamalıdır | Tenant izolasyon testleri geçer | Must |
| NFR-037 | Admin güvenliği | Admin işlemleri ek doğrulama gerektirmelidir | Kritik aksiyonlarda yeniden doğrulama | Should |
| NFR-038 | Dosya güvenliği | Yüklenen dosyalar taranmalıdır | Malware taraması uygulanır | Should |
| NFR-039 | Gözlemlenebilirlik | AI maliyetleri ve gecikmeleri izlenmelidir | Model, token, maliyet metrikleri tutulur | Must |
| NFR-040 | SLA raporlama | Enterprise için SLA ölçülmelidir | Aylık uptime raporu | Could |
| NFR-041 | Veri silme süresi | Silme talepleri zamanında tamamlanmalıdır | 30 gün içinde silme/anomize | Must |
| NFR-042 | Audit saklama | Audit kayıtları politika süresince saklanmalıdır | Varsayılan 1 yıl, enterprise ayarlanabilir | Should |
| NFR-043 | Güvenlik testi | Kritik sürümler güvenlik testinden geçmelidir | SAST/DAST bulguları takip edilir | Should |
| NFR-044 | API versiyonlama | Entegrasyon API’leri kırılmadan gelişmelidir | Versioned endpoint politikası | Could |
| NFR-045 | Maliyet kontrolü | AI maliyetleri plan ve kota ile sınırlandırılmalıdır | Kullanıcı/tenant maliyet raporu | Must |

# 17. User Stories

| ID | Rol olarak | İstiyorum ki | Böylece | Kabul kriterleri |
|---|---|---|---|---|
| US-001 | Satış temsilcisi | Telefon görüşmemden otomatik görevler çıkarılsın | Görüşme sonrası yapmam gereken işleri unutmayayım | Metin analiz edilir; görev önerilir; onayla kaydedilir |
| US-002 | Satış temsilcisi | Görüşmeden randevu önerisi gelsin | Müşteriyle kararlaştırdığım zamanı kaçırmayayım | Tarih/saat çıkarılır; çakışma kontrol edilir; onayla kaydedilir |
| US-003 | Satış temsilcisi | Fiyat isteyen müşterileri listeleyeyim | Dönüş yapmam gereken fırsatları göreyim | Semantik arama yapılır; kaynaklı liste döner |
| US-004 | Satış temsilcisi | Müşteri kartında tüm geçmişi göreyim | Görüşmeye hazırlıklı gireyim | Görüşme, mail, görev ve randevular timeline’da görünür |
| US-005 | Satış temsilcisi | Geciken takipleri dashboard’da göreyim | Önceliği kaçırmayayım | Geciken görevler ayrı gösterilir |
| US-006 | Satış temsilcisi | AI önerisinin güven puanını göreyim | Öneriye ne kadar güveneceğimi bileyim | Güven skoru gösterilir |
| US-007 | Satış temsilcisi | AI görevini düzenleyebileyim | Yanlış veya eksik bilgiyi düzelteyim | Alanlar düzenlenir ve kaydedilir |
| US-008 | Satış temsilcisi | Mailden cevap bekleyen müşterileri göreyim | Geri dönüşleri hızlandırayım | Bekleyen cevap sinyalleri listelenir |
| US-009 | Satış temsilcisi | Bugünkü iş planımı göreyim | Günümü önceliklendireyim | Toplantı, görev, mail ve öneriler görünür |
| US-010 | Satış temsilcisi | AI Chat’e satış soruları sorayım | Rapor hazırlamadan bilgi alayım | Chat kaynaklı cevap verir |
| US-011 | Emlak danışmanı | Görüşmeden lokasyon ve bütçe notu çıksın | Alıcı talebini hızlı hatırlayayım | Kişi kartına not önerilir |
| US-012 | Emlak danışmanı | Ev gösterimi randevusu önerilsin | Takvimimi düzenli tutayım | Randevu önerisi onay bekler |
| US-013 | Emlak danışmanı | Hafta sonu randevularımı göreyim | Sahada plan yapayım | Takvim filtrelenir |
| US-014 | Emlak danışmanı | Alıcıların son konuşmalarını göreyim | İhtiyaçlarını karıştırmayayım | Kişi timeline’ı görünür |
| US-015 | Emlak danışmanı | Portföyle ilgilenenleri arayayım | Satış fırsatını kaçırmayayım | İlgili konuşmalar listelenir |
| US-016 | Emlak danışmanı | Hatırlatma alayım | Randevuya geç kalmayayım | Seçilen zamanda bildirim gider |
| US-017 | Emlak danışmanı | Kişi etiketleri kullanayım | Alıcı/satıcı ayrımı yapayım | Etiket filtreleri çalışır |
| US-018 | Emlak danışmanı | Ses yerine metinle başlayayım | MVP’yi hızlı kullanayım | Manuel metin analizi çalışır |
| US-019 | Emlak danışmanı | AI’ın belirsiz tarihleri sormasını isterim | Yanlış randevu oluşmasın | Belirsiz tarih için netleştirme istenir |
| US-020 | Emlak danışmanı | Mobilde görevlerimi göreyim | Sahada takip edeyim | Mobil temel ekran çalışır |
| US-021 | Freelancer yazılımcı | Mailden revizyon görevleri çıksın | Müşteri taleplerini kaçırmayayım | Mail analizinden görev önerilir |
| US-022 | Freelancer yazılımcı | Teslim tarihleri otomatik yakalansın | Proje takvimi doğru olsun | Son tarih görevde görünür |
| US-023 | Freelancer yazılımcı | Müşteri bazlı not tutayım | Bağlamı kaybetmeyeyim | Kişiye not eklenir |
| US-024 | Freelancer yazılımcı | AI Chat geçmişi arasın | Uzun yazışmalarda bilgi bulayım | Semantik arama cevap döndürür |
| US-025 | Freelancer yazılımcı | Google Calendar’a randevu ekleyeyim | Kullandığım takvim güncel kalsın | Onayla harici takvime yazılır |
| US-026 | Freelancer yazılımcı | AI mail taslağı görüp düzenleyeyim | Cevap yazma süresini azaltayım | Taslak gönderilmeden düzenlenir |
| US-027 | Freelancer yazılımcı | Müşteri belgelerini ilişkilendireyim | Dosyalar bağlamlı dursun | Belge linki kişi kartında görünür |
| US-028 | Freelancer yazılımcı | Görevleri önceliklendireyim | Önce kritik işleri yapayım | Öncelik sıralaması çalışır |
| US-029 | Freelancer yazılımcı | Haftalık tamamlanan görevleri göreyim | Verimliliğimi ölçeyim | Haftalık metrik görünür |
| US-030 | Freelancer yazılımcı | Veri kaynağını istediğimde kaldırayım | Kontrol bende olsun | Bağlantı kaldırılır |
| US-031 | Küçük işletme sahibi | Sabah günlük özet göreyim | İşleri tek ekrandan yöneteyim | Dashboard günlük özet verir |
| US-032 | Küçük işletme sahibi | Önemli mailler işaretlensin | Kritik konuları kaçırmayayım | AI önemli mail önerir |
| US-033 | Küçük işletme sahibi | Müşteriye bağlı görev açayım | Takibi kişi bazında yapayım | Görev kişiyle ilişkilidir |
| US-034 | Küçük işletme sahibi | Geciken işleri göreyim | Operasyonel riskleri azaltayım | Geciken görev listesi görünür |
| US-035 | Küçük işletme sahibi | SMS veya e-posta hatırlatma seçeyim | Kritik işleri kaçırmayayım | Tercihe göre kanal çalışır |
| US-036 | Küçük işletme sahibi | Verilerimi indireyim | Taşıma hakkımı kullanayım | Export oluşturulur |
| US-037 | Küçük işletme sahibi | Hesabımı ve verilerimi sileyim | Gizlilik kontrolü sağlayayım | Silme süreci başlatılır |
| US-038 | Küçük işletme sahibi | AI’ın mail göndermeden önce onay almasını isterim | Yanlış iletişim gitmesin | Onaysız gönderim yapılmaz |
| US-039 | Küçük işletme sahibi | Haftalık müşteri dönüş raporu alayım | Satış takibini ölçeyim | Rapor görünür |
| US-040 | Küçük işletme sahibi | Basit arama kullanayım | Kayıtları hızlı bulayım | Anahtar kelime arama çalışır |
| US-041 | Avukat | Görüşmeden hukuki son tarih çıksın | Kritik süreleri kaçırmayayım | Tarih önerisi güven puanıyla çıkar |
| US-042 | Avukat | Hassas veriyi maskeleyeyim | Müvekkil gizliliğini koruyayım | Maskeli AI isteği yapılır |
| US-043 | Avukat | Müvekkil timeline’ını göreyim | Dosya geçmişini hızlı hatırlayayım | Timeline filtrelenebilir |
| US-044 | Avukat | AI belirsiz bilgiyi kesin söylemesin | Yanlış yönlendirme olmasın | Belirsizlik notu gösterilir |
| US-045 | Avukat | Rıza kayıtlarını göreyim | Uyum denetiminde kanıt sunayım | Rıza geçmişi görünür |
| US-046 | Avukat | Belgeleri müvekkile bağlayayım | Evrak bağlamını kaybetmeyeyim | Belge referansı görünür |
| US-047 | Avukat | Takvim çakışması uyarısı alayım | Aynı saate randevu koymayayım | Çakışma uyarısı çıkar |
| US-048 | Avukat | AI çıktısını düzenleyeyim | Hukuki dili doğru hale getireyim | Düzenleme kaydedilir |
| US-049 | Avukat | Kaynaklı özet alayım | Hangi görüşmeye dayandığını bileyim | Kaynak kayıt görünür |
| US-050 | Avukat | Tüm işlem geçmişi loglansın | Güven ve denetlenebilirlik olsun | Audit log oluşur |
| US-051 | Sigorta danışmanı | Poliçe yenileme görüşmeleri yakalansın | Yenilemeyi kaçırmayayım | Yenileme sinyali görev olur |
| US-052 | Sigorta danışmanı | Eksik belge görevi oluşsun | Müşteriden belge isteyeyim | Belge ihtiyacı görev önerir |
| US-053 | Sigorta danışmanı | Müşteri bazlı teklif geçmişi göreyim | Doğru teklif takibi yapayım | Kişi kartı geçmiş gösterir |
| US-054 | Sigorta danışmanı | Yaklaşan yenilemeler hatırlatılsın | Gelir kaybını azaltayım | Hatırlatma planlanır |
| US-055 | Sigorta danışmanı | Mailden poliçe son tarihi çıksın | Takvimim güncel olsun | Son tarih çıkarılır |
| US-056 | Sigorta danışmanı | Riskli müşteriler listelensin | Öncelikli arama yapayım | Risk skoru görünür |
| US-057 | Sigorta danışmanı | AI Chat’e müşteri sorayım | Hızlı bilgi alayım | Kaynaklı cevap döner |
| US-058 | Sigorta danışmanı | Mobilde hatırlatma alayım | Sahada da takip edeyim | Push bildirimi gider |
| US-059 | Sigorta danışmanı | Görev tamamlandı işaretleyeyim | Takip listem temiz kalsın | Tamamlanma zamanı kaydedilir |
| US-060 | Sigorta danışmanı | Haftalık tamamlanan yenilemeleri göreyim | Performansımı izleyeyim | Rapor görünür |
| US-061 | Teknik destek uzmanı | Görüşmeden sorun özeti çıksın | Talebi doğru anlayayım | Özet ve konu etiketi çıkar |
| US-062 | Teknik destek uzmanı | Kritik şikayetler riskli işaretlensin | Öncelik vereyim | Risk puanı gösterilir |
| US-063 | Teknik destek uzmanı | Takip görevi oluşsun | Müşteriye dönüşü unutmayayım | Görev onayla kaydedilir |
| US-064 | Teknik destek uzmanı | Müşteri geçmiş sorunlarını göreyim | Tekrar eden problemi anlayayım | Kişi timeline’ı görünür |
| US-065 | Teknik destek uzmanı | Konu sınıflandırması yapılsın | Raporlama kolaylaşsın | Etiket önerilir |
| US-066 | Teknik destek uzmanı | Kaydı arşivleyeyim | Listeyi temiz tutayım | Arşivden geri alınabilir |
| US-067 | Teknik destek uzmanı | Açık görevleri filtreleyeyim | İş yükümü göreyim | Durum filtresi çalışır |
| US-068 | Teknik destek uzmanı | AI yanlışsa feedback vereyim | Sistem kalitesi izlensin | Feedback kaydedilir |
| US-069 | Teknik destek uzmanı | Müşteri dönüş SLA’sı takip edilsin | Gecikmeyi önleyeyim | Geciken takip görünür |
| US-070 | Teknik destek uzmanı | Mail ve görüşme aynı kişiye bağlansın | Bağlam birleşsin | Eşleştirme önerilir |
| US-071 | Kurumsal yönetici | Ekip üyelerini göreyim | Operasyonu yöneteyim | Yetkili ekip listelenir |
| US-072 | Kurumsal yönetici | Rol atayayım | Erişimleri kontrol edeyim | Rol yetkileri uygulanır |
| US-073 | Kurumsal yönetici | Sadece ekibimin verisini göreyim | Gizlilik korunsun | Başka ekip verisi engellenir |
| US-074 | Kurumsal yönetici | Haftalık ekip raporu alayım | Performansı ölçeyim | Metrikler görünür |
| US-075 | Kurumsal yönetici | Audit log göreyim | Denetim yapayım | Kritik işlemler listelenir |
| US-076 | Kurumsal yönetici | Kullanıcı davet edeyim | Ekibi büyüteyim | Davet maili gider |
| US-077 | Kurumsal yönetici | Entegrasyon izinlerini yöneteyim | Kurumsal kontrol sağlayayım | Politika uygulanır |
| US-078 | Kurumsal yönetici | AI kullanım maliyetini göreyim | Bütçeyi kontrol edeyim | Kullanım raporu görünür |
| US-079 | Kurumsal yönetici | Veri saklama süresi belirleyeyim | Uyum politikasını uygulayayım | Tenant politikası kaydedilir |
| US-080 | Kurumsal yönetici | Kritik müşterileri takip edeyim | Riskleri azaltayım | Risk listesi görünür |
| US-081 | Kullanıcı | Google hesabımı bağlayayım | Takvimimi senkron kullanayım | OAuth bağlantısı başarılı olur |
| US-082 | Kullanıcı | Takvim çakışması görürüm | Hatalı plan yapmam | Çakışma uyarısı çıkar |
| US-083 | Kullanıcı | Hatırlatma saatini değiştireyim | Kendi çalışma tarzıma uysun | Tercih kaydedilir |
| US-084 | Kullanıcı | AI önerisini reddedeyim | Yanlış kayıt oluşmasın | Öneri kaydedilmez |
| US-085 | Kullanıcı | Düşük güvenli önerileri ayırt edeyim | Kontrolü artırayım | Düşük güven işaretlenir |
| US-086 | Kullanıcı | Kayıtları etiketleyeyim | Sonra filtreleyeyim | Etiket atanır |
| US-087 | Kullanıcı | Kişi arayayım | Doğru profili hızlı açayım | Arama sonucu kişi döner |
| US-088 | Kullanıcı | Görevleri tarihe göre sıralayayım | Önceliklendireyim | Sıralama çalışır |
| US-089 | Kullanıcı | AI Chat kaynağa götürsün | Cevabı doğrulayayım | Kaynak linki çalışır |
| US-090 | Kullanıcı | Bildirim kanallarını kapatayım | Rahatsız edilmeyeyim | Tercih uygulanır |
| US-091 | Kullanıcı | Outlook hesabımı bağlayayım | Mail ve takvimimi kullanayım | Microsoft OAuth çalışır |
| US-092 | Kullanıcı | Mail okuma iznini kaldırayım | Veri akışını durdurayım | Yeni mail çekilmez |
| US-093 | Kullanıcı | Profil saat dilimi seçeyim | Hatırlatmalar doğru gelsin | Saat dilimi uygulanır |
| US-094 | Kullanıcı | Oturumu uzaktan kapatayım | Güvenliği artırayım | Seçili cihaz çıkış yapar |
| US-095 | Kullanıcı | Şifremi değiştireyim | Hesabımı koruyayım | Yeni şifreyle giriş yapılır |
| US-096 | Kullanıcı | Arşivlenmiş kayıtları göreyim | Eski bilgiye erişeyim | Arşiv listesi açılır |
| US-097 | Kullanıcı | AI analiz geçmişini göreyim | Önceki çıktıları karşılaştırayım | Analiz versiyonları görünür |
| US-098 | Kullanıcı | Mail taslağını göndermeden göreyim | Hatalı mail gitmesin | Gönderim kullanıcı aksiyonu ister |
| US-099 | Kullanıcı | Randevuyu silerken onay vereyim | Yanlış silme olmasın | Silme doğrulaması çıkar |
| US-100 | Kullanıcı | Uygulama içinde yardım alayım | Akışları hızlı öğreneyim | Yardım içeriği görünür |
| US-101 | Admin | Kullanıcı hesabını pasifleştireyim | Güvenlik riskini azaltayım | Pasif kullanıcı giriş yapamaz |
| US-102 | Admin | Plan ve kota tanımlayayım | Gelir modelini uygulayayım | Kota aşımı kontrol edilir |
| US-103 | Admin | Sistem sağlık durumunu göreyim | Operasyonel sorunları anlayayım | Monitoring metrikleri görünür |
| US-104 | Admin | Hatalı AI çıktılarını raporlayayım | Kalite iyileştirmesi yapılsın | Feedback raporu oluşur |
| US-105 | Admin | Veri silme taleplerini takip edeyim | Uyum sürecini yöneteyim | Talep durumu görünür |

# 18. Acceptance Criteria

## 18.1 Kullanıcı Kaydı

- Kullanıcı geçerli e-posta, güçlü şifre ve gerekli onay kutularıyla kayıt formunu gönderebilmelidir.
- Sistem e-posta formatını, şifre gücünü ve zorunlu alanları doğrulamalıdır.
- Aynı e-posta ile ikinci hesap oluşturulmasına izin verilmemelidir.
- Kayıt sonrası kullanıcı profili oluşturulmalı ve varsayılan bildirim/AI tercihleri atanmalıdır.
- Kullanıcıya doğrulama e-postası gönderilmelidir.
- Kayıt sırasında aydınlatma metni ve kullanım şartları erişilebilir olmalıdır.
- Kayıt, audit log’a kimlik ve zaman bilgisiyle yazılmalıdır.

## 18.2 Giriş

- Kullanıcı doğru e-posta ve şifreyle giriş yapabilmelidir.
- Hatalı giriş denemelerinde güvenli ve açıklayıcı hata mesajı gösterilmelidir.
- Belirli sayıda hatalı denemeden sonra rate limit veya geçici kilit uygulanmalıdır.
- Başarılı girişte oturum tokenı oluşturulmalıdır.
- Kullanıcı aktif oturumlarını profil ekranından görebilmelidir.
- Google/Microsoft/Apple girişleri OAuth doğrulaması sonrası aynı oturum mantığına bağlanmalıdır.

## 18.3 Telefon Görüşmesi Metni Analizi

- Kullanıcı görüşme metni girmeden analiz başlatamamalıdır.
- Sistem analiz öncesi açık rıza durumunu kontrol etmelidir.
- Metin minimum uzunluk, maksimum uzunluk ve desteklenen format açısından doğrulanmalıdır.
- Analiz sonucunda özet, görev önerileri, randevu önerileri, kişi/firma önerileri ve confidence score gösterilmelidir.
- Analiz başarısız olursa kullanıcıya yeniden deneme ve metni düzenleme seçeneği verilmelidir.
- Hiç görev veya randevu bulunamazsa sistem bunu açıkça belirtmelidir.

## 18.4 AI Özet Oluşturma

- Özet, kaynak metindeki bilgilere dayanmalıdır.
- Kısa özet ve detaylı özet ayrımı yapılmalıdır.
- Özet içinde belirsiz veya tahmini bilgiler işaretlenmelidir.
- Kullanıcı özeti düzenleyebilmelidir.
- Özet kişi/firma kartına bağlanabilmelidir.
- Özetin hangi görüşmeden üretildiği görünmelidir.

## 18.5 AI Görev Çıkarma

- Sistem yapılacak iş, sorumlu kişi, son tarih ve öncelik alanlarını mümkün olduğunda çıkarmalıdır.
- Her görev önerisi kullanıcı onayı beklemelidir.
- Kullanıcı görev başlığını, açıklamasını, son tarihini, önceliğini ve kişi bağlantısını düzenleyebilmelidir.
- Kullanıcı onaylamadıkça görev listesine kayıt eklenmemelidir.
- Düşük güvenli görevler ayrı işaretlenmelidir.
- Reddedilen görev önerileri AI kalite ölçümü için anonimleştirilmiş feedback olarak saklanabilmelidir.

## 18.6 AI Randevu Çıkarma

- Sistem tarih, saat, katılımcı, konu ve kaynak ifadeyi göstermelidir.
- Belirsiz tarih varsa kullanıcıdan netleştirme istenmelidir.
- Takvim çakışması kontrol edilmelidir.
- Kullanıcı onayı olmadan uygulama içi veya harici takvim etkinliği oluşturulmamalıdır.
- Onay sonrası randevu uygulama takviminde görünmelidir.
- Google Calendar bağlıysa kullanıcı seçimiyle harici takvime de yazılmalıdır.

## 18.7 Randevu Kaydetme

- Randevu başlık, tarih, saat, süre, kişi/firma, açıklama ve hatırlatma alanlarıyla kaydedilmelidir.
- Geçmiş tarihe randevu oluşturulurken kullanıcı uyarılmalıdır.
- Saat dilimi profil ayarına göre uygulanmalıdır.
- Randevu detayında kaynak görüşme veya mail referansı bulunmalıdır.
- Güncelleme ve silme işlemleri audit log’a yazılmalıdır.

## 18.8 Hatırlatma Gönderme

- Kullanıcı 1 gün önce, 1 saat önce, 15 dakika önce veya özel zaman seçebilmelidir.
- Bildirim kanalı kullanıcı tercihlerine göre belirlenmelidir.
- Hatırlatma zamanında gönderilemezse sistem tekrar denemeli veya hata kaydı oluşturmalıdır.
- Gönderim durumu kullanıcıya veya sistem loglarına yansıtılmalıdır.
- Kullanıcı bildirimleri kapatmışsa ilgili kanaldan gönderim yapılmamalıdır.

## 18.9 Mail Analizi

- Kullanıcı Gmail/Outlook izni vermeden mail verisi işlenmemelidir.
- Mail okuma izni kapsamı açıkça gösterilmelidir.
- Sistem seçili veya izinli mailleri analiz etmelidir.
- Mailden özet, görev, randevu, son tarih ve bekleyen cevap sinyali çıkarılmalıdır.
- AI mail taslağı oluşturulsa bile kullanıcı onayı olmadan gönderilmemelidir.
- Kullanıcı entegrasyonu kaldırdığında yeni mail çekimi durmalıdır.

## 18.10 Takvim Entegrasyonu

- Kullanıcı OAuth ile Google Calendar bağlantısı kurabilmelidir.
- İzin kapsamları kullanıcıya anlaşılır gösterilmelidir.
- Bağlantı sonrası mevcut etkinlikler okunabilmelidir.
- Kullanıcı onayıyla etkinlik harici takvime yazılmalıdır.
- Token süresi dolarsa yeniden bağlantı akışı başlatılmalıdır.
- Çakışma kontrolü hem yerel hem bağlı takvim verisini dikkate almalıdır.

## 18.11 AI Chat Arama

- Kullanıcı doğal dilde soru sorabilmelidir.
- Sistem yalnızca kullanıcının erişim yetkisi olan veriler üzerinde arama yapmalıdır.
- Cevap kaynak kayıtlarla birlikte verilmelidir.
- Kaynak bulunamazsa sistem uydurma cevap üretmemeli, sonuç bulunamadığını belirtmelidir.
- Cevap içinde güven seviyesi veya belirsizlik notu gösterilmelidir.
- Kullanıcı cevaptan ilgili kayda geçebilmelidir.

## 18.12 Dashboard Günlük Özet

- Dashboard bugünkü toplantıları, yaklaşan randevuları, bekleyen görevleri, geciken işleri ve önemli mailleri göstermelidir.
- AI önerileri ayrı bir bölümde yer almalıdır.
- Kullanıcı hızlı aksiyonlarla görev tamamlama, randevu açma ve kişi kartına gitme işlemlerini yapabilmelidir.
- Boş durumda kullanıcıyı ilk analiz veya veri bağlantısına yönlendiren sade boş ekran gösterilmelidir.
- Dashboard verileri yetki ve veri kaynağı izinlerine uymalıdır.

# 19. İş Kuralları

| ID | İş kuralı |
|---|---|
| BR-001 | AI hiçbir zaman kullanıcı onayı olmadan mail gönderemez. |
| BR-002 | AI hiçbir zaman kullanıcı onayı olmadan takvim etkinliği oluşturamaz. |
| BR-003 | AI öneri üretir; kullanıcı onay verirse işlem yapılır. |
| BR-004 | Telefon görüşmesi kayıt/metin işleme için kullanıcı açık rızası gerekir. |
| BR-005 | Diğer tarafların bilgilendirilmesi gereken durumlar ürün akışında açıkça gösterilmelidir. |
| BR-006 | Kullanıcı veri kaynaklarını istediği zaman bağlayıp kaldırabilir. |
| BR-007 | Kullanıcı tüm verilerini silebilmelidir. |
| BR-008 | Kullanıcı verilerini dışa aktarabilmelidir. |
| BR-009 | Kurumsal hesaplarda yöneticiler sadece yetkili oldukları ekip verilerini görebilir. |
| BR-010 | Kişisel veriler şifreli saklanmalıdır. |
| BR-011 | Hassas veriler AI modeline gönderilmeden önce maskeleme opsiyonu sunulmalıdır. |
| BR-012 | Veriler üçüncü taraflara satılmaz. |
| BR-013 | Sistem güvenlik ve gizlilik odaklı tasarlanmalıdır. |
| BR-014 | AI cevabı kaynak bulunamadığında kesin iddia üretmemelidir. |
| BR-015 | Düşük confidence score’a sahip öneriler otomatik aksiyona dönüştürülemez. |
| BR-016 | Entegrasyon izinleri minimum gerekli kapsamla istenmelidir. |
| BR-017 | Silinen veri, yasal saklama zorunluluğu yoksa aktif sistemlerden kaldırılmalıdır. |
| BR-018 | Audit log kullanıcı tarafından değiştirilemez olmalıdır. |
| BR-019 | Kurumsal veri saklama politikası bireysel tercihlerden öncelikli olabilir, ancak kullanıcıya açıklanmalıdır. |
| BR-020 | WhatsApp ve mesajlaşma entegrasyonları yalnızca resmi API ve izinli kanallarla yapılmalıdır. |

# 20. Ürün Modülleri

## 20.1 Kullanıcı Yönetimi

Kapsam:

- Kayıt, giriş, çıkış.
- Şifre sıfırlama.
- Google, Microsoft, Apple ile giriş.
- Profil yönetimi.
- Cihaz yönetimi.
- Oturum yönetimi.
- Rıza ve izin yönetimi.
- Plan ve kota görünümü.

Başarı kriteri:

- Kullanıcı ilk oturumdan sonra 5 dakika içinde ilk görüşme analizini başlatabilmelidir.

## 20.2 Telefon Görüşmesi Modülü

MVP’de ses kaydı yerine görüşme metni temel alınacaktır. Ses transkripsiyonu orta vadeli kapsamdır.

Kapsam:

- Metin girişi/yükleme.
- Görüşme sonrası analiz.
- Özet, konuşmacı ayrımı, müşteri/kişi tespiti.
- Tarih/saat, randevu, görev önerisi.
- Etiketleme ve arşivleme.
- Gizlilik onayı.

## 20.3 AI Analiz Modülü

Kapsam:

- Özet çıkarma.
- Görev/randevu/son tarih çıkarma.
- Kişi/firma tespiti.
- Konu sınıflandırma.
- Öncelik ve risk puanı.
- Bekleyen iş tespiti.
- Confidence score.
- Kullanıcı onayı gerektiren işlem kuyruğu.

## 20.4 Randevu ve Takvim Modülü

Kapsam:

- Uygulama içi takvim.
- Google Calendar entegrasyonu.
- Outlook Calendar entegrasyonu.
- Manuel ve AI önerili randevu.
- Çakışma kontrolü.
- Boş zaman önerisi.
- Hatırlatma.
- Güncelleme/silme.

## 20.5 Görev Yönetimi

Kapsam:

- Manuel ve AI önerili görev.
- Öncelik, son tarih, hatırlatma.
- Tamamlandı/gecikti durumu.
- Kişi/firma, görüşme/mail bağlantısı.
- Dashboard ve raporlama entegrasyonu.

## 20.6 Mail Analizi

Kapsam:

- Gmail ve Outlook bağlantısı.
- Mail okuma izni.
- Önemli mail, son tarih, görev, randevu tespiti.
- Mail özeti.
- Bekleyen cevap tespiti.
- AI mail taslağı önerisi.

## 20.7 WhatsApp / Mesajlaşma

Kapsam:

- Resmi API ve izinli entegrasyon araştırması.
- WhatsApp Business API öncelikli değerlendirme.
- Mesajlardan görev/randevu/not çıkarma.
- Kişisel sohbetlere izinsiz erişimden kaçınma.
- Rıza ve taraf bilgilendirme akışları.

## 20.8 Kişi ve Müşteri Hafızası

Kapsam:

- Kişi profili.
- Firma profili.
- Timeline.
- Son görüşmeler ve mailler.
- Bekleyen görevler ve geçmiş randevular.
- Konuşulan konular, notlar, belgeler.

## 20.9 AI Chat

Kapsam:

- Doğal dilde sorgu.
- Kaynaklı cevap.
- Yetki sınırları.
- Semantik arama.
- Örnek sorular:
  - “Ahmet bana en son ne demişti?”
  - “Bu hafta kimlere teklif göndermem gerekiyor?”
  - “Cuma günü olan toplantılarımı göster.”
  - “Geçen ay fiyat isteyen ama dönüş yapmadığım müşterileri listele.”
  - “Bugün en önemli işlerim neler?”

## 20.10 Dashboard

Kapsam:

- Günlük özet.
- Bugünkü toplantılar.
- Bekleyen görevler.
- Geciken işler.
- Önemli mailler.
- Yaklaşan randevular.
- AI önerileri.
- Haftalık performans.
- Hızlı aksiyon butonları.

## 20.11 Bildirim Sistemi

Kapsam:

- Push, e-posta, SMS.
- Resmi API mümkünse WhatsApp bildirimi.
- Varsayılan ve özel hatırlatma zamanları.
- Kullanıcı tercihleri.
- Teslimat ve hata logları.

## 20.12 Analitik ve Raporlama

Kapsam:

- Haftalık görüşme ve mail sayısı.
- Oluşturulan/tamamlanan/geciken görevler.
- Randevu sayısı.
- Müşteri dönüş takibi.
- Satış ekibi performans raporları.
- AI öneri kabul oranı.

# 21. Kullanıcı Rolleri

| Rol | Açıklama | Temel yetkiler |
|---|---|---|
| Bireysel kullanıcı | Kendi verisini yöneten kullanıcı | Kendi kayıtlarını oluşturma, analiz, görev, takvim, chat |
| Takım üyesi | Kurumsal ekip içindeki standart kullanıcı | Kendi verisi ve paylaşılan ekip kayıtları |
| Takım yöneticisi | Belirli ekibi yöneten kullanıcı | Ekip raporları, ekip görevleri, yetkili müşteri kayıtları |
| Organizasyon admini | Kurumsal hesabın teknik/yönetim sorumlusu | Kullanıcı, rol, entegrasyon politikası, audit |
| Süper admin | Platform operasyon ekibi | Sistem yönetimi, destek amaçlı sınırlı ve loglanan erişim |
| Destek kullanıcısı | Müşteri destek personeli | Kullanıcı izniyle sınırlı destek görünümü |

# 22. Yetkilendirme Mantığı

Yetkilendirme role-based access control ve tenant isolation prensipleriyle tasarlanmalıdır.

Temel ilkeler:

- Kullanıcı varsayılan olarak yalnızca kendi verisini görür.
- Kurumsal yapılarda veri tenant bazında ayrılır.
- Ekip yöneticisi yalnızca kendisine bağlı ekip verilerine erişir.
- Admin rolleri içerik verisine sınırsız erişmemeli; gerekli durumlarda amaç, süre ve audit ile sınırlandırılmalıdır.
- AI Chat de aynı yetki kurallarına uymalıdır.
- Entegrasyon tokenları kullanıcı veya tenant bağlamında saklanmalıdır.
- Silme, export, rol atama ve entegrasyon kaldırma işlemleri audit log’a yazılmalıdır.

# 23. Veri Kaynakları

| Veri kaynağı | MVP durumu | İşleme amacı | Rıza gereksinimi |
|---|---|---|---|
| Manuel görüşme metni | MVP | Özet, görev, randevu, kişi hafızası | Açık rıza |
| Dosya olarak görüşme metni | MVP/Should | Metinden analiz | Açık rıza |
| Google Calendar | MVP | Etkinlik okuma/yazma, çakışma kontrolü | OAuth izni |
| Gmail | MVP opsiyonel | Mail özeti, görev, randevu, bekleyen cevap | OAuth izni |
| Outlook Calendar | Orta vadeli | Etkinlik yönetimi | OAuth izni |
| Outlook Mail | Orta vadeli | Mail analizi | OAuth izni |
| Telefon ses kaydı | Orta vadeli | Transkripsiyon ve analiz | Açık rıza + taraf bilgilendirme |
| WhatsApp Business API | Orta/uzun vadeli | İzinli mesaj analizi | Resmi API + rıza |
| Belgeler | Orta vadeli | Kişi/firma hafızası | Kullanıcı izni |
| Manuel notlar | MVP | Hafıza ve arama | Kullanıcı girişi |

# 24. AI Kullanım Alanları

AI sistem içinde karar verici değil, öneri ve analiz motorudur.

Kullanım alanları:

- Görüşme özeti.
- Mail özeti.
- Görev çıkarma.
- Randevu çıkarma.
- Son tarih tespiti.
- Kişi/firma tespiti.
- Konu sınıflandırma.
- Öncelik puanı.
- Risk tespiti.
- Bekleyen iş tespiti.
- AI Chat cevaplama.
- Semantik arama.
- Mail taslağı önerisi.
- Günlük iş planı önerisi.

AI kalite prensipleri:

- Kaynak gösterme zorunluluğu.
- Confidence score gösterimi.
- Düşük güvenli önerilerde insan onayı vurgusu.
- Veri maskeleme opsiyonu.
- Kullanıcı feedback döngüsü.
- Yetki ve rıza sınırlarına uyum.

# 25. Bildirim ve Hatırlatma Gereksinimleri

Bildirimler kullanıcının iş takip yükünü azaltmalı, ancak rahatsız edici olmamalıdır.

Gereksinimler:

- Görev son tarihi yaklaşınca bildirim.
- Randevu öncesi bildirim.
- Geciken görev bildirimi.
- Bekleyen müşteri dönüş bildirimi.
- Önemli mail bildirimi.
- Kullanıcı kanal tercihi: push, e-posta, SMS.
- Varsayılan hatırlatma: 1 gün önce, 1 saat önce, 15 dakika önce.
- Özel zamanlı hatırlatma.
- Sessiz saatler ve bildirim kapatma.
- Bildirim teslimat durumu.

# 26. Takvim Gereksinimleri

Takvim modülü NeuroDesk AI’ın aksiyon katmanının merkezindedir.

Gereksinimler:

- Gün/hafta/ay görünümü.
- Manuel etkinlik oluşturma.
- AI önerili etkinlik oluşturma.
- Google Calendar çift yönlü senkronizasyon.
- Outlook Calendar orta vadeli destek.
- Saat dilimi desteği.
- Çakışma kontrolü.
- Boş zaman önerisi.
- Katılımcı ve kişi/firma bağlantısı.
- Hatırlatma zamanları.
- Kaynak görüşme/mail bağlantısı.
- Güncelleme ve silme.
- Kullanıcı onaysız takvim yazımı yapılmaması.

# 27. Mail Analizi Gereksinimleri

Mail analizi, kullanıcı izin verdiğinde çalışmalıdır.

Gereksinimler:

- Gmail ve Outlook OAuth.
- Minimum izin kapsamı.
- Mail okuma izni açıklaması.
- Seçili mail veya etiket klasörü analizi.
- Önemli mail tespiti.
- Son tarih çıkarımı.
- Görev çıkarımı.
- Randevu çıkarımı.
- Mail özeti.
- Bekleyen cevap tespiti.
- AI mail taslağı önerisi.
- Onaysız mail gönderiminin engellenmesi.
- Entegrasyon kaldırıldığında veri çekiminin durması.

# 28. Telefon Görüşmesi Analizi Gereksinimleri

MVP, görüşme metni üzerinden başlar; ses transkripsiyonu sonraki fazdır.

Gereksinimler:

- Görüşme metni manuel girme/yükleme.
- Açık rıza kontrolü.
- Taraf bilgilendirme uyarıları.
- Konuşmacı ayrımı.
- Özet.
- Kişi/firma tespiti.
- Tarih/saat tespiti.
- Randevu önerisi.
- Görev önerisi.
- Etiket ve arşiv.
- AI confidence score.
- Kullanıcı onayı.

# 29. WhatsApp / Mesajlaşma Entegrasyonu Notları

NeuroDesk AI, kişisel WhatsApp sohbetlerine izinsiz erişimi hedeflemez. Mesajlaşma entegrasyonları yalnızca resmi API, kullanıcı izni ve platform politikalarına uygun şekilde değerlendirilmelidir.

Ürün ilkeleri:

- WhatsApp Business API öncelikli araştırma alanıdır.
- Kişisel WhatsApp hesabından izinsiz veri çekme kapsam dışıdır.
- Erişim, mesaj taraflarının bilgilendirilmesi gereken durumları dikkate almalıdır.
- Mesajlardan görev, randevu ve not çıkarma yalnızca izinli veri için yapılmalıdır.
- Kurumsal müşteriler için mesajlaşma kanalı politikaları admin tarafından yönetilebilmelidir.
- Mesaj verileri yüksek hassasiyetli kabul edilmeli ve şifreli saklanmalıdır.

# 30. CRM Benzeri Kişi Hafızası

NeuroDesk AI klasik CRM’in ağır satış pipeline yapısını MVP’de kopyalamamalıdır. Bunun yerine kişi ve firma bazlı hafıza sunmalıdır.

Kişi kartı alanları:

- Ad, soyad, telefon, e-posta.
- Firma, unvan, etiketler.
- Son görüşme özeti.
- Son mail özeti.
- Açık görevler.
- Yaklaşan randevular.
- Geçmiş randevular.
- Konuşulan konular.
- Notlar.
- Belgeler.
- Timeline.

Firma kartı alanları:

- Firma adı.
- İlgili kişiler.
- Açık görevler.
- Son iletişimler.
- Risk ve fırsat notları.
- Etiketler.

# 31. AI Chat Gereksinimleri

AI Chat, ürünün “ikinci beyin” deneyimini görünür kılan ana arayüzlerden biridir.

Gereksinimler:

- Doğal dilde soru.
- Kullanıcı verisi üzerinde yetkili arama.
- Kaynaklı cevap.
- Özet ve aksiyon önerisi ayrımı.
- Belirsizlik ve düşük güven notu.
- Tarih, kişi, firma, etiket ve kaynak tipi filtreleri.
- “Sonuç bulunamadı” durumunda uydurma cevap üretmeme.
- Cevaptan ilgili kayda geçiş.
- Kurumsal yetki sınırlarına uyum.

Örnek cevap prensibi:

- Önce kısa cevap.
- Sonra kaynaklar.
- Sonra önerilen aksiyonlar.
- Düşük güven varsa açık uyarı.

# 32. Dashboard Gereksinimleri

Dashboard kullanıcının günlük kontrol panelidir.

Bileşenler:

- Günlük özet.
- Bugünkü toplantılar.
- Bekleyen görevler.
- Geciken işler.
- Önemli mailler.
- Yaklaşan randevular.
- AI önerileri.
- Haftalık performans.
- Hızlı aksiyon butonları.

Boş ekran gereksinimi:

- İlk kez gelen kullanıcıya örnek görüşme analizi veya veri kaynağı bağlama önerilir.
- Boş ekran, ürünü açıklayan uzun pazarlama metni yerine doğrudan aksiyona yönlendirmelidir.

# 33. Arama ve Anlamsal Arama Gereksinimleri

Arama iki katmanda olmalıdır:

- Anahtar kelime arama.
- Anlamsal arama.

Gereksinimler:

- Kişi, firma, görev, randevu, görüşme, mail ve notlarda arama.
- Tarih aralığı filtresi.
- Kaynak tipi filtresi.
- Etiket filtresi.
- Semantik sorgular: “fiyat isteyenler”, “dönüş bekleyenler”, “riskli müşteriler”.
- Kaynaklı sonuçlar.
- Yetki sınırlarına uyum.
- AI Chat ile entegre çalışma.

# 34. Raporlama ve Analitik Gereksinimleri

Raporlama bireysel kullanıcıda kişisel verimlilik, takımda performans ve takip görünürlüğü sağlamalıdır.

Metrikler:

- Haftalık görüşme sayısı.
- Mail sayısı.
- Oluşturulan görevler.
- Tamamlanan görevler.
- Geciken görevler.
- Randevu sayısı.
- Müşteri dönüş takibi.
- AI öneri kabul oranı.
- Ortalama AI cevap süresi.
- Satış ekibi performansı.

Rapor görünümleri:

- Bireysel haftalık özet.
- Ekip performans raporu.
- Müşteri takip raporu.
- AI kullanım ve maliyet raporu.

# 35. Güvenlik ve KVKK/GDPR Gereksinimleri

Bu projede telefon görüşmesi, mail ve mesajlaşma verileri gibi kişisel veriler işleneceği için güvenlik ve uyum ürünün temel parçasıdır.

Bu bölüm hukuki danışmanlık değildir; ürün gereksinimi ve teknik uyumluluk çerçevesidir.

Gereksinimler:

- KVKK uyumluluğu.
- GDPR uyumluluğu.
- Açık rıza.
- Aydınlatma metni.
- Kullanıcı veri silme hakkı.
- Veri taşıma hakkı.
- Loglama ve audit trail.
- Şifreleme.
- Erişim kontrolü.
- Veri minimizasyonu.
- Onaysız işlem yapılmaması.
- Hassas veri maskeleme.
- Telefon görüşmelerinde tarafların bilgilendirilmesi.
- WhatsApp tarafında yalnızca resmi ve izinli entegrasyonlar.
- Veri işleme amaçlarının açık tanımı.
- Alt işleyen ve AI sağlayıcı sözleşmelerinde veri eğitimi yasağı tercih edilmesi.
- Kurumsal müşteriler için DPA ve güvenlik dokümantasyonu.

# 36. Veri Saklama Politikası

Varsayılan politika önerisi:

- Aktif kullanıcı verileri hesap aktif olduğu sürece saklanır.
- Kullanıcı hesap silme talebi verdiğinde kişisel veriler 30 gün içinde silinir veya anonimleştirilir.
- Audit log kayıtları güvenlik ve uyum amacıyla belirlenen süre boyunca saklanır.
- Yedeklerdeki silinen veriler yedek rotasyonu süresi içinde temizlenir.
- Kurumsal müşteriler veri saklama süresini planlarına göre özelleştirebilir.
- AI analiz ara çıktıları gereksizse kısa süreli saklanmalıdır.
- Kullanıcı açıkça izin vermedikçe veriler model eğitimi amacıyla kullanılmamalıdır.

Veri sınıfları:

- Kimlik verisi.
- İletişim verisi.
- İçerik verisi.
- Takvim verisi.
- Görev ve not verisi.
- Entegrasyon tokenları.
- Audit log.
- AI kullanım metrikleri.

# 37. Kullanıcı Onayı ve Rıza Yönetimi

Rıza yönetimi, ürünün güven inşası için görünür ve anlaşılır olmalıdır.

Gereksinimler:

- Veri kaynağı bağlama öncesi izin kapsamı açıkça gösterilir.
- Telefon/görüşme metni işleme öncesi açık rıza alınır.
- Kullanıcı rızasını geri çekebilir.
- Rıza geri çekildiğinde ilgili veri işleme durur.
- Rıza geçmişi tarih, kapsam, sürüm ve kaynakla saklanır.
- Aydınlatma metni erişilebilir olur.
- Kurumsal hesaplarda admin politikaları ve kullanıcı rızası ilişkisi açıkça gösterilir.

# 38. Hedef Pazar

Birincil pazar:

- Türkiye’de KOBİ’ler, satış ekipleri, emlak, sigorta, hukuk, muhasebe, danışmanlık ve yazılım hizmet firmaları.

İkincil pazar:

- Global prosumer kullanıcılar, freelancerlar ve küçük takımlar.

Enterprise pazar:

- Satış, müşteri başarı, teknik destek ve çağrı merkezi ekipleri olan orta/büyük ölçekli şirketler.

Pazar giriş stratejisi:

- İlk odak: satış ve emlak gibi iletişim yoğun, takip problemi açık segmentler.
- İkinci odak: freelancer ve profesyonel hizmet sağlayıcıları.
- Üçüncü odak: takım paketi ile KOBİ satış ekipleri.
- Enterprise’a geçiş: güvenlik, audit, SSO, veri saklama ve entegrasyon olgunluğu sonrası.

# 39. Rakip Analizi

Bu bölüm 08 Temmuz 2026 itibarıyla sınırlı resmi kaynak kontrolüyle hazırlanmıştır. Ayrıntılı fiyat, pazar payı ve yerel regülasyon karşılaştırması ayrıca güncel pazar araştırması ile doğrulanmalıdır.

Kaynak notları:

- Notion AI resmi sayfası; ajanlar, enterprise search, AI meeting notes, bağlı uygulamalar ve güvenlik kontrollerini vurgular: https://www.notion.com/product/ai
- Microsoft 365 Copilot resmi sayfası; Work IQ, Chat/Cowork, Search ve Agents kabiliyetlerini konumlar: https://www.microsoft.com/en-us/microsoft-365-copilot
- Google Workspace AI/Gemini resmi sayfası, Workspace içi AI üretkenlik özellikleri için referans alınmalıdır: https://workspace.google.com/solutions/ai/
- Fireflies.ai resmi sayfası; toplantı transkripsiyonu, özet, arama, conversation intelligence, CRM entegrasyonları ve güvenlik iddialarını konumlar: https://fireflies.ai/
- Otter.ai, Fathom, Read.ai ve Granola resmi siteleri toplantı notu/transkripsiyon odaklı ürün kategorisinin örnekleri olarak değerlendirilmiştir.

| Rakip/kategori | Ne yapıyor? | Güçlü yönleri | Zayıf yönleri | Bizim farklılaşma alanımız |
|---|---|---|---|---|
| Notion AI | Workspace içinde AI yazım, arama, ajan ve toplantı notu | Güçlü doküman/veritabanı ekosistemi, ekip kullanımı | Telefon, satış takibi ve kişi bazlı iletişim hafızası ana odak değil | Telefon, mail, takvim ve müşteri hafızasını aksiyona bağlama |
| Microsoft 365 Copilot | Microsoft 365 uygulamalarında iş bağlamlı AI | Kurumsal dağıtım, Microsoft Graph, güvenlik | Microsoft ekosistemine bağımlılık, KOBİ için karmaşık olabilir | Bağımsız, hafif, satış/takip odaklı asistan |
| Google Gemini Workspace | Gmail, Docs, Calendar gibi Workspace uygulamalarında AI | Google ekosistemi entegrasyonu | Telefon görüşmesi ve CRM benzeri hafıza sınırlı | Çoklu veri kaynağından müşteri aksiyonu çıkarımı |
| Otter.ai | Toplantı transkripsiyonu ve not alma | Transkripsiyon deneyimi, toplantı notu | İş aksiyonlarını CRM/takvim/kişi hafızasına bağlama sınırlı | Görüşme sonrası takip, görev, kişi hafızası |
| Fireflies.ai | Toplantı transkripsiyonu, özet, arama, conversation intelligence | Geniş entegrasyon, toplantı zekası, CRM bağlantıları | Telefon/mail kişisel çalışma hafızası için ayrı konumlanmayabilir | KOBİ ve bireysel profesyonel için ikinci beyin |
| Fathom | AI not alma ve toplantı özeti | Basit toplantı deneyimi | Toplantı dışı iletişim kapsamı sınırlı | Telefon, mail, görev, takvim birleşimi |
| Read.ai | Toplantı özetleri, transkript, arama | Toplantı analitiği ve enterprise search yaklaşımı | Günlük satış/takip iş akışı ana odak olmayabilir | Takip ve aksiyon odaklı dashboard |
| Mem.ai | Kişisel bilgi hafızası ve notlar | Kişisel bilgi yönetimi | Telefon/mail/takvim aksiyon çıkarımı sınırlı | İş iletişimi ve müşteri takip odaklı hafıza |
| Granola | AI not defteri ve toplantı notları | Hafif ve kullanıcı dostu toplantı notu | CRM, görev, randevu, mail entegrasyonu sınırlı | Dağınık iletişimden aksiyon çıkarma |
| Supernormal | Toplantı notu ve takip | Meeting notes ve ekip paylaşımı | Telefon görüşmesi ve satış hafızası sınırlı | Çok kanallı iletişim hafızası |
| CRM sistemleri | Müşteri ve satış süreçlerini yönetir | Pipeline, raporlama, kurumsal kullanım | Veri girişi manuel ve disiplin gerektirir | CRM’i otomatik besleyen AI hafıza katmanı |
| Takvim/görev uygulamaları | Görev ve randevu yönetir | Basitlik, alışkanlık | İletişimi anlamaz, aksiyon çıkarmaz | Görüşme ve mailden otomatik öneri |

# 40. SWOT Analizi

## Strengths

- Çoklu veri kaynağı yaklaşımı.
- AI destekli aksiyon çıkarımı.
- Kişi ve müşteri hafızası.
- Satış ve iş takibi odaklı kullanım.
- Mobil + web destek.
- Kullanıcı onaylı güvenli AI prensibi.
- KOBİ için CRM’den hafif, not uygulamasından daha sonuç odaklı yapı.

## Weaknesses

- Yasal izin süreçleri karmaşık olabilir.
- Telefon ve WhatsApp entegrasyonları platform ve mevzuat açısından zordur.
- AI doğruluk riski kullanıcı güvenini etkileyebilir.
- Güvenlik, şifreleme, audit ve uyum maliyetleri yüksektir.
- Çoklu veri kaynağı entegrasyonu operasyonel bakım gerektirir.
- İlk MVP’de manuel metin girişi kullanıcı beklentisini sınırlayabilir.

## Opportunities

- AI asistan pazarının büyümesi.
- KOBİ’lerin basit CRM ve takip ihtiyacı.
- Satış ekiplerinin takip problemi.
- Verimlilik araçlarına artan talep.
- Profesyonel hizmet sektörlerinde iletişim hafızası ihtiyacı.
- Yerel dil ve regülasyon uyumuyla Türkiye pazarı avantajı.

## Threats

- Büyük teknoloji şirketleri.
- KVKK/GDPR riskleri.
- Platform API kısıtlamaları.
- Kullanıcı güveni.
- AI maliyetlerinin artması.
- Rakip toplantı notu araçlarının CRM ve görev alanına genişlemesi.

# 41. İş Modeli

Değerlendirilecek iş modelleri:

- Freemium.
- Aylık abonelik.
- Kullanıcı başı lisanslama.
- Kurumsal paket.
- AI kullanım kotası bazlı fiyatlandırma.
- Takım paketi.
- CRM entegrasyonu ücretli paket.
- API erişimi ücretli paket.

Önerilen strateji:

- Bireysel pazarda freemium ile edinim.
- Pro pakette AI kota, mail ve takvim entegrasyonları.
- Team pakette ekip hafızası, raporlama ve paylaşım.
- Enterprise pakette güvenlik, SSO, SLA, veri saklama ve özel entegrasyon.

# 42. Gelir Modeli

Gelir kalemleri:

- Aylık/yıllık kullanıcı aboneliği.
- AI analiz kotası aşım paketleri.
- Kullanıcı başı takım lisansı.
- Kurumsal minimum lisans bedeli.
- Premium entegrasyon paketleri.
- API kullanım ücreti.
- Private deployment veya özel veri saklama ek ücreti.
- Profesyonel kurulum ve eğitim hizmetleri.

Fiyatlandırma metrikleri:

- Kullanıcı sayısı.
- Aylık analiz edilen görüşme/mail sayısı.
- AI Chat sorgu sayısı.
- Entegrasyon sayısı.
- Veri saklama süresi.
- Güvenlik ve SLA seviyesi.

# 43. Paketleme ve Abonelik Planları

| Plan | Hedef kullanıcı | İçerik |
|---|---|---|
| Free | Bireysel deneme | Sınırlı görüşme analizi, sınırlı görev, basit dashboard, manuel metin analizi |
| Pro | Profesyoneller | Daha fazla analiz, Gmail entegrasyonu, Google Calendar entegrasyonu, AI Chat, kişi hafızası |
| Team | KOBİ ve ekipler | Çoklu kullanıcı, ekip görevleri, paylaşımlı müşteri hafızası, ekip raporları, rol yönetimi |
| Enterprise | Kurumsal şirketler | SSO, özel veri saklama, gelişmiş güvenlik, SLA, audit, özel entegrasyonlar, admin politikaları |

Paketleme ilkeleri:

- Free plan ürün değerini gösterecek kadar cömert, maliyetleri koruyacak kadar sınırlı olmalıdır.
- Pro plan bireysel profesyonelin ana gelir kalemidir.
- Team plan ürünün B2B genişlemesini sağlar.
- Enterprise plan güvenlik ve entegrasyon olgunluğu sonrası aktif satılmalıdır.

# 44. Başarı Metrikleri

| Metrik | Tanım | Hedef kullanımı |
|---|---|---|
| DAU | Günlük aktif kullanıcı | Günlük kullanım sağlığı |
| WAU | Haftalık aktif kullanıcı | İş rutini entegrasyonu |
| MAU | Aylık aktif kullanıcı | Genel büyüme |
| Görüşme başına görev sayısı | Analizden çıkan ortalama görev | AI değer ölçümü |
| AI öneri kabul oranı | Önerilerin onaylanma yüzdesi | AI kalite ve güven |
| Oluşturulan randevu sayısı | AI/manual randevu toplamı | Takvim değer ölçümü |
| Tamamlanan görev oranı | Tamamlanan / oluşturulan görev | Aksiyon başarısı |
| Geciken görev oranı | Geciken / açık görev | İş takip riski |
| Kullanıcı başına analiz edilen iletişim | Görüşme/mail/not analiz hacmi | Ürün bağımlılığı |
| Retention | Kullanıcıların geri dönme oranı | Ürün pazar uyumu |
| Churn | Abonelik iptali veya terk | Gelir sağlığı |
| Conversion rate | Free’den ücretliye geçiş | İş modeli başarısı |
| Ortalama AI cevap süresi | AI analiz/chat yanıt süresi | Deneyim kalitesi |
| Kullanıcı memnuniyeti | Uygulama içi puan/anket | Ürün algısı |
| NPS | Tavsiye etme skoru | Marka ve sadakat |

# 45. Riskler ve Varsayımlar

## Riskler

- Telefon görüşmesi kaydı ve işlenmesi için farklı ülkelerde değişen yasal yükümlülükler.
- WhatsApp kişisel sohbet erişiminin platform politikaları ve gizlilik nedeniyle uygun olmaması.
- AI’ın yanlış görev/randevu çıkarması.
- Kullanıcının AI önerilerine güvenmemesi.
- Entegrasyon API limitleri veya politika değişiklikleri.
- AI maliyetlerinin karlılığı baskılaması.
- Kurumsal müşterilerin güvenlik beklentilerinin MVP seviyesini aşması.
- Veri ihlali riskinin marka güvenini zedelemesi.

## Varsayımlar

- Kullanıcılar görüşme sonrası manuel not almak yerine AI önerilerini düzenlemeyi tercih edecektir.
- Satış ve profesyonel hizmet kullanıcıları takip problemini yüksek değerli görür.
- İlk MVP’de manuel görüşme metni girişi ürün değerini doğrulamak için yeterlidir.
- Kullanıcı onaylı AI yaklaşımı güveni artırır.
- Google Calendar entegrasyonu MVP değerini belirgin artırır.
- Gmail entegrasyonu Pro plana geçişte güçlü tetikleyici olur.

# 46. Ürün Yol Haritası

## 0-3 Ay

- MVP.
- Auth.
- Telefon metni analizi.
- AI özet.
- Görev çıkarma.
- Randevu çıkarma.
- Uygulama içi takvim.
- Google Calendar entegrasyonu.
- Dashboard.
- Kişi kartı.
- Basit AI Chat.

## 3-6 Ay

- Gmail entegrasyonu.
- Outlook entegrasyonu.
- AI Chat geliştirmeleri.
- Kişi hafızası zenginleştirme.
- Mobil uygulama iyileştirmeleri.
- Bekleyen cevap tespiti.
- AI feedback ve kalite dashboard’u.

## 6-12 Ay

- Takım özellikleri.
- CRM görünümü.
- Gelişmiş raporlama.
- WhatsApp Business gibi resmi entegrasyonlar.
- Semantic search.
- AI Memory.
- Rol bazlı erişim.
- Audit log.

## 12+ Ay

- Enterprise.
- API Marketplace.
- ERP/CRM entegrasyonları.
- Çoklu dil.
- Global pazar.
- SSO.
- Private cloud opsiyonları.
- Sektörel paketler.

# 47. Sprint Bazlı Ürün Planı

| Sprint | Süre | Amaç | Kapsam | Çıktılar | Kabul kriterleri | Riskler |
|---|---|---|---|---|---|---|
| Sprint 1 — Ürün Temeli ve Auth | 2 hafta | Güvenli kullanıcı girişi | Kayıt, giriş, şifre sıfırlama, profil | Auth akış gereksinimleri | Kullanıcı kayıt/giriş yapar | OAuth yapılandırma |
| Sprint 2 — Rıza ve Profil | 2 hafta | Veri işleme kontrolü | Aydınlatma, rıza, profil, oturum | Rıza yönetimi | Rıza olmadan analiz başlamaz | Hukuki metin gecikmesi |
| Sprint 3 — Görüşme Metni Girişi | 2 hafta | İlk veri girişini sağlamak | Manuel metin, dosya yükleme, kaynak kayıt | Görüşme kayıt akışı | Metin kaydedilir | Format desteği |
| Sprint 4 — AI Özet | 2 hafta | İlk AI değerini sunmak | Kısa/detaylı özet, kaynak | Özet ekranı | Özet kaynakla gösterilir | AI doğruluğu |
| Sprint 5 — AI Görev Çıkarma | 2 hafta | Aksiyon üretmek | Görev önerisi, düzenleme, onay | Görev öneri akışı | Onayla görev oluşur | Yanlış görevler |
| Sprint 6 — AI Randevu Çıkarma | 2 hafta | Takvim aksiyonu üretmek | Tarih/saat tespiti, çakışma | Randevu öneri akışı | Onayla randevu oluşur | Belirsiz tarih |
| Sprint 7 — Görev Yönetimi | 2 hafta | Görev yaşam döngüsü | Liste, öncelik, durum, geciken | Görev modülü | Görev tamamlanır/gecikir | UX karmaşıklığı |
| Sprint 8 — Takvim MVP | 2 hafta | Uygulama içi takvim | Gün/hafta görünüm, etkinlik | Takvim ekranları | Etkinlik görüntülenir | Saat dilimi hatası |
| Sprint 9 — Google Calendar | 2 hafta | Harici takvim entegrasyonu | OAuth, okuma/yazma, çakışma | Google entegrasyonu | Onayla etkinlik yazılır | API limitleri |
| Sprint 10 — Kişi Kartı | 2 hafta | Hafıza katmanı | Kişi profili, timeline, not | Kişi modülü | Kişi geçmişi görünür | Eşleştirme hataları |
| Sprint 11 — Dashboard | 2 hafta | Günlük kontrol merkezi | Günlük özet, görev, randevu, öneriler | Dashboard | Günlük işler görünür | Veri boşluğu |
| Sprint 12 — Bildirimler | 2 hafta | Hatırlatma deneyimi | E-posta/push, tercih, teslimat | Bildirim modülü | Hatırlatma gider | Teslimat sorunları |
| Sprint 13 — Basit AI Chat | 2 hafta | Doğal dil sorgu | Soru, kaynaklı cevap, yetki | Chat MVP | Kaynaklı cevap döner | Halüsinasyon |
| Sprint 14 — Arama | 2 hafta | Kayıtlara erişim | Anahtar kelime, filtre, temel semantik | Arama ekranı | Sonuçlar filtrelenir | Arama kalitesi |
| Sprint 15 — Gmail Opsiyonel MVP | 2 hafta | Mail değerini test etmek | OAuth, seçili mail analizi, özet | Gmail beta | Mailden görev çıkar | İzin kapsamı |
| Sprint 16 — Beta Hazırlık ve Ölçüm | 2 hafta | Yayına hazırlık | Analitik, hata, feedback, onboarding | Beta paket | Pilot kullanıcı akışı tamamlar | Kalite ve maliyet |

# 48. Ekibin İhtiyaç Duyacağı Roller

| Rol | Sorumluluk |
|---|---|
| Product Manager | Vizyon, roadmap, kapsam, başarı metrikleri |
| CTO / Tech Lead | Mimari kararlar, teknik kalite, güvenlik yaklaşımı |
| Backend Developer | API, entegrasyon, veri modeli, görev/takvim servisleri |
| Frontend Developer | Web panel, dashboard, chat, görev/takvim UI |
| Mobile Developer | iOS/Android veya cross-platform mobil ekranlar |
| AI Engineer | Prompt, model orkestrasyonu, RAG, değerlendirme |
| Data Engineer | Veri pipeline, embedding, analitik |
| UX/UI Designer | Kullanıcı akışları, bilgi mimarisi, ürün deneyimi |
| QA Engineer | Test planı, kabul kriteri doğrulama |
| DevOps/SRE | Deployment, monitoring, backup, güvenilirlik |
| Security Engineer | Şifreleme, pentest, erişim kontrolü, audit |
| Legal/Compliance Advisor | KVKK/GDPR, rıza, aydınlatma, veri işleme sözleşmeleri |
| Customer Success | Pilot kullanıcı yönetimi, feedback, onboarding |
| Sales/BD | B2B satış, partnerlik, dikey pazar geliştirme |

# 49. Sonuç ve Stratejik Öneriler

NeuroDesk AI, doğru kapsamla başlatıldığında güçlü bir AI productivity ve hafif CRM ürünü olabilir. Ancak ürünün başarısı “her şeyi otomatik yapan AI” iddiasından değil, güvenilir şekilde öneren, kaynak gösteren, kullanıcı onayıyla aksiyon alan ve iletişim hafızasını iş sonuçlarına bağlayan yapıdan gelecektir.

Stratejik öneriler:

- MVP’de telefon ses kaydı ve WhatsApp gibi zor entegrasyonlara odaklanmadan, görüşme metni analiziyle değer hipotezi doğrulanmalıdır.
- İlk hedef segment satış, emlak ve profesyonel hizmetler gibi takip probleminin açık olduğu alanlar olmalıdır.
- AI güveni için her öneride kaynak, confidence score ve düzenleme/onay akışı bulunmalıdır.
- Google Calendar entegrasyonu MVP’de güçlü değer üretir; Gmail entegrasyonu Pro plana geçiş için kritik olabilir.
- Kurumsal satışa erken girilmeden önce audit, RBAC, veri saklama, DPA ve güvenlik dokümanları olgunlaştırılmalıdır.
- WhatsApp tarafında yalnızca resmi ve izinli entegrasyon stratejisi izlenmelidir.
- Ürün metrikleri baştan yerleştirilmeli; AI öneri kabul oranı ve tekrar kullanım MVP’nin ana doğrulama sinyalleri olmalıdır.

# 50. Codex İçin Sonraki Ciltlere Hazırlık Notları

Cilt 2’de sistem mimarisi hazırlanırken bu PRD’deki kapsam aşağıdaki teknik başlıklara dönüştürülmelidir:

- Backend servis sınırları.
- Frontend ve mobil uygulama mimarisi.
- AI servis orkestrasyonu.
- RAG ve semantic search yaklaşımı.
- Veri modeli ve tenant izolasyonu.
- Entegrasyon mimarisi.
- Event-driven architecture.
- Bildirim altyapısı.
- Audit ve loglama mimarisi.
- Güvenlik ve şifreleme tasarımı.
- Deployment ve monitoring mimarisi.
- API Gateway ve servisler arası iletişim.
- KVKK/GDPR uyumlu veri yaşam döngüsü.

# Codex İçin Sonraki Adım

Bir sonraki dokümanda sistem mimarisi hazırlanacaktır. Cilt 2; backend mimarisi, frontend mimarisi, mobil mimari, AI servis mimarisi, microservice yapısı, event-driven architecture, API Gateway, güvenlik mimarisi, deployment mimarisi ve servisler arası iletişim detaylarını içermelidir.
