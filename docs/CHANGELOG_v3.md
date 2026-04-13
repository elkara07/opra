# Changelog: v1.26.0 → v3.0.0 (aliorkun branch)

**Tarih:** 2026-03-29
**Commit Sayisi:** 87
**Degisen Dosya:** 65
**Eklenen Satir:** +7,061 | **Silinen Satir:** -2,017

---

## Ozet

Bu degisiklik seti, platformun **v1.26.0** surumunden **v3.0.0** surumune gecisini kapsamaktadir. Ana odak noktalari:

1. **Voice AI Pipeline** — Tamamen yeniden yazildi, multi-provider destegi eklendi
2. **Guvenlik** — SUPERADMIN izolasyonu, tenant guvenlik, API key sifreleme
3. **Akilli Rezervasyon** — Kapasite skorlama, SEATED uyari, calisma saati kontrolu
4. **Frontend UX** — Dashboard, Superadmin, Voice sayfalarinda kapsamli iyilestirmeler
5. **Dokumantasyon** — API referans, guvenlik denetimi, test raporlari

---

## 1. Voice AI Pipeline (Tamamen Yeniden Yazildi)

### 1.1 LiveKit Room Agent (`room_agent.py`) — YENi
- LiveKit room'a katilarak gercek zamanli ses pipeline
- VAD (Voice Activity Detection): 1300ms sessizlik esigi, 300ms minimum konusma
- Echo guard: %70 kelime benzerligi algılama (TTS echo onleme)
- Zone fuzzy matching: "pencere", "teras" gibi tercihleri otomatik esleme
- Otomatik onay: tum slotlar (tarih, saat, kisi, isim) doluysa direkt rezervasyon
- Maks 20 tur/arama limiti (abuse onleme)
- 5 bos STT sonucu → otomatik arama sonlandirma
- MP3/OGG/WAV → PCM 24kHz mono donusumu

### 1.2 Prompt Builder (`prompt_builder.py`) — YENi
- Turkce ve Ingilizce dinamik sistem prompt'u
- Adim adim guided conversation (karsilama → bilgi toplama → kontrol → onay → bitis)
- Guvenlik kurallari (jailbreak onleme, hassas veri paylasmamayi zorlama)
- STT hata toleransi (benzer kelimeler, sayi fuzzy matching)
- Filler mesajlari ("Hemen kontrol ediyorum...", "En uygun masayi ayarliyorum...")
- Yanit basi maks 2 cumle siniri

### 1.3 Rule Engine (`rule_engine.py`) — YENi
- Hybrid slot extraction: kural tabanli + LLM fallback
- Intent algilama: rezervasyon, iptal, bilgi, karsilama, belirsiz
- Tarih parsing: "bugun", "yarin", gun isimleri, YYYY-MM-DD
- Saat parsing: "saat 19:00", "aksam 8", "ogle"
- Kisi sayisi: sayi + yazili form ("iki kisi", "4 kisi")
- Isim cikarma: "adim X", "ben X olarak", "isim X"
- Confidence scoring: 0.1 (belirsiz) → 0.9 (tum slotlar dolu)
- LLM fallback tetikleyicileri: belirsiz intent, <2 slot, >20 kelime

### 1.4 Multi-Provider STT (`stt_router.py`)
- **Deepgram** Nova-3 (batch + streaming WebSocket)
- **Groq** Whisper Large v3 Turbo ($0.04/saat, 216x gercek zamanli)
- **OpenAI** Whisper-1 (batch)
- **Google Cloud** STT (REST API)
- **Azure** Speech Recognition
- Otomatik WAV header olusturma (raw PCM → valid media)
- Dil esleme (tr, en, es, zh, ko, vi)
- Fallback zinciri: primary → Whisper

### 1.5 Multi-Provider NLP (`nlp_router.py`)
- **Groq** llama-3.3-70b-versatile (OpenAI uyumlu)
- **Claude** claude-sonnet-4-20250514 (Anthropic)
- **DeepSeek** deepseek-chat (OpenAI uyumlu)
- **Gemini** gemini-2.0-flash (Google)
- **OpenAI** gpt-4o-mini
- **Dialogflow** REST API (Google)
- **Rasa** self-hosted NLP
- JSON response format zorlama
- Konusma gecmisi 800 karakter limiti (latency icin)
- Primary + automatic fallback stratejisi
- 150 max token/yanit

