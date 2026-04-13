# Symvera — Kubernetes Migration & Lisans Planı

**Versiyon:** 1.1
**Tarih:** 2026-03-22
**Kaynak:** Symvera_Kubernetes_Lisans_Plani_v4.docx + Symvera_Lisans_Planlama_Raporu_v3.docx
**Durum:** Docker Compose (mevcut) → Kubernetes (hedef)

---

## I. Mimari Genel Bakış

### Mevcut Durum (Docker Compose)
- Tek sunucu, tüm tenant'lar aynı DB ve servisler
- Rol: SUPERADMIN (Symvera) / OWNER / MANAGER / STAFF
- İzolasyon: tenantId foreign key ile DB seviyesinde

### Hedef Durum (Kubernetes)
- Her müşteri ayrı namespace
- Tam izole DB + servisler (veri sızıntısı sıfır)
- **İki katmanlı ingress:** Global (shared) + Tenant (per-namespace)
- Shared katman: ingress, monitoring, ArgoCD, cert-manager
- Merkezi kontrol düzlemi: platform-controller uygulaması

```
                        İnternet
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  KATMAN 1 — Global Ingress  (namespace: ingress-nginx)       │
│  nginx-ingress-controller (community — kubernetes/ingress-nginx) │
│                                                              │
│  • *.symvera.ai wildcard TLS termination (cert-manager)      │
│  • Subdomain → namespace routing                             │
│  • Per-tenant rate limiting (annotation bazlı)               │
│  • WAF kuralları (ModSecurity opsiyonel)                     │
│  • Global access log + Prometheus metrics                    │
│                                                              │
│  lezzet.symvera.ai  ──→  tenant-lezzet namespace             │
│  bogaz.symvera.ai   ──→  tenant-bogaz namespace              │
│  chain1.symvera.ai  ──→  tenant-chain1 namespace             │
│  admin.symvera.ai   ──→  symvera-system namespace            │
└─────────┬────────────────┬────────────────┬──────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│  SYMVERA KONTROL DÜZLEMİ  (namespace: symvera-system)      │
│                                                             │
│  platform-controller     ← Tenant lifecycle, lisans,       │
│  platform-db (PostgreSQL)   monitoring, alarm, MRR          │
│  platform-frontend       ← PLATFORM_ADMIN dashboard        │
│                                                             │
│  Prometheus + Grafana + Loki + AlertManager                 │
│  ArgoCD  ·  cert-manager  ·  External-DNS                   │
│  Cluster Autoscaler                                         │
└──────────┬──────────────────┬──────────────────┬────────────┘
           │                  │                  │
     ┌─────▼──────┐    ┌─────▼──────┐    ┌──────▼───────┐
     │ KATMAN 2    │    │ KATMAN 2    │    │ KATMAN 2     │
     │ Tenant      │    │ Tenant      │    │ Tenant       │
     │ Ingress     │    │ Ingress     │    │ Ingress      │
     │             │    │             │    │              │
     │ ns:lezzet   │    │ ns:bogaz    │    │ ns:chain1    │
     │ (Starter)   │    │ (Growth)    │    │  (Chain)     │
     │             │    │             │    │              │
     │ /api/v1/auth│    │ /api/v1/auth│    │ /api/v1/auth │
     │   →auth:3006│    │   →auth:3006│    │   →auth:3006 │
     │ /api/v1/res │    │ /api/v1/res │    │ /api/v1/res  │
     │   →res:3001 │    │   →res:3001 │    │   →res:3001  │
     │ /api/v1/... │    │ /api/v1/... │    │ /api/v1/...  │
     │ /→frontend  │    │ /→frontend  │    │ /→frontend   │
     │             │    │             │    │              │
     │ SUPERADMIN  │    │ SUPERADMIN  │    │ SUPERADMIN   │
     │ 1×OWNER     │    │ 1×OWNER     │    │ Sube1:OWNER  │
     │ N×STAFF     │    │ N×STAFF     │    │ Sube2:OWNER  │
     │ N×GUEST     │    │ N×GUEST     │    │ N×STAFF      │
     │             │    │             │    │ N×GUEST      │
     │ 8 svc       │    │ 8 svc       │    │ 8 svc        │
     │ 4 DB        │    │ 4 DB        │    │ 4 DB         │
     │ NetworkPol  │    │ NetworkPol  │    │ NetworkPol   │
     └─────────────┘    └─────────────┘    └──────────────┘
```

### İki Katmanlı Ingress Mimarisi

**Neden nginx-ingress community (kubernetes/ingress-nginx)?**
- Açık kaynak, ücretsiz, aktif bakım
- IngressClass desteği ile multi-instance çalışabilir
- Prometheus metrics endpoint native
- cert-manager ile sorunsuz entegrasyon
- NGINX Inc ticari versiyonu (nginxinc/kubernetes-ingress) DEĞİL

**Katman 1 — Global Ingress (shared, namespace: ingress-nginx)**

