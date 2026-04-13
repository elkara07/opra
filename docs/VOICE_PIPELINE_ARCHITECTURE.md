# Ses Pipeline Mimarisi (Voice Pipeline Architecture)

## Genel Bakis

Rezervasyon uygulamasi, restoranlara gelen telefonlari yapay zeka destekli sesli ajan ile karsilayan ve gerektiginde insan operatore yonlendiren bir ses pipeline sistemine sahiptir.

---

## 1. Mevcut vs Hedef Mimari

### Mevcut Mimari
- Twilio SIP Trunk uzerinden gelen cagrilar
- Tek bir STT/TTS provider (Whisper + ElevenLabs)
- Basit NLP isleme (Claude)
- Manuel fallback yonetimi

### Hedef Mimari
- Coklu SIP kanal destegi (Twilio, LiveKit, WebRTC, Direkt SIP)
- 3 katmanli provider sistemi (STT / NLP / TTS) ile otomatik fallback
- PBX entegrasyonu (Asterisk, FreePBX, 3CX)
- Tenant bazli konfigurasyon
- Maliyet optimizasyonu ve provider secimi

---

## 2. 3 Katmanli Provider Sistemi

### STT (Speech-to-Text)
Gelen ses verisini metne cevirir.

| Provider     | Dil Destegi | Gecikme  | Maliyet      | Notlar                  |
|-------------|-------------|----------|--------------|-------------------------|
| Whisper     | 99+ dil     | ~1-2sn   | $0.006/dk    | Varsayilan, self-host    |
| Google STT  | 125+ dil    | ~0.5-1sn | $0.006/dk    | Streaming destegi        |
| Azure STT   | 100+ dil    | ~0.5-1sn | $0.0085/dk   | Kurumsal SLA            |
| Deepgram    | 30+ dil     | ~0.3sn   | $0.0044/dk   | En dusuk gecikme         |

### NLP (Natural Language Processing)
Metni anlamlandirir, niyet cikarir ve cevap uretir.

| Provider     | Model          | Gecikme  | Maliyet         | Notlar                    |
|-------------|----------------|----------|-----------------|---------------------------|
| Claude      | claude-sonnet  | ~1-2sn   | $3/1M input     | Varsayilan, en iyi kalite |
| OpenAI      | gpt-4o         | ~1-2sn   | $2.50/1M input  | Fallback                  |
| Gemini      | gemini-2.0     | ~1sn     | $1.25/1M input  | Maliyet optimizasyonu     |

### TTS (Text-to-Speech)
Uretilen cevabi sese cevirir.

| Provider     | Ses Kalitesi | Gecikme  | Maliyet          | Notlar                  |
|-------------|-------------|----------|------------------|-------------------------|
| ElevenLabs  | Cok yuksek  | ~0.5-1sn | $0.30/1K karakter| Varsayilan               |
| Google TTS  | Yuksek      | ~0.3sn   | $0.016/1K kar.   | Maliyet optimizasyonu    |
| Azure TTS   | Yuksek      | ~0.3sn   | $0.016/1K kar.   | Kurumsal SLA            |
| PlayHT      | Cok yuksek  | ~0.8sn   | $0.25/1K kar.    | Ozel ses klonlama        |

---

## 3. Provider Registry ve Fallback Zinciri

Provider registry, her katman icin birincil ve yedek providerlari tanimlar. Bir provider basarisiz olursa (timeout, hata, kota asimi), otomatik olarak fallback providera gecilir.

### Fallback Stratejisi

```
STT: Whisper → Google STT → Azure STT
NLP: Claude → OpenAI → Gemini
TTS: ElevenLabs → Google TTS → Azure TTS
```

### Fallback Tetikleme Kosullari
- HTTP 5xx hatalari
- Timeout (provider bazli esik degerleri)
- Rate limit asimi (HTTP 429)
- Baglanti hatalari

