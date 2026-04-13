# SIP / PBX Entegrasyon Rehberi

Bu dokuman, sesli ajan sisteminin mevcut PBX altyapisiyla entegrasyonunu adim adim aciklar.

---

## 1. Asterisk / FreePBX SIP Trunk Kurulumu

### 1.1 Asterisk ile Direkt SIP Trunk

Asterisk `sip.conf` veya `pjsip.conf` dosyasina asagidaki trunk tanimini ekleyin:

#### pjsip.conf (Onerilen)

```ini
; === AI Voice Agent Trunk ===
[ai-voice-trunk]
type=endpoint
transport=transport-udp
context=from-ai-voice
disallow=all
allow=ulaw
allow=alaw
allow=opus
aors=ai-voice-trunk
outbound_auth=ai-voice-auth
direct_media=no

[ai-voice-trunk]
type=aor
contact=sip:voice.example.com:5060
qualify_frequency=60

[ai-voice-auth]
type=auth
auth_type=userpass
username=ai-agent
password=GUCLU_SIFRE_BURAYA

[ai-voice-identify]
type=identify
endpoint=ai-voice-trunk
match=VOICE_SERVER_IP_ADRESI
```

#### Dialplan (extensions.conf)

```ini
; Gelen cagrilari AI'a yonlendir
[from-pstn]
exten => _X.,1,NoOp(Gelen cagri: ${CALLERID(num)})
 same => n,Dial(PJSIP/ai-voice-trunk/${EXTEN},30)
 same => n,GotoIf($["${DIALSTATUS}" = "NOANSWER"]?noanswer)
 same => n,GotoIf($["${DIALSTATUS}" = "BUSY"]?busy)
 same => n,Hangup()
 same => n(noanswer),VoiceMail(${EXTEN}@default,u)
 same => n,Hangup()
 same => n(busy),VoiceMail(${EXTEN}@default,b)
 same => n,Hangup()

; AI'dan gelen transfer cagrilari
[from-ai-voice]
exten => _X.,1,NoOp(AI Transfer: ${EXTEN})
 same => n,Dial(PJSIP/${EXTEN},30,tT)
 same => n,Hangup()
```

### 1.2 FreePBX ile Kurulum

FreePBX web arayuzunden:

1. **Connectivity > Trunks > Add SIP (chan_pjsip) Trunk**
2. Trunk ayarlari:
   - Trunk Name: `AI-Voice-Agent`
   - Outbound CallerID: Restoran numarasi
3. pjsip Settings sekmesi:
   - Username: `ai-agent`
   - Secret: Guclu sifre
   - SIP Server: `voice.example.com`
   - SIP Server Port: `5060`
   - Transport: `UDP` (veya `TLS` guvenli baglanti icin)
4. **Connectivity > Inbound Routes > Add Incoming Route**
   - DID Number: Restoran DID numarasi
   - Destination: `Trunk` > `AI-Voice-Agent`
5. **Apply Config** tiklayin

### 1.3 Codec Ayarlari

Onerilen codec oncelik sirasi:
1. **Opus** - En iyi kalite/bant genisligi orani
2. **G.711 ulaw** - En yaygin uyumluluk
3. **G.711 alaw** - Avrupa standardi
4. **G.729** - Dusuk bant genisligi (lisans gerektirir)

---

## 2. 3CX Entegrasyonu

### 2.1 SIP Trunk Ekleme

1. 3CX Yonetim Konsoluna giris yapin
2. **SIP Trunks > Add SIP Trunk** secin
3. "Generic SIP Trunk" sablonunu secin
4. Ayarlar:

| Alan                  | Deger                          |
|-----------------------|--------------------------------|
| Trunk Name            | AI-Voice-Agent                 |
| Registrar/Server      | voice.example.com              |
| Outbound Proxy        | voice.example.com              |
| Auth ID               | ai-agent                       |
| Auth Password         | GUCLU_SIFRE                    |
| Main Trunk No         | Restoran DID numarasi          |
| Number of SIM Calls   | 10                             |
| Codec                 | G.711 (ulaw), Opus             |

### 2.2 Inbound Rule Olusturma

1. **Inbound Rules > Add DID Rule**
2. DID/DDI: Restoran numarasi
3. Route to: SIP Trunk > AI-Voice-Agent
4. "If no answer" icin:
   - Timeout: 30 saniye
   - Route to: Extension (restoran telefonu)

### 2.3 Outbound Rule (Opsiyonel)

AI ajanin disari arama yapmasi gerekiyorsa (onay aramalari vb.):

1. **Outbound Rules > Add Rule**
2. Rule Name: `AI-Outbound`
3. Calls from Extension: AI ajanin dahili numarasi
4. Route: Mevcut PSTN trunk uzerinden

