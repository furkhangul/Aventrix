# 🚀 PROFESYONEL URL INTELLIGENCE & CAMPAIGN PLATFORM — FULL DEVELOPMENT PROMPT

Sen kıdemli bir **Full-Stack Software Architect, Security Engineer, UI/UX Designer, DevOps Engineer, Backend Engineer ve Mobile/Web Developer** olarak hareket edeceksin.

Benim için sıfırdan, production seviyesinde, modern, güvenli, ölçeklenebilir ve profesyonel bir **URL Intelligence & Campaign Management Platform** geliştir.

Bu projeyi basit bir demo olarak değil, gerçek kullanıcıların kullanabileceği ticari bir SaaS ürünü seviyesinde geliştir.

---

# 1. ANA HEDEF

Platformun temel amacı:

Kullanıcının özel URL'ler oluşturabilmesi, bu URL'leri kampanyalarda kullanabilmesi, isteğe bağlı olarak görsellere/linklere bağlayabilmesi ve ziyaretler hakkında **yasal, şeffaf ve izinli şekilde** teknik analizler gerçekleştirebilmesidir.

Temel akış:

```text
Kullanıcı
   ↓
Dashboard
   ↓
Yeni Kampanya
   ↓
Yeni Tracking URL
   ↓
https://domain.com/t/ABC123
   ↓
Kullanıcı linke girer
   ↓
Consent / Bilgilendirme
   ↓
İzin verilen teknik veriler
   ↓
IP Intelligence API
   ↓
Analiz
   ↓
Database
   ↓
Dashboard
```

---

# 2. ÇOK ÖNEMLİ GÜVENLİK VE GİZLİLİK KURALI

Sistemi gizli veri toplama, phishing, credential harvesting veya kullanıcıyı habersiz izleme amacıyla geliştirme.

Kesinlikle:

* Şifre toplama
* Cookie çalma
* Session token toplama
* Authorization header toplama
* Clipboard okuma
* Gizli kamera kullanımı
* Gizli mikrofon kullanımı
* Gizli ekran görüntüsü alma
* Dosya okuma
* Keylogger
* Kullanıcının haberi olmadan GPS alma
* Kullanıcının haberi olmadan kamera görüntüsü alma
* Kullanıcının haberi olmadan kişisel veri toplama

oluşturma.

Kamera veya mikrofon gibi özellikler gerekiyorsa:

```text
Kullanıcı
   ↓
Açık bilgilendirme
   ↓
Tarayıcı permission
   ↓
Kullanıcı "İzin Ver"
   ↓
Özellik aktif
```

şeklinde çalışmalıdır.

---

# 3. ÜRÜNÜN ADI

Geçici proje adı:

# LinkScope

Ancak uygulama içinde daha profesyonel bir isim gerekiyorsa kendin alternatif isimler üret ve en uygun olanı seç.

Logo, favicon, renk sistemi ve marka kimliğini de oluştur.

---

# 4. TEKNOLOJİ STACK

Modern ve production-ready teknolojiler kullan.

Önerilen:

## Frontend

* React
* TypeScript
* Vite
* Tailwind CSS
* shadcn/ui
* React Query / TanStack Query
* React Router
* Recharts
* Framer Motion

## Backend

* Python
* FastAPI
* Pydantic
* SQLAlchemy
* Alembic

## Database

* PostgreSQL

## Cache

* Redis

## Queue

* Celery veya modern async task sistemi

## Authentication

* JWT
* Refresh Token
* Secure HTTP-only Cookie
* Role Based Access Control

## Deployment

* Docker
* Docker Compose
* Nginx
* HTTPS
* Environment Variables

---

# 5. MİMARİ

Modüler ve ölçeklenebilir architecture oluştur.

```text
linkscope/
│
├── frontend/
│
├── backend/
│
├── worker/
│
├── database/
│
├── nginx/
│
├── docker/
│
├── scripts/
│
├── tests/
│
├── docs/
│
├── .env.example
├── docker-compose.yml
├── README.md
└── LICENSE
```

Backend:

```text
backend/
├── app/
│   ├── main.py
│   │
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── repositories/
│   ├── middleware/
│   ├── security/
│   ├── analytics/
│   ├── integrations/
│   ├── workers/
│   └── utils/
│
└── tests/
```

