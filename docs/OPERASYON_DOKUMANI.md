# Operasyon Dökümanı — Restoran Yönetim Sistemi
**Versiyon 1.14.0 · Sprint 1-34 (Final)**

---

## 1. Sistem Gereksinimleri

| Bileşen | Minimum | Önerilen |
|---------|---------|----------|
| Docker | 24+ | 25+ |
| Docker Compose | 2.x | 2.24+ |
| RAM | 4 GB | 8 GB |
| Disk | 10 GB | 20 GB |
| İşletim Sistemi | Ubuntu 22.04 | Ubuntu 24.04 |

---

## 2. İlk Kurulum

### 2.1 ZIP'ten Kurulum

```bash
unzip restoran-saas-1.14.0.zip
cd restoran-saas
cp .env.example .env
# .env dosyasını düzenle (aşağıya bakın)
sudo docker compose up -d --build
sleep 60
./scripts/test.sh
```

### 2.2 Setup Wizard

İlk kurulumdan sonra tarayıcıda `http://localhost` adresine gidin. Sistem otomatik olarak `/setup` sayfasına yönlendirir. Setup Wizard 6 adımda kurulumu tamamlar:

1. **DB Kontrolü:** PostgreSQL, MongoDB, Redis bağlantı testi
2. **Superadmin:** İlk yönetici hesabı oluşturma
3. **Entegrasyonlar:** Twilio, Stripe, AI servisleri yapılandırma
4. **Tenant:** İlk restoran oluşturma
5. **Özet:** Tüm ayarları gözden geçirme
6. **Tamamla:** Dashboard'a yönlendirme

### 2.3 Zorunlu .env Değişkenleri

```bash
JWT_SECRET=<64 karakter hex — aşağıdaki komutla üret>
# node -e "require('crypto').randomBytes(64).toString('hex')"

POSTGRES_PASSWORD=GüçlüŞifre2026!
REDIS_PASSWORD=GüçlüŞifre2026!
MONGO_PASSWORD=GüçlüŞifre2026!
INTERNAL_SERVICE_KEY=internal_restoran_2026
APP_URL=http://localhost
BACKUP_ENCRYPTION_KEY=<64 karakter hex — yedek şifreleme anahtarı>
```

### 2.4 Opsiyonel .env Değişkenleri

```bash
# SMS + Sesli Arama
TWILIO_ACCOUNT_SID=ACxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx

# AI Özellikleri
ANTHROPIC_API_KEY=sk-ant-xxxx
OPENAI_API_KEY=sk-xxxx
ELEVENLABS_API_KEY=xxxx
ELEVENLABS_VOICE_ID=xxxx

# Ödeme
STRIPE_SECRET_KEY=sk_test_xxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxx

# Sesli Ajan Webhook (ngrok veya gerçek domain)
PUBLIC_HOST=xxxx.ngrok.io

# Yedek Şifreleme
BACKUP_ENCRYPTION_KEY=<64 karakter hex>
```

---

## 3. Servis Yönetimi

### 3.1 Temel Komutlar

```bash
# Tüm servisleri başlat
sudo docker compose up -d

# Tüm servisleri durdur (veri korunur)
sudo docker compose down

# Tüm servisleri sıfırla (VERİ SİLİNİR)
sudo docker compose down -v

# Tek servis yeniden başlat
sudo docker compose restart auth-service

# Tüm logları izle
sudo docker compose logs -f

# Tek servis logu
sudo docker compose logs --tail=50 auth-service

# Servis durumu
sudo docker compose ps
```

### 3.2 Servis Listesi

