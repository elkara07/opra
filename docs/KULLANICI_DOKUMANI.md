# Kullanıcı Dökümanı — Restoran Yönetim Sistemi
**Versiyon 1.14.0**

---

## Roller ve Yetkiler

| Rol | Kimler | Ne Yapabilir |
|-----|--------|-------------|
| SUPERADMIN | Platform yöneticisi | Tüm tenantları yönetme, tenant/kullanıcı ekleme |
| OWNER | Restoran sahibi | Tüm özellikler |
| MANAGER | Vardiya yöneticisi | Rezervasyon, personel, analitik (ayarlar hariç) |
| STAFF | Garson | Rezervasyon görüntüleme, durum güncelleme |

---

## Giriş ve Çıkış

**Giriş:** http://localhost → E-posta ve şifrenizi girin → "Giriş Yap"

**İlk Kayıt:** http://localhost/register → Restoran adı, e-posta, şifre, ad soyad

**Çıkış:** Sol menü → "↩ Çıkış Yap"

**Şifremi Unuttum:** Yöneticinizden şifre sıfırlama talep edin.

---

## Setup Wizard (İlk Kurulum)

İlk kez sisteme giriş yapıldığında otomatik olarak `/setup` sayfası açılır. Setup Wizard 6 adımdan oluşur:

1. **Veritabanı Kontrolü:** PostgreSQL, MongoDB ve Redis bağlantıları test edilir
2. **Superadmin Oluşturma:** İlk yönetici hesabı e-posta ve şifre ile oluşturulur
3. **Entegrasyonlar:** Twilio, Stripe, AI servisleri gibi opsiyonel entegrasyonlar yapılandırılır
4. **Tenant Oluşturma:** İlk restoran (tenant) adı, planı ve sahibi belirlenir
5. **Özet:** Tüm ayarların gözden geçirilmesi
6. **Tamamla:** Kurulum tamamlanır ve dashboard'a yönlendirilir

Setup Wizard tamamlandıktan sonra tekrar görünmez. Ayarlar daha sonra ilgili panellerden değiştirilebilir.

---

## Panel (Dashboard)

- **Bugünkü Rezervasyon:** Toplam rezervasyon sayısı
- **Onaylı / Oturuyor / Tamamlandı:** Anlık durum sayaçları
- **Aktif Personel:** Bugün görevdeki garson sayısı
- **Saatlik Yoğunluk Grafiği:** Hangi saatlerin yoğun olduğu
- **Başlangıç Rehberi:** İlk kez giriş yapınca adım adım yönlendirme

---

## Salon Planı

**Masa Ekleme:**
1. Sol panelden masa türünü sürükle → canvas'a bırak
2. Masaya tıkla → sağ panelde etiket (T1, T2...), kapasite, bölge, **etiket (VIP, Pencere, Teras...)** düzenle
3. "Kaydet" butonu

**Masa Etiketleri (Tags):** Her masaya önceden tanımlı veya özel etiket ekleyebilirsiniz. Etiketler AI sesli ajan tarafından tercih eşleştirme için kullanılır.
- Önceden tanımlı: VIP, Pencere, Teras, Bar, İç Salon, Özel, Balkon, Bahçe
- Özel: "Etiket ekle..." alanına yazıp Enter

**Masa Birleştirme:** Birden fazla masa seçip "Birleştir" → büyük grup rezervasyonu için tek rezervasyon oluşturulur.

---

## Rezervasyonlar

**Yeni Rezervasyon:**
1. "+ Rezervasyon" butonu
2. Misafir adı, tarih, saat, kişi sayısı, masa seçimi
3. "Oluştur" → SMS onayı otomatik gönderilir

**Walk-in:**
Ad/telefon gerekmez. Müşteri kapıda geldiğinde anlık SEATED rezervasyon oluşturur.

**Çoklu Masa:**
Rezervasyon formunda birden fazla masa seçilebilir. Toplam kapasite hesaplanır.

**Durum Akışı:**
```
CONFIRMED → SEATED → COMPLETED
     ↓           ↓
CANCELLED    CANCELLED
     ↓
 NO_SHOW
```