### 1.6 Multi-Provider TTS (`tts_router.py`)
- **Edge TTS** Microsoft ucretsiz (API key gereksiz)
- **OpenAI** tts-1 (PCM format, speed=1.15)
- **ElevenLabs** eleven_flash_v2_5 (dil bazli sesler)
- **Google Cloud** TTS (4M karakter/ay ucretsiz)
- **Azure** Cognitive Services (SSML)
- **Amazon Polly** neural sesler
- **Deepgram Aura** dusuk gecikme
- Fallback zinciri: primary → edge (ucretsiz) → elevenlabs
- Kadin sesi varsayilan (EmelNeural, tr-TR)

### 1.7 Call Router (`call_router.py`)
- PBX modlari: ai_first, pbx_first, ai_only, pbx_only
- Transfer kosullari: 3x bos STT, kullanici istegi, AI timeout, DTMF 0
- Sesli posta ve callback isleme
- SMS bildirimi (musteri + restoran)
- Tenant voice config cacheleme (60sn)

### 1.8 Pipeline Zamanlama
- STT/NLP/TTS ms cinsinden loglama
- Her adimin suresi olculuyor

---

## 2. Guvenlik Iyilestirmeleri

### 2.1 SUPERADMIN Izolasyonu
- SUPERADMIN artik tenant'tan bagimsiz (tenantId=null)
- Platform yoneticisi ile restoran sahibi ayrildi
- Tum servislerde tenant-null ve service-key destegi

### 2.2 Tenant Guvenlik Denetimi
- 3 CRITICAL, 5 HIGH, 5 MEDIUM, 3 LOW bulgu tespit ve duzeltme
- Analytics tenantId spoofing onlendi
- Voice DID tenant izolasyonu saglandi
- Communication log cross-tenant injection onlendi
- Stripe webhook tenant plan degisikligi guvenli hale getirildi

### 2.3 API Key Sifreleme (DB Bridge)
- AES-256-CBC ile sifreleme (IV + ciphertext)
- Tum API key'ler DB'de sifreli saklanıyor (app_configs tablosu)
- Voice service artik DB'den key okuyor (env yerine)
- SHA-256 hash ile 32-byte key uyumu
- Maskelenmiş gosterim (ilk 4 + **** + son 4)

### 2.4 Auth Middleware Guncelleme
- Tum servislere (menu, floor-plan, notification, reservation, staff) service-key destegi
- SUPERADMIN tenantId=null crash duzeltmesi
- Token blacklist Redis'ten kontrol

### 2.5 Input Guvenlik
- XSS onleme — sanitization
- Telefon format dogrulama (10-15 hane)
- Tarih/saat format dogrulama

---

## 3. Reservation Service Iyilestirmeleri

### 3.1 Akilli Availability Endpoint
- Kapasite skorlama: 100 (mukemmel uyum) → 20 (kotu uyum)
- SEATED masa uyarilari (misafir ismi + tahmini bitis)
- Tenant `avgSittingMinutes` destegi (varsayilan 90dk yerine)
- Calisma saati kontrolu (gece gecisi dahil: 23:00-02:00)
- Redis cache (30sn) ile performans
- Sonuc siralama: uygun > skor > kapasite

### 3.2 Rezervasyon Guvenligi
- Voice rezervasyon: otomatik tableId + slot_data merge
- Telefon + KVKK + tableId eklendi
- Otomatik onay — tum slotlar doluysa confirmed=true
- Idempotent creation (x-idempotency-key)

### 3.3 Voice Blacklist Sistemi
- Telefon numarasi kara liste yonetimi
- Abuse detection
- API + tenant UI destegi
- Redis + DB loglama

---

## 4. Frontend Degisiklikleri

### 4.1 DashboardPage
- Onboarding banner (adim adim kurulum rehberi)
- Saatlik yogunluk grafigi (totalGuests oncelikli)
- Peak saat gostergesi
- Coklu lokasyon (franchise) dashboard destegi
- SuperadminDashboard bileseni