| Sorumluluk | Detay |
|-----------|-------|
| TLS Termination | Wildcard cert `*.symvera.ai` (cert-manager Let's Encrypt) |
| Subdomain Routing | `lezzet.symvera.ai` → `tenant-lezzet` namespace'teki Katman 2 Ingress'e |
| Rate Limiting | Per-tenant: `nginx.ingress.kubernetes.io/limit-rps` annotation |
| Access Log | Tüm trafik loglanır → Loki |
| Health Check | `/healthz` upstream probe |
| WAF (opsiyonel) | ModSecurity OWASP CRS (Aşama 3+) |

**Katman 2 — Tenant Ingress (per-namespace, IngressClass: nginx-tenant)**

| Sorumluluk | Detay |
|-----------|-------|
| Path Routing | `/api/v1/auth/*` → auth-service:3006, `/api/v1/reservations/*` → reservation-service:3001, vb. |
| Frontend Routing | `/` → frontend:3000 (SPA fallback) |
| Namespace İzolasyonu | Sadece kendi namespace'indeki servislere yönlendirir |
| Per-Servis Rate Limit | Servis bazlı ek rate limit (opsiyonel) |
| CORS | Tenant domain'ine özel CORS headers |

**NetworkPolicy ile İzolasyon:**

```yaml
# Her tenant namespace'inde: deny-all + allow from ingress-nginx only
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-except-ingress
  namespace: tenant-lezzet
spec:
  podSelector: {}          # Tüm pod'lar
  policyTypes:
    - Ingress
    - Egress
  ingress:
    # Sadece Global Ingress Controller'dan gelen trafik
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-nginx
    # Namespace içi pod'lar arası (servis→DB, servis→Redis)
    - from:
        - podSelector: {}
  egress:
    # DNS çözümleme
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
    # Namespace içi iletişim
    - to:
        - podSelector: {}
    # Dış API'ler (Twilio, Stripe, Anthropic, vb.)
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except:
              - 10.0.0.0/8        # Diğer namespace'lere erişim engeli
              - 172.16.0.0/12
              - 192.168.0.0/16
      ports:
        - protocol: TCP
          port: 443
---
# Namespace'ler arası direkt erişim tamamen engelli
# Tenant A → Tenant B: DENIED
# Tenant A → symvera-system: DENIED (monitoring hariç — Prometheus scrape)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-prometheus-scrape
  namespace: tenant-lezzet
spec:
  podSelector: {}
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: monitoring
      ports:
        - protocol: TCP
          port: 9090    # Prometheus metrics
```

**Trafik Akışı Örnek:**

```
Kullanıcı tarayıcı
  → https://lezzet.symvera.ai/api/v1/reservations
  → DNS: *.symvera.ai → Load Balancer IP
  → Katman 1 (Global Ingress): TLS terminate, subdomain=lezzet → tenant-lezzet
  → Katman 2 (Tenant Ingress): path=/api/v1/reservations → reservation-service:3001
  → reservation-service pod (namespace: tenant-lezzet)
  → PostgreSQL pod (namespace: tenant-lezzet) — aynı namespace, NetworkPolicy izin verir

Katman 2'deki Ingress başka namespace'e yönlendiremez — K8s Ingress kuralı
gereği backend service aynı namespace'te olmalıdır.
```

---

## II. Rol Modeli Değişikliği

### Geçiş Matrisi

| Katman | Mevcut Rol | Yeni Rol | Konum | Yetki |
|--------|-----------|----------|-------|-------|
| Platform | SUPERADMIN | **PLATFORM_ADMIN** | symvera-system namespace | Tüm namespace CRUD, impersonate, lisans, faturalama, infra monitoring |
| Müşteri | OWNER | **SUPERADMIN** | Tenant namespace | Kendi namespace'i: kullanıcı yönetimi, entegrasyon config, şube CRUD, fatura görüntüleme |
| Şube | MANAGER | **OWNER** | Tenant namespace / locationId | Şube bazlı: rezervasyon, personel, menü, analitik, ödeme |
| Şube | STAFF | **STAFF** | Tenant namespace / locationId | Kısıtlı: rez görüntüle/güncelle, KDS, walk-in |
| Şube | — | **GUEST** | Tenant namespace / locationId | Public: QR sipariş, menü görüntüle, sadakat puanı |

### JWT Token Yapısı (Yeni)

```json
{
  "sub": "user-uuid",
  "tenantId": "tenant-uuid",
  "namespace": "lezzet",
  "locationId": "location-uuid",
  "role": "OWNER",
  "permissions": ["res:read", "res:write", "staff:read", "analytics:read"]
}
```

### Yetki Matrisi

| Endpoint Grubu | PLATFORM_ADMIN | SUPERADMIN | OWNER | STAFF | GUEST |
|----------------|:-:|:-:|:-:|:-:|:-:|
| Platform API (namespace CRUD, MRR) | ✓ | ✗ | ✗ | ✗ | ✗ |
| Tenant ayarları, entegrasyon config | ✓ | ✓ | ✗ | ✗ | ✗ |
| Kullanıcı yönetimi (CRUD) | ✓ | ✓ | ✗ | ✗ | ✗ |
| Şube CRUD | ✓ | ✓ | ✗ | ✗ | ✗ |
| Rezervasyon CRUD | ✓ | ✓ | ✓ | Kısıtlı | ✗ |
| Personel yönetimi | ✓ | ✓ | ✓ | ✗ | ✗ |
| Menü yönetimi | ✓ | ✓ | ✓ | ✗ | ✗ |
| Analitik | ✓ | ✓ | ✓ | ✗ | ✗ |
| Salon planı | ✓ | ✓ | ✓ | Görüntüle | ✗ |
| KDS / Sipariş güncelle | ✓ | ✓ | ✓ | ✓ | ✗ |
| Walk-in / Rez durum güncelle | ✓ | ✓ | ✓ | ✓ | ✗ |
| QR Sipariş / Public menü | ✓ | ✓ | ✓ | ✓ | ✓ |
| Sadakat puanı görüntüle | ✓ | ✓ | ✓ | ✓ | ✓ |

---

## III. Lisans Durum Modeli

### Durum Geçiş Tablosu

```
TRIAL ──(ödeme yapıldı)──→ ACTIVE
  │                           │
  │(trial bitti)              │(ödeme başarısız)
  ▼                           ▼
SUSPENDED ←──(grace bitti)── GRACE (7 gün)
  │                           │
  │(30 gün)                   │(ödeme yapıldı)
  ▼                           ▼
DELETED ←──(iptal talebi)── ACTIVE
  ▲
  │(iptal onaylandı)
CANCELLED ──(30 gün)──→ DELETED
```

| Durum | Ses Kanalı | Panel | API | Tetikleyici |
|-------|:----------:|:-----:|:---:|-------------|
| TRIAL | Açık | Açık | Açık | Yeni kayıt |
| ACTIVE | Açık | Açık | Açık | Ödeme güncel |
| GRACE | Açık | Açık | Açık | Ödeme gecikmesi (1-7 gün) |
| SUSPENDED | **Kapalı** | Açık | Kısıtlı | Grace sona erdi / güvenlik / manuel |
| CANCELLED | **Kapalı** | Salt okunur | **Kapalı** | İptal talebi |
| DELETED | **Kapalı** | **Kapalı** | **Kapalı** | 30 gün sonra export + silme |

### Tenant Prisma Schema Eklentileri

```prisma
model Tenant {
  // ... mevcut alanlar ...

  // Lisans
  status            TenantStatus   @default(TRIAL)
  plan              PlanType       @default(STARTER)
  trialEndsAt       DateTime?
  graceEndsAt       DateTime?
  suspendedAt       DateTime?
  suspendReason     SuspendReason?
  deleteScheduledAt DateTime?
  lastPaymentAt     DateTime?
  exportCompletedAt DateTime?

  // Kullanım limitleri
  usageVoiceMinutes Int            @default(0)
  usageVoiceLimit   Int            @default(100)
  usageApiCalls     Int            @default(0)
  usageStorage      Int            @default(0)  // MB

  // K8s
  namespace         String?        @unique
  helmRelease       String?
}

enum TenantStatus {
  TRIAL
  ACTIVE
  GRACE
  SUSPENDED
  CANCELLED
  DELETED
}

enum SuspendReason {
  PAYMENT
  CANCELLED
  SECURITY
  MANUAL
  TRIAL
  USAGE
}

enum PlanType {
  STARTER
  GROWTH
  CHAIN
}
```

---

## IV. Kaynak Planlaması

### Servis Başına Kaynak

| Servis | Tip | CPU Req | CPU Lim | Mem Req | Mem Lim | Replicas (S/G/C) |
|--------|-----|---------|---------|---------|---------|:-:|
| auth-service | Node.js | 100m | 500m | 256Mi | 512Mi | 1/1/1 |
| reservation-service | Node.js | 200m | 1000m | 512Mi | 1Gi | 1/1/2 |
| floor-plan-service | Node.js | 100m | 500m | 256Mi | 512Mi | 1/1/1 |
| staff-service | Node.js | 100m | 500m | 256Mi | 512Mi | 1/1/1 |
| notification-service | Node.js | 100m | 500m | 256Mi | 512Mi | 1/1/1 |
| analytics-service | Python | 200m | 1000m | 512Mi | 1Gi | 1/1/1 |
| voice-agent-service | Python | 300m | 1500m | 512Mi | 1Gi | 1/2/2 |
| menu-service | Node.js | 100m | 500m | 256Mi | 512Mi | 1/1/1 |
| postgresql | DB | 500m | 2000m | 1Gi | 2Gi | 1/1/1 |
| mongodb | DB | 300m | 1500m | 512Mi | 1Gi | 1/1/1 |
| redis | Cache | 100m | 500m | 256Mi | 512Mi | 1/1/1 |
| timescaledb | DB | 200m | 1000m | 512Mi | 1Gi | 1/1/1 |
| **TOPLAM** | **12 pod** | **2300m** | — | **5GB** | — | — |

### PVC Boyutları (Plan Bazlı)

| DB | Starter | Growth | Chain | Saklama Süresi |
|----|---------|--------|-------|----------------|
| PostgreSQL | 5Gi | 5Gi | 10Gi | Abonelik + 30 gün |
| TimescaleDB | 2Gi | 2Gi | 4Gi | 1 ay (retention policy) |
| MongoDB | 5Gi | 5Gi | 10Gi | Süresiz (statik veri) |
| Redis | 1Gi | 1Gi | 2Gi | TTL bazlı |
| **Toplam** | **13Gi** | **13Gi** | **26Gi** | — |

### Node Büyüme Modeli

| Aşama | Müşteri | Altyapı | Deployment | EUR/ay |
|-------|---------|---------|------------|--------|
| Aşama 1 (0-15) | 8S+4G+1C | 2× Hetzner CX31, k3s | Helm Chart | €76-228 |
| Aşama 2 (15-30) | 20S+8G+2C | 3-4× Hetzner CX41 | Helm + ArgoCD | €228-532 |
| Aşama 3 (30-60) | 35S+15G+5C | AWS EKS t3.xlarge × 5-8 | ArgoCD + Autoscaler | €547-760 |
| Aşama 4 (60-100) | 60S+25G+10C | AWS EKS m5.2xlarge × 8+ | ArgoCD + KEDA | €1.800+ |

---

## V. Platform Controller App — Gereksinimler

### 5.1 Servis Yapısı

```
platform-controller/
├── src/
│   ├── index.ts                 # Express/Fastify API
│   ├── kubernetes/
│   │   ├── namespace.ts         # Namespace CRUD
│   │   ├── helm.ts              # Helm release management
│   │   ├── monitor.ts           # Pod/Node health checker
│   │   └── autoscaler.ts        # Scale actions
│   ├── license/
│   │   ├── checker.ts           # Cron: grace→suspend, 30d→delete
│   │   ├── stripe-webhook.ts    # Payment events
│   │   └── usage-tracker.ts     # Voice/API/storage counters
│   ├── tenant/
│   │   ├── provisioner.ts       # New tenant setup flow
│   │   ├── exporter.ts          # KVKK data export (ZIP)
│   │   └── destroyer.ts         # Namespace cleanup
│   ├── alerting/
│   │   ├── rules.ts             # Alert rule definitions
│   │   ├── slack.ts             # Slack webhook
│   │   └── sms.ts               # SMS alert (NetGSM/Twilio)
│   ├── routes/
│   │   ├── platform.routes.ts   # PLATFORM_ADMIN endpoints
│   │   ├── tenant-self.routes.ts# Tenant self-service
│   │   └── webhook.routes.ts    # Stripe, health
│   └── middleware/
│       └── platform-auth.ts     # PLATFORM_ADMIN JWT check
├── Dockerfile
├── package.json
└── prisma/
    └── schema.prisma            # Platform DB schema
```

### 5.2 API Endpoints

| Method | Endpoint | Rol | Açıklama |
|--------|----------|-----|----------|
| GET | /platform/tenants | PLATFORM_ADMIN | Tüm tenant listesi + durum + kaynak kullanımı |
| POST | /platform/tenants | PLATFORM_ADMIN | Yeni tenant oluştur (namespace + Helm + DNS) |
| GET | /platform/tenants/:slug | PLATFORM_ADMIN | Tenant detay: pods, events, resource usage |
| PATCH | /platform/tenants/:slug/status | PLATFORM_ADMIN | Durum değiştir (suspend/activate/grace) |
| DELETE | /platform/tenants/:slug | PLATFORM_ADMIN | Export trigger + namespace silme planla |
| POST | /platform/tenants/:slug/restart | PLATFORM_ADMIN | Tüm pod'ları restart et |
| POST | /platform/tenants/:slug/scale | PLATFORM_ADMIN | Servis replica sayısını değiştir |
| POST | /platform/tenants/:slug/impersonate | PLATFORM_ADMIN | Tenant admin olarak giriş (1 saat JWT) |
| GET | /platform/metrics | PLATFORM_ADMIN | Cluster genel: node sayısı, CPU%, RAM%, PVC |
| GET | /platform/mrr | PLATFORM_ADMIN | MRR, ARR, churn, tenant büyüme |
| GET | /platform/alerts | PLATFORM_ADMIN | Son 100 alert event |
| POST | /platform/alerts/:id/ack | PLATFORM_ADMIN | Alert'i onayla/kapat |
| GET | /self/status | SUPERADMIN | Kendi tenant durumu |
| GET | /self/usage | SUPERADMIN | Ses/API/storage kullanımı |
| GET | /self/billing | SUPERADMIN | Fatura geçmişi |
| POST | /self/upgrade | SUPERADMIN | Plan upgrade talebi |
| POST | /webhooks/stripe | — | Stripe ödeme olayları |

### 5.3 Cron Jobs

| Job | Zamanlama | İşlem |
|-----|----------|-------|
| license-checker | Her gece 02:00 | Grace→Suspend, 30gün→Export+Delete |
| usage-reset | Her ayın 1'i 00:00 | usageVoiceMinutes sıfırla |
| backup-check | Her gün 04:00 | Per-namespace backup doğrula |
| cert-expiry-check | Her gün 08:00 | SSL cert < 7 gün → alert |
| resource-report | Her gün 09:00 | Günlük kaynak kullanım raporu |

### 5.4 Alert Kuralları

| Alert | Koşul | Aksiyon | Bildirim |
|-------|-------|---------|----------|
| PodCrashLoop | restartCount > 5 (5dk) | Auto restart, log capture | Slack + SMS |
| HighCPU | namespace CPU > %80 (10dk) | HPA tetikle | Slack |
| HighMemory | namespace RAM > %85 (10dk) | Alert | Slack + SMS |
| PVCFull | PVC usage > %90 | Alert | Slack + SMS |
| DBConnectionExhausted | pool > %95 | Alert | Slack |
| NodeNotReady | node status != Ready | Alert | SMS |
| PaymentFailed | Stripe webhook | Grace başlat | Müşteriye e-posta |
| GraceExpired | graceEndsAt < now | Suspend | Müşteriye SMS + e-posta |
| TrialExpiring | trialEndsAt < now + 3d | Uyarı | Müşteriye e-posta |
| VoiceLimitNear | usage > %80 limit | Uyarı | Müşteriye e-posta |
| VoiceLimitReached | usage >= limit | Ses kanalı kapat | Müşteriye SMS |
| SSLExpiringSoon | cert expiry < 7d | cert-manager check | Slack |

---

## VI. Altyapı Gereksinimleri

### 6.1 Aşama 1 — Hetzner k3s (0-15 müşteri)

**Sunucu:**
- 2× Hetzner CX31 (4 vCPU, 16GB RAM, 160GB SSD) — €15.90/ay × 2
- 1× Hetzner CX21 (2 vCPU, 4GB RAM) — k3s master — €5.90/ay
- Hetzner Cloud Volumes (PVC backend) — GB başına €0.052/ay

**Yazılım:**
- k3s v1.29+ (lightweight K8s, `--disable traefik` ile kurulur)
- Helm v3.14+
- kubectl v1.29+
- cert-manager v1.14+
- **nginx-ingress-controller v1.10+ (community — kubernetes/ingress-nginx)**
  - Katman 1: Global ingress (namespace: ingress-nginx, IngressClass: nginx-global)
  - Katman 2: Tenant ingress kuralları (her namespace'te Ingress resource)
  - NOT: NGINX Inc ticari versiyonu (nginxinc/kubernetes-ingress) kullanılmaz
- Hetzner CSI driver (PVC)
- Hetzner Cloud Controller Manager

**DNS:**
- Wildcard DNS: `*.symvera.ai` → Load Balancer IP
- Hetzner Load Balancer (€5.49/ay)

**Toplam Aşama 1:** ~€43/ay altyapı

### 6.2 Aşama 2 — Hetzner Genişleme (15-30 müşteri)

**Ek sunucu:**
- 2× Hetzner CX41 (8 vCPU, 32GB RAM) — €29.90/ay × 2
- ArgoCD kurulumu
- Prometheus + Grafana + Loki stack

**Toplam Aşama 2:** ~€120/ay altyapı

### 6.3 Aşama 3 — AWS EKS (30-60 müşteri)

**Altyapı:**
- EKS cluster — $0.10/saat ($73/ay)
- 5-8× t3.xlarge (4 vCPU, 16GB) — ~$120/ay × count
- EBS gp3 volumes (PVC)
- nginx-ingress-controller (community) — aynı iki katmanlı mimari, ALB yerine NLB + nginx
- cert-manager (Let's Encrypt veya AWS ACM)
- Route53 DNS + External-DNS controller
- Cluster Autoscaler

**Toplam Aşama 3:** ~€547-760/ay

### 6.4 Aşama 4 — AWS Ölçek (60-100 müşteri)

**Altyapı:**
- 8+× m5.2xlarge (8 vCPU, 32GB)
- KEDA (event-driven autoscaling)
- Multi-AZ deployment
- RDS for shared platform DB

**Toplam Aşama 4:** ~€1.800+/ay

---

## VII. Kurulum Prosedürü

### 7.1 Aşama 1 Kurulum — k3s Cluster

```bash
# ── 1. Master Node (CX21) ────────────────────────────
ssh root@master-ip

# k3s kur
curl -sfL https://get.k3s.io | sh -s - server \
  --disable traefik \
  --write-kubeconfig-mode 644 \
  --tls-san master-ip \
  --tls-san symvera.ai

# Token al (worker'lar için)
cat /var/lib/rancher/k3s/server/node-token

# ── 2. Worker Nodes (CX31 × 2) ───────────────────────
ssh root@worker1-ip
curl -sfL https://get.k3s.io | K3S_URL=https://master-ip:6443 \
  K3S_TOKEN="<token>" sh -

# Worker 2 aynı komut
ssh root@worker2-ip
curl -sfL https://get.k3s.io | K3S_URL=https://master-ip:6443 \
  K3S_TOKEN="<token>" sh -

# ── 3. kubectl doğrulama (master'da) ─────────────────
kubectl get nodes
# NAME      STATUS   ROLES                  AGE   VERSION
# master    Ready    control-plane,master   1m    v1.29.x
# worker1   Ready    <none>                 30s   v1.29.x
# worker2   Ready    <none>                 30s   v1.29.x

# ── 4. Helm kur ──────────────────────────────────────
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# ── 5. Hetzner CSI Driver (PVC desteği) ──────────────
kubectl apply -f https://raw.githubusercontent.com/hetznercloud/csi-driver/main/deploy/kubernetes/hcloud-csi.yml
# Secret: Hetzner API token
kubectl create secret generic hcloud-csi -n kube-system \
  --from-literal=token=<HETZNER_API_TOKEN>

# ── 6. KATMAN 1 — Global nginx-ingress (community) ───
# NOT: kubernetes/ingress-nginx (community), nginxinc DEĞİL
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace \
  --set controller.service.type=LoadBalancer \
  --set controller.ingressClassResource.name=nginx-global \
  --set controller.ingressClassResource.controllerValue=k8s.io/ingress-nginx-global \
  --set controller.config.use-forwarded-headers="true" \
  --set controller.config.proxy-body-size="10m" \
  --set controller.config.limit-req-status-code="429" \
  --set controller.metrics.enabled=true \
  --set controller.metrics.serviceMonitor.enabled=true

# Label ingress-nginx namespace (NetworkPolicy selector için)
kubectl label namespace ingress-nginx kubernetes.io/metadata.name=ingress-nginx --overwrite

# ── 7. cert-manager (Let's Encrypt) ──────────────────
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set installCRDs=true

# ClusterIssuer
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@symvera.ai
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

# ── 8. Monitoring Stack ──────────────────────────────
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set grafana.adminPassword=<STRONG_PASSWORD> \
  --set prometheus.prometheusSpec.retention=30d

# Loki
helm repo add grafana https://grafana.github.io/helm-charts
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --set promtail.enabled=true

# ── 9. Symvera System Namespace ──────────────────────
kubectl create namespace symvera-system

# Platform DB
kubectl apply -n symvera-system -f - <<EOF
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: platform-db
spec:
  serviceName: platform-db
  replicas: 1
  selector:
    matchLabels:
      app: platform-db
  template:
    metadata:
      labels:
        app: platform-db
    spec:
      containers:
      - name: postgres
        image: postgres:16-alpine
        env:
        - name: POSTGRES_DB
          value: symvera_platform
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: platform-db-secret
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: platform-db-secret
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
EOF

# ── 10. DNS Ayarı ────────────────────────────────────
# Hetzner DNS veya Cloudflare'da:
# *.symvera.ai  →  A  →  <Load Balancer IP>
# symvera.ai    →  A  →  <Load Balancer IP>
```

### 7.2 İlk Tenant Deploy (Helm)

```bash
# ── Tenant namespace oluştur ─────────────────────────
helm install lezzet ./helm/symvera-tenant \
  --namespace tenant-lezzet --create-namespace \
  -f helm/symvera-tenant/values-starter.yaml \
  --set tenant.slug=lezzet \
  --set tenant.plan=starter \
  --set tenant.domain=lezzet.symvera.ai \
  --set secrets.jwtSecret=$(openssl rand -hex 64) \
  --set secrets.dbPassword=$(openssl rand -base64 24) \
  --set secrets.mongoPassword=$(openssl rand -base64 24) \
  --set secrets.redisPassword=$(openssl rand -base64 24)

# ── Doğrulama ────────────────────────────────────────
kubectl get pods -n tenant-lezzet
kubectl get ingress -n tenant-lezzet
curl -I https://lezzet.symvera.ai
```

---

## VIII. Sprint Planı

### Sprint K1 — Rol Refaktöring & Auth Hazırlık
**Süre:** 1 hafta
**Hedef:** Mevcut uygulama yeni rol modeliyle çalışır (Docker Compose üzerinde)

| # | Görev | Dosya/Konum | Detay |
|---|-------|-------------|-------|
| 1.1 | Prisma schema: Tenant model lisans alanları | auth-service/prisma/schema.prisma | status, trialEndsAt, graceEndsAt, suspendedAt, suspendReason, deleteScheduledAt, usageVoiceMinutes, usageVoiceLimit, lastPaymentAt, exportCompletedAt, namespace |
| 1.2 | Prisma schema: User model rol enum güncelle | auth-service/prisma/schema.prisma | PLATFORM_ADMIN, SUPERADMIN, OWNER, STAFF, GUEST |
| 1.3 | Auth middleware: Rol geçiş uyumluluğu | auth-service/src/middleware/auth.middleware.js | SUPERADMIN → PLATFORM_ADMIN mapping, yeni SUPERADMIN = eski OWNER |
| 1.4 | Auth middleware: Tenant status check | auth-service/src/middleware/auth.middleware.js | deleted/cancelled → 401, suspended + voice → 503 |
| 1.5 | Frontend: Rol guard güncellemesi | frontend/src/App.jsx, Layout.jsx | SuperadminRoute → PlatformAdminRoute, yeni SUPERADMIN sidebar |
| 1.6 | Frontend: GUEST rol UI | frontend/src/pages/ | QR sipariş, menü, sadakat — GUEST erişim |
| 1.7 | Seed script: Test kullanıcıları güncelle | scripts/test.sh | platform_admin@test.com, superadmin@test.com (eski owner), owner@test.com (eski manager) |
| 1.8 | Migration script | scripts/migrate-roles.sql | Mevcut SUPERADMIN → PLATFORM_ADMIN, OWNER → SUPERADMIN, MANAGER → OWNER |
| 1.9 | Test güncelleme | services/*/src/__tests__/ | Yeni rol isimleriyle test düzelt |

**Kabul Kriterleri:**
- [ ] Mevcut Docker Compose ortamında tüm roller doğru çalışıyor
- [ ] platform_admin@test.com PLATFORM_ADMIN olarak giriş yapabiliyor
- [ ] superadmin@test.com eski OWNER yetkileriyle giriyor
- [ ] GUEST rolü QR sipariş verebiliyor
- [ ] 380 test geçiyor
- [ ] CI yeşil

---

### Sprint K2 — Helm Chart & Kubernetes Manifests
**Süre:** 1 hafta
**Hedef:** `helm install` ile tek tenant deploy edilebilir

| # | Görev | Dosya/Konum | Detay |
|---|-------|-------------|-------|
| 2.1 | Chart.yaml + values.yaml (defaults) | helm/symvera-tenant/ | appVersion, chart version, default values |
| 2.2 | values-starter/growth/chain.yaml | helm/symvera-tenant/ | Plan bazlı CPU/RAM/PVC/replica override |
| 2.3 | Deployment templates (8 servis) | helm/symvera-tenant/templates/ | Her servis için deployment.yaml (env, resources, probes) |
| 2.4 | StatefulSet templates (4 DB) | helm/symvera-tenant/templates/ | PostgreSQL, MongoDB, Redis, TimescaleDB |
| 2.5 | Service templates | helm/symvera-tenant/templates/ | ClusterIP per service |
| 2.6 | Katman 2 Ingress template | helm/symvera-tenant/templates/ | IngressClass: nginx-global, path routing → servisler. Katman 1'den gelen trafiği namespace içi servislere yönlendirir |
| 2.7 | PVC templates | helm/symvera-tenant/templates/ | Plan bazlı boyutlar |
| 2.8 | NetworkPolicy (iki katmanlı izolasyon) | helm/symvera-tenant/templates/ | deny-all + allow from ingress-nginx ns + allow namespace internal + allow prometheus scrape. Namespace'ler arası trafik tamamen engelli |
| 2.9 | ConfigMap + Secret | helm/symvera-tenant/templates/ | DB URLs, JWT secret, API keys |
| 2.10 | ResourceQuota + LimitRange | helm/symvera-tenant/templates/ | Namespace bazlı kaynak limiti |
| 2.11 | HPA template | helm/symvera-tenant/templates/ | reservation-service, voice-agent auto scale |
| 2.12 | CronJob: DB backup | helm/symvera-tenant/templates/ | Günlük pg_dump + mongodump |
| 2.13 | Liveness/Readiness/Startup probes | tüm deployment templates | /health endpoint check |
| 2.14 | Docker image build & push | .github/workflows/ | GitHub Actions → container registry |
| 2.15 | Helm chart test | — | helm lint + helm template + dry-run |

**Kabul Kriterleri:**
- [ ] `helm lint` başarılı
- [ ] `helm install --dry-run` hatasız
- [ ] Tek tenant k3s'e deploy edilebiliyor
- [ ] Tüm 12 pod Running
- [ ] Ingress üzerinden HTTPS erişim
- [ ] NetworkPolicy namespace izolasyonu çalışıyor

---

### Sprint K3 — Platform Controller v1
**Süre:** 2 hafta
**Hedef:** Yeni tenant 1 API çağrısıyla oluşturulur, monitoring çalışır

| # | Görev | Dosya/Konum | Detay |
|---|-------|-------------|-------|
| 3.1 | Platform controller Node.js/TS projesi init | platform-controller/ | Express + Prisma + kubernetes/client-node |
| 3.2 | Platform DB Prisma schema | platform-controller/prisma/ | Tenant registry, alert log, billing history |
| 3.3 | PLATFORM_ADMIN auth (JWT) | platform-controller/src/middleware/ | Ayrı JWT secret, platform kullanıcı tablosu |
| 3.4 | Tenant CRUD API | platform-controller/src/routes/ | POST/GET/PATCH/DELETE /platform/tenants |
| 3.5 | Namespace provisioner | platform-controller/src/kubernetes/ | kubectl create ns + helm install + DNS |
| 3.6 | Namespace destroyer | platform-controller/src/kubernetes/ | KVKK export → helm uninstall → kubectl delete ns |
| 3.7 | Pod/Node health monitor | platform-controller/src/kubernetes/ | K8s API watch: pod status, events |
| 3.8 | Prometheus metrics query | platform-controller/src/kubernetes/ | CPU%, RAM%, PVC% per namespace |
| 3.9 | Alert engine | platform-controller/src/alerting/ | Rule evaluation, Slack webhook, SMS |
| 3.10 | MRR calculator | platform-controller/src/license/ | Tenant plan × count, churn tracking |
| 3.11 | Impersonate endpoint | platform-controller/src/routes/ | 1 saat JWT, audit log |
| 3.12 | Platform frontend (React) | platform-controller/frontend/ | Tenant listesi, detay, metrics, alerts, MRR |
| 3.13 | Dockerfile + Helm chart | platform-controller/ | Deploy to symvera-system namespace |
| 3.14 | ArgoCD kurulumu | — | ArgoCD install + repo connection + ApplicationSet |

**Kabul Kriterleri:**
- [ ] POST /platform/tenants ile yeni namespace + servisler deploy oluyor
- [ ] Platform dashboard'da tüm tenant'lar ve pod durumları görülüyor
- [ ] CPU/RAM/PVC metrikleri namespace bazlı görülüyor
- [ ] Alert: CrashLoopBackOff → Slack notification
- [ ] Impersonate: PLATFORM_ADMIN tenant'a giriş yapabiliyor
- [ ] ArgoCD tenant Application'ları sync ediyor

---

### Sprint K4 — Lisans Kontrolü & Ödeme
**Süre:** 1 hafta
**Hedef:** Trial/Grace/Suspend/Delete otomatik çalışır

| # | Görev | Dosya/Konum | Detay |
|---|-------|-------------|-------|
| 4.1 | license-checker cron job | platform-controller/src/license/ | Her gece 02:00: grace→suspend, 30d→delete |
| 4.2 | Stripe webhook handler | platform-controller/src/license/ | payment.failed → grace, payment.success → active |
| 4.3 | Trial yönetimi | platform-controller/src/license/ | trialEndsAt kontrolü, -3 gün/-1 gün uyarı |
| 4.4 | Voice usage counter | voice-agent-service | Her çağrı sonrası usageVoiceMinutes++ |
| 4.5 | Voice limit enforcement | auth middleware + voice-agent | limit aşımında 503, %80'de uyarı |
| 4.6 | Aylık usage reset | platform-controller cron | Her ayın 1'i usageVoiceMinutes=0 |
| 4.7 | Suspend aksiyon | platform-controller | voice-agent replica=0, API kısıtlı mod |
| 4.8 | Müşteri bildirimleri | platform-controller | Grace başlangıcı, suspend, trial bitiş → SMS + e-posta |
| 4.9 | Tenant self-service API | platform-controller | /self/status, /self/usage, /self/billing |
| 4.10 | Plan upgrade/downgrade | platform-controller | Helm values güncelle + rolling restart |

**Kabul Kriterleri:**
- [ ] Trial 14 gün sonra otomatik suspend
- [ ] Ödeme başarısız → 7 gün grace → suspend
- [ ] Ses limiti aşımı → ses kanalı kapanıyor
- [ ] Suspend edilen tenant panel'e giriyor ama ses kanalı kapalı
- [ ] 30 gün sonra export + namespace silme

---

### Sprint K5 — KVKK Export & Veri Temizleme
**Süre:** 1 hafta
**Hedef:** Abonelik sonlandırma → otomatik veri export + silme

| # | Görev | Dosya/Konum | Detay |
|---|-------|-------------|-------|
| 5.1 | KVKK data export endpoint | platform-controller/src/tenant/ | PostgreSQL + MongoDB → şifreli ZIP |
| 5.2 | S3 upload | platform-controller/src/tenant/ | ZIP → S3 bucket, presigned URL |
| 5.3 | E-posta ile teslim | platform-controller/src/tenant/ | SendGrid: indirme linki (7 gün geçerli) |
| 5.4 | PII anonimleştirme | platform-controller/src/tenant/ | İsim, telefon, e-posta → hash |
| 5.5 | Namespace silme | platform-controller/src/kubernetes/ | ArgoCD Application delete + kubectl delete ns |
| 5.6 | Audit log | platform-controller/src/tenant/ | Silme kaydı: tarih, slug, export URL |
| 5.7 | Per-namespace backup CronJob | helm/symvera-tenant/templates/ | Günlük pg_dump + mongodump → S3 |
| 5.8 | TimescaleDB retention policy | helm/symvera-tenant/templates/ | 30 gün otomatik temizlik |

**Kabul Kriterleri:**
- [ ] Suspend edilen tenant 30. günde otomatik export + silme
- [ ] ZIP dosyası e-posta ile müşteriye teslim
- [ ] PII verileri anonimleştirilmiş
- [ ] Namespace tamamen silinmiş
- [ ] Audit log'da kayıt var

---

### Sprint K6 — Production Hardening & Ölçekleme
**Süre:** 1 hafta
**Hedef:** Production-ready cluster

| # | Görev | Dosya/Konum | Detay |
|---|-------|-------------|-------|
| 6.1 | Pod Security Standards | helm templates | Restricted profile: non-root, read-only FS |
| 6.2 | RBAC: ServiceAccount per tenant | helm templates | En az yetki prensibi |
| 6.3 | Sealed Secrets veya External Secrets | cluster | API key'ler güvenli secret management |
| 6.4 | Image scanning (Trivy) | CI/CD | Her build'de vulnerability scan |
| 6.5 | Cluster Autoscaler config | cluster | Hetzner CCM veya AWS ASG |
| 6.6 | Prometheus alert rules YAML | monitoring/ | Tüm alert kuralları tanımı |
| 6.7 | Grafana dashboard: namespace bazlı | monitoring/ | CPU, RAM, PVC, pod count per tenant |
| 6.8 | External-DNS controller | cluster | Otomatik DNS kaydı: slug.symvera.ai |
| 6.9 | Backup doğrulama CronJob | cluster | Günlük restore test |
| 6.10 | Load test (k6) | tests/ | 10 tenant simülasyonu |
| 6.11 | Runbook dokümanı | docs/ | Operasyonel prosedürler |
| 6.12 | DR testi | — | Cluster yeniden oluşturma + restore |

**Kabul Kriterleri:**
- [ ] Tüm pod'lar non-root çalışıyor
- [ ] API key'ler Sealed Secrets ile korunuyor
- [ ] Trivy scan: critical vulnerability yok
- [ ] Cluster Autoscaler yeni node ekleyip çıkarabiliyor
- [ ] 10 tenant simülasyonu başarılı
- [ ] DR restore < 30 dakika

---

### Sprint K7 — Müşteri Onboarding & Self-Service
**Süre:** 1 hafta
**Hedef:** Yeni müşteri kendi kendine kayıt olup kullanmaya başlayabilir

| # | Görev | Dosya/Konum | Detay |
|---|-------|-------------|-------|
| 7.1 | Symvera marketing sitesi | symvera.ai | Landing page, pricing, signup |
| 7.2 | Self-service signup flow | platform-controller | E-posta → plan seç → ödeme → namespace oluştur |
| 7.3 | Stripe Checkout entegrasyonu | platform-controller | Plan seçimi → ödeme → otomatik provisioning |
| 7.4 | Tenant setup wizard (mevcut) | frontend | İlk giriş → wizard → restoran kurulumu |
| 7.5 | SUPERADMIN panel: kullanıcı yönetimi | frontend | OWNER/STAFF/GUEST ekle/sil |
| 7.6 | SUPERADMIN panel: fatura görüntüleme | frontend | Stripe Customer Portal link |
| 7.7 | SUPERADMIN panel: usage dashboard | frontend | Ses dakikası, API çağrı, storage |
| 7.8 | Plan upgrade/downgrade UI | frontend | Growth'a geç → Helm values güncelle |
| 7.9 | Tenant custom domain desteği | ingress, cert-manager | Müşteri kendi domain'ini bağlayabilir |
| 7.10 | Onboarding e-posta serisi | platform-controller | Hoşgeldin, setup rehberi, 3 gün sonra check-in |

**Kabul Kriterleri:**
- [ ] Yeni müşteri web sitesinden kayıt olabiliyor
- [ ] Ödeme sonrası ~5 dk içinde namespace hazır
- [ ] Setup wizard ile restoran konfigürasyonu tamamlanıyor
- [ ] SUPERADMIN kendi kullanıcılarını yönetebiliyor
- [ ] Plan upgrade Helm values'ı güncelleniyor

---

## IX. Genel Zaman Çizelgesi

| Sprint | İçerik | Süre | Birikimli | Çıktı |
|--------|--------|------|-----------|-------|
| **K1** | Rol refaktöring | 1 hafta | 1 hafta | Mevcut app yeni rollerle çalışır |
| **K2** | Helm Chart + K8s manifests | 1 hafta | 2 hafta | Tek tenant deploy edilebilir |
| **K3** | Platform Controller + ArgoCD | 2 hafta | 4 hafta | Tenant lifecycle otomatik |
| **K4** | Lisans + Ödeme kontrolü | 1 hafta | 5 hafta | Trial/Grace/Suspend çalışır |
| **K5** | KVKK Export + Veri temizleme | 1 hafta | 6 hafta | Abonelik sonlandırma otomatik |
| **K6** | Production hardening | 1 hafta | 7 hafta | Güvenlik + ölçekleme hazır |
| **K7** | Self-service onboarding | 1 hafta | 8 hafta | Müşteri kendi kendine kayıt olur |

**Toplam:** ~8 hafta (2 ay)

---

## X. Fiyatlandırma Özeti

| Plan | Fiyat (TL) | EUR | Dahil Ses | Marj | Namespace |
|------|-----------|-----|-----------|------|-----------|
| **Starter** | 2.990 ₺/ay | €58 | 100 dk | %14.8 | 1 |
| **Growth** | 7.490 ₺/ay | €146 | 400 dk | %60.7 | 1 |
| **Chain** | 18.900 ₺/ay | €368 | 600 dk | %82.7 | 1 (multi-location) |

Ses aşım: Starter 18 ₺/dk, Growth 14 ₺/dk, Chain 12 ₺/dk

---

## XI. Checklist — Başlamadan Önce

- [ ] Hetzner hesabı açılmış ve API token alınmış
- [ ] Domain (symvera.ai) DNS yönetimi erişilebilir
- [ ] Stripe hesabı açılmış, plan price ID'leri oluşturulmuş
- [ ] Container registry seçilmiş (GHCR / Docker Hub / Hetzner Registry)
- [ ] S3 bucket (backup + KVKK export) hazır (AWS S3 veya Hetzner Object Storage)
- [ ] Slack webhook URL'si (alert bildirimleri)
- [ ] SendGrid hesabı (müşteri bildirimleri)
- [ ] SSL wildcard cert veya cert-manager Let's Encrypt konfigürasyonu
- [ ] Git repo: Helm chart + ArgoCD ApplicationSet
- [ ] Monitoring: Grafana admin şifreleri belirlenmiş

---

*Symvera — Kubernetes Migration Plan v1.1 · Gizli — Şirket İçi*
*v1.1 değişiklik: İki katmanlı ingress mimarisi (Global + Tenant), nginx-ingress community (kubernetes/ingress-nginx), NetworkPolicy izolasyon kuralları, trafik akış şeması eklendi*
