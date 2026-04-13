# API Reference — Rezerve Platform v2.0.0

> Bu doküman 244 production baseline'ından (v2.0.0) oluşturulmuştur.
> Son güncelleme: 2026-03-25

---

## Genel Bilgiler

| Bilgi | Değer |
|-------|-------|
| Base URL | `/api/v1` |
| Auth | Bearer Token (JWT) — `Authorization: Bearer {token}` |
| Service-to-Service | `x-service-key: {INTERNAL_SERVICE_KEY}` |
| Rate Limit (Global) | 500 req / 15 dakika |
| Rate Limit (Auth) | 30 req / 15 dakika |
| Rate Limit (Public QR) | 60 req / dakika |
| Rate Limit (Public Order) | 10 req / dakika |

### JWT Token Yapısı

```json
{
  "sub": "user-uuid",
  "tenantId": "tenant-uuid",
  "email": "user@example.com",
  "role": "OWNER",
  "plan": "PROFESSIONAL",
  "iat": 1234567890,
  "exp": 1234671490
}
```

### Roller

| Rol | Açıklama | Kapsam |
|-----|----------|--------|
| SUPERADMIN | Platform yöneticisi (biz) | Tüm tenantlar |
| OWNER | Restoran sahibi | Kendi tenant'ı |
| MANAGER | Restoran müdürü | Kendi tenant'ı |
| STAFF | Garson / personel | Kendi tenant'ı |
| GUEST | Müşteri (QR, sadakat) | Sınırlı okuma |

---

## 1. AUTH SERVICE (Port 3006)

### 1.1 Authentication

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| POST | `/auth/register` | - | Public | Yeni tenant + kullanıcı kaydı |
| POST | `/auth/login` | - | Public | Giriş (email/şifre) |
| POST | `/auth/guest-token` | - | Public | QR misafir token |
| POST | `/auth/logout` | JWT | Tümü | Çıkış |
| POST | `/auth/refresh` | Cookie | Public | Token yenileme |
| POST | `/auth/revoke-all` | JWT | Tümü | Tüm cihazlardan çıkış |
| GET | `/auth/active-sessions` | JWT | Tümü | Aktif oturumlar |
| GET | `/auth/me` | JWT | Tümü | Kullanıcı bilgisi |
| POST | `/auth/change-password` | JWT | Tümü | Şifre değiştir |

### 1.2 MFA (İki Faktörlü Doğrulama)

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| POST | `/auth/mfa/setup` | JWT | Tümü | MFA kurulum (QR code) |
| POST | `/auth/mfa/verify` | JWT | Tümü | MFA etkinleştir |
| POST | `/auth/mfa/validate` | - | Public | Login sırasında TOTP doğrula |
| DELETE | `/auth/mfa/disable` | JWT | Tümü | MFA kapat |
| GET | `/auth/mfa/status` | JWT | Tümü | MFA durumu |

### 1.3 SSO (Google)

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/auth/sso/google` | - | Public | Google OAuth URL |
| GET | `/auth/sso/google/callback` | - | Public | Google callback |
| POST | `/auth/sso/exchange` | - | Public | SSO code → token |
| GET | `/auth/sso/status` | - | Public | SSO durumu |

### 1.4 KVKK / GDPR

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| POST | `/auth/kvkk-consent` | JWT | Tümü | KVKK onayı kaydet |
| POST | `/auth/data-delete-request` | JWT | Tümü | Veri silme talebi |
| GET | `/auth/data-export` | JWT | Tümü | Veri dışa aktarım |

### 1.5 Tenant Yönetimi

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/tenants/me` | JWT | Tümü | Kendi tenant bilgisi |
| PATCH | `/tenants/me` | JWT | OWNER, MANAGER | Tenant güncelle |
| GET | `/tenants/validate/:tenantId` | Service Key | Servis | Tenant doğrulama (S2S) |
| GET | `/auth/tenant-by-domain/:domain` | - | Public | Domain ile tenant bul |

