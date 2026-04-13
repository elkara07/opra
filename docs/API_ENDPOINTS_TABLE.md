# API Endpoint Tablosu — Symvera Rezerve v3.0.0

**Tarih:** 2026-03-29
**Toplam Endpoint:** 120+

---

## 1. Auth Service (Port 3006)

### Kimlik Dogrulama
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| POST | `/api/v1/auth/register` | Public | Yeni tenant + owner olustur |
| POST | `/api/v1/auth/login` | Public | Email/sifre ile giris (brute-force korumali) |
| POST | `/api/v1/auth/refresh` | Auth | Refresh token yenile (eski iptal) |
| POST | `/api/v1/auth/logout` | Auth | Cikis (token blacklist + refresh iptal) |
| POST | `/api/v1/auth/revoke-all` | Auth | Tum oturumlari sonlandir |
| GET | `/api/v1/auth/me` | Auth | Mevcut kullanici profili |
| GET | `/api/v1/auth/active-sessions` | Auth | Aktif oturum listesi |
| POST | `/api/v1/auth/change-password` | Auth | Sifre degistir (yeniden giris zorunlu) |
| POST | `/api/v1/auth/guest-token` | Public | QR menu icin misafir token (4 saat) |

### Tenant Yonetimi
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| GET | `/api/v1/superadmin/tenants` | SUPERADMIN | Tum tenantlari listele |
| GET | `/api/v1/superadmin/tenants/:id` | SUPERADMIN | Tenant detayi |
| POST | `/api/v1/superadmin/tenants` | SUPERADMIN | Yeni tenant olustur |
| PATCH | `/api/v1/superadmin/tenants/:id` | SUPERADMIN | Tenant guncelle |
| POST | `/api/v1/superadmin/tenants/:id/impersonate` | SUPERADMIN | Tenant olarak giris (1 saat JWT) |

### Kullanici Yonetimi
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| GET | `/api/v1/superadmin/users` | SUPERADMIN | Platform kullanicilari |
| PATCH | `/api/v1/superadmin/users/:id` | SUPERADMIN | Kullanici guncelle |
| POST | `/api/v1/superadmin/users/:id/reset-password` | SUPERADMIN | Sifre sifirla |
| GET | `/api/v1/superadmin/tenants/:id/users` | SUPERADMIN | Tenant kullanicilari |
| POST | `/api/v1/superadmin/tenants/:id/users` | SUPERADMIN | Tenant kullanicisi olustur |

### Ayarlar
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| GET | `/api/v1/settings` | Auth + Tenant | Tenant ayarlari + voice config |
| PATCH | `/api/v1/settings` | OWNER/MANAGER | Ayarlari guncelle |
| GET | `/api/v1/settings/integrations` | Auth | Entegrasyon listesi |
| POST | `/api/v1/settings/integrations` | OWNER | Entegrasyon kaydet |
| POST | `/api/v1/settings/integrations/test` | OWNER | Entegrasyon testi |
| GET | `/api/v1/settings/integrations/keys` | Service-Key | Sifresi cozulmus API keyler (S2S) |
| GET | `/api/v1/settings/all-voice-configs` | Service-Key | Tum tenant voice configleri |

### Platform Config (Sifreli API Key Yonetimi)
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| GET | `/api/v1/superadmin/configs` | SUPERADMIN | Tum configler (maskelenmis) |
| GET | `/api/v1/superadmin/configs/:service` | SUPERADMIN | Servis bazli configler |
| POST | `/api/v1/superadmin/configs` | SUPERADMIN | Config kaydet (AES-256 sifreli) |
| POST | `/api/v1/superadmin/configs/:service/test` | SUPERADMIN | Servis baglanti testi |
| DELETE | `/api/v1/superadmin/configs/:id` | SUPERADMIN | Config sil |
| GET | `/api/v1/superadmin/configs/tenant/:tenantId` | SUPERADMIN | Tenant bazli configler |

### Plan Yonetimi
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| GET | `/api/v1/superadmin/plans` | SUPERADMIN | Plan listesi |
| PATCH | `/api/v1/superadmin/plans/:id` | SUPERADMIN | Plan guncelle |
| POST | `/api/v1/superadmin/tenants/:id/plan-override` | SUPERADMIN | Tenant plan limiti override |

### Platform Istatistik
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| GET | `/api/v1/superadmin/stats` | SUPERADMIN | Platform genel istatistikler |
| GET | `/api/v1/superadmin/dashboard` | SUPERADMIN | Kapsamli platform dashboard |
| GET | `/api/v1/superadmin/voice-dashboard` | SUPERADMIN | Voice AI metrikleri |
| GET | `/api/v1/superadmin/integration-health` | SUPERADMIN | Entegrasyon saglik kontrolleri |
| GET | `/api/v1/superadmin/platform-costs` | SUPERADMIN | Maliyet hesaplama |

