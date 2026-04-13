# Release Checklist

Her versiyon ciksinda kontrol edilecekler:

## Versiyon Senkronizasyonu
- [ ] `./scripts/release.sh <version>` calistirildi (tum package.json, manifest, Helm, README, auth-service)
- [ ] CHANGELOG.md yeni versiyon eklendi
- [ ] CHANGELOG.md onceki versiyonlar eksik degil (completeness check)
- [ ] Git tag olusturuldu (v{major}.{minor}.{patch})
- [ ] CI version consistency check yesil (manifest vs changelog vs chart)

## Test
- [ ] test.sh calistirildi (min 360/390)
- [ ] CI pipeline yesil
- [ ] Frontend build basarili

## Guvenlik
- [ ] npm audit — critical yok
- [ ] .env.example guncel
- [ ] Hardcoded secret/password yok

## Helm Chart
- [ ] helm lint basarili (helm lint helm/symvera-tenant/)
- [ ] helm template dry-run basarili
- [ ] Plan-specific values guncel (starter/growth/chain)

## Deployment
- [ ] Docker Compose build basarili
- [ ] Tum container'lar healthy
- [ ] nginx restart sonrasi 200
- [ ] Platform-db migration calistirildi (npx prisma migrate deploy --schema=platform/platform-controller/prisma/schema.prisma)
- [ ] Platform Controller healthy (GET /platform/health)