### Circuit Breaker
Her provider icin circuit breaker mekanizmasi:
- **Kapali (Normal):** Istekler providera gider
- **Acik (Devre Kesik):** 5 ardisik hata sonrasi, 60sn boyunca istekler dogrudan fallback providera yonlendirilir
- **Yari Acik:** 60sn sonra tek bir test istegi gonderilir, basariliysa devre kapanir

---

## 4. Ses Kanallari

### 4.1 Twilio SIP Trunk
- En yaygin kullanim senaryosu
- Twilio uzerinden DID numara alinir
- SIP trunk voice-server'a yonlendirilir
- SRTP/TLS destegi
- Maliyet: ~$1/ay DID + $0.0085/dk gelen cagri

### 4.2 LiveKit SIP
- LiveKit'in SIP Bridge ozeligi uzerinden
- WebRTC ↔ SIP donusumu
- Dusuk gecikme, yuksek kalite
- LiveKit Cloud veya self-hosted
- Maliyet: LiveKit lisansi + SIP trunk maliyeti

### 4.3 WebRTC (Tarayici/Mobil)
- Dogrudan tarayici veya mobil uygulama uzerinden
- SIP trunk gerektirmez
- Dahili cagrilar icin idealdir
- STUN/TURN sunucu gerektirir

### 4.4 Direkt SIP
- Mevcut PBX sisteminden dogrudan SIP baglantisi
- Ucuncu parti SIP trunk gerektirmez
- On-premise kurulumlar icin
- SIP URI: `sip:restaurant@voice.example.com`

---

## 5. PBX Entegrasyon Modlari

### ai_first (Varsayilan)
```
Gelen Cagri → AI Sesli Ajan → [Basarisiz/Transfer] → PBX → Insan Operator
```
- AI once cevaplar
- Musteri isterse veya AI cevaplayamazsa PBX'e aktarir
- En yaygin mod

### pbx_first
```
Gelen Cagri → PBX IVR Menusu → [Rezervasyon Secenegi] → AI Sesli Ajan
```
- PBX IVR menusu once calisir
- Musteri "rezervasyon" secenegini secerse AI'a yonlendirilir
- Mevcut IVR altyapisi olan restoranlar icin

### ai_only
```
Gelen Cagri → AI Sesli Ajan → [Basarisiz] → SMS Bildirimi
```
- Sadece AI kullanilir, PBX yok
- Basarisiz cagrilarda SMS gonderilir
- Kucuk isletmeler icin

### pbx_only
```
Gelen Cagri → PBX → Insan Operator (AI yok)
```
- AI devre disi
- Geleneksel PBX kullanimi
- Sesli ajan istenmeyen durumlar icin

---

## 6. Call Fallback Zinciri

```
1. AI Sesli Ajan cevaplar
   ├── Basarili → Rezervasyon olusturulur
   └── Basarisiz (timeout, hata, musteri istegi)
       ↓
2. PBX'e transfer (eger yapilandirilmissa)
   ├── Basarili → Insan operator cevaplar
   └── Cevapsiz (ringTimeout suresi doldu)
       ↓
3. SMS Bildirimi
   - Musteriye: "Cagriniz alinamadi, sizi en kisa surede arayacagiz"
   - Restorana: "Kacirilmis cagri: +90XXX, saat: HH:MM"
```

### Fallback Konfigurasyon Parametreleri
- `ringTimeout`: PBX'te calma suresi (varsayilan: 30sn)
- `noAnswerAction`: Cevapsiz durumda aksiyon (`sms`, `voicemail`, `queue`)
- `maxRetries`: AI yeniden deneme sayisi (varsayilan: 1)

---

## 7. voiceConfig JSON Yapisi

Her tenant icin `voiceConfig` alani asagidaki yapiyi tasir:

