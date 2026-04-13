# Menü → API Endpoint Eşleştirmesi

> Her UI menüsü, butonu ve aksiyonunun hangi API endpoint'ini tetiklediğini gösterir.

---

## Rol Erişim Matrisi

| Menü | SUPERADMIN | OWNER | MANAGER | STAFF | GUEST |
|------|:----------:|:-----:|:-------:|:-----:|:-----:|
| Dashboard | ✓ | ✓ | ✓ | ✓ | - |
| Rezervasyonlar | ✓ | ✓ | ✓ | ✓ | - |
| Salon Planı | ✓ | ✓ | ✓ | ✓ (RO) | - |
| Menü Yönetimi | ✓ | ✓ | ✓ | - | - |
| Mutfak Ekranı (KDS) | ✓ | ✓ | ✓ | ✓ | - |
| Fiyatlandırma | ✓ | ✓ | - | - | - |
| Stok Yönetimi | ✓ | ✓ | ✓ | - | - |
| Personel | ✓ | ✓ | ✓ | - | - |
| Vardiya Takvimi | ✓ | ✓ | ✓ | - | - |
| Ödemeler | ✓ | ✓ | ✓ | ✓ | - |
| Kasa | ✓ | ✓ | ✓ | - | - |
| Faturalama | ✓ | ✓ | - | - | - |
| Muhasebe | ✓ | ✓ | - | - | - |
| Analitik | ✓ | ✓ | ✓ | - | - |
| Günlük Rapor | ✓ | ✓ | ✓ | - | - |
| Heatmap | ✓ | ✓ | ✓ | - | - |
| Müşteriler | ✓ | ✓ | ✓ | - | - |
| Arayan Profilleri | ✓ | ✓ | ✓ | - | - |
| İletişim Logları | ✓ | ✓ | ✓ | - | - |
| Genel Ayarlar | ✓ | ✓ | - | - | - |
| Bildirim Şablonları | ✓ | ✓ | - | - | - |
| Şubeler | ✓ | ✓ | - | - | - |
| Kullanıcı Yönetimi | ✓ | ✓ | ✓ | - | - |
| Denetim Kayıtları | ✓ | ✓ | - | - | - |
| Superadmin Panel | ✓ | - | - | - | - |
| Platform Maliyetleri | ✓ | - | - | - | - |
| Sistem Sağlığı | ✓ | ✓ | - | - | - |

---

## 1. Dashboard (`/`)

**Sayfa:** `DashboardPage.jsx`
**Roller:** SUPERADMIN, OWNER, MANAGER, STAFF

| Aksiyon / Widget | API Endpoint | Method |
|------------------|-------------|--------|
| Sayfa yüklenince — bugünkü rezervasyonlar | `/reservations/today` | GET |
| Sayfa yüklenince — aktif salon planı | `/floor-plans/active` | GET |
| Sayfa yüklenince — personel listesi | `/staff` | GET |
| Sayfa yüklenince — analitik özet | `/analytics/summary` | GET |
| Sayfa yüklenince — lokasyonlar | `/locations` | GET |
| Onboarding banner tıklama | İlgili sayfalara yönlendirme | - |

---

## 2. Rezervasyonlar (`/reservations`)

**Sayfa:** `ReservationsPage.jsx`
**Roller:** SUPERADMIN, OWNER, MANAGER, STAFF

| Aksiyon | API Endpoint | Method |
|---------|-------------|--------|
| Sayfa yüklenince — rezervasyon listesi | `/reservations?date=&status=` | GET |
| "Yeni Rezervasyon" butonu | `/reservations` | POST |
| Rezervasyon düzenle | `/reservations/:id` | PATCH |
| Rezervasyon iptal | `/reservations/:id` | DELETE |
| Durum değiştir (Oturdu, Tamamlandı vb.) | `/reservations/:id/status` | PATCH |
| Müsaitlik kontrolü | `/availability?date=&startTime=` | GET |
| Zaman çizelgesi | `/availability/timeline` | GET |
| Tekrarlayan kural ekle | `/reservations/recurring` | POST |
| Tekrarlayan kuralları göster | `/reservations/recurring` | GET |
| Tekrarlayan kural sil | `/reservations/recurring/:id` | DELETE |
| Bekleme listesine ekle | `/reservations/waitlist` | POST |
| Bekleme listesi | `/reservations/waitlist` | GET |
| Bekleme listesinden çıkar | `/reservations/waitlist/:id` | DELETE |
| Onay mesajı gönder | `/notifications/confirmation/trigger` | POST |
| Salon planı çek (masa seçimi) | `/floor-plans` | GET |

---

## 3. Salon Planı (`/floor-plan`)