### 1.6 Kullanıcı Yönetimi

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/users` | JWT | SA, OWNER, MANAGER | Kullanıcı listesi |
| PATCH | `/users/:id` | JWT | SA, OWNER | Kullanıcı güncelle |

### 1.7 Davetiyeler

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| POST | `/invites` | JWT | SA, OWNER, MANAGER | Davet oluştur |
| GET | `/invites` | JWT | SA, OWNER, MANAGER | Davet listesi |
| GET | `/invites/:token/info` | - | Public | Davet bilgisi |
| POST | `/invites/:token/accept` | - | Public | Daveti kabul et |

### 1.8 Ayarlar

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/settings` | JWT | SA, OWNER, MANAGER | Ayarları getir |
| PATCH | `/settings` | JWT | OWNER, SA | Ayarları güncelle |
| GET | `/settings/integrations` | JWT | SA, OWNER | Entegrasyonlar |
| POST | `/settings/integrations` | JWT | SA, OWNER | Entegrasyon kaydet |
| POST | `/settings/integrations/test` | JWT | SA, OWNER | Entegrasyon test |
| POST | `/settings/logo` | JWT | Tümü | Logo yükle (multipart) |
| GET | `/settings/tenant/:tenantId` | JWT | SA | Herhangi bir tenant ayarı |
| PATCH | `/settings/tenant/:tenantId` | JWT | SA | Herhangi bir tenant güncelle |
| GET | `/settings/:tenantId` | Service Key | Servis | S2S ayar sorgulama |

### 1.9 Lokasyonlar / Franchise

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/locations` | JWT | Tümü | Lokasyon listesi |
| POST | `/locations` | JWT | SA, OWNER | Lokasyon oluştur |
| PATCH | `/locations/:id` | JWT | SA, OWNER, MANAGER | Lokasyon güncelle |
| DELETE | `/locations/:id` | JWT | SA, OWNER | Lokasyon sil |
| GET | `/locations/:id/stats` | JWT | SA, OWNER, MANAGER | Lokasyon istatistikleri |
| PATCH | `/locations/:id/assign-user` | JWT | SA, OWNER, MANAGER | Kullanıcı ata |
| GET | `/locations/franchise/overview` | JWT | SA, OWNER, MANAGER | Franchise genel bakış |
| GET | `/locations/franchise/comparison` | JWT | SA, OWNER, MANAGER | Franchise karşılaştırma |
| POST | `/locations/franchise/broadcast` | JWT | SA, OWNER | Toplu mesaj gönder |

### 1.10 Denetim Kayıtları

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/audit-logs` | JWT | SA, OWNER, MANAGER, STAFF | Kayıtlar |
| GET | `/audit-logs/resources` | JWT | SA, OWNER, MANAGER, STAFF | Kaynak türleri |
| GET | `/audit-logs/export` | JWT | SA, OWNER, MANAGER | Dışa aktar |

### 1.11 Faturalama

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/billing/plans` | - | Public | Plan listesi |
| GET | `/billing/usage` | JWT | Tümü | Kullanım istatistikleri |
| POST | `/billing/checkout` | JWT | SA, OWNER | Stripe checkout |
| POST | `/billing/webhook` | - | Stripe | Stripe webhook |

### 1.12 Admin / Superadmin

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/admin/health` | JWT | SA, OWNER | Sistem sağlık |
| GET | `/admin/tenants` | JWT | SA | Tüm tenantlar |
| POST | `/superadmin/backup/create` | JWT | SA | Yedek oluştur |
| POST | `/superadmin/backup/restore` | JWT | SA | Yedekten geri yükle |
| GET | `/superadmin/backup/status` | JWT | SA | Yedek durumu |

### 1.13 Diğer

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/version` | - | Public | Platform versiyon bilgisi |
| GET | `/.well-known/jwks.json` | - | Public | JWKS (RS256) |
| GET | `/health` | - | Public | Health check |
| GET | `/metrics` | - | Public | Prometheus metrikleri |

---

## 2. RESERVATION SERVICE (Port 3001)

### 2.1 Rezervasyonlar

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/reservations/today` | JWT | Tümü | Bugünkü rezervasyonlar |
| GET | `/reservations` | JWT | Tümü | Rezervasyon listesi (sayfalı) |
| GET | `/reservations/:id` | JWT | Tümü | Tekil rezervasyon |
| POST | `/reservations` | JWT | SA, OWNER, MANAGER, STAFF | Rezervasyon oluştur |
| PATCH | `/reservations/:id` | JWT | SA, OWNER, MANAGER, STAFF | Güncelle |
| PATCH | `/reservations/:id/status` | JWT | SA, OWNER, MANAGER, STAFF | Durum değiştir |
| DELETE | `/reservations/:id` | JWT | SA, OWNER, MANAGER | İptal |
| POST | `/reservations/:id/deposit` | JWT | SA, OWNER, MANAGER | Depozito oluştur |
| POST | `/reservations/:id/deposit/refund` | JWT | SA, OWNER, MANAGER | Depozito iade |