**Düzenleme:**
CONFIRMED durumundaki rezervasyonda "Düzenle" → saat, masa, misafir bilgisi değiştirilebilir.

**Zaman Çizelgesi:**
"Liste / Zaman Çizelgesi" toggle → masalar satırda, saatler sütunda, renkli bloklarla görünüm.

---

## Menü Yönetimi

Sol menü → "Menü" (OWNER/MANAGER)

**Kategoriler:**
- "+ Kategori" butonu ile yeni kategori ekleyin
- Sürükle-bırak ile kategori sıralamasını değiştirin
- Kategori adı ve açıklaması düzenlenebilir

**Menü Öğeleri:**
Her menü öğesi için aşağıdaki bilgiler girilebilir:
- **Ad:** Yemeğin adı
- **Açıklama:** Kısa tanım
- **Fiyat:** Güncel satış fiyatı (TL)
- **Allerjenler:** Gluten, süt, fıstık vb. allerjen etiketleri
- **Hazırlık Süresi:** Tahmini hazırlık süresi (dakika)
- **Görsel:** Yemek fotoğrafı yükleme

**Dinamik Fiyatlandırma:**
Sol menü → "Fiyatlandırma" sayfasından happy hour kuralları tanımlanabilir:
- Başlangıç/bitiş saati ve günleri belirleyin
- Yüzdesel indirim veya sabit fiyat ayarlayın
- Kurallar otomatik olarak dijital menüye yansır

---

## Dijital Sipariş (QR)

Müşteriler masadan QR kod okutarak sipariş verebilir.

**Sipariş Akışı:**
1. Müşteri masadaki QR kodu okutur
2. `/order/:tableId` adresi açılır → dijital menü görüntülenir
3. Müşteri ürün seçer, sepete ekler
4. Sipariş gönderilir

**Sipariş Durumu Takibi:**
```
Bekliyor → Hazırlanıyor → Hazır → Teslim Edildi
```

Müşteri sipariş durumunu aynı sayfadan canlı takip edebilir.

---

## Mutfak Ekranı (KDS)

Sol menü → "Mutfak" (OWNER/MANAGER/STAFF)

Mutfak Ekranı (Kitchen Display System) 3 kolonlu görünüm sunar:

| Kolon | Açıklama |
|-------|----------|
| **Bekliyor** | Yeni gelen siparişler |
| **Hazırlanıyor** | Mutfakta hazırlanmakta olan siparişler |
| **Hazır** | Servise hazır siparişler |

**Kullanım:**
- Siparişe tıklayarak durumu bir sonraki aşamaya ilerletin
- Renk kodları bekleme süresine göre otomatik değişir:
  - **Kırmızı:** 15 dakikadan fazla bekleyen
  - **Sarı:** 10 dakikadan fazla bekleyen
  - **Yeşil:** Normal sürede

---

## Ödeme & Kasa

Sol menü → "Ödeme" ve "Kasa"

**Ödeme Yöntemleri:**
- **Nakit:** Manuel tutar girişi
- **Kredi Kartı:** Stripe/iyzico entegrasyonu
- **Online:** Dijital sipariş üzerinden ödeme
- **Bölünmüş Ödeme:** Hesabı birden fazla kişi arasında bölme (eşit veya özel tutar)

**Kasa Vardiyası:**
- Vardiya başlangıcında kasayı "Aç" → başlangıç tutarını girin
- Vardiya sonunda kasayı "Kapat" → günlük rapor otomatik oluşturulur
- Nakit sayımı ile sistem tutarı karşılaştırılır
- Günlük kasa raporu PDF olarak indirilebilir

---

## Stok Yönetimi

Sol menü → "Stok" (OWNER/MANAGER)

Stok yönetimi 5 sekmeden oluşur:

| Sekme | İçerik |
|-------|--------|
| **Malzemeler** | Hammadde listesi, birim, mevcut stok, minimum stok uyarısı |
| **Reçeteler** | Menü öğelerinin malzeme reçeteleri, porsiyon maliyeti hesaplama |
| **Stok Sayımı** | Manuel sayım girişi, fark raporu |
| **Tedarikçiler** | Tedarikçi bilgileri, sipariş geçmişi |
| **Rapor** | Stok hareket raporu, tüketim analizi, maliyet raporu |