**Sayfa:** `FloorPlanPage.jsx`
**Roller:** SUPERADMIN, OWNER, MANAGER, STAFF (sadece görüntüleme)

| Aksiyon | API Endpoint | Method |
|---------|-------------|--------|
| Salon listesi | `/floor-plans` | GET |
| Yeni salon oluştur | `/floor-plans` | POST |
| Salon düzenle (tüm elemanlar) | `/floor-plans/:id` | PUT |
| Salon sil | `/floor-plans/:id` | DELETE |
| Salonu aktif yap | `/floor-plans/:id/activate` | PATCH |
| QR kodları indir | `/menu/qr/:slug/pdf` | GET |

---

## 4. Menü Yönetimi (`/menu`)

**Sayfa:** `MenuPage.jsx`
**Roller:** SUPERADMIN, OWNER, MANAGER

| Aksiyon | API Endpoint | Method |
|---------|-------------|--------|
| Kategori listesi | `/menu/categories` | GET |
| Kategori oluştur | `/menu/categories` | POST |
| Kategori güncelle | `/menu/categories/:id` | PATCH |
| Kategori sil | `/menu/categories/:id` | DELETE |
| Ürün listesi | `/menu/items` | GET |
| Ürün ekle | `/menu/items` | POST |
| Ürün düzenle | `/menu/items/:id` | PATCH |
| Ürün sil | `/menu/items/:id` | DELETE |
| Fiyatlandırma kuralları | `/menu/pricing-rules` | GET |

---

## 5. Mutfak Ekranı — KDS (`/kds`)

**Sayfa:** `KDSPage.jsx`
**Roller:** SUPERADMIN, OWNER, MANAGER, STAFF

| Aksiyon | API Endpoint | Method |
|---------|-------------|--------|
| Mutfak kuyruğu | `/orders/kitchen-queue` | GET |
| Sipariş durumu değiştir | `/orders/:id/status` | PATCH |
| Ürün süreleri | `/orders/analytics/item-times` | GET |

---

## 6. Fiyatlandırma (`/pricing`)

**Sayfa:** `PricingPage.jsx`
**Roller:** SUPERADMIN, OWNER

| Aksiyon | API Endpoint | Method |
|---------|-------------|--------|
| Kural listesi | `/menu/pricing-rules` | GET |
| Kural oluştur | `/menu/pricing-rules` | POST |
| Kural güncelle | `/menu/pricing-rules/:id` | PATCH |
| Kural sil | `/menu/pricing-rules/:id` | DELETE |
| Fiyat geçmişi | `/menu/price-history` | GET |

---

## 7. Stok Yönetimi (`/stock`)

**Sayfa:** `StockPage.jsx`
**Roller:** SUPERADMIN, OWNER, MANAGER

| Aksiyon | API Endpoint | Method |
|---------|-------------|--------|
| Malzeme listesi | `/stock/ingredients` | GET |
| Malzeme ekle | `/stock/ingredients` | POST |
| Malzeme güncelle | `/stock/ingredients/:id` | PATCH |
| Malzeme sil | `/stock/ingredients/:id` | DELETE |
| Reçeteler | `/stock/recipes` | GET |
| Reçete kaydet | `/stock/recipes` | POST |
| Reçete sil | `/stock/recipes/:id` | DELETE |
| Stok hareketleri | `/stock/transactions` | GET |
| Hareket ekle | `/stock/transactions` | POST |
| Sayım listesi | `/stock/counts` | GET |
| Sayım oluştur | `/stock/counts` | POST |
| Tedarikçiler | `/stock/suppliers` | GET |
| Tedarikçi ekle | `/stock/suppliers` | POST |
| Tedarikçi güncelle | `/stock/suppliers/:id` | PATCH |
| Tedarikçi sil | `/stock/suppliers/:id` | DELETE |
| Düşük stok uyarıları | `/stock/low-stock` | GET |
| Stok raporu | `/stock/report` | GET |

---

## 8. Personel (`/staff`)

**Sayfa:** `StaffPage.jsx`
**Roller:** SUPERADMIN, OWNER, MANAGER

| Aksiyon | API Endpoint | Method |
|---------|-------------|--------|
| Personel listesi | `/staff` | GET |
| Personel ekle | `/staff` | POST |
| Personel düzenle | `/staff/:id` | PATCH |
| Personel deaktif et | `/staff/:id` | DELETE |
| Otomatik atama test | `/staff/auto-assign` | POST |
| Görev tamamla | `/staff/assignments/:id/complete` | POST |

---

## 9. Vardiya Takvimi (`/shifts`)

**Sayfa:** `ShiftCalendarPage.jsx`
**Roller:** SUPERADMIN, OWNER, MANAGER