---

## 3. DID Numara Routing

### 3.1 DID Numara Edinme

DID (Direct Inward Dialing) numarasi asagidaki kaynaklardan edinilebilir:

| Saglayici   | Ulke    | Aylik Maliyet | Dakika Maliyeti |
|------------|---------|---------------|-----------------|
| Twilio     | TR      | ~$1/ay        | $0.0085/dk      |
| Telnyx     | TR      | ~$1/ay        | $0.007/dk       |
| Vonage     | TR      | ~$1.50/ay     | $0.009/dk       |
| Turk Telekom| TR     | Degisken      | Degisken        |

### 3.2 DID Routing Yapisi

```
DID Numara (+90 850 XXX XX XX)
    │
    ├── Twilio/Telnyx SIP Trunk
    │       │
    │       └── Voice Server (ai_first modu)
    │               │
    │               ├── AI Basarili → Rezervasyon
    │               │
    │               └── AI Basarisiz → PBX Transfer
    │                       │
    │                       ├── Operator Cevapladi → Gorusme
    │                       │
    │                       └── Cevapsiz → SMS
    │
    └── Alternatif: Direkt PBX'e
            │
            └── PBX IVR → "Rezervasyon icin 1" → AI Voice Agent
```

### 3.3 Coklu DID Yonetimi

Bir restoran zincirinin birden fazla subesi icin:

```json
{
  "tenantId": "chain-restaurant",
  "branches": [
    {
      "name": "Kadikoy Sube",
      "did": "+908501111111",
      "voiceConfig": { "pbx": { "mode": "ai_first" } }
    },
    {
      "name": "Besiktas Sube",
      "did": "+908502222222",
      "voiceConfig": { "pbx": { "mode": "pbx_first" } }
    }
  ]
}
```

---

## 4. Superadmin Panelden Trunk Yonetimi

### 4.1 Web Panel Uzerinden Trunk Ekleme

1. Superadmin panele giris yapin (`/admin`)
2. **Tenants** listesinden ilgili restorani secin
3. **Voice Settings** sekmesine gidin
4. **SIP Trunk** bolumunde:
   - Trunk tipi secin (Twilio, Telnyx, Direkt SIP)
   - Kimlik bilgilerini girin
   - DID numarayi atayin
5. **PBX Mode** secin (ai_first, pbx_first, ai_only, pbx_only)
6. **Fallback** ayarlarini yapilandirin
7. **Kaydet** butonuna tiklayin

### 4.2 API Uzerinden Trunk Yonetimi

```bash
# Tenant voice config guncelleme
curl -X PATCH https://api.example.com/api/admin/tenants/{tenantId} \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "voiceConfig": {
      "pbx": {
        "mode": "ai_first",
        "sipTrunk": {
          "host": "pbx.restaurant.com",
          "port": 5060,
          "username": "ai-agent",
          "password": "sifre"
        }
      }
    }
  }'
```

### 4.3 Trunk Durumu Izleme

Superadmin panelde her trunk icin:
- **Baglanti Durumu**: Kayitli / Kayitsiz / Hata
- **Son Cagri**: Tarih ve sonuc
- **Aktif Cagri Sayisi**: Anlik
- **Gunluk Istatistikler**: Toplam cagri, ortalama sure, basari orani

---

## 5. Test Proseduru

### 5.1 On Kontroller

1. **Network Kontrolu**
   ```bash
   # SIP portu acik mi?
   nc -zv voice.example.com 5060

   # RTP port araligi acik mi?
   nc -zv voice.example.com 10000-20000
   ```

2. **DNS Kontrolu**
   ```bash
   # SRV kaydi kontrol
   dig _sip._udp.voice.example.com SRV

   # A kaydi kontrol
   dig voice.example.com A
   ```

3. **Firewall Kurallari**
   ```
   Gelen: UDP 5060 (SIP sinyal)
   Gelen: UDP 10000-20000 (RTP medya)
   Gelen: TCP 5061 (SIP TLS - opsiyonel)
   Giden: UDP 5060 (SIP sinyal)
   Giden: UDP 10000-20000 (RTP medya)
   ```

### 5.2 Temel Test Adimlari

1. **SIP Registration Testi**
   ```bash
   # Voice server loglarindan kontrol
   docker logs voice-server 2>&1 | grep "REGISTER"
   ```

2. **Test Cagrisi**
   - Test DID numarasini arayin
   - AI ajanin selamlama mesajini dinleyin
   - "Yarin aksam 4 kisilik masa istiyorum" deyin
   - AI'nin cevabini kontrol edin