Stok seviyeleri minimum eşiğin altına düştüğünde otomatik bildirim gönderilir.

---

## Personel Yönetimi

**Personel Ekleme:** "+ Garson Ekle" → ad, bölge, maksimum yük, vardiya saatleri

**Vardiya Saatleri:** 17:00-23:00 gibi çalışma saati girilebilir. Otomatik atama bu saate göre filtreler.

**Otomatik Atama:** Rezervasyon oluştururken "Otomatik Atama" → en uygun garson seçilir (boş, bölge uyumlu, en az yüklü).

**Düzenleme:** Kalem ikonu → tüm bilgiler güncellenebilir.

**Deaktif Etme:** Çöp kutusu ikonu → garson yeni atamalarda görünmez (veri silinmez).

---

## Analitik

| Sekme | İçerik |
|-------|--------|
| Genel Bakış | Toplam/tamamlanan/no-show, kanal dağılımı, yoğun saatler |
| Masalar | Masa bazlı rezervasyon ve doluluk |
| Personel | Garson performansı, yük dağılımı |
| AI Tavsiye | Veri bazlı öneriler (ANTHROPIC_API_KEY gerekli) |

**Gün Sonu Raporu:** Sol menü → "Gün Sonu Raporu" → tarih seç → CSV export

**Isı Haritası:** Sol menü → "Isı Haritası" → saat x masa doluluk renk haritası

---

## Arayan Profilleri

Sol menü → "Arayan Profilleri" (AI sesli ajan kullanılıyorsa otomatik dolar)

- Her arayanın telefonu, adı, kaç kez aradığı
- Tercih ettiği bölge, etiket ve saat
- Son rezervasyonları
- Not ekleme özelliği

**İkinci Aramada Tanıma:** Aynı numara tekrar aradığında AI "Hoş geldiniz [İsim], sizi tanıdık. Yine pencere kenarı masa mı istersiniz?" şeklinde karşılar.

---

## İletişim Logları

Sol menü → "İletişim Logları" → Ses aramaları, SMS'ler ve sistem olayları

Filtreler: Tip (Ses/SMS/Sistem), Telefon, Tarih aralığı

---

## Bildirim Tercihleri

Ayarlar → Bildirim & Entegrasyonlar

**Kanal Seçimi:**
Her bildirim türü için aşağıdaki kanallardan bir veya birkaçını etkinleştirebilirsiniz:
- **SMS:** Twilio veya NetGSM üzerinden
- **E-posta:** Sistem e-postası ile
- **WhatsApp:** Twilio WhatsApp API üzerinden
- **Calendar:** Google Calendar etkinliği olarak

**Google Calendar Bağlama:**
Ayarlar → Entegrasyonlar → Google Calendar → "Bağla" butonuna tıklayın. Google hesabınızla oturum açıp izin verin. Rezervasyonlar otomatik olarak takvime eklenir.

**Telegram Bot:**
Ayarlar → Entegrasyonlar → Telegram → Bot token'ı girin. Rezervasyon bildirimleri Telegram üzerinden inline keyboard ile gelir; onaylama/reddetme doğrudan Telegram'dan yapılabilir.

---

## Bildirim Şablonları

Sol menü → "Şablonlar" (OWNER)

Bildirim şablonları kanal ve bildirim tipi matris editörü ile yönetilir.

**Kanal x Tip Matrisi:**
Her bildirim kanalı (SMS, E-posta, WhatsApp, Telegram) ve her bildirim tipi (onay, hatırlatma, iptal vb.) için ayrı şablon tanımlanabilir.

**Kullanılabilir Değişkenler:**
- `{guestName}` — Misafir adı
- `{date}` — Rezervasyon tarihi
- `{time}` — Rezervasyon saati
- `{partySize}` — Kişi sayısı
- `{tableName}` — Masa adı
- `{restaurantName}` — Restoran adı
- `{confirmationCode}` — Onay kodu

