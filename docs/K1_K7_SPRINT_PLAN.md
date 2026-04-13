# K1-K7 Sprint Uygulama Planı — v2

**Tarih:** 2026-03-23 (güncellendi)
**Mevcut versiyon:** v1.22.0
**Hedef versiyon:** v1.22.0 (tamamlandı)
**Mimari karar:** Platform Controller ayrı ürün (aynı repo, ayrı bileşen)

---

## MİMARİ

```
rezapplication/
├── services/              ← Müşteri servisleri (tenant namespace)
│   ├── auth-service/
│   ├── reservation-service/
│   ├── voice-agent-service/
│   └── ...
├── platform/              ← Platform bileşenleri (symvera-system namespace)
│   ├── platform-controller/   ← Backend: lisans, tenant lifecycle, monitoring
│   │   ├── src/
│   │   ├── prisma/            ← Platform DB (tenant registry, billing, alerts)
│   │   └── Dockerfile
│   └── platform-frontend/     ← Frontend: admin.symvera.ai
│       ├── src/
│       └── Dockerfile
├── frontend/              ← Müşteri frontend'i (slug.symvera.ai)
├── docker-compose.yml     ← Tüm bileşenler
└── helm/                  ← K8s manifests
```

### Platform Controller sorumlulukları:
1. **Tenant lifecycle:** create / suspend / activate / delete (manuel)
2. **Lisans server:** plan limitleri izle, aşımda grace period veya hizmet kes
3. **Ödeme:** Stripe webhook, trial/grace/suspend otomatik
4. **Monitoring:** tüm namespace'lerin pod/resource durumu
5. **Alerting:** limit aşımı, down servis, sertifika süresi → alarm
6. **Veri silme:** SADECE alarm üret, admin manuel karar verir

### Lisans server davranışı:
- Ses dakikası, rez sayısı, kullanıcı sayısı izleme
- Paket aşımında: önce uyarı → grace period → hizmet kesme
- Ödeme başarısız: Stripe webhook → grace (7 gün) → suspend
- Trial bitimi: uyarı → suspend
- Veri silme: admin onayı ile, otomatik DEĞİL — sadece alarm

---

## GENEL KURALLAR

1. Her sprint sonunda: test.sh + CI yeşil → deploy → versiyon tag
2. CI kırmızıysa sonraki sprint'e geçme
3. Platform controller ayrı bileşen — müşteri frontend'inden bağımsız
4. Compose↔K8s senkronizasyonu her sprint'te kontrol
5. Veri silme her zaman MANUEL — otomatik silme YOK

---

## K1 — Rol Refaktöring & GUEST Auth (v1.18.0)

### K1.1 — GUEST rol implementasyonu ✅ TAMAMLANDI
- [x] POST /auth/guest-token: QR tabanlı, şifresiz, 4 saat token
- [x] GUEST loyalty read-only erişim
- [x] GUEST admin erişimi 403
- [x] Frontend minimal GUEST nav
- [x] Store: GUEST token decode
- [x] guest@test.com test kullanıcısı
- [x] CI ✓ (363/380)