**Durum Değerleri:** `CONFIRMED`, `SEATED`, `COMPLETED`, `CANCELLED`, `NO_SHOW`

### 2.2 Tekrarlayan Rezervasyonlar

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| POST | `/reservations/recurring` | JWT | SA, OWNER, MANAGER | Kural oluştur |
| GET | `/reservations/recurring` | JWT | Tümü | Kuralları listele |
| DELETE | `/reservations/recurring/:id` | JWT | SA, OWNER, MANAGER | Kural sil |

### 2.3 Bekleme Listesi

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| POST | `/reservations/waitlist` | JWT | SA, OWNER, MANAGER, STAFF | Listeye ekle |
| GET | `/reservations/waitlist` | JWT | SA, OWNER, MANAGER, STAFF | Listeyi göster |
| DELETE | `/reservations/waitlist/:id` | JWT | SA, OWNER, MANAGER | Listeden çıkar |

### 2.4 Müsaitlik

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/availability` | JWT | Tümü | Müsait masalar (date, startTime) |
| GET | `/availability/timeline` | JWT | Tümü | Saatlik müsaitlik zaman çizelgesi |

### 2.5 Sadakat (Loyalty)

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/loyalty` | JWT | SA, OWNER, MANAGER, GUEST | VIP müşteri listesi |
| GET | `/loyalty/detail?phone=` | JWT | SA, OWNER, MANAGER, GUEST | Müşteri profili |
| PATCH | `/loyalty/update?phone=` | JWT | SA, OWNER, MANAGER | Müşteri güncelle |
| POST | `/loyalty/redeem?phone=` | JWT | SA, OWNER, MANAGER | Puan kullan |

### 2.6 Arayan Profilleri & İletişim

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/callers` | JWT | SA, OWNER, MANAGER | Arayan listesi |
| GET | `/callers/:phone` | JWT | SA, OWNER, MANAGER | Arayan profili |
| PATCH | `/callers/:phone` | JWT | SA, OWNER, MANAGER | Not ekle |
| GET | `/communication-logs` | JWT | SA, OWNER, MANAGER | İletişim logları |
| POST | `/communication-logs` | JWT | SA, OWNER, MANAGER, STAFF | Log oluştur |

### 2.7 Entegrasyonlar

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/reservations/integrations` | JWT | Tümü | Entegrasyon listesi |
| GET | `/reservations/integrations/sync-log` | JWT | Tümü | Senkronizasyon geçmişi |
| GET | `/reservations/integrations/:platform/status` | JWT | Tümü | Platform durumu |
| POST | `/reservations/integrations/:platform/test` | JWT | SA, OWNER, MANAGER | Bağlantı test |
| POST | `/reservations/integrations/:platform/sync` | JWT | SA, OWNER, MANAGER | Manuel senkronizasyon |

