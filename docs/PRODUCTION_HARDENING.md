# Production Hardening Checklist

**Version:** v1.22.0
**Last updated:** 2026-03-23

---

## TLS Configuration
- [x] TLS termination at nginx (self-signed for dev, Let's Encrypt for production)
- [x] HSTS header: `max-age=31536000; includeSubDomains`
- [x] HTTP → HTTPS 301 redirect configured (commented, ready to enable)
- [x] Security headers: X-Frame-Options, X-Content-Type-Options, CSP
- [x] TLS 1.2+ only (no SSLv3, TLS 1.0, TLS 1.1)

## Authentication & Authorization
- [x] MFA/2FA zorunlu OWNER/MANAGER roles (TOTP + backup codes)
- [x] HttpOnly cookie for refresh tokens
- [x] JWT refresh token rotation on every refresh
- [x] 15-minute access token TTL in production
- [x] Login rate limiting (Redis-based, per-email)
- [x] RBAC audit completed: 8 security gaps fixed across all route files (K1)
- [x] GUEST role: limited scope, 4h token, no admin access
- [x] OPERATIONS_ADMIN role removed, merged into SUPERADMIN (14 files)
- [x] Analytics: role-based access control on all 28 endpoints
- [x] Voice service: auth on SIP trunk management and LiveKit call endpoints
- [x] Notification service: role checks on template CRUD and confirmation settings
- [x] Menu service: dynamic pricing restricted to SUPERADMIN/OWNER
- [x] Stock service: STAFF blocked from suppliers, recipes, transactions, low-stock

## Container Security
- [x] SVG upload XSS validation
- [x] CI Trivy image scan on all Docker images
- [x] Startup env var validation (missing required vars → exit 1)
- [x] Path traversal protection on all file upload endpoints
- [x] No hardcoded secrets in Docker images

## K8s Security (Helm Chart)
- [x] Pod Security Standards: runAsNonRoot, readOnlyRootFilesystem, drop ALL capabilities
- [x] ServiceAccount per-tenant (automountServiceAccountToken: false)
- [x] NetworkPolicy: deny-all default + ingress-nginx + intra-tenant + DNS + HTTPS egress
- [x] NetworkPolicy: DNS egress restricted to kube-system namespace
- [x] Namespace isolation per tenant (SMB: shared, Enterprise: dedicated)

## Pending K8s Items
- [x] JWT RS256/JWKS endpoint implemented (backward compatible, HS256 fallback) — v1.22.0
- [x] License middleware in auth-service (Redis cached 5min, 402 on expired) — v1.22.0
- [x] SVG upload disabled (PNG/JPEG/WebP only) — v1.22.0
- [ ] **TODO:** PostgreSQL Row-Level Security (RLS) per tenant namespace
- [ ] **TODO:** Sealed Secrets for K8s secret management (currently plain Secrets)
- [ ] **TODO:** ArgoCD GitOps deployment pipeline
- [ ] **TODO:** Cluster Autoscaler configuration
- [ ] **TODO:** External-DNS for automatic DNS record management

## Monitoring & Alerting
- [x] Prometheus scraping all 8 backend services
- [x] Grafana dashboards (embeddable in superadmin panel)
- [x] Grafana auth proxy configured
- [x] Grafana IP restriction: Docker internal network + localhost only
- [x] Loki log aggregation from all services
- [x] AlertManager integration
- [ ] **TODO:** Prometheus alert rules for SLA thresholds (response time, error rate, uptime)
- [ ] **TODO:** PagerDuty / OpsGenie integration for on-call alerting
- [ ] **TODO:** Grafana namespace-level dashboards for multi-tenant monitoring

## Backup & Recovery
- [x] Pre-migration backup script: PostgreSQL + MongoDB + Redis (K1)
- [x] Rollback migration script with confirmation prompt (K1)
- [x] AES-256 backup encryption when BACKUP_ENCRYPTION_KEY is set
- [x] Daily automated backup (cron 03:00)
- [x] Disaster Recovery plan documented (S29-DR)
- [ ] **TODO:** Backup verification schedule (weekly restore test to staging)
- [ ] **TODO:** Per-tenant backup CronJob in K8s
- [ ] **TODO:** TimescaleDB retention policy (auto-drop old partitions)
- [ ] **TODO:** Offsite backup replication to secondary region

## CI/CD Security
- [x] npm audit --audit-level=high (no longer silently swallows failures)
- [x] OWASP Top 10 automated scan (owasp-check.sh)
- [x] Docker image vulnerability scanning (Trivy)
- [ ] **TODO:** SAST (Static Application Security Testing) integration
- [ ] **TODO:** Dependency bot for automated security updates

## Pentest
- [ ] **TODO:** Firma secimi (security vendor selection)
- [ ] **TODO:** Kapsam belgesi (scope document — API, frontend, mobile, infrastructure)
- [ ] **TODO:** Takvim belirleme (schedule — target: before first enterprise customer)
- [ ] **TODO:** Remediation plan template

## Incident Response
- [ ] **TODO:** Incident severity classification (P1-P4)
- [ ] **TODO:** On-call rotation schedule
- [ ] **TODO:** Incident communication template (status page, customer notification)
- [ ] **TODO:** Post-mortem template and process
- [ ] **TODO:** Security incident escalation path
- [ ] **TODO:** Data breach notification procedure (KVKK 72-hour requirement)

---

*Last reviewed: v1.21.0 — K1-K7 sprints complete*
