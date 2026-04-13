# Twilio Kurulum Kılavuzu

## 1. Hesap Oluştur

1. https://twilio.com adresine git
2. "Sign up for free" ile ücretsiz hesap oluştur
3. Telefon numaranı doğrula

## 2. API Bilgilerini Al

Twilio Console'dan (https://console.twilio.com):
- **Account SID**: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- **Auth Token**: Dashboard'da görünür (göz ikonuna tıkla)

## 3. Telefon Numarası Al

1. Console → Phone Numbers → Manage → Buy a number
2. Turkey (+90) filtresiyle SMS + Voice destekli numara seç
3. Ücretsiz hesaplarda deneme numarası verilir

## 4. .env Dosyasını Güncelle

```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx
```

## 5. Servisi Yeniden Başlat

```bash
sudo docker compose restart notification-service
```

## 6. Test Et

Ayarlar sayfasından → SMS Test bölümü → Numaranı gir → Test SMS Gönder

## Ücretler

- Ücretsiz hesap: 15.50$ kredi, +1 numarası
- SMS: ~0.0075$/mesaj
- Ses araması: ~0.0135$/dakika
- Türkiye'ye SMS: ~0.05$/mesaj

## Sesli Hatırlatma için Webhook

Sesli hatırlatma özelliğini kullanmak için sisteminizin dışarıdan erişilebilir olması gerekir:

```bash
# ngrok ile geçici public URL
ngrok http 80
# .env'e ekle:
PUBLIC_HOST=xxxx.ngrok.io
```

## Sorun Giderme

- **SMS gitmiyor**: Twilio trial hesabında sadece doğrulanmış numaralara gönderim yapılabilir
- **Sesli arama çalışmıyor**: PUBLIC_HOST doğru ayarlanmış mı kontrol edin
- **401 hatası**: Auth Token yanlış