### 2.8 Diğer

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/reservations/no-show-report` | JWT | SA, OWNER, MANAGER | No-show raporu |
| POST | `/reservations/call-waiter` | JWT | Tümü | Garson çağır (Socket.IO) |
| GET | `/reservations/qr/:tableId` | JWT | Tümü | Masa QR kodu |
| POST | `/reservations/kvkk-anonymize` | Service Key | Servis | KVKK anonimleştirme (S2S) |

---

## 3. FLOOR-PLAN SERVICE (Port 3002)

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/floor-plans` | JWT | Tümü | Salon listesi |
| GET | `/floor-plans/active` | JWT | Tümü | Aktif salon planı |
| GET | `/floor-plans/:id` | JWT | Tümü | Salon detayı |
| POST | `/floor-plans` | JWT | SA, OWNER, MANAGER | Salon oluştur |
| PUT | `/floor-plans/:id` | JWT | SA, OWNER, MANAGER | Salon güncelle (tam) |
| DELETE | `/floor-plans/:id` | JWT | SA, OWNER, MANAGER | Salon sil (soft) |
| PATCH | `/floor-plans/:id/activate` | JWT | SA, OWNER, MANAGER | Aktif yap |
| POST | `/floor-plans/:id/elements` | JWT | SA, OWNER, MANAGER | Masa/eleman ekle |
| PATCH | `/floor-plans/:id/elements/:elementId` | JWT | SA, OWNER, MANAGER | Eleman güncelle |
| DELETE | `/floor-plans/:id/elements/:elementId` | JWT | SA, OWNER, MANAGER | Eleman sil |

---

## 4. STAFF SERVICE (Port 3003)

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/staff` | JWT | OWNER, MANAGER, STAFF | Personel listesi |
| GET | `/staff/assignments` | JWT | OWNER, MANAGER, STAFF | Görev atamaları |
| GET | `/staff/:id` | JWT | OWNER, MANAGER, STAFF | Personel detayı |
| GET | `/staff/:id/workload` | JWT | SA, OWNER, MANAGER | İş yükü |
| POST | `/staff` | JWT | SA, OWNER, MANAGER | Personel ekle |
| PATCH | `/staff/:id` | JWT | SA, OWNER, MANAGER | Personel güncelle |
| DELETE | `/staff/:id` | JWT | SA, OWNER, MANAGER | Personel deaktif et |
| POST | `/staff/auto-assign` | JWT | OWNER, MANAGER, STAFF | Otomatik atama (AI) |
| POST | `/staff/assignments/:id/complete` | JWT | OWNER, MANAGER, STAFF | Görev tamamla |

---

## 5. MENU SERVICE (Port 3008)

### 5.1 Kategoriler

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/menu/categories` | JWT | Tümü | Kategori listesi |
| POST | `/menu/categories` | JWT | SA, OWNER, MANAGER | Kategori oluştur |
| PATCH | `/menu/categories/:id` | JWT | SA, OWNER, MANAGER | Kategori güncelle |
| DELETE | `/menu/categories/:id` | JWT | SA, OWNER, MANAGER | Kategori sil |

### 5.2 Menü Öğeleri

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/menu/items` | JWT | Tümü | Ürün listesi |
| GET | `/menu/items/priced` | JWT | Tümü | Dinamik fiyatlı ürünler |
| POST | `/menu/items` | JWT | SA, OWNER, MANAGER | Ürün ekle |
| PATCH | `/menu/items/:id` | JWT | SA, OWNER, MANAGER | Ürün güncelle |
| DELETE | `/menu/items/:id` | JWT | SA, OWNER, MANAGER | Ürün sil |

### 5.3 Dinamik Fiyatlandırma

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/menu/pricing-rules` | JWT | SA, OWNER, MANAGER | Kural listesi |
| POST | `/menu/pricing-rules` | JWT | SA, OWNER | Kural oluştur |
| PATCH | `/menu/pricing-rules/:id` | JWT | SA, OWNER | Kural güncelle |
| DELETE | `/menu/pricing-rules/:id` | JWT | SA, OWNER | Kural sil |
| GET | `/menu/price-history` | JWT | SA, OWNER, MANAGER | Fiyat geçmişi |