---

# 6. KULLANICI SİSTEMİ

Profesyonel authentication sistemi oluştur.

Özellikler:

* Register
* Login
* Logout
* Forgot password
* Reset password
* Email verification
* Refresh token
* Session management
* Active sessions
* Account deletion
* Profile
* Avatar
* 2FA
* Backup codes
* Login history

Roller:
```text
SUPER_ADMIN
ADMIN
MANAGER
USER
VIEWER
```

RBAC sistemini backend seviyesinde uygula.

Frontend'deki butonları gizlemek yeterli değildir.

Backend her request'te authorization kontrolü yapmalıdır.

---

# 7. DASHBOARD

Ana dashboard son derece modern olmalı.

Göster:

```text
Total Links
Total Visits
Unique Visitors
Today's Visits
Active Campaigns
Conversion Rate
Top Countries
Top Devices
Top Browsers
Top Referrers
```

Grafikler:
* Günlük ziyaret
* Haftalık ziyaret
* Aylık ziyaret
* Ülke dağılımı
* Cihaz dağılımı
* Browser dağılımı
* Operating system
* Referrer
* Campaign performance

Dashboard gerçek zamanlı veya near-real-time güncellenebilir.

---

# 8. URL OLUŞTURMA SİSTEMİ

Kullanıcı:

```text
Campaign Name
Target URL
Custom Alias
Description
Expiration
Tags
```

belirleyebilsin.

Örnek:

```text
https://domain.com/t/8F72KD
```

Custom alias:

```text
https://domain.com/t/summer2026
```

desteklensin.

Kurallar:

* Collision detection
* Reserved words
* URL validation
* HTTPS validation
* Expiration
* Disable/enable
* Password protected links
* Optional consent page
* Custom redirect
* UTM parameters

---
# 9. GÖRSEL KAMPANYA SİSTEMİ

Kullanıcı bir görsel yükleyebilsin.

Örneğin:

```text
image.jpg
```

ve sistem:

```text
[ IMAGE ]
    ↓
Tracking URL
```

oluştursun.

HTML export:

```html
<a href="TRACKING_URL">
    <img src="IMAGE_URL">
</a>
```

üretsin.

Kullanıcı:
* HTML kodunu kopyalayabilsin
* Markdown kodunu kopyalayabilsin
* URL'yi kopyalayabilsin
* QR oluşturabilsin

---

# 10. QR CODE

Her URL için otomatik QR oluştur.

Özellikler:

* PNG
* SVG
* Download
* Logo ekleme
* QR renkleri
* Size
* Error correction

---

# 11. ZİYARET ANALİZİ

Her ziyaret için yalnızca izin verilen ve gerekli teknik bilgileri analiz et.

Örnek:

```text
IP
Country
City
Region
Timezone
ISP
ASN
Organization
Browser
OS
Device
Screen size
Language
Referrer
Timestamp
Campaign
Link
```

IP geolocation sonuçlarının yaklaşık olabileceğini UI'da açıkça belirt.

---

# 12. IP INTELLIGENCE

Backend üzerinden güvenilir bir IP intelligence servisi entegre et.

API sağlayıcısını hard-code etme.

Environment variable kullan:

```env
IP_INTELLIGENCE_API_KEY=
IP_INTELLIGENCE_BASE_URL=
```

API adapter architecture oluştur.

Örneğin:

```text
IPService
   ↓
ProviderAdapter
   ↓
IP Intelligence Provider
```

Böylece sağlayıcı daha sonra kolayca değiştirilebilsin.

---

# 13. IP SONUÇ EKRANI

Sonuç ekranı:

```text
IP ADDRESS
185.xxx.xxx.xxx

LOCATION
Türkiye
İstanbul

NETWORK
ISP:
Example ISP

ASN:
AS12345

SECURITY
VPN:
Unknown

Proxy:
No

Tor:
No

Hosting:
No
```

Harita gösterimi yalnızca yaklaşık IP geolocation bilgisini temsil etsin.

Harita üzerinde:

```text
Approximate Location
```

ifadesi kullan.

Kesin fiziksel adres iddiasında bulunma.

---

# 14. HARİTA

Leaflet veya MapLibre kullan.

Göster:

