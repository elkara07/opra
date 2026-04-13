# Simülasyon Test Sonuçları — v2.3.0

> Tarih: 2026-03-26
> Ortam: 10.1.1.244

---

## Test Tenant'ları

### Lezzet Sarayi (owner@test1.com)
- Çalışma saatleri: Varsayılan (tenant ayarlanmadı)
- 2 salon: Ana Salon (10 masa) + Teras (5 masa)
- avgSittingMinutes: 90

### Moonlight Lounge (owner@gece.com)
- Çalışma saatleri: 04:30 - 17:00 (erken sabah mekanı)
- Pazar kapalı
- 1 salon: 8 masa (Bar 1-3, Masa 1-3, VIP 1-2)
- avgSittingMinutes: 120

---

## Çalışma Saati Testleri

| Test | Tenant | Saat | Sonuç |
|------|--------|------|-------|
| Mesai içi (19:00) | Lezzet Sarayi | 19:00 | ✅ CONFIRMED |
| VIP rez (21:00) | Lezzet Sarayi | 21:00 | ✅ CONFIRMED |
| Gece geç (23:30) | Lezzet Sarayi | 23:30 | ✅ CONFIRMED |
| Gece yarısı sonrası (02:00) | Lezzet Sarayi | 02:00 | ✅ CONFIRMED |
| Mesai içi (05:00) | Moonlight | 05:00 | ✅ CONFIRMED |
| Mesai dışı (03:00) | Moonlight | 03:00 | ❌ Reddedildi (04:30 öncesi) |
| Mesai dışı (18:00) | Moonlight | 18:00 | ❌ Reddedildi (17:00 sonrası) |
| Kapalı gün (Pazar) | Moonlight | 20:00 | ❌ Reddedildi (kapalı gün) |
| Walk-in mesai dışı | Moonlight | 10:00 | ✅ WALK_IN (bypass) |

---

## Dolu Masa Testleri

| Test | Sonuç |
|------|-------|
| Dolu masaya (m4) yeni rez | ❌ "Seçilen masa bu saatte dolu" |
| Walk-in dolu masaya | ⚠️ Confirm dialog |

---

## Akıllı Masa Seçimi Testleri

### 2 kişi, Lezzet Sarayi
| Masa | Kapasite | Skor | Sonuç |
|------|----------|------|-------|
| Masa 1 | 2 | 100 | ⭐ Önerilen |
| Masa 2 | 2 | 100 | ⭐ Önerilen |
| Masa 3 | 4 | 75 | Önerilen |
| Masa 4 | 4 | 75 | Önerilen |
| Masa 5 | 4 | 75 | Önerilen |
| VIP 1 | 4 | 75 | Normal |
| Masa 6 | 6 | 50 | Normal |
| Masa 7 | 6 | 50 | Normal |
| VIP 2 | 6 | 50 | Normal |
| Masa 8 | 8 | 20 | Normal (düşük uyum) |

### 2 kişi, Moonlight Lounge
| Masa | Kapasite | Skor |
|------|----------|------|
| Bar 1-3 | 2 | 100 ⭐ |
| Masa 1-2 | 4 | 75 |

### SEATED Algılama
- t1 masasında Walk-in oturuyor → Available: 9, Seated: 1, Total: 10 ✅
- SEATED uyarısı API'den dönüyor ✅

---

## API Endpoint Testleri

| Endpoint | Durum |
|----------|-------|
| GET /availability | ✅ Floor-plan S2S çalışıyor |
| POST /reservations (normal) | ✅ |
| POST /reservations (dolu masa) | ✅ Reddediyor |
| POST /reservations (mesai dışı) | ✅ Reddediyor |
| POST /reservations (kapalı gün) | ✅ Reddediyor |
| POST /reservations (walk-in bypass) | ✅ |
| GET /settings (SUPERADMIN) | ✅ tenantId=null OK |
| GET /superadmin/configs | ✅ |
| POST /superadmin/configs (API key) | ✅ Encrypt + mask |
| GET /settings/integrations/keys (S2S) | ✅ Decrypt |
| GET /voice/providers | ✅ hasKey + keySource |
| GET /version | ✅ v2.3.0 |
