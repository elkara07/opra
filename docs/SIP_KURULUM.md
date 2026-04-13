# Twilio + SIP Trunk Kurulum Rehberi

## Mimari

```
Müşteri Telefonu
      ↓
Sabit Hat / GSM
      ↓
SIP Trunk (Türk operatör veya Twilio SIP)
      ↓
  ┌───────────────────────────────┐
  │  Yol 1: Twilio               │   Yol 2: LiveKit SIP Bridge
  │  Twilio → Webhook            │   SIP Trunk → LiveKit Server
  │       ↓                      │        ↓
  │  voice-agent-service         │   LiveKit Room (WebRTC)
  │                              │        ↓
  │                              │   voice-agent-service
  └───────────────────────────────┘
      ↓
AI: Whisper STT → Claude NLP → ElevenLabs TTS
      ↓
Rezervasyon kaydedildi ✓
```

---

## Adım 1 — Public URL (ngrok)

```bash
ngrok http 3007
# → https://xxxx.ngrok.io

# .env'e ekle:
PUBLIC_HOST=xxxx.ngrok.io
```

Üretimde: Nginx reverse proxy + Let's Encrypt veya Cloudflare Tunnel.

---

## Adım 2 — Twilio SIP Trunk

1. [console.twilio.com](https://console.twilio.com) → Elastic SIP Trunking → Create Trunk
2. Trunk adı: `restoran-rezervasyon`
3. Phone Numbers → mevcut numaranı trunk'a bağla
4. Voice URL:
   ```
   https://xxxx.ngrok.io/api/v1/voice/incoming?tenantId=YOUR_TENANT_ID
   ```

---

## Adım 3 — LiveKit SIP Bridge (Opsiyonel)

LiveKit SIP Bridge, WebRTC tabanlı ses iletimi sağlar. Twilio'ya alternatif olarak kullanılabilir.

### 3.1 LiveKit Kurulumu

LiveKit servisi `docker-compose.yml` içinde tanımlıdır. Etkinleştirmek için:

```bash
# .env'e ekle:
VOICE_CHANNEL=livekit
LIVEKIT_API_KEY=APIxxxxxxxx
LIVEKIT_API_SECRET=xxxxxxxxxxxxxxxx
LIVEKIT_URL=ws://livekit:7880
```

### 3.2 LiveKit SIP Trunk Yapılandırması

LiveKit Dashboard veya API üzerinden SIP trunk oluşturun:

```bash
# LiveKit CLI ile SIP trunk oluşturma
lk sip trunk create \
  --name "restoran-sip" \
  --inbound-numbers "+90XXXXXXXXXX" \
  --inbound-username "restoran" \
  --inbound-password "GüçlüŞifre2026!"
```

### 3.3 DID Numara → Tenant Routing

LiveKit ile gelen aramalarda aranan DID numarası üzerinden tenant tespiti yapılır:

```
Gelen Arama (DID: +902121234567)
      ↓
voice-agent-service → DID tablosunda arama
      ↓
Tenant bulundu: "Restoran ABC" (tenantId: xxx)
      ↓
İlgili tenant'ın menüsü, masaları ve ayarları yüklenir
```

**DID Numara Eşleştirme:**
Superadmin paneli → Tenantlar → Tenant seç → "DID Numaraları" sekmesi → DID numara ekle.

Her tenant'a bir veya birden fazla DID numara atanabilir. Gelen arama aranan numaraya göre otomatik olarak doğru tenant'a yönlendirilir.

### 3.4 Twilio vs LiveKit Karşılaştırması

| Özellik | Twilio | LiveKit |
|---------|--------|---------|
| Protokol | PSTN/SIP → HTTP webhook | SIP → WebRTC |
| Gecikme | Orta (~300ms) | Düşük (~100ms) |
| Maliyet | Dakika başı ücret | Kendi sunucu (sabit maliyet) |
| Kurulum | Kolay (SaaS) | Orta (self-hosted) |
| Türk operatör | Twilio SIP trunk | Doğrudan SIP bağlantı |
| Fallback | - | Otomatik Twilio fallback |

**Fallback:** `VOICE_CHANNEL=livekit` ayarlandığında LiveKit bağlantısı başarısız olursa sistem otomatik olarak Twilio'ya geçer.

---

## Adım 4 — NetGSM SIP Trunk (Türk Operatör)

NetGSM, Türk GSM operatörleri üzerinden SIP trunk hizmeti sunar. Mevcut restoranın sabit veya GSM numarası korunabilir.

### 4.1 NetGSM SIP Yapılandırması

```bash
# .env'e ekle:
SMS_PROVIDER=netgsm
NETGSM_USERCODE=XXXXXXXX
NETGSM_PASSWORD=XXXXXXXX
NETGSM_HEADER=RESTORAN

# SIP Trunk ayarları (sesli arama için)
NETGSM_SIP_HOST=sip.netgsm.com.tr
NETGSM_SIP_USERNAME=XXXXXXXX
NETGSM_SIP_PASSWORD=XXXXXXXX
```

### 4.2 NetGSM SIP Trunk Oluşturma

1. [netgsm.com.tr](https://www.netgsm.com.tr) → Hesap → SIP Trunk Başvuru
2. DID numara tahsis edin (mevcut sabit hat portalama mümkün)
3. SIP kimlik bilgilerini `.env`'e ekleyin
4. Trunk yönlendirme: NetGSM panelinden webhook URL'yi ayarlayın:
   ```
   https://your-domain.com/api/v1/voice/incoming?tenantId=YOUR_TENANT_ID
   ```

### 4.3 NetGSM ile LiveKit Entegrasyonu

NetGSM SIP trunk doğrudan LiveKit SIP Bridge'e bağlanabilir:

```
NetGSM SIP Trunk → LiveKit SIP Bridge → WebRTC Room → voice-agent-service
```

LiveKit SIP trunk yapılandırmasında NetGSM bilgilerini kullanın:

```bash
lk sip trunk create \
  --name "netgsm-trunk" \
  --outbound-address "sip.netgsm.com.tr" \
  --outbound-username "$NETGSM_SIP_USERNAME" \
  --outbound-password "$NETGSM_SIP_PASSWORD" \
  --inbound-numbers "+90XXXXXXXXXX"
```

---

## Adım 5 — G.711 Codec Yapılandırması

Türk SIP operatörleri genellikle G.711 codec gerektirir. Desteklenen codec'ler:

| Codec | Env Değeri | Bant Genişliği | Kullanım |
|-------|-----------|----------------|----------|
| G.711 μ-law | `SIP_CODEC=pcmu` | 64 kbps | Kuzey Amerika |
| G.711 A-law | `SIP_CODEC=pcma` | 64 kbps | Avrupa/Türkiye (önerilen) |

```bash
# .env'e ekle:
SIP_CODEC=pcma
```

**Türk operatörler için önerilen:** `pcma` (G.711 A-law). Bu codec Türk Telekom, Vodafone ve Turkcell SIP trunk'ları ile uyumludur.

LiveKit kullanıyorsanız codec ayarı LiveKit SIP trunk yapılandırmasında belirtilir:

```bash
lk sip trunk create \
  --name "netgsm-trunk" \
  --media-codecs "PCMA,PCMU" \
  ...
```

---

## Adım 6 — Türk Operatör SIP (Asterisk, opsiyonel)

Twilio veya LiveKit yerine doğrudan Asterisk ile Türk Telekom veya Vodafone SIP trunk kullanılabilir.
Mevcut restoranın sabit numarası korunur, Twilio dakika ücreti ödemezsin.

**Asterisk entegrasyonu:**
```conf
[from-trunk]
exten => _X.,1,NoOp(Gelen arama)
exten => _X.,n,Dial(SIP/voice-agent)
exten => _X.,n,Hangup()
```

---

## Adım 7 — .env yapılandırması

```bash
# Twilio (varsayılan ses kanalı)
TWILIO_ACCOUNT_SID=ACxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxx
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx

# LiveKit (alternatif ses kanalı)
VOICE_CHANNEL=livekit          # twilio (varsayılan) veya livekit
LIVEKIT_API_KEY=APIxxxxxxxx
LIVEKIT_API_SECRET=xxxxxxxx
LIVEKIT_URL=ws://livekit:7880

# NetGSM (Türk operatör SMS + SIP)
SMS_PROVIDER=netgsm             # twilio (varsayılan) veya netgsm
NETGSM_USERCODE=xxxxxxxx
NETGSM_PASSWORD=xxxxxxxx
NETGSM_HEADER=RESTORAN
NETGSM_SIP_HOST=sip.netgsm.com.tr
NETGSM_SIP_USERNAME=xxxxxxxx
NETGSM_SIP_PASSWORD=xxxxxxxx

# SIP Codec
SIP_CODEC=pcma                  # pcmu veya pcma

# AI Servisleri
OPENAI_API_KEY=sk-xxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
ELEVENLABS_API_KEY=xxxxxxxx
ELEVENLABS_VOICE_ID=xxxxxxxx

# Genel
PUBLIC_HOST=xxxx.ngrok.io
FALLBACK_PHONE_NUMBER=+905XXXXXXXXX
```

---

## Konuşma Akışı

```
Müşteri: "Rezervasyon yapmak istiyorum"
AI:      "Hangi tarih için?"
Müşteri: "Cumartesi akşamı 4 kişi"
AI:      "Adınız nedir?"
Müşteri: "Ahmet Yılmaz"
AI:      "22 Mart Cumartesi 20:00, 4 kişi — Ahmet Yılmaz.
          Onaylıyor musunuz?"
Müşteri: "Evet"
AI:      "Rezervasyonunuz alındı! SMS ile onay gönderildi. İyi günler."
```

---

## DID Numara → Tenant Routing Detayları

Birden fazla restoran (tenant) tek bir sistem üzerinde çalıştığında, gelen aramaların doğru restorana yönlendirilmesi DID (Direct Inward Dialing) numaraları ile sağlanır.

### Routing Akışı

```
Gelen Arama → Aranan Numara (DID) Tespiti
      ↓
did_numbers tablosunda arama
      ↓
  ┌─ Eşleşme bulundu → İlgili tenant yüklenir
  └─ Eşleşme bulunamadı → Varsayılan tenant veya hata mesajı
```

### DID Yönetimi

Superadmin veya OWNER, DID numara yönetimini şu şekilde yapar:

1. Superadmin Panel → Tenantlar → Tenant seç → DID Numaraları
2. "+ DID Ekle" → Numara gir (ör. +902121234567)
3. Numara tenant'a bağlanır

Bir DID numarası sadece bir tenant'a atanabilir. Aynı numara birden fazla tenant'a atanamaz.

---

## Fallback Senaryoları

| Durum | Davranış |
|-------|----------|
| 3 kez anlayamadı | FALLBACK_PHONE_NUMBER'a yönlendir |
| Çakışma (masa dolu) | Alternatif saat öner |
| API hatası | Fallback numarasına yönlendir |
| İptal isteği | Operatöre yönlendir |
| LiveKit bağlantı hatası | Twilio'ya otomatik geçiş |
| NetGSM SIP hatası | Twilio SIP trunk'a fallback |

---

## Tahmini Maliyet (100 arama/ay)

| Kalem | Twilio | LiveKit (self-hosted) |
|-------|--------|----------------------|
| Gelen arama | $1.70 | Sunucu maliyeti |
| Whisper STT | $1.20 | $1.20 |
| Claude NLP | $0.50 | $0.50 |
| ElevenLabs TTS | $0.72 | $0.72 |
| **Toplam** | **~$4.12/ay** | **~$2.42/ay + sunucu** |

NetGSM ile Türk numaralar için maliyet Twilio'ya göre %40-60 daha düşüktür.