Şablonlarda Handlebars sözdizimi kullanılır. Önizleme butonu ile şablon gerçek verilerle test edilebilir.

---

## Konfirmasyon Araması

Sistem, rezervasyondan 2 saat önce otomatik IVR (Interactive Voice Response) araması yapar.

**Arama Akışı:**
- Müşteriye otomatik arama yapılır
- Sesli menü sunulur:
  - **1 tuşla:** Rezervasyonu onayla
  - **2 tuşla:** Rezervasyonu iptal et
  - **3 tuşla:** Operatöre bağlan

**Fallback Mekanizması:**
Müşteriye ulaşılamazsa sırasıyla:
1. SMS gönderilir
2. WhatsApp mesajı gönderilir

Konfirmasyon süresi `CONFIRMATION_HOURS_BEFORE` env değişkeni ile ayarlanabilir.

---

## Dijital Sipariş (QR) — Detaylı

Müşteri masadan QR okutarak sipariş verebilir.

**QR Kod Oluşturma:**
Salon Planı → Masaya tıkla → "QR Kodu İndir" butonu. Her masa için benzersiz QR kodu oluşturulur.

---

## Plan ve Fatura

Sol menü → "Plan & Fatura" (sadece OWNER)

| Plan | Masa | Rezervasyon/ay | Ücret |
|------|------|----------------|-------|
| Starter | 3 | 50 | Ücretsiz |
| Professional | 20 | 500 | ₺299/ay |
| Enterprise | Sınırsız | Sınırsız | ₺999/ay |

---

## Kullanıcı Davet Sistemi

Sol menü → "Ayarlar" → "Kullanıcı Davet Et"

1. E-posta (opsiyonel) + rol seç → "Davet Oluştur"
2. 48 saat geçerli link oluşturulur → "Kopyala"
3. Linki çalışana ilet → link üzerinden kayıt olur → otomatik tenant'a bağlanır

---

## Kullanıcı Yönetimi (OWNER)

Sol menü → "Kullanıcılar"

- Rol değiştirme: OWNER, MANAGER, STAFF
- Kullanıcı deaktif etme (erişim engelleme)
- "Düzenle" → inline düzenleme

---

## Ayarlar (OWNER)

Sol menü → "Ayarlar"

- **Temel Bilgiler:** Restoran adı, telefon, adres, dil, saat dilimi
- **Marka:** Logo URL, ana renk ve ikincil renk → tüm arayüz bu renklere uyum sağlar
- **SMS Test:** Twilio yapılandırılmışsa test SMS gönderimi
- **Kullanıcı Davet:** Davet linki oluşturma ve geçmiş davetler

---

## White-Label

Ayarlar → White-Label

White-label özelliği ile platformu kendi markanız altında sunabilirsiniz:

- **Özel Domain:** Kendi domain adresinizi bağlayın (ör. rezervasyon.restoraniniz.com)
- **Logo:** Sidebar ve giriş sayfasında görünen logo
- **Favicon:** Tarayıcı sekmesinde görünen ikon
- **Giriş Arka Planı:** Login sayfasının arka plan görseli

DNS ayarları için CNAME kaydı oluşturup destek ekibiyle paylaşın.

---

## Müşteri Sadakat Detayları

**Puan Kazanma:**
Her COMPLETED (tamamlanmış) rezervasyonda müşteriye otomatik puan eklenir.

**Sadakat Tier'leri:**

| Tier | Koşul |
|------|-------|
| STANDARD | Varsayılan |
| SILVER | Belirli puan eşiği aşıldığında |
| GOLD | Daha yüksek puan eşiği |
| VIP | En yüksek puan eşiği |

**No-Show Kara Liste:**
Belirli sayıda no-show yapan müşteriler otomatik olarak kara listeye alınır. Kara listedeki müşteriler için depozito talep edilebilir.

**Doğum Günü SMS:**
Müşteri profilinde doğum tarihi kayıtlıysa, doğum gününde otomatik kutlama SMS'i gönderilir.

