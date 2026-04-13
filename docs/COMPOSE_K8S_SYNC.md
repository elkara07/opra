# Compose ↔ K8s Senkronizasyon Kuralları

## Genel Prensip
Docker Compose **geliştirme ve test** ortamıdır. K8s **production** ortamıdır.
Her değişiklik önce Compose'da geliştirilip test edilir, sonra K8s'e taşınır.

## Senkronizasyon Checklist

Her sprint'in kabul kriterlerine bu checklist eklenir:

### Servis değişikliği yapıldığında:
- [ ] docker-compose.yml güncellendi
- [ ] Helm values güncellendi (CPU/RAM/env var)
- [ ] Helm deployment template güncellendi (yeni volume, port, vb.)

### Yeni servis eklendiğinde:
- [ ] docker-compose.yml'e container eklendi
- [ ] Helm chart'a deployment + service template eklendi
- [ ] nginx routing eklendi (Compose + Ingress)
- [ ] Network policy güncellendi

### Environment variable değiştiğinde:
- [ ] docker-compose.yml env section güncellendi
- [ ] .env.example güncellendi
- [ ] Helm values.yaml güncellendi
- [ ] Helm secret template güncellendi

### Veritabanı schema değiştiğinde:
- [ ] Prisma schema güncellendi
- [ ] Runtime migration (startup ALTER) eklendi
- [ ] Helm init-container veya migration job güncellendi
- [ ] Pre-migration backup script test edildi

## Drift Algılama

Aşağıdaki dosyalar eşleşmeli:

| Compose | K8s |
|---------|-----|
| docker-compose.yml services | helm/templates/deployment-*.yaml |
| docker-compose.yml env vars | helm/values.yaml + templates/secret.yaml |
| docker-compose.yml ports | helm/templates/service.yaml |
| docker-compose.yml volumes | helm/templates/pvc.yaml |
| nginx/conf.d/default.conf | helm/templates/ingress.yaml |

## Platform Controller (ayrı bileşen)

Platform Controller (platform/) Docker Compose'da:
```yaml
platform-controller:
  ...
  networks: [restoran-net]
platform-frontend:
  ...
  networks: [restoran-net]
```

K8s'te: `symvera-system` namespace'inde ayrı deploy.

## Sync Scope Table

Tum senkronize edilmesi gereken servisler:

| Service | Compose Service Name | K8s Resource | Namespace | Port |
|---------|---------------------|-------------|-----------|------|
| auth-service | auth-service | deployment/auth-service | tenant | 3006 |
| reservation-service | reservation-service | deployment/reservation-service | tenant | 3001 |
| floor-plan-service | floor-plan-service | deployment/floor-plan-service | tenant | 3002 |
| staff-service | staff-service | deployment/staff-service | tenant | 3003 |
| notification-service | notification-service | deployment/notification-service | tenant | 3004 |
| analytics-service | analytics-service | deployment/analytics-service | tenant | 3005 |
| voice-agent-service | voice-agent-service | deployment/voice-agent-service | tenant | 3007 |
| menu-service | menu-service | deployment/menu-service | tenant | 3008 |
| frontend | frontend | deployment/frontend | tenant | 3000 |
| nginx | nginx | ingress-nginx | tenant | 80/443 |
| platform-controller | platform-controller | deployment/platform-controller | symvera-system | 3009 |
| platform-frontend | platform-frontend | deployment/platform-frontend | symvera-system | 3010 |
| platform-db | platform-db | statefulset/platform-db | symvera-system | 5432 |
| postgres | postgres | statefulset/postgres | tenant | 5432 |
| mongo | mongo | statefulset/mongo | tenant | 27017 |
| redis | redis | statefulset/redis | tenant | 6379 |
| timescaledb | timescaledb | statefulset/timescaledb | tenant | 5433 |
| prometheus | prometheus | deployment/prometheus | monitoring | 9090 |
| grafana | grafana | deployment/grafana | monitoring | 3100 |
| loki | loki | deployment/loki | monitoring | 3200 |
| alertmanager | alertmanager | deployment/alertmanager | monitoring | 9093 |