* Country
* Region
* City
* Approximate coordinates

Ancak koordinatların IP geolocation tahmini olduğu açıkça belirtilsin.

---

# 15. VISITOR ANALYTICS

Ziyaretçileri analiz et.

Dashboard:

```text
Visitors
├── New
├── Returning
├── Device
├── Browser
├── OS
├── Country
├── Region
└── Language
```

Privacy-preserving yaklaşım kullan.

Gereksiz kişisel veri saklama.

---

# 16. CAMPAIGN SYSTEM

Kullanıcı:

```text
Campaign
   ├── Links
   ├── QR Codes
   ├── Images
   ├── Analytics
   └── Reports
```

oluşturabilsin.

Campaign detayında:

```text
Total Clicks
Unique Visitors
CTR
Top Country
Top Device
Top Browser
Time Line
```

göster.

---

# 17. UTM BUILDER

Kullanıcı:

```text
utm_source
utm_medium
utm_campaign
utm_term
utm_content
```

alanlarını doldurabilsin.

Sistem otomatik URL oluştursun.

Örnek:

```text
https://example.com
?
utm_source=instagram
&utm_medium=social
&utm_campaign=summer
```

---

# 18. LINK PREVIEW

URL oluşturulurken:

* Title
* Description
* Favicon
* Preview image

mümkünse güvenli şekilde alınsın.

SSRF saldırılarına karşı koruma uygula.

Kullanıcı tarafından verilen URL'yi backend'den fetch ederken:

* Private IP ranges engelle
* localhost engelle
* Internal network engelle
* Cloud metadata endpoint engelle
* DNS rebinding koruması
* Timeout
* Maximum response size
* Redirect limit

uygula.

---

# 19. SECURITY CENTER

Ayrı Security Center oluştur.

Göster:

```text
Security Score
SSL
Headers
Domain reputation
URL reputation
Redirect chain
Suspicious indicators
```

Kullanıcı kendi domainlerini analiz edebilsin.

---

# 20. URL REPUTATION

Güvenilir URL reputation servisleri için adapter sistemi oluştur.

Örneğin:

```text
ReputationService
├── Provider A
├── Provider B
└── Provider C
```

API key'leri:

```env
REPUTATION_API_KEY=
```

şeklinde environment üzerinden yönet.

---

# 21. API MANAGEMENT

Kullanıcılar API key oluşturabilsin.

```text
API Keys
├── Create
├── Revoke
├── Rotate
└── Usage
```

Rate limits:

```text
Free
100 requests/day

Pro
10,000 requests/day

Business
100,000 requests/day
```

değerlerini configurable yap.

---

# 22. WEBHOOK

Webhook sistemi oluştur.

Events:

```text
link.created
link.clicked
campaign.created
campaign.completed
security.alert
```

Webhook retry sistemi ekle.

HMAC signature kullan.

---

# 23. EXPORT

Kullanıcı:

* CSV
* JSON
* PDF

rapor export edebilsin.

Rapor:

```text
Campaign
Date range
Total visits
Unique visitors
Countries
Devices
Browsers
Operating systems
Referrers
```

içersin.

---

# 24. REAL-TIME

WebSocket veya Server-Sent Events kullan.

Dashboard'da:

```text
Live Visitors
```

bölümü oluştur.

Yeni ziyaret geldiğinde UI güncellensin.

---

# 25. NOTIFICATION SYSTEM

Bildirim merkezi oluştur.

Örneğin:

```text
🔔 New campaign visit
🔔 Link expired
⚠ Suspicious traffic
⚠ Reputation warning
```

Email notification altyapısı ekle.

---

# 26. ADMIN PANEL

Admin:

```text
Users
Campaigns
Links
Visits
Reports
API usage
Security events
System logs
Abuse reports
```

görebilsin.

Admin action log oluştur.

---

# 27. AUDIT LOG

Önemli işlemleri kaydet:

```text
User
Action
IP
Timestamp
Resource
Result
```

Örneğin:

```text
USER_CREATED
LOGIN_SUCCESS
LOGIN_FAILED
LINK_CREATED
LINK_DELETED
API_KEY_CREATED
CAMPAIGN_CREATED
ADMIN_ACTION
```

---

# 28. RATE LIMITING