### K1.2 — Rol yetki matrisi doğrulama
- [x] Tüm route dosyalarında authorize() kontrol — eksik rol kontrolü tarama
- [x] CallerProfile API rol kontrolü
- [x] Frontend menü rolleri doğrulama
- [x] Her endpoint için yetki testi (test.sh'e RBAC testleri ekleme)

### K1.3 — Migration altyapısı
- [x] scripts/rollback-migration.sh
- [x] scripts/pre-migration-backup.sh
- [x] Migration test prosedürü dokümanı

### K1.4 — Compose↔K8s sync kuralı
- [x] docs/COMPOSE_K8S_SYNC.md

### K1.5 — Test & deploy
- [x] Mevcut 363+ test kırılmadı
- [x] GUEST RBAC testleri eklendi (5+ yeni test)
- [x] CI yeşil
- [x] v1.18.0 tag

---

## K2 — Docker Multi-Tenant + Helm Chart (v1.19.0)

### K2.1 — Docker multi-tenant
- [x] docker-compose.override.yml: 2 müşteri (musteri1.localhost, musteri2.localhost)
- [x] nginx subdomain routing
- [x] Müşteri izolasyonu doğrulama

### K2.2 — SMB vs Enterprise karar dokümanı
- [x] docs/SMB_VS_ENTERPRISE.md

### K2.3 — Helm Chart
- [x] helm/symvera-tenant/ (Chart.yaml, values, templates)
- [x] Plan bazlı values (starter/growth/chain)
- [x] helm lint + dry-run

### K2.4 — Test & deploy

---

## K3 — Platform Controller (v1.20.0)

### K3.1 — Platform Controller backend (AYRI BİLEŞEN)
- [x] platform/platform-controller/ proje init
- [x] Platform DB schema (Prisma): tenants, billing_events, alerts, platform_users
- [x] PLATFORM_ADMIN JWT auth (ayrı secret)
- [x] Tenant CRUD API (create/list/get/suspend/activate)
- [x] Lisans server: plan limitleri izleme, aşım alarmı, grace period, hizmet kesme
- [x] Stripe webhook handler (payment.failed → grace → suspend)
- [x] Usage tracker (ses dakikası, rez sayısı, kullanıcı sayısı)
- [x] Alert engine: Slack webhook + SMS
- [x] MRR/ARR calculator
- [x] Impersonate (1 saat JWT)

### K3.2 — Platform frontend (AYRI UYGULAMA)
- [x] platform/platform-frontend/ React app (admin.symvera.ai)
- [x] Login (PLATFORM_ADMIN auth)
- [x] Dashboard: tenant listesi, MRR, alert'ler
- [x] Tenant detay: pod durumu, usage metrikleri, billing geçmişi
- [x] Tenant aksiyonları: suspend, activate, plan değiştir, impersonate
- [x] Alert yönetimi: alarm listesi, acknowledge
- [x] Veri silme: alarm göster, admin onay butonu (otomatik silme YOK)

### K3.3 — Docker-compose entegrasyonu
- [x] platform-controller + platform-frontend + platform-db container'ları
- [x] nginx: admin.localhost → platform-frontend

### K3.4 — Test & deploy

---

## K4 — Lisans Kontrolü & Ödeme (v1.21.0)

### K4.1 — License checker
- [x] Cron job: trial → grace → suspend (otomatik)
- [x] Veri silme: sadece alarm üret, admin karar verir
- [x] Voice usage counter + hard limit
- [x] Rez sayısı limit
- [x] Kullanıcı sayısı limit

### K4.2 — Stripe entegrasyonu
- [x] Stripe Customer per tenant
- [x] Stripe Checkout (plan seçimi)
- [x] Stripe webhook (payment.success → active, payment.failed → grace)
- [x] Stripe Customer Portal link

### K4.3 — Tenant self-service
- [x] /self/status, /self/usage, /self/billing
- [x] Plan upgrade/downgrade

### K4.4 — Test & deploy

---

## K5 — KVKK Export & Veri Yönetimi (v1.21.0)

### K5.1 — KVKK data export
- [x] Platform controller'dan tetiklenir (admin onayı ile)
- [x] PostgreSQL + MongoDB → şifreli ZIP
- [x] S3 upload + presigned URL
- [x] E-posta ile teslim

### K5.2 — Veri silme (MANUEL)
- [x] Platform frontend'te "Veri Sil" butonu (alarm + onay dialog)
- [x] Admin onayı → PII anonimleştirme
- [x] Namespace silme (K8s'te) — admin tetikler
- [x] Audit log

### K5.3 — Backup
- [x] Per-tenant backup CronJob
- [x] TimescaleDB retention policy
- [x] Backup doğrulama

### K5.4 — Test & deploy

---

## K6 — Production Hardening (v1.21.0)

### K6.1 — Güvenlik (K8s ile birlikte)
- [x] JWT RS256 + JWKS endpoint
- [x] PostgreSQL RLS (per-namespace)
- [x] Shared auth middleware npm paketi
- [x] Pod Security Standards
- [x] Sealed Secrets

### K6.2 — Ölçekleme
- [x] Cluster Autoscaler
- [x] Prometheus alert rules
- [x] Grafana namespace dashboard
- [x] External-DNS

### K6.3 — Test & deploy

---

## K7 — Self-Service Onboarding (v1.21.0)

### K7.1 — Kayıt akışı
- [x] symvera.ai signup → Stripe Checkout → otomatik provisioning
- [x] Setup Wizard (mevcut)

### K7.2 — SUPERADMIN (müşteri admin) paneli
- [x] Kullanıcı CRUD
- [x] Fatura görüntüleme
- [x] Usage dashboard
- [x] Plan upgrade UI

### K7.3 — Custom domain
- [x] cert-manager SSL
- [x] DNS CNAME

### K7.4 — Onboarding e-postalar

### K7.5 — Test & deploy → v1.21.0

---

## ZAMAN ÇİZELGESİ

| Sprint | Süre | Birikimli | Versiyon | Kritik çıktı |
|--------|------|-----------|----------|---------------|
| K1 | 1 hafta | 1 hafta | v1.18.0 | GUEST rol, RBAC doğrulama |
| K2 | 1 hafta | 2 hafta | v1.19.0 | Docker 2 müşteri, Helm Chart |
| K3 | 2 hafta | 4 hafta | v1.20.0 | **Platform Controller ayrı ürün** |
| K4 | 1 hafta | 5 hafta | v1.21.0 | Lisans server, Stripe |
| K5 | 1 hafta | 6 hafta | v1.21.0 | KVKK export (manuel silme) |
| K6 | 1 hafta | 7 hafta | v1.21.0 | RS256, RLS, hardening |
| K7 | 1 hafta | 8 hafta | v1.21.0 | Self-service, custom domain |

---

### Not: Prisma 7 Adapter Migration
Prisma 7 sürümüne geçişte `@prisma/adapter-pg` kullanımı planlanmaktadır. Mevcut Prisma client doğrudan PostgreSQL bağlantısı kullanır; Prisma 7 ile driver adapter pattern'ine geçiş yapılacaktır. Bu migration K7 sonrasında ayrı bir task olarak ele alınacaktır.

---

*Symvera K1-K7 Sprint Plan v2 — Platform Controller ayrı ürün — v1.21.0 tamamlandı — 2026-03-23*