### Kullanim & Koruma
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| GET | `/api/v1/superadmin/usage-limits/:tenantId` | SUPERADMIN | Tenant kullanim limitleri |
| PATCH | `/api/v1/superadmin/usage-limits/:tenantId` | SUPERADMIN | Limitleri guncelle |
| POST | `/api/v1/superadmin/usage-limits/:tenantId/reset` | SUPERADMIN | Kullanim sayaclarini sifirla |
| GET | `/api/v1/superadmin/usage-alerts` | SUPERADMIN | Uyari esikleri |
| GET | `/api/v1/superadmin/blocked-countries` | SUPERADMIN | Engelli ulkeler |
| POST | `/api/v1/superadmin/blocked-countries` | SUPERADMIN | Ulke engelleme |

---

## 2. Reservation Service (Port 3001)

### Rezervasyonlar
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| GET | `/api/v1/reservations` | Auth + Tenant | Rezervasyon listesi (filtreli) |
| GET | `/api/v1/reservations/today` | Auth + Tenant | Bugunun rezervasyonlari (timezone) |
| GET | `/api/v1/reservations/:id` | Auth + Tenant | Tekil rezervasyon |
| POST | `/api/v1/reservations` | Auth + Tenant | Yeni rezervasyon (idempotent) |
| PATCH | `/api/v1/reservations/:id` | Auth + Tenant | Rezervasyon guncelle |
| PATCH | `/api/v1/reservations/:id/status` | Auth + Tenant | Durum degistir |
| DELETE | `/api/v1/reservations/:id` | Auth + Tenant | Rezervasyon iptal |

### Availability (Akilli Masa Secimi)
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| GET | `/api/v1/availability` | Auth + Tenant | Musait masalar (kapasite skoru + SEATED uyari) |
| GET | `/api/v1/availability/timeline` | Auth + Tenant | Saatlik doluluk timeline |

### Ozel Islemler
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| POST | `/api/v1/reservations/deposit` | Auth + Tenant | Depozito olustur |
| POST | `/api/v1/reservations/refund-deposit` | Auth + Tenant | Depozito iade |
| GET | `/api/v1/reservations/no-show-report` | OWNER/MANAGER | No-show raporu |
| POST | `/api/v1/reservations/call-waiter` | Auth | Garson cagir (Socket.IO) |
| POST | `/api/v1/reservations/auto-complete` | SUPERADMIN/Service | Otomatik tamamlama tetikle |
| POST | `/api/v1/reservations/kvkk-anonymize` | OWNER | KVKK veri silme |

### Blacklist (Sesli Arama Kara Liste)
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| GET | `/api/v1/reservations/blacklist` | Auth + Tenant | Kara liste |
| POST | `/api/v1/reservations/blacklist` | Auth + Tenant | Numara ekle |
| DELETE | `/api/v1/reservations/blacklist/:phone` | Auth + Tenant | Numara kaldir |

### Tekrarlayan Rezervasyon
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| GET | `/api/v1/reservations/recurring-rules` | Auth + Tenant | Kural listesi |
| POST | `/api/v1/reservations/recurring-rules` | Auth + Tenant | Kural olustur |
| DELETE | `/api/v1/reservations/recurring-rules/:id` | Auth + Tenant | Kural sil |

### Bekleme Listesi
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| GET | `/api/v1/reservations/waitlist` | Auth + Tenant | Bekleme listesi |
| POST | `/api/v1/reservations/waitlist` | Auth + Tenant | Listeye ekle |
| DELETE | `/api/v1/reservations/waitlist/:id` | Auth + Tenant | Listeden cikar |

---

## 3. Voice Agent Service (Port 3007)

### Arama Yonetimi
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| POST | `/api/v1/voice/call` | Twilio Webhook | Gelen arama isleme |
| POST | `/api/v1/voice/gather` | Twilio Webhook | DTMF toplama |
| POST | `/api/v1/voice/opt-out` | Twilio Webhook | Arama sonlandirma |
| WS | `/api/v1/voice/media-stream` | WebSocket | Gercek zamanli medya akisi |
| POST | `/api/v1/voice/transfer-complete` | Twilio Webhook | Transfer tamamlama |
| POST | `/api/v1/voice/voicemail-saved` | Twilio Webhook | Sesli mesaj kaydi |

### LiveKit
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| POST | `/api/v1/voice/livekit/token` | Auth | LiveKit room token olustur |
| GET | `/api/v1/voice/livekit/rooms` | SUPERADMIN | Aktif room listesi |