Aşağıdaki endpoint'lere rate limit uygula:

```text
/login
/register
/password-reset
/link-create
/analytics
/api/*
```

Redis kullan.

IP + user + API key bazlı limitler uygulanabilsin.

---

# 29. SECURITY

Aşağıdaki saldırılara karşı koruma ekle:

```text
SQL Injection
XSS
CSRF
SSRF
Open Redirect
Path Traversal
Command Injection
Brute Force
Credential Stuffing
Rate Limit Bypass
JWT Abuse
IDOR
Broken Access Control
Mass Assignment
```

OWASP standartlarını takip et.

---

# 30. IDOR KORUMASI

Örneğin:

```text
/api/campaigns/15
```

isteği yapan kullanıcının gerçekten campaign 15'e erişim hakkı olup olmadığını backend kontrol etsin.

Sadece ID tahmin ederek başka kullanıcının verisine ulaşılmamalı.

---

# 31. INPUT VALIDATION

Tüm kullanıcı girdilerini validate et.

Özellikle:

```text
URL
Email
Alias
Campaign name
Description
Tags
API parameters
```

Whitelist yaklaşımını mümkün olduğunca kullan.

---

# 32. DATABASE

Tablolar:

```text
users
sessions
roles
permissions
campaigns
links
visits
ip_intelligence
analytics_events
api_keys
webhooks
webhook_deliveries
notifications
audit_logs
security_events
reports
subscriptions
```

Foreign key ve indexleri doğru tasarla.

---

# 33. DATABASE INDEX

Özellikle:

```text
links.short_code
links.user_id
visits.link_id
visits.created_at
visits.ip_hash
campaigns.user_id
audit_logs.user_id
```

alanlarını sorgu kullanımına göre indexle.

---

# 34. PRIVACY

Minimum data principle uygula.

Hassas verileri gereksiz yere saklama.

IP adreslerini mümkünse:

* kısa süreli ham veri
* hash/anonymization
* retention policy

ile yönet.

Kullanıcıya:

```text
Privacy Settings
Data Retention
Delete Data
Export Data
Consent Records
```

sun.

---

# 35. COOKIE

Gereksiz tracking cookie kullanma.

Session cookie:

```text
HttpOnly
Secure
SameSite
```

özelliklerine sahip olsun.

---

# 36. HTTPS

Production ortamında HTTPS zorunlu.

HTTP:

```text
301 → HTTPS
```

redirect.

---

# 37. SECRET MANAGEMENT

Asla kod içine:

```text
API KEY
JWT SECRET
DATABASE PASSWORD
SMTP PASSWORD
```

yazma.

Sadece:

```env
.env
```

kullan.

`.env` Git'e gönderilmesin.

`.env.example` oluştur.

---

# 38. API INTEGRATION MANAGER

Bütün harici API'leri tek yerde yönet:

```text
integrations/
├── ip_intelligence/
├── reputation/
├── email/
├── maps/
├── qr/
└── analytics/
```

Her provider için interface oluştur.

---

# 39. API KONFİGÜRASYONU

Ben sana tek tek API sormadan önce sistemi provider abstraction ile oluştur.

Örneğin:

```env
IP_PROVIDER=
IP_API_KEY=

MAP_PROVIDER=
MAP_API_KEY=

REPUTATION_PROVIDER=
REPUTATION_API_KEY=

EMAIL_PROVIDER=
EMAIL_API_KEY=
```

Eksik API key varsa uygulama crash olmamalı.

UI'da:

```text
Integration not configured
```

göstermeli.

---

# 40. FALLBACK SYSTEM

Harici API çalışmıyorsa:

```text
Provider A
   ↓ fail
Provider B
   ↓ fail
Local fallback
```

uygula.

API timeout:

```text
5-10 seconds
```

civarında configurable olsun.

Retry mekanizması ekle.

---

# 41. RESPONSIVE DESIGN

Platform:

```text
Desktop
Laptop
Tablet
Mobile
```

üzerinde kusursuz çalışmalı.

---

# 42. UI/UX

Tasarım:

* Modern
* Minimal
* Premium
* Profesyonel
* Hızlı
* Kullanışlı

olsun.

Dark mode + Light mode ekle.

Sidebar:

```text
Dashboard
Campaigns
Links
Analytics
QR Codes
URL Tools
Security
Reports
API
Webhooks
Notifications
Settings
```

---

# 43. URL TOOLS

Platformu yalnızca tracking sistemi yapma.

Aşağıdaki araçları da ekle:

```text
URL Shortener
UTM Builder
QR Generator
URL Analyzer
Redirect Checker
URL Encoder/Decoder
Domain Analyzer
Link Preview
Campaign Builder
```

---

# 44. DOMAIN ANALYZER

Kullanıcı bir domain girsin.

Sistem mümkün olan güvenli ve halka açık bilgileri analiz etsin:

```text
Domain
Registrar information
DNS records
Nameservers
SSL information
Expiration
Basic security headers
```

Rate limit uygula.

---

# 45. SECURITY HEADERS ANALYZER

Domain için:

```text
CSP
HSTS
X-Frame-Options
X-Content-Type-Options
Referrer-Policy
Permissions-Policy
```

kontrol edilsin.

Security score oluştur.

---

# 46. LINK HEALTH MONITOR

Kullanıcı linklerini düzenli kontrol ettirebilsin.

```text
200 OK
301
302
404
500
Timeout
SSL Error
```

durumlarını takip et.

Link bozulduğunda notification gönder.

---

# 47. SCHEDULED TASKS

Background worker kullan.

Örneğin:

```text
Every 5 minutes
Every hour
Every day
```

gibi scheduled jobs destekle.

---

# 48. PERFORMANCE

Hedefler:

```text
Fast first load
Lazy loading
Code splitting
Database indexing
Caching
Compression
Pagination
Background processing
```

Büyük analytics sorgularını request sırasında çalıştırma.

Worker/background job kullan.

---

# 49. PAGINATION

Tüm büyük listelerde pagination:

```text
Users
Links
Visits
Logs
Reports
API usage
```

uygula.

---

# 50. SEARCH

Global search oluştur.

Aranabilecekler:

```text
Campaign
Link
User
Domain
IP
Event
```

---

# 51. FILTER

Analytics filtreleri:

```text
Date
Country
Device
Browser
OS
Campaign
Link
```

---

# 52. DATE RANGE

Destekle:

```text
Today
Yesterday
7 Days
30 Days
90 Days
Custom
```

---

# 53. ACCESSIBILITY

WCAG prensiplerini mümkün olduğunca uygula.

* Keyboard navigation
* Screen reader
* Focus states
* ARIA labels
* Contrast
* Error messages

---

# 54. ERROR HANDLING

Frontend'de:

```text
Loading
Empty
Error
Success
Retry
```

durumlarının tamamını tasarla.

Backend:

```text
400
401
403
404
409
422
429
500
503
```

için standart response formatı oluştur.

---

# 55. LOGGING

Structured logging kullan.

Örneğin:

```json
{
  "timestamp": "...",
  "level": "INFO",
  "service": "analytics",
  "event": "visit_created"
}
```

Şifre ve secret değerleri loglama.

---

# 56. MONITORING

Production için:

```text
Health check
Database health
Redis health
API health
Worker health
```

endpointleri oluştur.

Örneğin:

```text
/health
/ready
```

---

# 57. TESTLER

Testleri sonradan ekleme.

Geliştirme sırasında oluştur.

## Unit

* Auth
* URL generator
* Validation
* Analytics
* IP service

## Integration

* Database
* API
* Authentication
* Link redirect

## Security

* IDOR
* SSRF
* XSS
* SQL injection
* Rate limiting
* JWT

## Frontend

* Component tests
* Form tests
* Navigation
* Error states

---

# 58. DOCKER

Development ortamını:

```bash
docker compose up
```

ile çalıştırabilecek hale getir.

Servisler:

```text
frontend
backend
postgres
redis
worker
nginx
```

---

# 59. CI/CD

GitHub Actions oluştur.

Pipeline:

```text
Push
 ↓
Lint
 ↓
Type Check
 ↓
Unit Tests
 ↓
Security Scan
 ↓
Build
 ↓
Docker Build
```

---

# 60. DOCUMENTATION

Otomatik olarak:

```text
README.md
SETUP.md
API.md
SECURITY.md
ARCHITECTURE.md
DATABASE.md
DEPLOYMENT.md
ENVIRONMENT.md
CONTRIBUTING.md
```