| Aksiyon | API Endpoint | Method |
|---------|-------------|--------|
| Personel listesi | `/staff?activeOnly=true` | GET |
| Görevler (tarih aralığı) | `/staff/assignments?from=&to=` | GET |

---

## 10. Ödemeler (`/payments`)

**Sayfa:** `PaymentPage.jsx`
**Roller:** SUPERADMIN, OWNER, MANAGER, STAFF

| Aksiyon | API Endpoint | Method |
|---------|-------------|--------|
| Teslim edilmiş siparişler | `/orders?status=DELIVERED` | GET |
| Ödeme listesi | `/payments` | GET |
| Ödeme kaydet | `/payments` | POST |
| Hesap böl | `/payments/split` | POST |
| Günlük rapor | `/payments/daily-report` | GET |
| Aktif vardiya | `/shifts/current` | GET |

---

## 11. Kasa (`/cash-register`)

**Sayfa:** `CashRegisterPage.jsx`
**Roller:** SUPERADMIN, OWNER, MANAGER

| Aksiyon | API Endpoint | Method |
|---------|-------------|--------|
| Vardiya listesi | `/shifts` | GET |
| Aktif vardiya | `/shifts/current` | GET |
| Vardiya aç | `/shifts/open` | POST |
| Vardiya kapat | `/shifts/close` | POST |
| Ödeme listesi | `/payments` | GET |

---

## 12. Faturalama (`/billing`)

**Sayfa:** `BillingPage.jsx`
**Roller:** SUPERADMIN, OWNER

| Aksiyon | API Endpoint | Method |
|---------|-------------|--------|
| Plan listesi | `/billing/plans` | GET |
| Kullanım bilgisi | `/billing/usage` | GET |
| Versiyon bilgisi | `/version` | GET |
| Plan yükselt (Stripe) | `/billing/checkout` | POST |

---

## 13. Muhasebe (`/accounting`)

**Sayfa:** `AccountingPage.jsx`
**Roller:** SUPERADMIN, OWNER

| Aksiyon | API Endpoint | Method |
|---------|-------------|--------|
| Bağlantı listesi | `/analytics/accounting/connectors` | GET |
| CSV dışa aktar | `/analytics/accounting/export/csv` | POST |
| XML dışa aktar | `/analytics/accounting/export/xml` | POST |
| Paraşüt'e aktar | `/analytics/accounting/export/parasut` | POST |
| Logo'ya aktar | `/analytics/accounting/export/logo` | POST |
| Mikro'ya aktar | `/analytics/accounting/export/mikro` | POST |
| Faturalar | `/analytics/accounting/invoices` | GET |

---

## 14. Analitik (`/analytics`)

**Sayfa:** `AnalyticsPage.jsx`
**Roller:** SUPERADMIN, OWNER, MANAGER

| Aksiyon | API Endpoint | Method |
|---------|-------------|--------|
| Özet | `/analytics/summary` | GET |
| Masa analizi | `/analytics/tables` | GET |
| Personel analizi | `/analytics/staff` | GET |
| Kanal dağılımı | `/analytics/channels` | GET |
| Yoğun saatler | `/analytics/peak-hours` | GET |
| AI Danışman | `/analytics/advisor` | GET |
| Sesli arama istatistikleri | `/analytics/voice-stats` | GET |
| CSV indir | `/analytics/export/csv` | GET |
| PDF indir | `/analytics/export/pdf` | GET |

---

## 15. Müşteriler (`/customers`)

**Sayfa:** `CustomerPage.jsx`
**Roller:** SUPERADMIN, OWNER, MANAGER

| Aksiyon | API Endpoint | Method |
|---------|-------------|--------|
| Müşteri listesi | `/loyalty` | GET |
| Müşteri detayı | `/loyalty/detail?phone=` | GET |
| Müşteri güncelle (not, doğum günü) | `/loyalty/detail?phone=` | PATCH |
| Kara listeye al/çıkar | `/loyalty/detail?phone=` | PATCH |
| Veri silme talebi | `/auth/data-delete-request` | POST |

---

## 16. Ayarlar (`/settings`)

**Sayfa:** `TenantSettingsPage.jsx`
**Roller:** SUPERADMIN, OWNER

