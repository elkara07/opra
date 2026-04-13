# Disaster Recovery Plan
## RTO: 4 hours | RPO: 1 hour

---

## 1. Backup Schedule

| Bileşen | Sıklık | Yöntem | Saklama Süresi |
|---------|--------|--------|----------------|
| PostgreSQL | Her saat | WAL archiving | 30 gün |
| MongoDB | Her 6 saat | mongodump | 30 gün |
| Redis | Her saat | BGSAVE | 7 gün |
| .env & config | Her gün | Dosya kopyalama | 90 gün |

### Offsite Backup (S3)

- Tüm yedekler günlük olarak AWS S3'e gönderilir
- S3 bucket: `restoran-saas-backups-<environment>`
- Yedekler **AES-256** şifreleme ile korunur (BACKUP_ENCRYPTION_KEY)
- S3 versiyonlama aktif, lifecycle policy ile 90 gün sonra Glacier'a taşınır
- Cross-region replication aktif (ikincil bölge: eu-central-1)

```bash
# Manuel S3 yedekleme
./scripts/backup.sh --offsite

# S3 yedeklerini listeleme
aws s3 ls s3://restoran-saas-backups-prod/ --recursive
```

---

## 2. Communication Plan

### Bildirim Sırası

Felaket durumunda aşağıdaki sırayla bildirim yapılır:

| Sıra | Kim | İletişim Yöntemi | Süre |
|------|-----|-----------------|------|
| 1 | DevOps Ekibi | PagerDuty / Telefon | İlk 5 dakika |
| 2 | CTO / Teknik Lider | Telefon + Slack | İlk 15 dakika |
| 3 | Ürün Müdürü | Slack + E-posta | İlk 30 dakika |
| 4 | Müşteri Destek Ekibi | E-posta + Slack | İlk 30 dakika |
| 5 | Etkilenen Tenantlar | E-posta / SMS | İlk 1 saat |
| 6 | Üst Yönetim | E-posta | İlk 2 saat |

### Bildirim Şablonu

**Dahili bildirim:**
> [SEVİYE] Sistem kesintisi tespit edildi. Etkilenen servisler: [SERVİS_LİSTESİ]. Tahmini kurtarma süresi: [SÜRE]. Sorumlular: [İSİMLER].

**Müşteri bildirimi:**
> Değerli müşterimiz, sistemimizde teknik bir bakım/sorun nedeniyle geçici bir kesinti yaşanmaktadır. Tahmini çözüm süresi: [SÜRE]. Anlayışınız için teşekkür ederiz.

---

## 3. Escalation Matrix

| Seviye | Koşul | Sorumlu | Maksimum Yanıt Süresi |
|--------|-------|---------|----------------------|
| **SEV-1 (Kritik)** | Tüm sistem erişilemez | DevOps Lead + CTO | 15 dakika |
| **SEV-2 (Yüksek)** | Birden fazla servis çökmüş | DevOps Lead | 30 dakika |
| **SEV-3 (Orta)** | Tek servis çökmüş, workaround mevcut | DevOps Engineer | 1 saat |
| **SEV-4 (Düşük)** | Performans düşüklüğü | DevOps Engineer | 4 saat |

### Eskalasyon Akışı

```
Alarm tetiklendi (monitoring)
    ↓ (5 dk)
DevOps Engineer müdahale
    ↓ (15 dk çözüm yoksa)
DevOps Lead devreye girer
    ↓ (30 dk çözüm yoksa)
CTO devreye girer, SEV-1 ilan edilir
    ↓ (1 saat çözüm yoksa)
Üst yönetime bilgi, harici destek değerlendirilir
```

---

## 4. Recovery Steps

### 4.1 Altyapı Hazırlığı

1. Yeni sunucu / VM provision et (veya yedek sunucuyu aktif et)
2. Docker ve Docker Compose kurulumunu doğrula
3. Ağ yapılandırmasını kontrol et (firewall, DNS)

### 4.2 Veri Kurtarma

```bash
# 1. En son yedeği S3'ten indir
aws s3 cp s3://restoran-saas-backups-prod/latest/ ./restore/ --recursive

# 2. Yedekleri AES-256 ile çöz
./scripts/restore.sh --decrypt --source ./restore/

# 3. PostgreSQL geri yükleme
sudo docker compose exec -T postgres psql -U restoran -d restoran < restore/postgres_backup.sql

# 4. MongoDB geri yükleme
sudo docker compose exec -T mongo mongorestore --drop restore/mongo_backup/

# 5. Redis geri yükleme
sudo docker compose cp restore/dump.rdb redis:/data/dump.rdb
sudo docker compose restart redis
```

### 4.3 Servis Başlatma