### 4.2 ReservationsPage
- Akilli masa onerisi (availability API entegrasyonu)
- Kanal rozetleri: APP, PHONE, VOICE_AI, OPENTABLE, RESY, YELP, SEVENROOMS
- Tekrarlayan rezervasyon kurallari yonetimi
- Bekleme listesi yonetimi
- Walk-in coklu masa secimi

### 4.3 SuperadminPage
- 8 tab: Genel, Tenantlar, Kullanicilar, API Keys, Planlar, Guvenlik, Voice, Kullanim
- API key yonetimi (kategori bazli: LiveKit, NetGSM, DID, Adisyo, uluslararasi)
- Entegrasyon test kartlari
- Voice istatistikleri + LiveKit room izleme
- Impersonation ozelligi
- Plan dagilimi gorsellestirme

### 4.4 VoiceSettingsPage — YENi TASARIM
- Platform geneli STT/NLP/TTS yapilandirmasi
- Provider dropdown'lari (ipuclari ile)
- Yedek provider secimi
- Ses cinsiyet secimi (kadin/erkek, Turkce sesler)
- Alan bazli dogrulama

### 4.5 VoiceTopologyPage — YENi TASARIM
- 5 fazli pipeline gorsellestirmesi: Gelen Arama → STT → NLP → TTS → Yanit
- Provider durum kartlari: UP (yesil), NOKEY (gri), STANDBY, WARNING
- Primary/Backup rol rozetleri
- Key kaynak gostergesi (DB vs ENV)
- Canli LiveKit durum bilgisi

### 4.6 PlatformCostsPage
- Donem secici (Bugun, Bu Hafta, Bu Ay, Tum Zamanlar)
- Provider bazli maliyet ozeti
- Gunluk maliyet toplamlari

### 4.7 CustomerPage — YENi
- Musteri listesi (sayfalama, filtreleme)
- Kademe sistemi: VIP, GOLD, SILVER, STANDARD
- Voice blacklist yonetimi (iki tab)
- Telefon numarasi maskeleme

### 4.8 Timeline Bileşeni
- Responsive grid (tenant calisma saatlerine gore)
- Renk kodlu doluluk: yesil (<50%), turuncu (50-80%), kirmizi (>80%)
- Peak slot vurgulama (nabiz animasyonu)
- Canli kirmizi cizgi (simdi gostergesi)
- Surukleme destegi (zaman kaydirma)

### 4.9 Layout/Navigasyon
- Rol bazli menu gosterimi (SUPERADMIN ayri menuler)
- Superadmin-only sayfalar: Platform Yonetimi, Voice Topoloji, Voice Ayarlar, Platform Maliyetleri
- Karanlik mod toggle

### 4.10 Store (Zustand)
- sessionStorage'a gecis (localStorage yerine — XSS guvenlik iyilestirmesi)
- GUEST token icin JWT decode (API cagrisi atlanir)
- Service worker cache temizleme (logout)

---

## 5. Analytics Service Iyilestirmeleri

- Superadmin icin platform geneli istatistikler
- Voice cost endpoint
- Period filtresi (bugun, hafta, ay)
- Kullanici yonetimi guvenlik iyilestirmeleri
- Tenant izolasyonu duzeltmeleri

---

## 6. Yeni Dokumanlar

| Dosya | Icerik |
|-------|--------|
| `PROJE_DOKUMANI.md` | Kapsamli proje dokumantasyonu (Turkce) |
| `docs/API_REFERENCE.md` | 568 satir — tum API endpoint'leri, JWT yapisi, rate limit |
| `docs/MENU_ENDPOINT_MAP.md` | 414 satir — 22 sayfa UI → API eslesmesi |
| `docs/SECURITY_AUDIT.md` | 226 satir — guvenlik denetim raporu (3C, 5H, 5M, 3L) |
| `docs/FAZ3_BULGULAR.md` | 129 satir — UX bulgulari ve sprint plani |
| `docs/SIMULATION_RESULTS.md` | 92 satir — v2.3.0 simulasyon test sonuclari |
| `docs/TEST_REPORT_v2.6.md` | 94 satir — 33/35 PASS, Grade A guvenlik |
| `docs/CHANGELOG_v3.md` | Bu dokuman |
| `docs/API_ENDPOINTS_TABLE.md` | Servis bazli tum endpoint tablosu |