### Provider Durumu
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| GET | `/api/v1/voice/providers/status` | Auth | Provider durumlari (UP/NOKEY/STANDBY) |
| GET | `/api/v1/voice/health` | Public | Servis saglik kontrolu |

### DID Yonetimi
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| GET | `/api/v1/voice/did-mappings` | SUPERADMIN | DID → tenant eslemeleri |
| POST | `/api/v1/voice/did-mappings` | SUPERADMIN | DID esleme ekle |
| DELETE | `/api/v1/voice/did-mappings/:did` | SUPERADMIN | DID esleme sil |

---

## 4. Analytics Service (Port 3005)

### Temel Analitik
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| POST | `/api/v1/analytics/events` | Service-Key | Olay kaydet |
| GET | `/api/v1/analytics/occupancy` | Auth + Tenant | Masa doluluk orani |
| GET | `/api/v1/analytics/summary` | Auth + Tenant | Aylik ozet (rezervasyon, misafir, ort. parti) |
| GET | `/api/v1/analytics/tables` | Auth + Tenant | Masa performansi |
| GET | `/api/v1/analytics/staff` | Auth + Tenant | Personel performansi |
| GET | `/api/v1/analytics/channels` | Auth + Tenant | Kanal dagilimi |
| GET | `/api/v1/analytics/peak-hours` | Auth + Tenant | Saatlik dagilim |
| GET | `/api/v1/analytics/voice-stats` | Auth + Tenant | Sesli arama metrikleri |
| GET | `/api/v1/analytics/heatmap` | Auth + Tenant | Saat x kapasite isi haritasi |

### AI Tavsiyeleri
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| GET | `/api/v1/analytics/advisor` | Auth + Tenant | AI tavsiye motoru (Anthropic/Groq/Gemini) |
| GET | `/api/v1/analytics/advisor/mock` | Auth + Tenant | Test icin mock tavsiye |

### Raporlama & Export
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| GET | `/api/v1/analytics/export/csv` | Auth + Tenant | CSV export |
| GET | `/api/v1/analytics/export/pdf` | Auth + Tenant | PDF rapor |
| GET | `/api/v1/analytics/daily-report` | Auth + Tenant | Gunluk ozet |
| GET | `/api/v1/analytics/revenue-forecast` | Auth + Tenant | Gelir tahmini (lineer regresyon) |
| GET | `/api/v1/analytics/comparison` | Auth + Tenant | Hafta/ay karsilastirma |

### Ileri Analitik
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| GET | `/api/v1/analytics/birthday-check` | Auth + Tenant | Bu haftaki dogum gunleri |
| GET | `/api/v1/analytics/staff-performance-detail` | Auth + Tenant | Detayli personel metrikleri |
| GET | `/api/v1/analytics/loyalty-tiers` | Auth + Tenant | Sadakat kademe dagilimi |
| GET | `/api/v1/analytics/revpash` | Auth + Tenant | Revenue Per Available Seat Hour |

### Call Center Analitik
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| GET | `/api/v1/analytics/calls/fcr` | Auth + Tenant | Ilk temasta cozum orani |
| GET | `/api/v1/analytics/calls/duration-trend` | Auth + Tenant | Arama suresi trendi |
| GET | `/api/v1/analytics/calls/tenant-comparison` | SUPERADMIN | Multi-tenant arama metrikleri |

### Muhasebe Entegrasyonu
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| POST | `/api/v1/analytics/accounting/export/csv` | Auth + Tenant | Muhasebe CSV |
| POST | `/api/v1/analytics/accounting/export/xml` | Auth + Tenant | UBL-TR XML (e-fatura) |
| POST | `/api/v1/analytics/accounting/export/parasut` | Auth + Tenant | Parasut export |
| POST | `/api/v1/analytics/accounting/export/logo` | Auth + Tenant | Logo GO export |
| POST | `/api/v1/analytics/accounting/export/mikro` | Auth + Tenant | Mikro export |

---

## 5. Floor Plan Service (Port 3002)

| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| GET | `/api/v1/floor-plans` | Auth + Tenant | Tum kat planlari |
| GET | `/api/v1/floor-plans/:id` | Auth + Tenant | Tekil kat plani |
| POST | `/api/v1/floor-plans` | OWNER/MANAGER | Yeni kat plani |
| PATCH | `/api/v1/floor-plans/:id` | OWNER/MANAGER | Kat plani guncelle |
| DELETE | `/api/v1/floor-plans/:id` | OWNER | Kat plani sil |
| POST | `/api/v1/floor-plans/:id/activate` | OWNER/MANAGER | Aktif plan olarak ayarla |

---