**Müşteri 360 Profili:**
Müşteri detay sayfasında tek ekranda:
- Tüm rezervasyon geçmişi
- Toplam harcama
- Tercih edilen masa/bölge/saat
- Sadakat puanı ve tier
- İletişim geçmişi
- Notlar

---

## Çoklu Şube

Sol menü → "Şubeler" (OWNER)

**Şube Oluşturma:**
"+ Şube Ekle" butonu ile yeni şube tanımlayın. Her şube için ayrı salon planı, menü ve personel yönetimi yapılır.

**Kullanıcı Atama:**
Her şubeye MANAGER ve STAFF rolünde kullanıcılar atanabilir. Bir kullanıcı birden fazla şubeye atanabilir.

**Franchise Genel Bakış:**
OWNER tüm şubelerin performansını tek panelden karşılaştırmalı olarak görüntüleyebilir:
- Şube bazlı doluluk oranları
- Gelir karşılaştırması
- Toplu bildirim gönderimi (broadcast)

---

## Muhasebe Export

Sol menü → "Muhasebe" (OWNER)

Muhasebe verilerini farklı formatlarda dışa aktarabilirsiniz:

| Format | Açıklama |
|--------|----------|
| **CSV** | Genel amaçlı tablo formatı |
| **XML (UBL-TR)** | Türkiye e-fatura standardı |
| **Parasut** | Parasut muhasebe entegrasyonu |
| **Logo** | Logo muhasebe yazılımı entegrasyonu |
| **Mikro** | Mikro muhasebe yazılımı entegrasyonu |

Tarih aralığı seçerek ilgili dönemin verilerini export edin.

---

## Dark Mode

Sol menü altında bulunan güneş/ay toggle butonu ile karanlık mod açılıp kapatılabilir.

- Tüm arayüz koyu renklere geçer
- Tercih `localStorage`'da saklanır, tarayıcı kapatılıp açılsa bile korunur
- Sistem temasına göre otomatik algılama desteklenir

---

## Mobil Kullanım

Her masa için URL: `http://restoran-adresiniz/table/T1`

Garson masanın başından telefonu ile QR okutarak:
- Müşterinin rezervasyon bilgisini görür
- "Oturdu" veya "Tamamlandı" butonuyla durumu günceller

---

## Güvenlik (Kullanıcı)

**Oturum Yönetimi:**
Ayarlar → Güvenlik → "Tüm Cihazlarda Çıkış Yap" butonu ile tüm aktif oturumlar sonlandırılır. Şifre değişikliğinden sonra bu işlem önerilir.

**KVKK — Verilerimi Sil:**
Ayarlar → Güvenlik → "Verilerimi Sil" butonu. KVKK kapsamında tüm kişisel verilerinizin silinmesini talep edebilirsiniz. Talep 30 gün içinde işleme alınır. Bu işlem geri alınamaz.

---

## Superadmin Paneli (SUPERADMIN)

Sol menü → "Superadmin"

Superadmin paneli 7 sekmeden oluşur:

| Sekme | İçerik |
|-------|--------|
| **Genel Bakış** | Platform istatistikleri, MRR dashboard, aktif tenant sayısı |
| **Tenantlar** | Tüm restoranlar, plan değiştirme, deaktif etme, tenant ekleme |
| **Kullanıcılar** | Tüm platform kullanıcıları, kullanıcı ekleme |
| **API Keys** | AES-256 şifrelenmiş API key yönetimi, Twilio/Stripe/AI anahtarları |
| **Planlar** | Veritabanı tabanlı plan limitleri ve fiyatlandırma yapılandırması |
| **Güvenlik** | CORS ayarları, rate limit yapılandırması, IP kısıtlamaları |
| **Monitoring** | Servis sağlık durumu, uptime, hata logları |

**Impersonation:**
Superadmin herhangi bir tenant hesabına geçici giriş yapabilir (1 saatlik JWT token). Bu özellik destek ve hata ayıklama amacıyla kullanılır. Tüm impersonation işlemleri loglanır.

**Compliance Sekmesi:**
Tüm tenantların IYS/KVKK/BTK uyumluluk durumunu tek sayfada görüntüleyin. Uyumsuz tenantlara otomatik bildirim gönderin.