oluştur.

---

# 61. API DOCUMENTATION

FastAPI Swagger/OpenAPI kullan.

Endpointleri:

```text
/api/v1/...
```

şeklinde versionla.

---

# 62. FRONTEND STATE MANAGEMENT

Server state için:

```text
TanStack Query
```

kullan.

Gereksiz global state oluşturma.

---

# 63. COMPONENT SYSTEM

Reusable componentler oluştur:

```text
Button
Modal
Dialog
Input
Select
Table
Chart
Card
Badge
Toast
Tooltip
Dropdown
Sidebar
Navbar
DatePicker
Pagination
EmptyState
LoadingState
ErrorState
```

---

# 64. PREMIUM DASHBOARD

Dashboard'u hazır template gibi göstermemeli.

Modern SaaS ürünlerinden ilham alan ama özgün tasarım oluştur.

Örneğin:

```text
┌─────────────────────────────────────────────┐
│ Welcome back                    🔔 👤       │
├──────────────┬──────────────────────────────┤
│              │                              │
│ Dashboard    │ Total Visitors              │
│ Campaigns    │ 12,421                       │
│ Links        │ ↑ 18.4%                      │
│ Analytics    │                              │
│ Security     │ ┌────────────────────────┐   │
│ Reports      │ │                        │   │
│ API          │ │      GRAPH             │   │
│ Settings     │ │                        │   │
│              │ └────────────────────────┘   │
└──────────────┴──────────────────────────────┘
```

---

# 65. ONBOARDING

İlk girişte:

```text
Welcome
 ↓
Create workspace
 ↓
Create first campaign
 ↓
Create first link
 ↓
Generate QR
 ↓
Open analytics
```

şeklinde onboarding oluştur.

---

# 66. WORKSPACE

Kullanıcılar workspace oluşturabilsin.

```text
Workspace
├── Members
├── Campaigns
├── Links
├── Analytics
└── Settings
```

Üyeler:

```text
Owner
Admin
Editor
Viewer
```

---

# 67. TEAM COLLABORATION

Invite sistemi:

```text
Invite member
Remove member
Change role
```

---

# 68. BILLING ARCHITECTURE

Gerçek ödeme entegrasyonunu hemen zorunlu yapma.

Ancak altyapıyı subscription-ready oluştur:

```text
Free
Pro
Business
Enterprise
```

Feature limits backend'den kontrol edilsin.

---

# 69. FEATURE FLAGS

Feature flag sistemi ekle.

Örneğin:

```text
ENABLE_QR
ENABLE_WEBHOOK
ENABLE_REALTIME
ENABLE_DOMAIN_ANALYZER
```

---

# 70. SECURITY-FIRST REDIRECT

Tracking URL redirect mekanizması çok dikkatli tasarlanmalı.

Open redirect oluşturma.

Yalnızca sistem tarafından doğrulanmış hedef URL'lere redirect yapılmalı.

---

# 71. CONSENT PAGE

İsteğe bağlı olarak URL sahibi:

```text
Require consent
```

seçebilsin.

Consent ekranı:

```text
Bu bağlantı ziyaret sırasında bazı teknik
bilgileri analiz amacıyla işleyebilir.

Devam etmek için seçiminizi yapın.

[ Kabul Et ]
[ Reddet ]
```

olsun.

Reddeden kullanıcı için gerekli olmayan telemetry gönderilmesin.

---

# 72. KAMERA / MEDYA ÖZELLİĞİ

Platform ileride kullanıcıdan kamera görüntüsü almak isterse:

ASLA otomatik/gizli kamera kullanma.

Bunun yerine:

```text
Camera Feature
      ↓
Explanation
      ↓
Browser Permission
      ↓
User Approval
      ↓
Camera
```

akışını kullan.

Kullanıcı izin vermezse uygulama normal şekilde çalışmaya devam etsin.

---

# 73. AI FEATURES

Platforma AI katmanı ekle.

Örneğin:

### AI Campaign Assistant

Kullanıcı:

```text
Instagram kampanyası oluşturacağım.
```

dediğinde AI:

* Campaign önerisi
* UTM önerisi
* Link isimlendirme
* QR önerisi
* Analytics önerisi