## 6. Staff Service (Port 3003)

| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| GET | `/api/v1/staff` | Auth + Tenant | Personel listesi |
| GET | `/api/v1/staff/:id` | Auth + Tenant | Personel detayi |
| POST | `/api/v1/staff` | OWNER/MANAGER | Personel ekle |
| PATCH | `/api/v1/staff/:id` | OWNER/MANAGER | Personel guncelle |
| DELETE | `/api/v1/staff/:id` | OWNER | Personel sil |
| POST | `/api/v1/staff/auto-assign` | OWNER/MANAGER | Otomatik gorevlendirme |
| GET | `/api/v1/staff/:id/workload` | Auth + Tenant | Personel is yuku |

---

## 7. Notification Service (Port 3004)

| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| POST | `/api/v1/notifications/sms` | Service-Key | SMS gonder |
| POST | `/api/v1/notifications/whatsapp` | Service-Key | WhatsApp mesaj |
| POST | `/api/v1/notifications/email` | Service-Key | Email gonder |
| POST | `/api/v1/notifications/telegram` | Service-Key | Telegram mesaj |
| GET | `/api/v1/notifications/preferences` | Auth | Bildirim tercihleri |
| PATCH | `/api/v1/notifications/preferences` | Auth | Tercihleri guncelle |
| GET | `/api/v1/notifications/templates` | Auth + Tenant | Sablon listesi |
| POST | `/api/v1/notifications/templates` | OWNER | Sablon olustur |
| PATCH | `/api/v1/notifications/templates/:id` | OWNER | Sablon guncelle |
| GET | `/api/v1/notifications/usage` | Auth + Tenant | Kullanim istatistikleri |

---

## 8. Menu Service (Port 3008)

### Menu & Siparis
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| GET | `/api/v1/menu/categories` | Auth + Tenant | Kategori listesi |
| POST | `/api/v1/menu/categories` | OWNER/MANAGER | Kategori olustur |
| GET | `/api/v1/menu/items` | Auth + Tenant | Urun listesi |
| POST | `/api/v1/menu/items` | OWNER/MANAGER | Urun olustur |
| GET | `/api/v1/menu/qr/:tableId` | Public | QR menu (misafir) |
| POST | `/api/v1/orders` | Auth | Siparis olustur |
| PATCH | `/api/v1/orders/:id/status` | STAFF | Siparis durumu guncelle |

### KDS (Mutfak Ekrani)
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| GET | `/api/v1/kds/queue` | STAFF | Aktif siparis kuyrugi |
| PATCH | `/api/v1/kds/:orderId/items/:itemId` | STAFF | Urun durumu guncelle |

### Stok & Kasa
| Method | Endpoint | Yetki | Aciklama |
|--------|----------|-------|----------|
| GET | `/api/v1/stock/ingredients` | Auth + Tenant | Malzeme listesi |
| POST | `/api/v1/stock/ingredients` | OWNER/MANAGER | Malzeme ekle |
| POST | `/api/v1/stock/counts` | STAFF | Stok sayimi |
| POST | `/api/v1/payments/close-table` | STAFF | Masa hesap kapama |
| POST | `/api/v1/register/open` | MANAGER | Kasa acilis |
| POST | `/api/v1/register/close` | MANAGER | Kasa kapanis |

---

## Kimlik Dogrulama

### JWT Token Yapisi
```json
{
  "userId": "uuid",
  "email": "user@example.com",
  "role": "OWNER",
  "tenantId": "uuid",
  "plan": "PROFESSIONAL",
  "iat": 1234567890,
  "exp": 1234568790
}
```

### Yetki Seviyeleri
| Yontem | Kullanim |
|--------|----------|
| **Bearer Token** | Kullanici istekleri (`Authorization: Bearer <jwt>`) |
| **Service Key** | Servisler arasi (`x-service-key: <key>`) |
| **Twilio Signature** | Webhook dogrulama (`X-Twilio-Signature`) |

### Rate Limiting
| Endpoint | Limit |
|----------|-------|
| `/api/v1/auth/login` | 5 deneme / 15 dakika / email |
| Genel API | 100 istek / dakika / IP |
| Voice webhook | Sinir yok (Twilio imza dogrulama) |

---

## Veritabani Dagılımı

| Veritabani | Servisler | Kullanim |
|------------|-----------|----------|
| **PostgreSQL** | auth, reservation, floor-plan, staff, notification | Ana iliskisel veri |
| **MongoDB** | menu, analytics (document store) | Menu, siparis, stok |
| **TimescaleDB** | analytics (time-series) | Zaman serisi analitik |
| **Redis** | Tum servisler | Cache, oturum, kuyruk, rate limit, blacklist |