---

## 7. Altyapi Degisiklikleri

### 7.1 Docker Compose
- Voice agent service bagimliliklari guncellendi
- INTERNAL_SERVICE_KEY eklendi

### 7.2 CI/CD
- `.github/workflows/ci.yml` kaldirildi (token scope sorunu)

### 7.3 Voice Agent Dependencies (requirements.txt)
- `livekit-api>=0.7.0` + `livekit-agents>=1.0` eklendi
- `groq>=0.10.0` eklendi
- `deepgram-sdk>=3.0.0` eklendi
- `edge-tts>=6.1.0` eklendi
- `numpy>=2.0.0` + `audioop-lts>=0.2.1` eklendi

---

## 8. Commit Gecmisi (Onem Sirasina Gore)

### Buyuk Ozellikler
| Commit | Aciklama |
|--------|----------|
| `747242f` | v3.0.0: Voice pipeline sprint + reservation guvenlik + frontend fix |
| `ee2a70a` | Hybrid voice rule engine — kural tabanli slot extraction |
| `9b342fc` | Multi-step guided conversation — filler + availability check |
| `afe3034` | LiveKit Agent room katilimi — gercek ses pipeline |
| `d362189` | Ses topolojisi fazli pipeline + provider DB bridge + yeni AI'lar |
| `77c1c05` | Voice call blacklist system — abuse detection, API, tenant UI |
| `1be4247` | Prompt guvenlik katmani + Turkce karakter duzeltmesi |
| `87d5a74` | SUPERADMIN tenant'tan bagimsiz — platform yonetici ayrildi |
| `b703b17` | Akilli availability endpoint — kapasite skoru, SEATED uyari |
| `704fe99` | Saatlik yogunluk yeniden tasarim + timeline responsive |

### Guvenlik
| Commit | Aciklama |
|--------|----------|
| `f3069fc` | CRITICAL guvenlik duzeltmeleri — tenant izolasyonu |
| `6fc5b42` | Kalan guvenlik duzeltmeleri — voice, KVKK, Stripe, token depolama |
| `bb6c5a6` | SUPERADMIN auth — tum servislerde tenant-null ve service-key destegi |
| `61f6538` | API Key DB Bridge — voice service DB'den key okuyor |
| `a6665fe` | Encryption key SHA-256 hash — AES-256-CBC 32 byte uyumu |

### Voice Pipeline Fixler
| Commit | Aciklama |
|--------|----------|
| `c288537` | UnboundLocalError response_text duzeltmesi |
| `2b57765` | NLP bos dondugunde slotlar doluysa otomatik rezervasyon |
| `06a5592` | Voice reservation — otomatik tableId + slot_data merge |
| `2ac5fe6` | Groq JSON mode zorlandi |
| `7c38ec8` | Tarih cuma→YYYY-MM-DD donusumu + NLP raw text fallback |
| `d665c2c` | Echo guard + zone fuzzy match + Deepgram keyword boost |
| `917c494` | Deepgram STT raw PCM format — linear16 48kHz |
| `eddebaa` | Kadin sesi (EmelNeural) + Turkce karakter + STT debug logging |
| `d26370c` | TTS MP3→PCM donusumu — av (ffmpeg) ile 24kHz mono |

### Frontend
| Commit | Aciklama |
|--------|----------|
| `d7faee6` | Akilli masa secimi + dashboard UX iyilestirmeleri |
| `cfdffb5` | Kullanilmayan ozellikler kaldirildi (voice personality, deposit UI, Google Calendar toggles) |
| `e767da6` | STT ve TTS yedek provider secimi eklendi |
| `bf27f8d` | PlatformCostsPage — kalan kredi gosterimi |