| Servis | Port | Teknoloji | Görev |
|--------|------|-----------|-------|
| auth-service | 3006 | Node.js 22 + Prisma | Auth, tenant, kullanıcı, davet |
| reservation-service | 3001 | Node.js 22 + Prisma | Rezervasyon, arayan profili |
| floor-plan-service | 3002 | Node.js 22 + Mongoose | Salon planı |
| staff-service | 3003 | Node.js 22 + Prisma | Personel |
| notification-service | 3004 | Node.js 22 + Bull | SMS, sesli arama |
| analytics-service | 3005 | Python 3.13 + FastAPI | Analitik, ısı haritası |
| voice-agent-service | 3007 | Python 3.13 + FastAPI | AI sesli ajan |
| menu-service | 3008 | Node.js 22 + Prisma | Menü, kategoriler, dijital sipariş |
| nginx | 80/443 | nginx:alpine | Gateway, rate limiting |
| postgres | 5432 | PostgreSQL 16 | Ana veritabanı |
| timescale | 5433 | TimescaleDB | Zaman serisi analitik |
| mongo | 27017 | MongoDB 7 | Salon planları |
| redis | 6379 | Redis 7 | Cache, queue |

### 3.3 Yeni Sprint ZIP ile Güncelleme

```bash
# .env'i yedekle
cp .env /tmp/.env.backup

# Yeni ZIP'i aç
unzip -o restoran-saas-1.14.0.zip

# .env'i geri yükle
cp /tmp/.env.backup .env

# Temiz yeniden kurulum
sudo docker compose down -v
sudo docker compose up -d --build
sleep 60
./scripts/test.sh
```

---

## 4. Yedekleme

### 4.1 Manuel Yedekleme

```bash
./scripts/backup.sh
```

Yedekler `/var/backups/restoran-saas/` klasörüne kaydedilir. Tüm yedekler **AES-256** şifreleme ile korunur. Şifreleme anahtarı `.env` dosyasındaki `BACKUP_ENCRYPTION_KEY` değişkeninde tanımlanır.

### 4.2 Otomatik Yedekleme (Cron)

```bash
# Her gün saat 03:00'te
0 3 * * * /path/to/restoran-saas/scripts/backup.sh >> /var/log/restoran-backup.log 2>&1
```

### 4.3 Manuel DB Yedekleme

```bash
# PostgreSQL
sudo docker compose exec postgres pg_dump -U restoran restoran > backup_$(date +%Y%m%d).sql

# MongoDB
sudo docker compose exec mongo mongodump --out /data/backup
```

---

## 5. Superadmin Kurulumu

### 5.1 Seed Script ile

```bash
./scripts/seed-superadmin.sh superadmin@restoran.app SuperAdmin2026!
```

### 5.2 Manuel SQL ile

```bash
sudo docker compose exec postgres psql -U restoran -d restoran -c \
  "UPDATE users SET role='SUPERADMIN' WHERE email='owner@test.com';"
```

Değişikliği aktif etmek için yeniden giriş yapılması gerekir.

---

## 6. Rate Limiting

| Zone | Limit | Hedef |
|------|-------|-------|
| auth | 30 istek/dakika | Giriş denemesi |
| api | 1200 istek/dakika | Genel API |
| webhook | 120 istek/dakika | Twilio webhook |

### Rate Limit Sıfırlama

```bash
sudo docker compose restart nginx        # nginx limiti sıfırla
sudo docker compose restart auth-service # auth limiti sıfırla
```

---

## 7. Sorun Giderme

| Hata | Olası Sebep | Çözüm |
|------|-------------|-------|
| 502 Bad Gateway | Servis çökmüş | docker compose logs \<servis\> |
| 429 Too Many Requests | Rate limit doldu | nginx veya auth-service restart |
| Token alınamadı | JWT_SECRET eksik | .env kontrol et |
| Tablo bulunamadı | DB init çalışmamış | down -v && up --build |
| python-multipart hatası | Voice agent paketi eksik | docker exec voice pip install python-multipart |
| Analytics 500 | reportlab/font sorunu | analytics-service loglarına bak |
| SMS gitmiyor | Twilio yapılandırılmamış | docs/TWILIO_KURULUM.md |

---

## 8. Performans İzleme