### 5.4 QR Menü (Public)

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/menu/public/:tenantSlug/categories` | - | Public | QR kategoriler |
| GET | `/menu/public/:tenantSlug/items` | - | Public | QR ürünler |
| GET | `/menu/qr/:tenantSlug/all` | JWT | Tümü | Tüm QR kodları (JSON) |
| GET | `/menu/qr/:tenantSlug/pdf` | JWT | Tümü | Tüm QR kodları (PDF) |
| GET | `/menu/qr/:tenantSlug/:tableId` | - | Public | Tek masa QR |

### 5.5 Siparişler

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/orders` | JWT | Tümü | Sipariş listesi |
| GET | `/orders/:id` | JWT | Tümü | Sipariş detayı |
| POST | `/orders` | JWT | Tümü | Sipariş oluştur |
| POST | `/orders/public` | - | Public (10/dk) | QR sipariş (auth'suz) |
| GET | `/orders/public/:id` | - | Public | Sipariş takip |
| PATCH | `/orders/:id/status` | JWT | SA, OWNER, MANAGER, STAFF | Sipariş durumu güncelle |
| GET | `/orders/kitchen-queue` | JWT | Tümü | Mutfak kuyruğu |
| GET | `/orders/analytics/prep-times` | JWT | Tümü | Hazırlık süreleri |
| GET | `/orders/analytics/performance` | JWT | Tümü | Mutfak performansı |
| GET | `/orders/analytics/item-times` | JWT | Tümü | Ürün bazlı süreler |

### 5.6 Ödemeler

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/payments` | JWT | Tümü | Ödeme listesi |
| POST | `/payments` | JWT | Tümü | Ödeme kaydet |
| GET | `/payments/daily-report` | JWT | Tümü | Günlük rapor |
| POST | `/payments/split` | JWT | Tümü | Hesap böl |
| POST | `/payments/stripe-intent` | JWT | Tümü | Stripe ödeme |
| POST | `/payments/iyzico-intent` | JWT | Tümü | iyzico ödeme |
| POST | `/payments/:id/refund` | JWT | SA, OWNER, MANAGER | İade |

### 5.7 Vardiyalar

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/shifts` | JWT | Tümü | Vardiya listesi |
| GET | `/shifts/current` | JWT | Tümü | Aktif vardiya |
| POST | `/shifts/open` | JWT | Tümü | Vardiya aç |
| POST | `/shifts/close` | JWT | Tümü | Vardiya kapat |

### 5.8 Stok Yönetimi

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/stock/ingredients` | JWT | Tümü | Malzeme listesi |
| POST | `/stock/ingredients` | JWT | SA, OWNER, MANAGER | Malzeme ekle |
| PATCH | `/stock/ingredients/:id` | JWT | SA, OWNER, MANAGER | Malzeme güncelle |
| DELETE | `/stock/ingredients/:id` | JWT | SA, OWNER, MANAGER | Malzeme sil |
| GET | `/stock/recipes` | JWT | SA, OWNER, MANAGER | Reçeteler |
| POST | `/stock/recipes` | JWT | SA, OWNER, MANAGER | Reçete kaydet |
| DELETE | `/stock/recipes/:id` | JWT | SA, OWNER, MANAGER | Reçete sil |
| GET | `/stock/transactions` | JWT | SA, OWNER, MANAGER | Stok hareketleri |
| POST | `/stock/transactions` | JWT | SA, OWNER, MANAGER | Stok hareketi kaydet |
| GET | `/stock/counts` | JWT | Tümü | Sayım listesi |
| POST | `/stock/counts` | JWT | SA, OWNER, MANAGER | Sayım oluştur |
| GET | `/stock/low-stock` | JWT | SA, OWNER, MANAGER | Düşük stok uyarıları |
| GET | `/stock/suppliers` | JWT | SA, OWNER, MANAGER | Tedarikçiler |
| POST | `/stock/suppliers` | JWT | SA, OWNER, MANAGER | Tedarikçi ekle |
| PATCH | `/stock/suppliers/:id` | JWT | SA, OWNER, MANAGER | Tedarikçi güncelle |
| DELETE | `/stock/suppliers/:id` | JWT | SA, OWNER, MANAGER | Tedarikçi sil |
| GET | `/stock/report` | JWT | SA, OWNER, MANAGER | Stok raporu |

### 5.9 POS Entegrasyonları

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| POST | `/menu/pos/adisyo/sync` | S.Key/JWT | Servis | Adisyo menü senkronizasyon |
| POST | `/menu/pos/adisyo/order` | S.Key/JWT | Servis | Adisyo'ya sipariş gönder |
| GET | `/menu/pos/adisyo/status` | S.Key/JWT | Servis | Adisyo durum |
| POST | `/menu/pos/adisyo/test` | S.Key/JWT | Servis | Adisyo test |
| GET | `/menu/pos/toast/status` | S.Key/JWT | Servis | Toast POS durum |
| POST | `/menu/pos/toast/test` | S.Key/JWT | Servis | Toast test |
| POST | `/menu/pos/toast/sync` | S.Key/JWT | Servis | Toast senkronizasyon |

---

## 6. NOTIFICATION SERVICE (Port 3004)

### 6.1 SMS & Mesajlaşma

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| POST | `/notifications/sms` | Service Key | Servis | SMS gönder |
| POST | `/notifications/sms-test` | JWT | Kullanıcı | Test SMS gönder |
| POST | `/notifications/whatsapp/send` | Service Key | Servis | WhatsApp mesaj |
| GET | `/notifications/whatsapp/status` | JWT | Kullanıcı | WhatsApp durumu |
| POST | `/notifications/email` | Service Key | Servis | Email gönder |
| GET | `/notifications/email/status` | JWT | Kullanıcı | Email durumu |
| POST | `/notifications/telegram/send` | Service Key | Servis | Telegram mesaj |
| GET | `/notifications/telegram/status` | JWT | Kullanıcı | Telegram durumu |

### 6.2 Tercihler & Şablonlar

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/notifications/preferences` | JWT | Kullanıcı | Bildirim tercihleri |
| POST | `/notifications/preferences` | JWT | Kullanıcı | Tercihleri güncelle |
| GET | `/notifications/templates` | JWT | Kullanıcı | Şablon listesi |
| POST | `/notifications/templates` | JWT | Kullanıcı | Şablon oluştur |
| DELETE | `/notifications/templates/:id` | JWT | Kullanıcı | Şablon sil |
| POST | `/notifications/templates/preview` | JWT | Kullanıcı | Şablon önizleme |

### 6.3 Onay Aramaları (IVR)

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| POST | `/notifications/confirmation/trigger` | JWT | Kullanıcı | Manuel onay tetikle |
| GET | `/notifications/confirmation/settings` | JWT | Kullanıcı | Onay ayarları |
| PATCH | `/notifications/confirmation/settings` | JWT | Kullanıcı | Onay ayarları güncelle |
| POST | `/notifications/confirmation/schedule` | Service Key | Servis | Onay zamanla |

### 6.4 Google Takvim

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/notifications/google/auth-url` | JWT | Kullanıcı | Google OAuth URL |
| GET | `/notifications/google/status` | JWT | Kullanıcı | Takvim durumu |

### 6.5 Durum & Maliyet

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/notifications/netgsm/status` | JWT | Kullanıcı | NetGSM durumu |
| POST | `/notifications/netgsm/test` | JWT | Kullanıcı | NetGSM test |
| GET | `/notifications/usage` | JWT | Kullanıcı | Kullanım istatistikleri |
| GET | `/notifications/cost` | JWT | Kullanıcı | Maliyet takibi |
| GET | `/notifications/iys/status` | JWT | Kullanıcı | İYS durumu |

---

## 7. ANALYTICS SERVICE (Port 3005 — Python/FastAPI)

### 7.1 Dashboard Analitiği

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/analytics/occupancy` | JWT | SA, OWNER, MANAGER | Doluluk oranları |
| GET | `/analytics/summary` | JWT | SA, OWNER, MANAGER | 30 günlük özet |
| GET | `/analytics/tables` | JWT | SA, OWNER, MANAGER | Masa performansı |
| GET | `/analytics/staff` | JWT | SA, OWNER, MANAGER | Personel performansı |
| GET | `/analytics/channels` | JWT | SA, OWNER, MANAGER | Kanal dağılımı |
| GET | `/analytics/peak-hours` | JWT | SA, OWNER, MANAGER | Yoğun saatler |
| GET | `/analytics/voice-stats` | JWT | SA, OWNER, MANAGER | Sesli arama istatistikleri |
| GET | `/analytics/revpash` | JWT | SA, OWNER, MANAGER | Koltuk başı gelir |
| GET | `/analytics/trend` | JWT | SA, OWNER, MANAGER | Trend analizi |
| GET | `/analytics/loyalty-tiers` | JWT | SA, OWNER, MANAGER | Sadakat seviyeleri |

### 7.2 AI Danışman

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/analytics/advisor` | JWT | SA, OWNER | AI öneriler (Claude) |
| GET | `/analytics/advisor/mock` | JWT | SA, OWNER | Test modu |

### 7.3 Dışa Aktarım

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/analytics/export/csv` | JWT | SA, OWNER, MANAGER | CSV dışa aktar |
| GET | `/analytics/export/pdf` | JWT | SA, OWNER, MANAGER | PDF dışa aktar |

### 7.4 Muhasebe Entegrasyonu

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/analytics/accounting/connectors` | JWT | SA, OWNER | Muhasebe bağlantıları |
| POST | `/analytics/accounting/export/csv` | JWT | SA, OWNER | CSV dışa aktar |
| POST | `/analytics/accounting/export/xml` | JWT | SA, OWNER | XML dışa aktar |
| POST | `/analytics/accounting/export/parasut` | JWT | SA, OWNER | Paraşüt entegrasyonu |
| POST | `/analytics/accounting/export/logo` | JWT | SA, OWNER | Logo entegrasyonu |
| POST | `/analytics/accounting/export/mikro` | JWT | SA, OWNER | Mikro entegrasyonu |
| GET | `/analytics/accounting/invoices` | JWT | SA, OWNER | Fatura listesi |

### 7.5 Arama Analitiği

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| GET | `/analytics/calls/fcr` | JWT | SA, OWNER, MANAGER | İlk aramada çözüm |
| GET | `/analytics/calls/duration-trend` | JWT | SA, OWNER, MANAGER | Arama süre trendi |
| GET | `/analytics/calls/tenant-comparison` | JWT | SA | Tenant karşılaştırma |

---

## 8. VOICE-AGENT SERVICE (Port 3007 — Python)

| Method | Endpoint | Auth | Roller | Açıklama |
|--------|----------|------|--------|----------|
| POST | `/voice/incoming` | Twilio Sig | Webhook | Gelen arama (TwiML) |
| POST | `/voice/gather/:call_sid` | Twilio Sig | Webhook | Konuşma girişi işle |
| POST | `/voice/optout/:call_sid` | Twilio Sig | Webhook | TCPA opt-out (tuş 9) |
| GET | `/health` | - | Public | Health check |

---

## Servis Altyapısı

### Docker Network (restoran-net)

```
Frontend          → http://frontend:3000
Nginx (Gateway)   → http://nginx:80 / https://nginx:443
Auth Service      → http://auth-service:3006
Reservation Svc   → http://reservation-service:3001
Floor-Plan Svc    → http://floor-plan-service:3002
Staff Service     → http://staff-service:3003
Notification Svc  → http://notification-service:3004
Analytics Svc     → http://analytics-service:3005
Voice Agent Svc   → http://voice-agent-service:3007
Menu Service      → http://menu-service:3008
Platform Ctrl     → http://platform-controller:3009
Platform UI       → http://platform-frontend:3010

PostgreSQL        → postgres:5432
MongoDB           → mongo:27017
Redis             → redis:6379
TimescaleDB       → timescaledb:5432
LiveKit           → livekit-server:7880
LiveKit SIP       → livekit-sip:5060
```

### Veritabanı Dağılımı

| Servis | Veritabanı | Tip | Amaç |
|--------|-----------|-----|------|
| auth-service | PostgreSQL | İlişkisel | Kullanıcılar, tenantlar, ayarlar |
| reservation-service | PostgreSQL | İlişkisel | Rezervasyonlar, sadakat |
| floor-plan-service | MongoDB | Doküman | Salon planları |
| staff-service | PostgreSQL | İlişkisel | Personel, görevler |
| menu-service | MongoDB | Doküman | Menü, siparişler, stok |
| analytics-service | TimescaleDB | Zaman serisi | Metrikler |
| voice-agent-service | Redis | Cache | Oturum, DID eşleme |

---

## Güvenlik Notu

**Tespit Edilen Sorun:** Frontend'de access token `localStorage`'da tutuluyor. XSS saldırılarına karşı savunmasız. İdeal olarak token yalnızca memory'de (Zustand store) tutulmalı, refresh token HttpOnly cookie ile yönetilmeli.