```bash
# .env dosyasını geri yükle
cp restore/.env .env

# Tüm servisleri başlat
sudo docker compose up -d --build

# Sağlık kontrolü
curl http://localhost/api/v1/admin/health
```

### 4.4 DNS Güncelleme

1. DNS A/CNAME kaydını yeni sunucu IP'sine yönlendir
2. TTL süresinin dolmasını bekle (genellikle 5-15 dakika)
3. SSL sertifikasını yenile veya geri yükle

### 4.5 Doğrulama ve Bildirim

1. Recovery Validation Checklist'i tamamla (aşağıya bakın)
2. Tüm paydaşlara "sistem aktif" bildirimi gönder
3. Post-mortem toplantısı planla

---

## 5. Recovery Validation Checklist

Kurtarma sonrası aşağıdaki kontroller yapılmalıdır:

- [ ] Tüm servisler `docker compose ps` ile "Up" durumunda
- [ ] `/api/v1/admin/health` endpoint'i 200 döndürüyor
- [ ] PostgreSQL bağlantısı ve veri bütünlüğü doğrulandı
- [ ] MongoDB bağlantısı ve salon planı verileri doğrulandı
- [ ] Redis bağlantısı ve cache çalışıyor
- [ ] Auth servisi: login/logout çalışıyor
- [ ] Rezervasyon oluşturma/listeleme çalışıyor
- [ ] SMS/bildirim servisi çalışıyor (test SMS gönder)
- [ ] Salon planı yüklenebiliyor
- [ ] Analytics dashboard veri gösteriyor
- [ ] Voice agent (eğer aktifse) arama alabiliyor
- [ ] SSL sertifikası geçerli
- [ ] Rate limiting aktif
- [ ] Cron yedekleme job'ları yeniden kuruldu
- [ ] Monitoring/alerting yeniden yapılandırıldı
- [ ] `./scripts/test.sh` ile 326 testin tamamı geçiyor

---

## 6. Restore Test Procedure (Aylık)

Her ayın ilk Pazartesi günü staging ortamında restore testi yapılır:

### Test Adımları

1. **Hazırlık:** Staging sunucusunda mevcut verileri temizle
2. **Yedek İndirme:** S3'ten en güncel production yedeğini indir
3. **Geri Yükleme:** Recovery Steps 4.2 ve 4.3'ü staging üzerinde uygula
4. **Doğrulama:** Recovery Validation Checklist'i tamamla
5. **Performans Testi:** Temel API endpoint'lerine yük testi yap
6. **Raporlama:** Test sonuçlarını dokümante et

### Başarı Kriterleri

- Geri yükleme RTO (4 saat) içinde tamamlanmalı
- Veri kaybı RPO (1 saat) sınırını aşmamalı
- Tüm 326 API testi geçmeli
- Salon planları ve rezervasyonlar görüntülenebilmeli

### Test Rapor Formatı

```
Tarih: YYYY-MM-DD
Yedek Tarihi: YYYY-MM-DD HH:MM
Geri Yükleme Süresi: X saat Y dakika
Test Sonucu: BAŞARILI / BAŞARISIZ
Notlar: [varsa sorunlar ve çözümleri]
Test Eden: [Ad Soyad]
```

---

## 7. Contact Information

> **NOT:** Aşağıdaki bilgiler yer tutucu olarak eklenmiştir. Gerçek iletişim bilgileri ile güncellenmelidir.

| Rol | İsim | Telefon | E-posta |
|-----|------|---------|---------|
| DevOps Lead | [AD SOYAD] | [TELEFON] | [E-POSTA] |
| CTO | [AD SOYAD] | [TELEFON] | [E-POSTA] |
| Ürün Müdürü | [AD SOYAD] | [TELEFON] | [E-POSTA] |
| Müşteri Destek Lead | [AD SOYAD] | [TELEFON] | [E-POSTA] |
| Hosting/Cloud Sağlayıcı | [FİRMA ADI] | [DESTEK HATTI] | [DESTEK E-POSTA] |
| DNS Sağlayıcı | [FİRMA ADI] | [DESTEK HATTI] | [DESTEK E-POSTA] |

### Harici Servis Destek Hatları

| Servis | Destek Sayfası |
|--------|---------------|
| AWS | https://aws.amazon.com/support |
| Twilio | https://support.twilio.com |
| Stripe | https://support.stripe.com |
| LiveKit | https://livekit.io/support |

---

## 8. Revision History

| Tarih | Versiyon | Değişiklik |
|-------|----------|-----------|
| - | v1.0 | İlk DR planı oluşturuldu |
| - | v1.1 | S3 offsite backup eklendi |
| - | v1.2 | İletişim planı, eskalasyon matrisi, aylık restore testi, doğrulama checklist'i eklendi |
