<p align="right">Türkçe · <a href="./README.en.md">English</a></p>

# Aventrix

**Sorumlu bir URL zekâsı ve kampanya yönetimi platformu**: takip edilen bağlantılar oluştur, bunları kampanyalarda grupla, QR kod üret, alan adı/güvenlik keşfi (recon) yap ve kimlerin tıkladığını gizliliğe saygılı analitiklerle gör — ziyaretçi onayı sonradan eklenmiş bir yama değil, akışın merkezinde.

Tam üretim-şekilli bir SaaS olarak inşa edildi: FastAPI + async SQLAlchemy backend, React + TypeScript frontend, Postgres, Redis, bir arka plan worker'ı ve uzaktan cihaz kontrolü için opsiyonel bir Android companion uygulaması — hepsi nginx arkasında container'lanmış.

```mermaid
flowchart LR
    A[Panel] --> B[Kampanya]
    B --> C[Takip bağlantısı<br/>/t/KOD]
    C --> D{Onay /<br/>şifre kapısı}
    D --> E[Yönlendirme]
    D --> F[Ziyaret kaydedildi]
    F --> G[IP zekâsı<br/>asenkron]
    G --> A
```

<p align="center">
  <img src="docs/screenshots/04-dashboard.png" alt="Aventrix paneli" width="860">
</p>

---

## İçindekiler