**Voice Dashboard:**
Sesli arama istatistikleri: toplam arama, ortalama süre, başarı oranı, dil dağılımı, LiveKit/Twilio kullanım karşılaştırması.

**Superadmin Yetkisi Alma:**
```bash
./scripts/seed-superadmin.sh superadmin@restoran.app SuperAdmin2026!
```

---

## Kullanım Limitleri & Maliyet

Sistem, arama ve SMS kullanımını günlük limitlerle kontrol eder:

- **Günlük Arama Limiti:** Tenant planına göre günlük maksimum sesli arama sayısı belirlenir. Limit aşıldığında aramalar kuyruklanır.
- **Günlük SMS Limiti:** Tenant planına göre günlük maksimum SMS sayısı belirlenir. Limit aşıldığında SMS gönderimi durdurulur.
- **Maliyet Takibi:** Her arama ve SMS'in maliyeti otomatik olarak hesaplanır ve kaydedilir.
- **Kullanım Özeti:** Ayarlar → Bildirimler altında günlük/haftalık/aylık kullanım özeti görüntülenebilir. Limit yaklaştığında uyarı bildirimi gönderilir.

---

## QR Sipariş

Müşteriler masadan QR kod okutarak sipariş verebilir:

- **QR Kod Oluşturma:** Salon Planı → masaya tıklayın → "QR İndir" butonu ile her masa için benzersiz QR kodu indirin.
- **Müşteri QR ile Menü Görüntüleme:** Müşteri QR kodu okutur → dijital menü otomatik olarak açılır. Menüdeki aktif kategoriler ve ürünler listelenir.
- **Take-away Sipariş:** QR sipariş sayfasında "Paket Servis" seçeneği ile take-away sipariş oluşturulabilir. Müşteri adı ve telefon numarası girilerek sipariş kaydedilir.
- **Sipariş Takip Sayfası:** Sipariş gönderildikten sonra müşteri aynı sayfada siparişinin durumunu canlı olarak takip edebilir (Bekliyor → Hazırlanıyor → Hazır → Teslim Edildi).

---

## İki Faktörlü Doğrulama (2FA)

Hesap güvenliğini artırmak için TOTP tabanlı iki faktörlü doğrulama (MFA) kullanılabilir:

1. **Kurulum:** Ayarlar → Güvenlik → MFA Kurulumu butonuna tıklayın
2. **QR Kod Tarama:** Ekranda görünen QR kodu Google Authenticator, Authy veya benzeri bir uygulama ile tarayın
3. **Doğrulama:** Uygulamanın ürettiği 6 haneli kodu girerek kurulumu tamamlayın
4. **Backup Kodları:** Kurulum sonrası gösterilen tek kullanımlık backup kodlarını güvenli bir yere kaydedin. Telefonunuza erişemediğinizde bu kodlarla giriş yapabilirsiniz.

Her giriş yapıldığında e-posta/şifre sonrası 6 haneli doğrulama kodu istenecektir.

---

## Google ile Giriş (SSO)

Kullanıcılar Google hesapları ile hızlı giriş yapabilir:

- Login sayfasında "Google ile Giriş" butonuna tıklayın
- Google hesabınızı seçin ve izin verin
- Hesabınız otomatik olarak eşleştirilir veya yeni hesap oluşturulur

**Not:** Google SSO kullanılabilmesi için sistem yöneticisinin `GOOGLE_CLIENT_ID` ve `GOOGLE_CLIENT_SECRET` ortam değişkenlerini yapılandırması gerekmektedir.

---

## Logo Yükleme

Restoran logonuzu platforma yükleyerek sidebar, giriş sayfası ve beyaz etiket (white-label) alanlarında kullanabilirsiniz:

1. Ayarlar → Marka & Logo bölümüne gidin
2. "Dosya Seç" butonu ile logonuzu yükleyin (PNG veya SVG, önerilen boyut: 200x200 piksel)
3. "Kaydet" butonuna tıklayın

Logo, sidebar üst kısmında ve giriş sayfasında otomatik olarak görüntülenir.

---

