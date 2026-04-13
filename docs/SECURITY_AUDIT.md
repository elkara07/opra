# Güvenlik Denetimi — v2.0.0

> Tarih: 2026-03-25
> Kapsam: RBAC, Tenant İzolasyonu, DB Bypass, Servisler Arası Auth

---

## Özet

| Seviye | Bulgu Sayısı |
|--------|-------------|
| CRITICAL | 3 |
| HIGH | 5 |
| MEDIUM | 5 |
| LOW | 3 |

---

## CRITICAL Bulgular

### C1. Analytics — Query Parameter ile Tenant Spoofing
**Dosya:** `services/analytics-service/main.py` (satır 172-378)

**Sorun:** Tüm analytics endpoint'lerinde `tenantId` query parametreden alınabiliyor ve JWT'deki değeri geçersiz kılıyor.

```python
tenantId = tenantId or get_tenant_from_jwt(authorization)
# Eğer ?tenantId=başka-tenant varsa, JWT'deki değer kullanılmıyor!
```

**Etkilenen Endpoint'ler:**
- `GET /analytics/occupancy`
- `GET /analytics/summary`
- `GET /analytics/tables`
- `GET /analytics/staff`
- `GET /analytics/channels`
- `GET /analytics/peak-hours`
- `GET /analytics/voice-stats`
- `GET /analytics/advisor`

**Etki:** Herhangi bir authenticated kullanıcı, başka tenant'ın tüm analitik verilerini görebilir.

**Düzeltme:**
```python
tenantId = get_tenant_from_jwt(authorization)
if not tenantId:
    raise HTTPException(status_code=401, detail="Invalid token")
# Query parametresindeki tenantId kesinlikle kullanılMAMALI
```

---

### C2. Voice Service — DID Mapping Tenant İzolasyonu Yok
**Dosya:** `services/voice-agent-service/main.py` (satır 132-168, 2275-2290)

**Sorun:** DID numarası eşlemeleri global Redis hash'inde tutuluyor (`did_mappings`), tenant bazlı scope yok.

- SIP trunk kaydı endpoint'i (`/voice/sip/register`) tenantId'yi request body'den alıyor — doğrulama yok
- `set_did_mapping()` fonksiyonu auth olmadan çağrılabiliyor
- Bir servis key ile tüm tenant'ların DID eşlemeleri değiştirilebilir

**Etki:** Aramaların yanlış tenant'a yönlendirilmesi, çağrı dinleme potansiyeli.

**Düzeltme:**
- DID key'leri tenant-scoped yapılmalı: `did:{tenantId}:{number}`
- REST endpoint'leri SUPERADMIN + service key gerektirecek şekilde güncellenmeli
- Audit logging eklenmeli

---

### C3. Analytics Events — Tenant Doğrulaması Yok
**Dosya:** `services/analytics-service/main.py` (satır 151-168)

**Sorun:** `POST /analytics/events` endpoint'i sadece service key kontrol ediyor, payload'daki `tenantId` doğrulanmıyor.

**Etki:** Bozulmuş bir servis, başka tenant'ların analitik verilerini kirletebilir (data poisoning).

**Düzeltme:** Calling service context'i ile tenantId çapraz doğrulama.

---

## HIGH Bulgular

### H1. Communication Log — tenantId Body Fallback
**Dosya:** `services/reservation-service/src/controllers/caller.controller.js` (satır 136)

```javascript
const tenantId = req.user?.tenantId || req.body.tenantId;
```

**Sorun:** JWT'de tenantId yoksa, request body'den alınıyor. Cross-tenant log enjeksiyonu mümkün.

**Düzeltme:** Fallback kaldırılmalı, sadece JWT'den alınmalı.

---

### H2. Voice Incoming — tenantId Query Parameter Güvenilmiyor
**Dosya:** `services/voice-agent-service/main.py` (satır 899-920)

```python
raw_tenant = request.query_params.get("tenantId", "")
```

**Sorun:** Gelen arama webhook'unda tenantId doğrudan URL'den alınıyor.

**Düzeltme:** Sadece DID mapping veya signed callback URL kullanılmalı.

---

### H3. Reservation Auto-Complete — Route'suz DB Yazma
**Dosya:** `services/reservation-service/src/index.js` (satır 293-321)

**Sorun:** `setInterval` ile her 10 dakikada bir çalışan cron job, doğrudan DB'ye yazıyor:
- SEATED/CONFIRMED → COMPLETED
- Geçmiş tarihli CONFIRMED → NO_SHOW