- [Öne çıkanlar](#öne-çıkanlar)
- [Özellik turu](#özellik-turu)
- [Ekran görüntüleri](#ekran-görüntüleri)
- [Mimari](#mimari)
- [Proje yapısı](#proje-yapısı)
- [Teknoloji yığını](#teknoloji-yığını)
- [Hızlı başlangıç](#hızlı-başlangıç)
- [Dokümantasyon](#dokümantasyon)
- [Güvenlik ve gizlilik](#güvenlik-ve-gizlilik)
- [Testler](#testler)
- [Yol haritası](#yol-haritası-henüz-yapılmadı)
- [Lisans](#lisans)

---

## Öne çıkanlar

- 🔗 **Akıllı bağlantılar** — özel takma adlar, son kullanma tarihi, şifre koruması, opsiyonel onay kapısı, ayrılmış kelime/çakışma kontrolleri, UTM oluşturucu
- 📊 **Gizliliğe saygılı analitik** — ziyaret trendleri, en çok ülke/cihaz/tarayıcı/işletim sistemi/yönlendiren, tarih aralığı filtreleri, CSV/JSON dışa aktarma
- 🧭 **Keşif ve OSINT araç seti** — alt alan adı taraması, DNS yayılım kontrolleri, teknoloji tespiti, robots.txt/sitemap ayrıştırma, çerez analizi, WHOIS, SSL incelemesi
- 🛡️ **Güvenlik Merkezi** — DNS/WHOIS/SSL kontrolleri, güvenlik başlığı analizörü, itibar puanlaması; hepsi geçmişiyle birlikte 0-100 arası tek bir puana toplanıyor
- 📱 **QR kodları** — sunucu tarafında üretilen PNG/SVG, özelleştirilebilir boyut/renk/hata düzeltme, opsiyonel gömülü logo
- 🧰 **URL araçları** — kodlayıcı/çözücü, UTM oluşturucu, SSRF'ye karşı sertleştirilmiş URL analizörü, yönlendirme zinciri denetleyicisi
- 🔑 **Katmanlı API anahtarları** — Free/Pro/Business, kayıtta hash'lenmiş, katman başına hız sınırı
- 🪝 **Webhook'lar** — HMAC imzalı, olay tabanlı, yeniden deneme geri çekilmesiyle asenkron teslimat ve teslimat günlüğü
- 🔔 **Bildirimler** — uygulama içi + e-posta, ilk ziyaretler, son kullanma tarihleri, webhook hataları ve düşük güvenlik puanlarıyla tetiklenir
- 🔐 **Ciddi kimlik doğrulama** — refresh-token rotasyonu, e-posta doğrulama, şifre sıfırlama, 2FA (TOTP + yedek kodlar), oturum yönetimi, sunucu tarafında zorunlu kılınan RBAC (`SUPER_ADMIN → ADMIN → MANAGER → USER → VIEWER`)
- 📲 **Cihazlar modülü** — bir Android companion istemcisi üzerinden AirDroid tarzı uzaktan ekran kontrolü

## Özellik turu

### Bağlantılar ve kampanyalar
Özel takma adlar, son kullanma tarihleri, şifre koruması ve opsiyonel ziyaretçi onay kapısıyla takip edilen bağlantılar oluştur. Bağlantıları kampanyalarda grupla ve kampanya bazlı performansa in: toplam tıklama, tekil ziyaretçi, TO (CTR), en çok ülke/cihaz/tarayıcı ve bir ziyaret zaman çizelgesi. Yönlendirme sistemi hedefi asla istek girdisine güvenmez — hedef adres yalnızca veritabanından geri okunur, bu da klasik açık-yönlendirme (open redirect) açığını kapatır.

### Analitik
Filtrelenebilir, dışa aktarılabilir bir analitik sayfası: istatistik kartları, zaman içindeki ziyaret trendleri, ülke/cihaz/tarayıcı/işletim sistemi/yönlendiren kırılımları. Her ziyaret IP zekâsını (varsayılan olarak mock sağlayıcı, gerçek sağlayıcı adaptörü bağlanmaya hazır) ve bot-güven skoru dahil UA kaynaklı sinyalleri kaydeder. Ham istemci IP'si her ziyarette kaydedilir; daha zengin cihaz/tarayıcı/UTM parmak izi ise yalnızca ziyaretçi açıkça onay verdiğinde yakalanır (bkz. [`docs/SECURITY.md`](./docs/SECURITY.md#privacy)).

### Güvenlik Merkezi ve keşif/OSINT
Sahibi olduğun ya da test etmeye açıkça yetkili olduğun herhangi bir alan adını analiz et:

- DNS kayıtları, çözümleyiciler arası DNS yayılımı, WHOIS, SSL sertifika detayları
- Alt alan adı taraması ve teknoloji/yığın tespiti
- `robots.txt` / sitemap ayrıştırma
- Çerez analizi (bayraklar, kapsam, güvenlik öznitelikleri)
- Güvenlik başlığı analizörü (CSP, HSTS, X-Frame-Options vb.) ve itibar kontrolü (varsayılan mock, gerçek adaptör hazır)

Tüm bulgular tam tarama geçmişiyle birlikte tek bir 0-100 güvenlik puanına toplanır.

### QR kodları ve URL araçları
Herhangi bir bağlantı için yapılandırılabilir boyut, renk, hata düzeltme seviyesi ve opsiyonel gömülü logo ile bir QR kodu (PNG/SVG) üret. URL araçları sayfası buna bir kodlayıcı/çözücü, bir UTM oluşturucu, SSRF'ye karşı sertleştirilmiş bir URL analizörü (başlık/açıklama/favicon önizlemesi) ve bir yönlendirme zinciri denetleyicisi ekler.

### API, webhook'lar ve bildirimler
Tüm API için alternatif bir kimlik bilgisi olarak katmanlı API anahtarları (Free/Pro/Business) üret — bir kez gösterilir, kayıtta hash'lenir, katman başına hız sınırlıdır. Webhook'lara abone ol (`link.created/clicked`, `campaign.created/completed`, `security.alert`) — HMAC imzalarıyla, asenkron yeniden deneme geri çekilmesiyle ve bir teslimat günlüğüyle teslim edilir. Uygulama içi + e-posta bildirim merkezi bir bağlantının ilk ziyaretini, son kullanma tarihini, webhook hatalarını ve düşük güvenlik puanlarını, tür başına e-posta tercihleriyle birlikte kapsar.

### Cihazlar (uzaktan kontrol)
Bir Android companion istemcisi (`android/`), kendi sinyalleşme protokolüyle birlikte inşa edilmiş AirDroid tarzı uzaktan ekran görüntüleme/kontrolü etkinleştirmek için platformla eşleşir (bkz. [`docs/DEVICE_CONTROL_PROTOCOL.md`](./docs/DEVICE_CONTROL_PROTOCOL.md)).

### Güvenlik temeli (platform genelinde)
Hız sınırlama, güvenlik başlıkları, CORS, standart bir hata zarfı, yapılandırılmış JSON loglar, bir denetim (audit) günlüğü, her yerde IDOR'a karşı güvenli sahiplik kontrolleri ve kullanıcı tarafından sağlanan bir URL'nin sunucu tarafında çekildiği her yerde SSRF'ye karşı sertleştirilmiş giden istekler.

## Ekran görüntüleri

Aşağıdaki her ekran, gerçekten çalışan uygulamanın, oturum açılmış ve gerçek etkinlikle doldurulmuş hâlinin gerçek bir görüntüsüdür — kurgu değil, boş durum değil.

### Giriş ve hesap

<table>
<tr>
<td width="33%"><img src="docs/screenshots/01-login.png" alt="Giriş sayfası"><br><sub>Giriş</sub></td>
<td width="33%"><img src="docs/screenshots/02-register.png" alt="Kayıt sayfası"><br><sub>Hesap oluştur</sub></td>
<td width="33%"><img src="docs/screenshots/03-forgot-password.png" alt="Şifremi unuttum sayfası"><br><sub>Şifre sıfırlama</sub></td>
</tr>
</table>

### Panel — açık & koyu tema, gerçek trafikle

<table>
<tr>
<td width="50%"><img src="docs/screenshots/04-dashboard.png" alt="Panel, açık tema, gerçek ziyaretlerle dolu"><br><sub>Açık tema</sub></td>
<td width="50%"><img src="docs/screenshots/05-dashboard-dark.png" alt="Panel, koyu tema, gerçek ziyaretlerle dolu"><br><sub>Koyu tema</sub></td>
</tr>
</table>

Toplam bağlantı, ziyaret, tekil ziyaretçi, bugünkü ziyaretler, aktif proje sayısı ve tekillik oranı, bir ziyaret trend grafiği ve en çok ülke/cihaz/tarayıcı — hepsi bu tur sırasında gerçekten tıklanan bağlantılardan gelen gerçek rakamlar.

### Projeler ve bağlantılar, gerçek tıklama verisiyle

<table>
<tr>
<td width="50%"><img src="docs/screenshots/06-projects-list.png" alt="Projeler listesi"><br><sub>Projeler</sub></td>
<td width="50%"><img src="docs/screenshots/07-project-detail.png" alt="Gerçek istatistiklerle proje detay sayfası"><br><sub>Proje detayı — gerçek ziyaret/tekil sayıları</sub></td>
</tr>
<tr>
<td colspan="2"><img src="docs/screenshots/08-links-list.png" alt="Gerçek tıklama sayılarıyla bağlantılar listesi"><br><sub>Bağlantılar — her satır, altı farklı ülkeden simüle edilmiş tıklamalardan gelen gerçek ziyaret ve tekil ziyaretçi sayılarını gösteriyor</sub></td>
</tr>
</table>

### Analitik

<p align="center"><img src="docs/screenshots/09-analytics.png" alt="Dolu grafik ve kırılımlarla analitik sayfası" width="860"></p>

### Güvenlik Merkezi — baştan sona gerçek bir tarama

<p align="center"><img src="docs/screenshots/10-security-scan.png" alt="Bulgular, DNS ve WHOIS ile tamamlanmış example.com taraması" width="860"></p>

`example.com` üzerinde canlı bir tarama: DNS kayıtları, IP/ASN bilgisi, önem derecesine göre işaretlenmiş eksik güvenlik başlıkları ve hesaplanmış bir 0-100 puan — bir placeholder ekran değil.

### URL Çözümleri — gerçek girdiyle çalıştırılmış her araç

<table>
<tr>
<td width="50%"><img src="docs/screenshots/11-urltools-encoder.png" alt="Gerçek bir sonuçla URL kodlayıcı/çözücü"><br><sub>Kodla / çöz</sub></td>
<td width="50%"><img src="docs/screenshots/12-urltools-utm.png" alt="Gerçek bir sonuçla UTM oluşturucu"><br><sub>UTM oluşturucu</sub></td>
</tr>
<tr>
<td width="50%"><img src="docs/screenshots/13-urltools-analyzer.png" alt="Gerçek bir sonuçla URL analizcisi"><br><sub>URL analizcisi — canlı HTTP isteği, başlık, içerik türü</sub></td>
<td width="50%"><img src="docs/screenshots/14-urltools-redirect.png" alt="Gerçek bir sonuçla yönlendirme zinciri denetleyicisi"><br><sub>Yönlendirme denetleyicisi</sub></td>
</tr>
<tr>
<td colspan="2"><img src="docs/screenshots/15-urltools-qr.png" alt="Gerçek bir bağlantı için üretilmiş QR kod"><br><sub>QR kod oluşturucu — yukarıda oluşturulan bağlantılardan biri için gerçek bir QR</sub></td>
</tr>
</table>

### Platform — API, webhook'lar, bildirimler, cihazlar, ayarlar

<table>
<tr>
<td width="50%"><img src="docs/screenshots/17-platform-api-list.png" alt="Oluşturulmuş bir anahtarla API sayfası"><br><sub>Katmanlı API anahtarları</sub></td>
<td width="50%"><img src="docs/screenshots/18-webhooks-list.png" alt="Oluşturulmuş bir webhook ile webhook'lar sayfası"><br><sub>Webhook'lar — HMAC imzalı, olaya abone</sub></td>
</tr>
<tr>
<td width="50%"><img src="docs/screenshots/19-notifications.png" alt="Gerçek ilk-ziyaret bildirimleriyle bildirimler sayfası"><br><sub>Bildirimler — gerçek "ilk ziyaret" olayları</sub></td>
<td width="50%"><img src="docs/screenshots/20-devices-pairing.png" alt="Canlı QR kod ve kodla cihaz eşleştirme diyaloğu"><br><sub>Cihazlar — bir telefonu eşleştirme (QR + kod, süreli)</sub></td>
</tr>
<tr>
<td colspan="2"><img src="docs/screenshots/21-settings.png" alt="Ayarlar sayfası"><br><sub>Ayarlar</sub></td>
</tr>
</table>

> Cihazlar ekranı eşleştirme adımını gösteriyor — Android companion uygulamasının bağlanmak için taradığı QR kodu / kısa kodu üretme aşaması. Canlı el sıkışmayı tamamlamak ve bir telefonun ekranını yansıtmak, görüntü alınırken eşleştirilmiş fiziksel bir Android cihaz gerektirdiği için burada gösterilmiyor; tam iletişim protokolü [`docs/DEVICE_CONTROL_PROTOCOL.md`](./docs/DEVICE_CONTROL_PROTOCOL.md) içinde eksiksiz belgelenmiştir.

## Mimari

```mermaid
flowchart TB
    NGINX[nginx — reverse proxy]
    FE[Frontend — React + TS + Vite]
    BE[Backend — FastAPI + async SQLAlchemy]
    PG[(PostgreSQL<br/>ana veri deposu)]
    REDIS[(Redis<br/>cache / kuyruk / hız sınırı)]
    WORKER[Arka plan worker'ı<br/>e-postalar, webhook'lar, işler]
    EXT[[Harici entegrasyonlar<br/>IP zekâsı · itibar · e-posta · alan adı zekâsı<br/>hepsi adaptör tabanlı ve mock'lanabilir]]

    NGINX --> FE
    NGINX --> BE
    FE <-- REST API --> BE
    BE --> PG
    BE --> REDIS
    BE --> WORKER
    WORKER --> PG
    WORKER --> REDIS
    BE -.-> EXT
    WORKER -.-> EXT
```

`backend/app/` altındaki backend modülleri:

```text
app/
├── api/v1/          REST uç noktaları (auth, campaigns, links, analytics, tracking,
│                    qr, url_tools, security_center, api_keys, webhooks,
│                    notifications, devices, dashboard)
├── core/            config, DB session, ayarlar
├── models/          SQLAlchemy modelleri
├── schemas/         Pydantic istek/yanıt şemaları
├── services/        iş mantığı (domain başına bir servis)
├── repositories/    veri erişim katmanı
├── middleware/      hız sınırlama, güvenlik başlıkları, hata zarfı
├── security/        auth, RBAC, hash'leme, token'lar
├── analytics/       toplulaştırma mantığı
├── integrations/    sağlayıcı adaptörleri — ip_intelligence/, reputation/, email/, domain_intel/
├── workers/         arka plan iş işleyicileri
└── utils/
```

## Proje yapısı

```text
Aventrix/
├── android/       companion Android istemcisi (cihaz kontrolü)
├── backend/       FastAPI uygulaması + Alembic migration'ları + testler
├── frontend/      React + TypeScript + Vite SPA
├── worker/        arka plan worker Dockerfile/entrypoint
├── nginx/         reverse proxy config (dev + üretim)
├── docker/        yardımcı Docker varlıkları
├── scripts/       dev-setup yardımcıları, DB yedekleme, Let's Encrypt init
├── docs/          SETUP, ARCHITECTURE, DATABASE, API, SECURITY,
│                  ENVIRONMENT, DEPLOYMENT, DEPLOY_VPS, CONTRIBUTING,
│                  DEVICE_CONTROL_PROTOCOL, screenshots/
├── docker-compose.yml       geliştirme yığını
├── docker-compose.prod.yml  üretim yığını
├── LICENSE
└── .env.example   yapılandırılabilir her ortam değişkeni
```

## Teknoloji yığını

**Frontend** — React 18 · TypeScript · Vite · Tailwind CSS · Radix primitifleri · TanStack Query · React Router

**Backend** — Python · FastAPI · Pydantic · SQLAlchemy (async) · Alembic

**Veri** — PostgreSQL · Redis (cache, hız sınırlama, kuyruk)

**Altyapı** — Docker Compose · nginx · özel bir arka plan worker servisi

**Mobil** — Kotlin / Android (companion cihaz-kontrol istemcisi)

## Hızlı başlangıç

**Docker ile (önerilen):**

```bash
cp .env.example .env      # gerekirse secret'ları/URL'leri düzenle
docker compose up
```

Ya da `scripts/dev-setup.ps1` (Windows) / `scripts/dev-setup.sh` (macOS/Linux) çalıştır — senin için `.env` oluşturur ve Docker'ın PATH'te olup olmadığını kontrol eder.

Bu, Postgres, Redis, API'yi, arka plan worker'ını, frontend dev sunucusunu ve nginx'i ayağa kaldırır. Migration'lar ve bir geliştirme admin seed'i backend başlangıcında otomatik çalışır — bir kereliğine yazdırılan admin şifresi için logları izle.

| Servis | URL |
| --- | --- |
| Uygulama (nginx üzerinden) | http://localhost:8080 |
| Frontend doğrudan | http://localhost:5173 |
| API dokümanları (Swagger) | http://localhost:8000/api/docs |

**Docker olmadan:** backend ve frontend'i kendi Postgres/Redis'ine karşı yerelde çalıştırmak için [`docs/SETUP.md`](./docs/SETUP.md) dosyasına bak.

**Android istemcisi:** companion uygulamayı derlemek için [`android/README.md`](./android/README.md) dosyasına bak (`./gradlew assembleDebug`).

## Dokümantasyon

| Doküman | Amaç |
| --- | --- |
| [SETUP.md](./docs/SETUP.md) | Docker ve manuel yerel kurulum |
| [ARCHITECTURE.md](./docs/ARCHITECTURE.md) | Sistem tasarımı, modül yerleşimi, yapılan vs. ertelenen |
| [DATABASE.md](./docs/DATABASE.md) | Şema, indeksler, saklama |
| [API.md](./docs/API.md) | Uç nokta referansı |
| [SECURITY.md](./docs/SECURITY.md) | Tehdit modeli, korumalar, bilinen uyarılar |
| [ENVIRONMENT.md](./docs/ENVIRONMENT.md) | Her ortam değişkeninin açıklaması |
| [DEPLOYMENT.md](./docs/DEPLOYMENT.md) | Üretim dağıtım notları ve kontrol listesi |
| [DEPLOY_VPS.md](./docs/DEPLOY_VPS.md) | Adım adım VPS dağıtımı |
| [DEVICE_CONTROL_PROTOCOL.md](./docs/DEVICE_CONTROL_PROTOCOL.md) | Uzaktan cihaz kontrolü sinyalleşme protokolü |
| [CONTRIBUTING.md](./docs/CONTRIBUTING.md) | Kod stili, test, PR beklentileri |

## Güvenlik ve gizlilik

Bu platform katı bir kurala göre inşa edildi: **gizli veri toplama yok.** Bir ziyaretçinin cihazına ya da verisine dokunan her özellik, sessiz bir varsayılan değil, açık bir onaydan geçer. Somut olarak:

- Ziyaretçi onayı, herhangi bir cihaz/tarayıcı/UTM parmak izi yakalanmadan önce birinci sınıf bir arayüz adımıdır
- Tüm harici entegrasyonlar (IP zekâsı, itibar, e-posta, alan adı zekâsı) adaptör tabanlıdır, ortam değişkenleriyle yapılandırılır ve anahtar tanımlanmadığında bir mock sağlayıcıyla zarifçe geri düşer — uygulama üçüncü taraf bir anahtar eksik diye asla çökmez
- Kullanıcı tarafından sağlanan URL'lerin giden istekleri (bağlantı önizlemeleri, alan adı analizi, yönlendirme kontrolleri) SSRF'ye karşı sertleştirilmiştir: özel IP aralıkları, localhost, iç ağlar ve bulut metadata uç noktaları engellenir; zaman aşımları, yanıt boyutu sınırları ve yönlendirme sınırları zorunlu kılınır
- Yetkilendirme her istekte sunucu tarafında kontrol edilir (RBAC), sadece arayüzde gizlenmez — ID tahmin ederek IDOR yok
- Şifreler, JWT secret'ları ve API anahtarları asla koda gömülmez; secret'lar yalnızca `.env` içinde yaşar (bkz. `.env.example`)

Tam tehdit modeli ve bilinen uyarılar [`docs/SECURITY.md`](./docs/SECURITY.md) içinde.

> **Yalnızca sorumlu kullanım.** Keşif/OSINT ve Güvenlik Merkezi araçları (alt alan adı taraması, DNS/WHOIS/SSL kontrolleri, başlık/itibar analizi) sahibi olduğun ya da açıkça test etmeye yetkili olduğun alan adları ve varlıklar için tasarlanmıştır.

## Testler

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test
```

Testler özelliklerle birlikte yazılır, sonradan eklenmez — auth, bağlantı üretimi, doğrulama, analitik ve IP servisi için birim testleri; veritabanı, API, auth akışı ve yönlendirme sistemi için entegrasyon testleri; IDOR, SSRF ve hız sınırlama için özel güvenlik testleri; frontend'de bileşen/form/navigasyon testleri.

## Yol haritası (henüz yapılmadı)

PDF rapor dışa aktarma · gerçek zamanlı SSE/WebSocket canlı-ziyaretçi paneli · AI kampanya/analitik asistanı · tam admin paneli · çok kullanıcılı çalışma alanları · faturalama/abonelikler · CI/CD pipeline'ı.

Tam yapılan-vs-ertelenen dökümü için [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) dosyasına bak.

## Lisans

[MIT Lisansı](./LICENSE) altında yayınlanmıştır — tam metin için dosyaya bak.