```json
{
  "voiceConfig": {
    "stt": {
      "provider": "whisper",
      "language": "tr",
      "model": "large-v3",
      "fallback": "google"
    },
    "nlp": {
      "primary": "claude",
      "model": "claude-sonnet-4-20250514",
      "fallback": "openai",
      "systemPrompt": "Sen bir restoran rezervasyon asistanisin...",
      "maxTokens": 500,
      "temperature": 0.3
    },
    "tts": {
      "provider": "elevenlabs",
      "voiceId": "pNInz6obpgDQGcFmaJgB",
      "language": "tr",
      "speed": 1.0,
      "fallback": "google"
    },
    "pbx": {
      "mode": "ai_first",
      "sipTrunk": {
        "host": "pbx.restaurant.com",
        "port": 5060,
        "transport": "udp",
        "username": "ai-agent",
        "password": "***"
      },
      "extension": "100",
      "transferExtension": "200"
    },
    "fallback": {
      "enabled": true,
      "phone": "+905551234567",
      "sipAddress": "sip:fallback@pbx.restaurant.com",
      "ringTimeout": 30,
      "noAnswerAction": "sms",
      "smsTemplate": "Kacirilmis cagri: {{callerNumber}}, {{dateTime}}"
    },
    "channels": {
      "twilio": {
        "enabled": true,
        "accountSid": "AC...",
        "authToken": "***",
        "phoneNumber": "+908501234567"
      },
      "livekit": {
        "enabled": false,
        "serverUrl": "wss://livekit.example.com",
        "apiKey": "***",
        "apiSecret": "***"
      },
      "webrtc": {
        "enabled": true,
        "stunServer": "stun:stun.l.google.com:19302",
        "turnServer": "turn:turn.example.com:3478"
      },
      "directSip": {
        "enabled": false,
        "listenPort": 5060,
        "transport": "udp"
      }
    },
    "recording": {
      "enabled": true,
      "format": "wav",
      "retention": 90
    },
    "analytics": {
      "enabled": true,
      "trackCost": true,
      "trackLatency": true
    }
  }
}
```

---

## 8. Tenant Konfigurasyon Rehberi

### Temel Kurulum (Sadece AI)
Minimum konfigurasyon, hizli baslangilc:

```json
{
  "voiceConfig": {
    "stt": { "provider": "whisper", "language": "tr" },
    "nlp": { "primary": "claude" },
    "tts": { "provider": "elevenlabs" },
    "pbx": { "mode": "ai_only" },
    "fallback": { "enabled": true, "phone": "+905551234567", "noAnswerAction": "sms" }
  }
}
```

### Orta Seviye (AI + PBX Fallback)
AI oncelikli, PBX yedekli:

```json
{
  "voiceConfig": {
    "stt": { "provider": "whisper", "language": "tr", "fallback": "google" },
    "nlp": { "primary": "claude", "fallback": "openai" },
    "tts": { "provider": "elevenlabs", "fallback": "google" },
    "pbx": {
      "mode": "ai_first",
      "sipTrunk": { "host": "pbx.example.com", "port": 5060 },
      "transferExtension": "200"
    },
    "fallback": { "enabled": true, "phone": "+905551234567", "ringTimeout": 30, "noAnswerAction": "sms" }
  }
}
```

### Kurumsal (Tam Entegrasyon)
Tum ozellikler aktif, coklu kanal:

Yukaridaki tam JSON yapisini kullanin ve tum kanallari etkinlestirin.

---

## 9. Maliyet Karsilastirmasi

### Senaryo: Ayda 1000 cagri, ortalama 2 dakika/cagri

| Bilesen      | Ekonomik          | Standart           | Premium            |
|-------------|-------------------|--------------------|--------------------|
| STT         | Whisper: $12      | Whisper: $12       | Deepgram: $8.80    |
| NLP         | Gemini: ~$5       | Claude: ~$12       | Claude: ~$12       |
| TTS         | Google: $6.40     | ElevenLabs: $120   | ElevenLabs: $120   |
| SIP/Telekom | Twilio: $17       | Twilio: $17        | LiveKit+SIP: $25   |
| **Toplam**  | **~$40/ay**       | **~$161/ay**       | **~$166/ay**       |

### Maliyet Optimizasyon Onerileri
- Kisa cagrilar icin Deepgram STT kullanin (daha dusuk gecikme, daha az maliyet)
- Yogun saatlerde Google TTS'e gecis yapin (ElevenLabs kotasi korumak icin)
- NLP cache kullanin (sik sorulan sorular icin)
- Cagri kayitlarini 30 gun sonra silin (depolama maliyeti)