3. **Fallback Testi**
   - AI servisini gecici olarak durdurun
   - Test cagrisi yapin
   - Cagrinin PBX'e yonlendirildigini dogrulayin
   - PBX'te cevap vermeden bekleyin
   - SMS bildiriminin geldigini dogrulayin

4. **Ses Kalitesi Testi**
   - Farkli ag kosullarinda test edin
   - Codec degisikliklerini deneyin
   - Gecikme (latency) olcun: hedef < 500ms toplam RTT

### 5.3 Yukleme Testi

```bash
# SIPp ile yukleme testi (opsiyonel)
sipp -sn uac voice.example.com:5060 -r 10 -d 60000 -l 50
# -r 10: saniyede 10 cagri
# -d 60000: 60sn cagri suresi
# -l 50: maksimum 50 es zamanli cagri
```

---

## 6. Sorun Giderme

### 6.1 SIP Registration Basarisiz

| Belirti                          | Olasi Neden                    | Cozum                                    |
|---------------------------------|--------------------------------|-------------------------------------------|
| 401 Unauthorized                | Yanlis kimlik bilgileri        | Username/password kontrol edin            |
| 403 Forbidden                   | IP beyaz listede degil         | SIP saglayicide IP ekleyin                |
| 408 Request Timeout             | Firewall engelliyor            | UDP 5060 portunu acin                     |
| Connection Refused              | Sunucu erisim yok              | Host/port bilgilerini kontrol edin        |

### 6.2 Ses Yok (One-way / No Audio)

| Belirti                          | Olasi Neden                    | Cozum                                    |
|---------------------------------|--------------------------------|-------------------------------------------|
| Tek yonlu ses                   | NAT problemi                   | STUN/TURN yapilandirin                    |
| Hic ses yok                    | RTP portlari kapali            | UDP 10000-20000 acin                      |
| Kesik kesik ses                 | Yuksek paket kaybi             | QoS ayarlarini yapin, codec degistirin    |
| Eko                             | Akustik geri besleme           | Echo cancellation etkinlestirin           |

### 6.3 AI Ajan Cevap Vermiyor

| Belirti                          | Olasi Neden                    | Cozum                                    |
|---------------------------------|--------------------------------|-------------------------------------------|
| Sessizlik                       | STT calismadi                  | Whisper servis loglarini kontrol edin     |
| Yanlis cevap                    | NLP hatasi                     | System prompt'u gozden gecirin            |
| Geciken cevap                   | Yuksek gecikme                 | Provider degistirin, cache ekleyin        |
| Cagri kopuyor                   | Timeout                        | MAX_CALL_DURATION artirin                 |

### 6.4 Fallback Calismiyor

| Belirti                          | Olasi Neden                    | Cozum                                    |
|---------------------------------|--------------------------------|-------------------------------------------|
| Transfer basarisiz              | PBX trunk baglanti yok         | SIP trunk kayitini kontrol edin           |
| SMS gitmiyor                   | SMS servisi hata               | Twilio SMS loglarini kontrol edin         |
| Yanlis numaraya yonleniyor      | Konfigurasyon hatasi           | voiceConfig.fallback.phone kontrol edin   |

### 6.5 Log Kontrol Komutlari

```bash
# Voice server loglari
docker logs voice-server --tail 100 -f

# SIP trafigi izleme
docker exec voice-server sngrep

# Belirli cagri loglari
docker logs voice-server 2>&1 | grep "CALL_ID"

# Provider hatalari
docker logs voice-server 2>&1 | grep -E "ERROR|WARN|FAIL"

# Aktif cagrilari goruntuleme
curl -s http://localhost:3001/api/voice/active-calls | jq
```

### 6.6 Yaygin Hata Kodlari

| SIP Kodu | Anlami                  | Aksiyon                                   |
|----------|------------------------|-------------------------------------------|
| 100      | Trying                 | Normal, bekleyin                          |
| 180      | Ringing                | Normal, caliyor                           |
| 200      | OK                     | Basarili                                  |
| 401      | Unauthorized           | Kimlik bilgilerini kontrol edin           |
| 403      | Forbidden              | IP/izin kontrol edin                      |
| 404      | Not Found              | Numara/extension kontrol edin             |
| 408      | Timeout                | Ag baglantisi kontrol edin                |
| 480      | Temporarily Unavailable| Hedef musait degil                        |
| 486      | Busy Here              | Hat mesgul                                |
| 487      | Request Terminated     | Cagri iptal edildi                        |
| 488      | Not Acceptable         | Codec uyumsuzlugu, codec listesini genisletin |
| 500      | Server Error           | Sunucu loglarini kontrol edin             |
| 503      | Service Unavailable    | Sunucu kaynagi yetersiz                   |