oluştursun.

### AI Analytics Assistant

Kullanıcı:

```text
Son 30 günde ne oldu?
```

dediğinde dashboard verilerini analiz ederek açıklasın.

AI hiçbir şekilde gizli kişisel veri çıkarımı yapmasın.

---

# 74. SMART INSIGHTS

Dashboard otomatik olarak:

```text
📈 Traffic increased 24%

🌍 Türkiye traffic is dominant.

📱 Most visitors are using mobile.

⚠ One campaign has unusual traffic.

🔗 One link has increased error rate.
```

gibi açıklamalar üretsin.

---

# 75. ANOMALY DETECTION

Şüpheli trafik için:

```text
Sudden traffic spike
Unusual country distribution
Repeated requests
Bot-like behavior
High-frequency requests
```

tespit etmeye yönelik sistem oluştur.

Yanlış pozitiflerin mümkün olduğunu belirt.

---

# 76. BOT DETECTION

Temel bot detection ekle.

Ama ziyaretçileri saldırgan olarak etiketlemeden önce:

```text
Likely bot
Possible bot
Likely human
Unknown
```

gibi confidence seviyeleri kullan.

---

# 77. PRIVACY-FRIENDLY ANALYTICS

Analytics'i mümkün olduğunca:

```text
Aggregated
Anonymized
Minimal
Purpose-limited
```

tasarla.

---

# 78. DATA RETENTION

Admin ayarlayabilsin:

```text
7 days
30 days
90 days
180 days
Custom
```

süre sonunda eski analytics verileri otomatik silinsin/anonymize edilsin.

---

# 79. DATABASE BACKUP

Backup sistemi için architecture oluştur.

```text
Daily Backup
Weekly Backup
Retention
Restore Procedure
```

dokümante et.

---

# 80. DEPLOYMENT

Production deployment için:

```text
Cloud VPS
Docker
Nginx
HTTPS
PostgreSQL
Redis
Worker
```

yapısını hazırla.

---

# 81. DEVELOPMENT MANTIĞI

Çok önemli:

Ben sana her ayrıntıyı tek tek söylemeyeceğim.

Sen:

1. Eksik gereksinimleri kendin tespit et.
2. Güvenlik açıklarını kendin düşün.
3. UX problemlerini kendin tespit et.
4. Performans problemlerini önceden düşün.
5. Ölçeklenebilirliği düşün.
6. Production deployment'ı düşün.
7. Kullanıcı deneyimini iyileştirecek özellikleri kendin öner.
8. Gereksiz özellik ekleme.
9. Bir özellik eklerken güvenlik ve privacy etkisini kontrol et.

---

# 82. KOD YAZMA KURALLARI

Kod:

* Clean Code
* SOLID
* DRY
* KISS
* Type-safe
* Modular
* Testable

olmalı.

Tek dosyada devasa kod oluşturma.

---

# 83. GELİŞTİRME SIRASI

Projeyi aşağıdaki sırayla geliştir:

```text
PHASE 1
Architecture

PHASE 2
Database

PHASE 3
Authentication

PHASE 4
Dashboard

PHASE 5
URL System

PHASE 6
Redirect System

PHASE 7
Consent

PHASE 8
Analytics

PHASE 9
IP Intelligence

PHASE 10
Campaigns

PHASE 11
QR

PHASE 12
URL Tools

PHASE 13
Security Center

PHASE 14
API

PHASE 15
Webhooks

PHASE 16
Reports

PHASE 17
Realtime

PHASE 18
AI

PHASE 19
Admin

PHASE 20
Testing

PHASE 21
Docker

PHASE 22
CI/CD

PHASE 23
Production Hardening
```

---

# 84. HER PHASE SONRASI

Her phase tamamlandığında:

```text
✓ Code
✓ Tests
✓ Security check
✓ Error handling
✓ Documentation
```

kontrolü yap.

Bir sonraki phase'e geçmeden önce mevcut sistemin bozulmadığını doğrula.

---

# 85. HATA YÖNETİMİ

Bir hata aldığında:

1. Hatanın sebebini bul.
2. Kök sebebi düzelt.
3. Geçici workaround kullanma.
4. Test ekle.
5. Aynı hatanın tekrar oluşmasını engelle.