Bu işlem:
- Hiçbir REST API endpoint'i üzerinden geçmiyor
- Audit log üretmiyor
- Bildirim tetiklemiyor
- Business logic validation atlanıyor

**Düzeltme:** Dedicated controller + endpoint oluşturulmalı, audit log ve bildirim eklenmeli.

---

### H4. KVKK Anonymize — Yetersiz Auth
**Dosya:** `services/reservation-service/src/index.js` (satır 242-291)

**Sorun:** `POST /kvkk-anonymize` sadece service key ile çalışıyor, JWT gerektirmiyor. Cascade silme yapıyor (reservation, callerProfile, communicationLog, loyaltyPoint).

**Düzeltme:** JWT + admin onayı + audit logging gerekli.

---

### H5. Stripe Webhook — Tenant Plan Direkt Değiştirme
**Dosya:** `services/auth-service/src/controllers/billing.controller.js` (satır 176-222)

**Sorun:** Webhook sadece Stripe signature ile doğrulanıyor. Compromised webhook secret ile herhangi bir tenant'ın planı değiştirilebilir.

**Düzeltme:** Ek tenant context doğrulaması eklenmeli.

---

## MEDIUM Bulgular

### M1. Service Key — Tek Key, Tüm Servisler
Tüm servisler aynı `INTERNAL_SERVICE_KEY`'i kullanıyor. Key rotation mekanizması yok, rate limiting yok.

**Düzeltme:** Per-service key, HMAC-SHA256, rate limiting.

### M2. Metrics Endpoint — Auth Yok
`GET /metrics` tüm servislerde public. Request pattern'ları, hata oranları ifşa olabilir.

**Düzeltme:** IP whitelist veya auth eklenmeli.

### M3. localStorage Token Depolama
Frontend'de access token `localStorage`'da tutuluyor — XSS'e açık.

**Düzeltme:** Token sadece memory'de (Zustand), refresh token HttpOnly cookie.

### M4. Timezone Parameter Validasyonu Yok
Staff workload endpoint'inde timezone parametresi doğrulanmıyor.

### M5. Audit Log Hata Yutma
Audit middleware'de DB yazma hatası sessizce yutulmuyor, fail-open çalışıyor.

---

## LOW Bulgular

| # | Bulgu | Durum |
|---|-------|-------|
| L1 | Health endpoint'leri auth'suz | Tasarım gereği — OK |
| L2 | Version endpoint bilgi ifşası | Kabul edilebilir |
| L3 | Prometheus metrikler public | IP whitelist önerilir |

---

## Tenant İzolasyon Durumu

| Servis | Model | Tenant Scoped | Durum |
|--------|-------|:------------:|:-----:|
| Reservation | Reservation | ✓ | OK |
| Reservation | CallerProfile | ✓ | OK |
| Reservation | CommunicationLog | ✓* | *Body fallback sorunu |
| Reservation | LoyaltyPoint | ✓ | OK |
| Floor-Plan | FloorPlan | ✓ | OK |
| Staff | Staff | ✓ | OK |
| Menu | Category | ✓ | OK |
| Menu | MenuItem | ✓ | OK |
| Analytics | occupancy_events | ✓* | *Query param override |
| Voice | DID Mappings | ✗ | CRITICAL — global scope |

---

## Route'suz DB Yazma İşlemleri

| İşlem | Dosya | Auth | API Endpoint | Risk |
|-------|-------|------|:----------:|:----:|
| Auto-complete reservations | reservation/index.js:293-321 | Yok (cron) | **YOK** | HIGH |
| Audit log yazma | auth/middleware/audit.middleware.js | Middleware | Yok (yan etki) | LOW |
| DID mapping güncelleme | voice-agent/main.py:143-159 | Service key | Kısmi | CRITICAL |

---

## Düzeltme Öncelik Sırası

### Acil (Bu sprint)
1. Analytics tenantId query param → sadece JWT'den al
2. Communication log tenantId body fallback → kaldır
3. Voice incoming tenantId query param → kaldır, sadece DID mapping
4. DID mapping → tenant-scoped Redis key + REST endpoint

### Kısa Vade (Sonraki sprint)
5. Auto-complete cron → controller + endpoint + audit log
6. KVKK anonymize → JWT + admin onay + audit
7. Service key → per-service key + HMAC
8. localStorage → memory-only token

### Orta Vade
9. Metrics endpoint → IP whitelist
10. Stripe webhook → ek tenant doğrulama
11. Audit middleware → fail-closed modu
12. Timezone validation