## Çoklu Salon

Tek bir restoran lokasyonunda birden fazla salon (iç salon, teras, bahçe vb.) yönetebilirsiniz:

- **Salon Sekmeleri:** Salon Planı sayfasında her salon ayrı bir sekme olarak görüntülenir. Sekmeler arası geçiş yaparak farklı salonların masa düzenlerini yönetebilirsiniz.
- **Yeni Salon Oluşturma:** Salon Planı → "+" sekmesine tıklayın → salon adını girin → yeni salon oluşturulur. Her salon için bağımsız masa düzeni, kapasite ve bölge tanımlaması yapılabilir.
- **Salon Bazlı Rezervasyon:** Rezervasyon oluştururken salon seçimi yapılabilir. Müşteri tercihi (iç salon, teras vb.) kaydedilir.

---

## Sık Sorulan Sorular

**SMS gitmiyor:** Twilio yapılandırılmadı → docs/TWILIO_KURULUM.md

**AI tavsiyeler "Mock" gösteriyor:** ANTHROPIC_API_KEY eksik

**Salon planı boş:** Masaları ekleyip kaydedin. Test.sh çalıştırıldıysa nginx restart gerekebilir.

**429 Too Many Requests:** `sudo docker compose restart nginx`

**"Bu masa dolu" hatası:** Farklı masa veya saat seçin. Zaman çizelgesinde boş slotları görün.

**Sesli ajan çalışmıyor:** PUBLIC_HOST .env'e eklenmeli, ngrok veya gerçek domain olmalı.

**Menü öğeleri dijital siparişte görünmüyor:** Menü öğesinin "Aktif" durumda olduğundan emin olun. Kategori de aktif olmalıdır.

**Mutfak ekranı güncellenmiyor:** Tarayıcı sayfasını yenileyin. WebSocket bağlantısı kopmuş olabilir.

**Dark mode düzgün çalışmıyor:** Tarayıcı cache'ini temizleyin (Ctrl+Shift+Delete).

**Bildirim şablonu değişkenleri çalışmıyor:** Değişken adlarının `{guestName}` formatında olduğundan emin olun. Büyük/küçük harf duyarlıdır.

**QR kod okutulamıyor:** QR kodun yeterli çözünürlükte basıldığından emin olun. Minimum 200x200 piksel önerilir.

**Kasa raporu uyuşmuyor:** Bölünmüş ödemelerin tamamının girildiğinden emin olun. Açık hesapları kontrol edin.

**Setup Wizard tekrar açılmıyor:** Setup tamamlandıktan sonra wizard deaktif olur. Manuel yapılandırma için Ayarlar panelini kullanın.

**Google Calendar senkronize olmuyor:** Entegrasyon sayfasından bağlantıyı kaldırıp tekrar bağlayın. Google API izinlerini kontrol edin.

---

## Ses Ayarları (v1.17.0)

Sol menüden **Ses Ayarları** sayfasına gidin. Bu sayfa sesli ajan pipeline'ını yönetir.

### Provider Seçimi
- **STT**: Deepgram Nova-3 (streaming, önerilen), Whisper (batch), Google STT
- **NLP**: Groq (hızlı), Claude (kaliteli), DeepSeek (ekonomik), Gemini, OpenAI — birincil + yedek seçilebilir
- **TTS**: OpenAI TTS (dengeli, önerilen), ElevenLabs (premium), Google TTS (ekonomik)

### Yedek Yönlendirme
AI başarısız olursa çağrı restorana aktarılır: yedek telefon veya SIP adresi tanımlayın. Aktarma koşulları: 3x anlaşılamadı, insan talebi, AI timeout, DTMF 0. Cevapsız: SMS, sesli mesaj veya geri arama.

### PBX Entegrasyonu
4 mod: Önce AI (önerilen), Önce PBX, Sadece AI, Sadece PBX. Detay: `docs/SIP_PBX_ENTEGRASYON.md`

### Mobil
Profil > Ses Ayarları'ndan pipeline durumu ve "Restoranı Ara" (tel: link) erişilebilir. Detaylı config web panelinden yapılır.
