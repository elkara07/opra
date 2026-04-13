# Faz 3 — Menü Tarama & UX Bulguları

---

## Dashboard Bulguları

### Çalışan
- Bugünkü özet anlamlı metrikler gösteriyor (toplam, onaylı, oturan, tamamlanan, gelmedi, iptal)
- Çalışma saatleri ve timezone desteği var
- Walk-in özelliği salon durumundan çalışıyor
- Masa çakışma uyarıları var (oturmuş + süresi geçmiş)
- Onboarding banner düzgün çalışıyor

### Eksik / Sorunlu
1. **Doluluk oranı yok** — "3/40 masa dolu (%7.5)" bilgisi eksik
2. **Misafir ismi araması yok** — 50 masalı restoranda "Ahmet nereye oturacak?" sorusu cevaplanamıyor
3. **Kapasite haritası 20 masa ile sınırlı** — büyük restoranlar için yetersiz
4. **Saatlik yoğunluk görselliği kötü** — 140px yükseklik, küçük etiketler
5. **Anlık doluluk** — şu an içeride kaç kişi oturuyor bilgisi yok

---

## Rezervasyon Akışı Bulguları

### KRITIK: Walk-in Akışı Ters
**Mevcut:** Masa seç → Kişi sayısı gir
**Olması gereken:** Kişi sayısı gir → Uygun masalar filtrelensin → En verimli masa önerilsin

### KRITIK: Akıllı Masa Seçimi Yok (GUI)
- 2 kişilik parti 6 kişilik masayı aynı öncelikte görüyor
- Voice agent'ta var (score bazlı, en küçük uygun masa önce) ama GUI'de yok
- **Çözüm:** Voice agent'ın `smart_table_selection` mantığını availability endpoint'ine taşı

### Availability Endpoint Sorunları
- `duration` parametresi hardcoded 90dk — tenant'ın `avgSittingMinutes` ayarını KULLANMIYOR
- "Bu masada biri hâlâ oturuyor olabilir" uyarısı API'den gelmiyor
- Masalar kapasiteye göre sıralanmıyor

### Çalışma Saatleri ✓
- Backend'de tam doğrulama var (gece yarısı geçişi dahil)
- Walk-in çalışma saati kontrolünü bypass ediyor (doğru — müşteri zaten orada)
- Voice agent çalışma saati kontrolü YAPMIYOR — backend'e güveniyor (kabul edilebilir)

### avgSittingMinutes
- Prisma'da var (`@default(90)`), backend kullanıyor
- Ama **frontend'de ayar UI'ı yok** — tenant bunu ayarlayamıyor
- Availability endpoint bu değeri kullanmıyor (hardcoded 90)

---

## Kural Motoru Bulguları

### KRITIK: Kurallar Dağınık

| Kural | GUI | Voice Agent | Backend API |
|-------|:---:|:-----------:|:-----------:|
| Çalışma saati kontrolü | ✗ | ✗ | ✓ |
| Masa kapasitesi doğrulama | Kısmen | ✓ (score) | ✓ |
| Zaman çakışması | ✗ | ✗ | ✓ |
| Akıllı masa önerisi | ✗ | ✓ | ✗ |
| Kişi sayısına göre filtreleme | ✗ | ✓ | ✗ |
| SEATED uyarısı | ✓ (confirm) | ✗ | ✗ |
| Telefon doğrulama | ✓ | ✗ | ✓ |
| XSS koruması | ✗ | ✗ | ✓ |

**Çözüm:** Availability endpoint'ini "akıllı" yapıp hem GUI hem voice agent oradan alsın.

---

## Timeline / Zaman Çizelgesi Bulguları
- Sabit 80px sol kolon — dar ekranlarda sıkışıyor
- Her saat 80px — geniş ekranlarda boş alan bırakılıyor
- Responsive breakpoint yok
- Geniş ekranda timeline genişlemeli

---

## Ayarlar Sayfası Bulguları
- Çalışma saatleri UI ✓ (7 gün, açılış/kapanış, kapalı seçeneği)
- `avgSittingMinutes` UI ✗ — tenant bu ayarı göremez/değiştiremez
- DID mapping yönetimi UI ✗ — SUPERADMIN panelinden yapılmalı

---

## Aksiyon Planı — Öncelik Sırası

### Sprint 1: Temel UX Düzeltmeleri (En Yüksek Etki)

#### 1.1 Availability Endpoint'ini Akıllı Yap
- `avgSittingMinutes`'ı tenant'tan çek, hardcoded 90'ı kaldır
- Masaları kapasiteye göre sırala (küçükten büyüğe)
- SEATED masalar için uyarı flag'i ekle
- Kişi sayısına göre filtrele ve `suitability_score` döndür

#### 1.2 Walk-in Akışını Düzelt
- Kişi sayısı ÖNCE sorulsun
- Masalar kişi sayısına göre filtrelenip sıralansın
- En uygun masa yeşil, büyük masalar sarı, küçük masalar kırmızı

#### 1.3 Dashboard İyileştirmeleri
- Anlık doluluk oranı ekle: "X/Y masa dolu (%Z)"
- Misafir ismi arama ekle
- Kapasite haritası limitini kaldır veya yükselt

### Sprint 2: Kural Standardizasyonu

#### 2.1 Availability Endpoint'i Tek Kaynak Yap
- Voice agent ve GUI aynı endpoint'i kullansın
- Akıllı masa seçimi backend'e taşınsın
- Frontend sadece sonuçları göstersin

#### 2.2 Ayarlar Sayfasına avgSittingMinutes Ekle
- "Ortalama oturma süresi (dakika)" input'u

### Sprint 3: Görsel İyileştirmeler

#### 3.1 Saatlik Yoğunluk Yeniden Tasarımı
- Daha büyük, okunabilir grafikler
- Anlık doluluk + beklenen varışlar
- Full kapasiteye yakın saatler kırmızı

#### 3.2 Timeline Responsive
- Geniş ekranda full genişlik
- Dar ekranda yatay scroll iyileştirmesi

#### 3.3 Genel Görsel Polish
- Dashboard kartları daha belirgin
- Renk kodlaması tutarlı (yeşil=boş, sarı=yaklaşan, kırmızı=dolu)