| Aksiyon | API Endpoint | Method |
|---------|-------------|--------|
| Ayarları yükle | `/settings` | GET |
| Ayarları güncelle | `/settings` | PATCH |
| Logo yükle | `/settings/logo` | POST |
| Entegrasyonları göster | `/settings/integrations` | GET |
| Entegrasyon kaydet | `/settings/integrations` | POST |
| Entegrasyon test | `/settings/integrations/test` | POST |
| Bildirim tercihleri | `/notifications/preferences` | GET |
| Tercihleri güncelle | `/notifications/preferences` | POST |
| Google OAuth URL | `/notifications/google/auth-url` | GET |
| Google durumu | `/notifications/google/status` | GET |
| WhatsApp durumu | `/notifications/whatsapp/status` | GET |
| Email durumu | `/notifications/email/status` | GET |
| Email test gönder | `/notifications/email` | POST |
| MFA durumu | `/auth/mfa/status` | GET |
| MFA kurulum | `/auth/mfa/setup` | POST |
| MFA doğrulama | `/auth/mfa/verify` | POST |
| MFA kapat | `/auth/mfa/disable` | DELETE |
| Onay ayarları | `/notifications/confirmation/settings` | GET |
| Onay ayarları güncelle | `/notifications/confirmation/settings` | PATCH |
| Sesli kişilik | `/voice/personality/:tenantId` | GET/PATCH |
| İYS durumu | `/notifications/iys/status` | GET |

---

## 17. Bildirim Şablonları (`/templates`)

**Sayfa:** `TemplateEditorPage.jsx`
**Roller:** SUPERADMIN, OWNER

| Aksiyon | API Endpoint | Method |
|---------|-------------|--------|
| Şablon listesi | `/notifications/templates` | GET |
| Şablon oluştur/güncelle | `/notifications/templates` | POST |
| Şablon sil | `/notifications/templates/:id` | DELETE |
| Önizleme | `/notifications/templates/preview` | POST |

---

## 18. Şubeler (`/locations`)

**Sayfa:** `LocationsPage.jsx`
**Roller:** SUPERADMIN, OWNER

| Aksiyon | API Endpoint | Method |
|---------|-------------|--------|
| Lokasyon listesi | `/locations` | GET |
| Lokasyon oluştur | `/locations` | POST |
| Lokasyon güncelle | `/locations/:id` | PATCH |
| Lokasyon sil | `/locations/:id` | DELETE |
| İstatistikler | `/locations/:id/stats` | GET |
| Kullanıcı ata | `/locations/:id/assign-user` | PATCH |
| Franchise genel bakış | `/locations/franchise/overview` | GET |
| Kullanıcı listesi | `/users` | GET |

---

## 19. Kullanıcı Yönetimi (`/users`)

**Sayfa:** `UsersPage.jsx`
**Roller:** SUPERADMIN, OWNER, MANAGER

| Aksiyon | API Endpoint | Method |
|---------|-------------|--------|
| Kullanıcı listesi | `/users` | GET |
| Rol değiştir / aktif-pasif | `/users/:id` | PATCH |

---

## 20. Denetim Kayıtları (`/audit-logs`)

**Sayfa:** `AuditLogPage.jsx`
**Roller:** SUPERADMIN, OWNER

| Aksiyon | API Endpoint | Method |
|---------|-------------|--------|
| Kaynak türleri | `/audit-logs/resources` | GET |
| Kayıtlar | `/audit-logs` | GET |
| Dışa aktar | `/audit-logs/export` | GET |

---

## 21. Superadmin Panel (`/superadmin`)

**Sayfa:** `SuperadminPage.jsx`
**Roller:** SUPERADMIN

| Aksiyon | API Endpoint | Method |
|---------|-------------|--------|
| Dashboard istatistikler | `/superadmin/stats` | GET |
| Tenant listesi | `/superadmin/tenants` | GET |
| Tenant oluştur | `/superadmin/tenants` | POST |
| Tenant güncelle | `/superadmin/tenants/:id` | PATCH |
| Kullanıcı listesi | `/superadmin/users` | GET |
| Kullanıcı güncelle | `/superadmin/users/:id` | PATCH |
| Tenant olarak giriş yap | `/superadmin/impersonate/:tenantId` | POST |
| Yedek oluştur | `/superadmin/backup/create` | POST |
| Yedekten geri yükle | `/superadmin/backup/restore` | POST |
| Sesli arama istatistikleri | `/superadmin/voice-stats` | GET |

---

## 22. Public Sayfalar (Auth Gerektirmez)

| Sayfa | Route | API Endpoint | Method |
|-------|-------|-------------|--------|
| Login | `/login` | `/auth/login` | POST |
| Register | `/register` | `/auth/register` | POST |
| QR Menü | `/menu/:tenantSlug` | `/menu/public/:slug/categories`, `/menu/public/:slug/items` | GET |
| QR Sipariş | `/order/:tableId` | `/orders/public` | POST |
| Sipariş Takip | `/order-track/:orderId` | `/orders/public/:id` | GET |
| Davet Kabul | `/invite/:token` | `/invites/:token/info`, `/invites/:token/accept` | GET, POST |
