# SMB vs Enterprise Mimari Kararı

**Karar tarihi:** 2026-03-23
**Durum:** KİLİTLENDİ

## Karar

| Segment | İzolasyon | Altyapı | Fiyat |
|---------|-----------|---------|-------|
| **SMB (Starter/Growth)** | Shared services, tenantId FK izolasyonu | Tek namespace, ortak DB | 2.990-7.490 TL/ay |
| **Enterprise (Chain)** | Namespace izolasyonu, ayrı DB | Ayrı namespace per müşteri | 18.900+ TL/ay |

## Neden bu karar?

1. **Maliyet:** SMB müşterilere ayrı namespace = 12 pod × N müşteri. 30 SMB müşteri = 360 pod. Sürdürülemez.
2. **Marj:** Starter %14.8 marj — ayrı altyapı ile negatif marj olur.
3. **Güvenlik:** SMB müşteriler arası veri sızıntı riski uygulama katmanı izolasyonu + RBAC ile kabul edilebilir seviyede.
4. **Enterprise:** Chain müşteriler yüksek fiyat ödüyor, tam izolasyonu hak ediyor.

## Uygulama

### SMB (Starter/Growth)
- Tek K8s namespace: `symvera-shared`
- Ortak PostgreSQL, MongoDB, Redis
- tenantId FK izolasyonu (mevcut)
- RBAC + scopeToTenant middleware
- Horizontal scaling: HPA ile pod sayısı artırılır

### Enterprise (Chain)
- Ayrı namespace: `tenant-{slug}`
- Ayrı PostgreSQL, MongoDB, Redis StatefulSet'leri
- NetworkPolicy ile tam izolasyon
- Kendi Helm release'i

### Platform Controller
- `symvera-system` namespace
- Tüm segment'leri yönetir
- Lisans server: SMB ve Enterprise ayrımını bilir

## K2 Helm Chart etkileri
- `values-starter.yaml` / `values-growth.yaml` → shared namespace deploy
- `values-chain.yaml` → ayrı namespace deploy
- Helm Chart her iki modu desteklemeli