---

# 86. API KEY EKSİKSE

API key yok diye:

```text
Uygulamayı durdurma.
```

Bunun yerine:

```text
Integration unavailable
```

durumunu göster.

Mock/development provider oluştur.

---

# 87. MOCK MODE

Development ortamında gerçek API olmadan çalışabilmesi için:

```env
APP_ENV=development
USE_MOCK_PROVIDERS=true
```

destekle.

---

# 88. PRODUCTION CHECKLIST

Deploy öncesinde:

```text
[ ] HTTPS
[ ] Secrets secured
[ ] Database backup
[ ] Rate limiting
[ ] CORS configured
[ ] Security headers
[ ] JWT security
[ ] Password hashing
[ ] SSRF protection
[ ] XSS protection
[ ] CSRF protection
[ ] SQL injection protection
[ ] IDOR protection
[ ] Logging
[ ] Monitoring
[ ] Error handling
[ ] Privacy settings
[ ] Data retention
[ ] API limits
[ ] Docker security
```

kontrol et.

---

# 89. BENİM SORMAMI BEKLEME

Eksik gördüğün özellikleri kendin tespit et.

Örneğin:

* Search
* Filtering
* Pagination
* Export
* Notifications
* Audit logs
* Backup
* Monitoring
* Error tracking
* Feature flags
* API versioning
* Workspace
* Roles
* Permissions
* Rate limiting
* Caching
* Queue
* Background workers

gibi ihtiyaçları ben söylemeden sisteme dahil et.

Ancak özellik eklerken:

```text
Useful?
Secure?
Privacy-friendly?
Maintainable?
Scalable?
```

kontrolü yap.

---

# 90. SON HEDEF

Ortaya çıkan sistem şu seviyede olmalı:

```text
                 LINK SCOPE
                      │
       ┌──────────────┼──────────────┐
       │              │              │
     LINKS        CAMPAIGNS       QR CODES
       │              │              │
       └──────────────┼──────────────┘
                      │
                 ANALYTICS
                      │
        ┌─────────────┼─────────────┐
        │             │             │
       IP          DEVICE        LOCATION
   INTELLIGENCE    ANALYSIS       DATA
        │             │             │
        └─────────────┼─────────────┘
                      │
                 SECURITY
                      │
        ┌─────────────┼─────────────┐
        │             │             │
      DOMAIN       URL CHECK       HEADERS
      ANALYZER
        │             │             │
        └─────────────┼─────────────┘
                      │
                    AI
                      │
             SMART INSIGHTS
```

Amaç yalnızca "IP gösteren site" yapmak değil;

**URL yönetimi + kampanya yönetimi + analytics + IP intelligence + QR + güvenlik analizleri + raporlama + API + AI destekli analiz** özelliklerini tek bir modern platformda birleştirmektir.

---

# 91. SON TALİMAT

Projeyi baştan sona kendin analiz et.

Bana sürekli:

> "Bunu da yapayım mı?"

diye sorma.

Gereksinimlerden mantıklı şekilde çıkarılabilecek özellikleri kendin ekle.

Ancak **dış servis gerektiren işlemlerde gerçek API anahtarlarını uydurma.** Bunun yerine:

```text
.env.example
Mock provider
Provider adapter
Configuration screen
```

oluştur.

Gerçek API anahtarı gerekiyorsa sistem bunu sonradan ekleyebileceğim şekilde hazır olsun.

Benim bilgisayarımda çalıştırabileceğim şekilde:

```bash
docker compose up
```

ile ayağa kalkabilen bir development ortamı oluştur.

İlk açılışta gerekli database migrationlarını ve seed işlemlerini çalıştır.

Default admin hesabı için güvenli bir development seed mekanizması oluştur ve production'da varsayılan credential bırakma.

Her aşamada önce mevcut kodu analiz et, sonra değişiklik yap.

Mevcut çalışan özellikleri bozma.

Bir özelliği tamamlanmış kabul etmeden:

```text
Implementation
+
Testing
+
Security
+
Error handling
+
Documentation
```

kontrolünü tamamla.

**Sonuç: production'a mümkün olduğunca yakın, modern, hızlı, güvenli, responsive, modüler ve genişletilebilir profesyonel bir SaaS platformu oluştur.**