```bash
# CPU ve bellek kullanımı
sudo docker stats

# Sistem sağlığı (API)
curl http://localhost/api/v1/admin/health | python3 -m json.tool

# PostgreSQL aktif bağlantılar
sudo docker compose exec postgres psql -U restoran -d restoran -c \
  "SELECT count(*) FROM pg_stat_activity;"
```

---

## 8.5. Production TLS Kurulumu (ZORUNLU)

Production'a cikmadan once TLS **zorunlu** olarak aktif edilmelidir:

1. SSL sertifikasi al: `sudo certbot --nginx -d yourdomain.com`
2. `nginx/conf.d/default.conf` dosyasinda:
   - Port 80 bloguna `return 301 https://$host$request_uri;` ekle
   - Port 443 SSL blogunu yorum satirindan cikar
3. `sudo docker compose restart nginx`
4. Dogrula: `curl -I http://domain` -> 301 redirect
5. Dogrula: `curl -I https://domain` -> HSTS basligi mevcut

TLS olmadan HSTS basligi islevsizdir. HTTP uzerinden production kullanimi **kesinlikle yasaktir**.

---

## 9. Güvenlik

- Tüm servisler Docker ağı içinde izole
- Nginx HTTPS için SSL sertifikası eklenebilir (Let's Encrypt)
- JWT: 15 dakika access token + 7 gün refresh token, Redis'te blacklist
- Şifreler bcrypt(12) ile hash'lenir
- CORS sadece tanımlı origin'lere izin verir
- Rate limiting brute-force koruması sağlar
- Yedekler AES-256 şifreleme ile korunur

---

## 10. Test

```bash
# 356 API testi (Sprint 1-34)
./scripts/test.sh

# Belirli test grubu
./scripts/test.sh 2>/dev/null | grep -E "Test [0-9]+"

# E2E testler (Playwright)
cd tests/e2e && npx playwright test

# UI testleri
cat scripts/ui-test-senaryolari.sh
```

---

## 11. Sprint S22.1-S31 Operasyon Notlari

### S22.1 — Setup Wizard
- Ilk kurulumda otomatik /setup sayfasi
- 6 adim: DB kontrolu → Superadmin → Entegrasyonlar → Tenant → Ozet → Tamamla
- Tamamlandiktan sonra tekrar gorunmez
- Manuel kurulum icin seed scriptleri hala kullanilabilir

### S22.5 — Compliance (IYS/KVKK/BTK/TCPA/ADA)
- IYS entegrasyonu: SMS/WhatsApp gonderim oncesi onay kontrolu
- KVKK: kullanici veri silme/anonimlesirme, onay kaydi
- BTK: sesli aramalarda yapay zeka bildirimi
- TCPA: 9'a basarak arama sonlandirma, AI kendini tanitiyor
- ADA: SLOW_SPEECH_MODE ile TTS hizi azaltma
- **Env var:** `IYS_API_KEY`, `OUTBOUND_CALLER_ID`, `SLOW_SPEECH_MODE`

### S22.8 — Guvenlik Guncellemeleri
- Oturum yonetimi: "Tum Cihazlarda Cikis Yap" butonu
- KVKK "Verilerimi Sil" butonu ile kullanici veri silme talebi
- Access token suresi 15 dakikaya dusuruldu (onceki: 7 gun)
- Refresh token: 7 gun gecerli
- Impersonation loglama iyilestirmeleri

### S23 — Superadmin Config UI + API Key Merkezi
- AES-256 sifrelenmis API key depolama (app_configs tablosu)
- Impersonation: superadmin tenant hesabina gecici giris (1 saat JWT)
- PlanConfig: DB tabanli plan limitleri ve fiyatlandirma
- MRR dashboard, sesli arama dashboard
- **Env var:** `CONFIG_ENCRYPTION_KEY`

### S24 — LiveKit + NetGSM + DID Routing
- LiveKit SIP bridge: VOICE_CHANNEL=livekit ile WebRTC tabanli ses
- NetGSM SMS adapter: SMS_PROVIDER=netgsm ile Turk GSM uzerinden SMS
- DID numara → tenant yonlendirme: gelen aramada aranan numaradan tenant tespiti
- G.711 codec destegi: SIP_CODEC=pcmu/pcma Turk SIP operatorleri icin
- **Env var:** `VOICE_CHANNEL`, `SIP_CODEC`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `SMS_PROVIDER`, `NETGSM_USERCODE`, `NETGSM_PASSWORD`, `NETGSM_HEADER`

### S25 — Sesli Konfirmasyon + AI Veri + No-Show
- Otomatik IVR aramasi: 1=Onayla, 2=Iptal, 3=Operatore bagla
- AI canli veri enjeksiyonu: musait masalar, yogun saatler, doluluk orani
- Depozito sistemi, no-show otomasyonu ve kara liste
- **Env var:** `CONFIRMATION_HOURS_BEFORE`, `DEPOSIT_MIN_PARTY_SIZE`

### S26 — Telegram + Sablon Editoru + White-Label
- Telegram bot: inline keyboard ile rezervasyon onayi
- Bildirim sablon sistemi: Handlebars degisken degistirme, CRUD API
- White-label: ozel domain, favicon, giris sayfasi markalasmasi
- **Env var:** `TELEGRAM_BOT_TOKEN`

### S27 — UI Tasarim Sistemi + Dashboard + Mobil-First
- Design Token sistemi, dark mode, responsive sidebar
- RevPASH metrigi, trend karsilastirma, musteri 360 profili
- iyzico taksit destegi
- **Env var:** `IYZICO_API_KEY`, `IYZICO_SECRET_KEY`, `IYZICO_BASE_URL`

### S28 — Franchise + Adisyo POS + Cagri Analitik
- Franchise overview/comparison/broadcast
- Adisyo POS connector: menu sync, order push
- FCR analytics, call duration trend
- **Env var:** `ADISYO_API_KEY`, `ADISYO_BASE_URL`

### S29 — ABD Entegrasyonlari + DR Notlari
- OpenTable, Resy, Yelp Guest Manager, SevenRooms connector
- Cift yonlu sync, cakisma yonetimi, kaynak etiketleme
- DR Plan guncellendi: iletisim plani, eskalasyon matrisi, aylik restore testi
- Offsite yedekler S3'te AES-256 sifrelenmis olarak saklanir
- **Env var:** `OPENTABLE_API_KEY`, `RESY_API_KEY`, `YELP_API_KEY`, `SEVENROOMS_API_KEY`

### S30 — Cok Dilli (6 dil) + Cok Kisilik
- 6 dil destegi: TR, EN, ES, ZH, KO, VI
- Karakter tabanli dil algilama, dil bazli TTS ses secimi
- Tenant ses kisiligi: ton/hiz/karsilama stili (Redis)
- Cok dilli bildirim sablonlari
- **Env var:** `ELEVENLABS_VOICE_ID_ES`, `ELEVENLABS_VOICE_ID_ZH`, `ELEVENLABS_VOICE_ID_KO`, `ELEVENLABS_VOICE_ID_VI`

### S31 — Release & Stabilizasyon (Final)
- Superadmin compliance report: tum tenantlarin IYS/KVKK/BTK durumu
- Integration health summary: tum entegrasyonlarin durumu
- Version endpoint: 8 servis versiyonu + lastDeployment
- LiveKit → Twilio fallback durum alani
- E2E test genisletme: compliance, impersonation, cok dilli dogrulama
- CHANGELOG v1.1.1-v1.14.0 tamamlandi
- 356 test (tum sprintler dahil)

### Entegrasyon Dokumantasyon Linkleri
- Twilio kurulum: `docs/TWILIO_KURULUM.md`
- LiveKit SIP bridge: `docker-compose.yml` icerisinde LIVEKIT_* env var
- NetGSM SMS: `docker-compose.yml` icerisinde NETGSM_* env var
- Stripe odeme: README.md Entegrasyonlar bolumu
- iyzico taksit: README.md Entegrasyonlar bolumu
- ABD platformlari: `.env.example` icerisinde OPENTABLE/RESY/YELP/SEVENROOMS env var
- Adisyo POS: `.env.example` icerisinde ADISYO_* env var
- Muhasebe (Parasut/Logo/Mikro): `.env.example` icerisinde ilgili env var

---

## 12. Monitoring Stack (Grafana / Prometheus / Loki)

Monitoring servisleri ana `docker-compose.yml` icerisinde tanimlidir ve uygulama ile birlikte ayaga kalkar:

| Servis | Port | Gorev |
|--------|------|-------|
| **Grafana** | 3100 | Dashboard ve goruntuleme (varsayilan: admin/admin) |
| **Prometheus** | 9090 | Metrik toplama, alert kurallari |
| **Loki** | 3200 | Log aggregation (Promtail ile) |
| **AlertManager** | 9093 | Alert yonetimi ve e-posta bildirimleri |

- Tum 8 backend servis Prometheus tarafindan scrape edilir
- Grafana dashboardlari superadmin paneline iframe olarak gomulmustur
- Loki structured loglar toplar, Promtail container loglarini yonlendirir
- AlertManager Prometheus alert kurallarini e-posta bildirimine donusturur

```bash
# Monitoring servislerinin durumunu kontrol et
sudo docker compose ps grafana prometheus loki alertmanager

# Grafana dashboard erisimi
open http://localhost:3100

# Prometheus hedef durumu
curl http://localhost:9090/api/v1/targets | python3 -m json.tool
```

---

## 13. Arama Koruma & Maliyet Kontrolu

Sistem, sesli arama ve SMS kullanimi icin gunluk limitler ve maliyet takibi saglar:

### 13.1 Gunluk Limitler

- Her tenant icin plan bazli gunluk arama ve SMS limitleri tanimlanir
- Limit asildiginda aramalar kuyruklanir, SMS gonderimi durdurulur
- Limitler `plan_configs` tablosunda `daily_call_limit` ve `daily_sms_limit` alanlari ile yonetilir

### 13.2 Maliyet Takibi

- Her arama ve SMS'in maliyeti otomatik hesaplanir (Twilio/NetGSM fiyatlandirmasi)
- Aylik maliyet raporu superadmin panelinde goruntulenir
- Tenant bazli maliyet karsilastirmasi franchise panelinde mevcuttur

### 13.3 Koruma Mekanizmalari

- Anormal arama paterni tespit edildiginde otomatik uyari
- Gunluk limit yaklastiginda owner'a bildirim gonderilir
- Rate limiting ile dakika basina maksimum arama sayisi sinirlandirilir

---

## 14. Ulke Engelleme (Country Blocking) Admin Komutlari

Belirli ulkelerden gelen aramalari engellemek icin asagidaki admin komutlari kullanilabilir:

```bash
# Engelli ulke listesini goruntule
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost/api/v1/admin/blocked-countries

# Ulke engelle (ISO 3166-1 alpha-2 kodu ile)
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"countryCode": "XX", "reason": "Spam aramalari"}' \
  http://localhost/api/v1/admin/blocked-countries

# Ulke engelini kaldir
curl -X DELETE -H "Authorization: Bearer $TOKEN" \
  http://localhost/api/v1/admin/blocked-countries/XX

# Engelli ulkelerden gelen arama loglarini goruntule
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost/api/v1/admin/blocked-calls?days=7
```

Engellenen ulkelerden gelen aramalar otomatik olarak reddedilir ve loga kaydedilir. Bu ozellik BTK ve TCPA uyumlulugu kapsaminda kullanilabilir.