### Dokumantasyon
| Commit | Aciklama |
|--------|----------|
| `5715363` | Kapsamli API referans ve menu-endpoint esleme dokumanları |
| `63a7000` | Guvenlik denetimi — 3 CRITICAL, 5 HIGH bulgu |
| `a02aaef` | Kapsamli test raporu v2.6 — 33/35 PASS |
| `34f5ddb` | Simulasyon test sonuclari |

---

## 9. Degisen Dosyalar (Tam Liste)

### Yeni Dosyalar
| Dosya | Satir |
|-------|-------|
| `PROJE_DOKUMANI.md` | +1,196 |
| `docs/API_REFERENCE.md` | +567 |
| `docs/MENU_ENDPOINT_MAP.md` | +413 |
| `docs/SECURITY_AUDIT.md` | +225 |
| `docs/FAZ3_BULGULAR.md` | +128 |
| `docs/SIMULATION_RESULTS.md` | +91 |
| `docs/TEST_REPORT_v2.6.md` | +94 |
| `services/voice-agent-service/src/prompt_builder.py` | +238 |
| `services/voice-agent-service/src/rule_engine.py` | +268 |
| `frontend/src/pages/CustomerPage.jsx` | +88 |
| `services/auth-service/src/routes/settings.routes.js` | +23 |

### Buyuk Degisiklikler
| Dosya | Degisiklik |
|-------|-----------|
| `services/voice-agent-service/main.py` | +961 / -kalanlar (tamamen yeniden yazildi) |
| `services/voice-agent-service/src/room_agent.py` | +664 (buyuk genisleme) |
| `services/reservation-service/src/controllers/availability.controller.js` | +409 (akilli availability) |
| `services/reservation-service/src/index.js` | +267 (blacklist, guvenlik) |
| `frontend/src/pages/VoiceTopologyPage.jsx` | +672/-672 (tamamen yeniden tasarim) |
| `frontend/src/pages/ReservationsPage.jsx` | +360/-360 (buyuk guncelleme) |
| `frontend/src/pages/SuperadminPage.jsx` | +316/-316 (buyuk guncelleme) |
| `frontend/src/pages/TenantSettingsPage.jsx` | -331 (sadeleştirme) |
| `frontend/src/pages/DashboardPage.jsx` | +268 (yeni ozellikler) |

### Kucuk Degisiklikler
| Dosya | Degisiklik |
|-------|-----------|
| `frontend/src/pages/VoiceSettingsPage.jsx` | +140 |
| `services/auth-service/src/controllers/settings.controller.js` | +119 |
| `services/voice-agent-service/src/nlp_router.py` | +114 |
| `services/voice-agent-service/src/stt_router.py` | +89 |
| `services/voice-agent-service/src/call_router.py` | +87 |
| `frontend/src/components/UI/Layout.jsx` | +88 |
| `services/reservation-service/src/controllers/reservation.controller.js` | +79 |
| `services/analytics-service/main.py` | +73 |
| `services/auth-service/src/controllers/config.controller.js` | +61 |
| `frontend/src/components/Reservation/Timeline.jsx` | +61 |
| `services/voice-agent-service/src/tts_router.py` | +53 |

### Middleware Guncellemeleri (Her Servise Eklenen)
- `services/auth-service/src/middleware/auth.middleware.js` (+11)
- `services/floor-plan-service/src/middleware/auth.middleware.js` (+14)
- `services/menu-service/src/middleware/auth.middleware.js` (+14)
- `services/notification-service/src/middleware/auth.middleware.js` (+14)
- `services/reservation-service/src/middleware/auth.middleware.js` (+14)
- `services/staff-service/src/middleware/auth.middleware.js` (+14)

---

## 10. Versiyon Gecmisi

| Versiyon | Tarih | Aciklama |
|----------|-------|----------|
| v1.26.0 | 2026-03-23 | elkara/main — son stabil surum |
| v2.0.0 | 2026-03-24 | Dashboard, analitik, auth fix, simulasyon |
| v2.3.0 | 2026-03-25 | Voice hizlandirma, kapsamli audit, 20+ ticket |
| v2.6.0 | 2026-03-26 | Guvenlik, SUPERADMIN ayrimi, API key DB bridge |
| v3.0.0 | 2026-03-27–29 | Voice pipeline sprint, LiveKit, multi-provider, rule engine |