---

## 10. Docker Compose Ortam Degiskenleri

```env
# === Genel Ses Ayarlari ===
VOICE_ENABLED=true
VOICE_DEFAULT_LANGUAGE=tr
VOICE_MAX_CALL_DURATION=600
VOICE_RECORDING_ENABLED=true

# === STT (Speech-to-Text) ===
STT_PROVIDER=whisper
STT_FALLBACK_PROVIDER=google
WHISPER_MODEL=large-v3
WHISPER_API_URL=http://whisper:9000
GOOGLE_STT_CREDENTIALS=/secrets/google-stt.json
AZURE_STT_KEY=
AZURE_STT_REGION=westeurope
DEEPGRAM_API_KEY=

# === NLP ===
NLP_PRIMARY_PROVIDER=claude
NLP_FALLBACK_PROVIDER=openai
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_AI_API_KEY=
NLP_MAX_TOKENS=500
NLP_TEMPERATURE=0.3

# === TTS (Text-to-Speech) ===
TTS_PROVIDER=elevenlabs
TTS_FALLBACK_PROVIDER=google
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=pNInz6obpgDQGcFmaJgB
GOOGLE_TTS_CREDENTIALS=/secrets/google-tts.json
AZURE_TTS_KEY=
AZURE_TTS_REGION=westeurope
PLAYHT_API_KEY=
PLAYHT_USER_ID=

# === Twilio ===
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=+908501234567
TWILIO_SIP_DOMAIN=restaurant.sip.twilio.com

# === LiveKit ===
LIVEKIT_URL=wss://livekit.example.com
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
LIVEKIT_SIP_ENABLED=false

# === WebRTC ===
WEBRTC_ENABLED=true
STUN_SERVER=stun:stun.l.google.com:19302
TURN_SERVER=turn:turn.example.com:3478
TURN_USERNAME=
TURN_PASSWORD=

# === Direkt SIP ===
DIRECT_SIP_ENABLED=false
DIRECT_SIP_PORT=5060
DIRECT_SIP_TRANSPORT=udp

# === PBX ===
PBX_MODE=ai_first
PBX_SIP_HOST=
PBX_SIP_PORT=5060
PBX_SIP_USERNAME=
PBX_SIP_PASSWORD=
PBX_TRANSFER_EXTENSION=200

# === Fallback ===
FALLBACK_ENABLED=true
FALLBACK_PHONE=
FALLBACK_RING_TIMEOUT=30
FALLBACK_NO_ANSWER_ACTION=sms

# === Provider Circuit Breaker ===
CIRCUIT_BREAKER_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60000

# === Kayit ve Analitik ===
RECORDING_FORMAT=wav
RECORDING_RETENTION_DAYS=90
ANALYTICS_ENABLED=true
ANALYTICS_TRACK_COST=true
```

---

## Mimari Diyagram (Basitlestirilmis)

```
                    ┌─────────────┐
                    │  Gelen Cagri │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────┴─────┐ ┌───┴───┐ ┌─────┴─────┐
        │Twilio SIP │ │WebRTC │ │Direkt SIP │
        └─────┬─────┘ └───┬───┘ └─────┬─────┘
              │            │            │
              └────────────┼────────────┘
                           │
                    ┌──────┴──────┐
                    │ Voice Server│
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────┴─────┐ ┌───┴───┐ ┌─────┴─────┐
        │    STT    │ │  NLP  │ │    TTS    │
        │ Whisper   │ │Claude │ │ElevenLabs │
        │  ↓Google  │ │↓OpenAI│ │  ↓Google  │
        │  ↓Azure   │ │↓Gemini│ │  ↓Azure   │
        └───────────┘ └───────┘ └───────────┘
                           │
                    ┌──────┴──────┐
                    │  Fallback   │
                    │ PBX → SMS   │
                    └─────────────┘
```
