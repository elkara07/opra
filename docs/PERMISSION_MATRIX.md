# Permission Matrix

**Version:** v1.21.0
**Last updated:** 2026-03-23

Complete 5-role permission matrix for the Restoran SaaS platform.

---

## Role Definitions

| Role | Scope | Description |
|------|-------|-------------|
| **SUPERADMIN** | Cross-tenant | Full system access. Manages all tenants, users, API keys, plans, security settings. Can impersonate any tenant owner. |
| **OWNER** | Tenant | Tenant administrator. Full access within their tenant: staff, menu, settings, billing, integrations. |
| **MANAGER** | Branch | Branch-level management. Can manage reservations, staff, reports for assigned locations. |
| **STAFF** | Branch (limited) | Front-desk / waiter role. Can view and update reservations, take orders, view assigned tables. |
| **GUEST** | Public (limited) | QR-based anonymous access. 4-hour token, no password. Loyalty read-only, ordering from table QR. |

> **Note:** OPERATIONS_ADMIN role was **removed in v1.21.0** and merged into SUPERADMIN (14 files affected). All OPERATIONS_ADMIN permissions are now under SUPERADMIN.

---

## PLATFORM_ADMIN (Separate System)

PLATFORM_ADMIN is **not** part of the 5-role tenant system. It uses a separate JWT system via the Platform Controller (port 3009) with its own PostgreSQL database and `PLATFORM_JWT_SECRET`.

| Capability | Description |
|------------|-------------|
| Tenant lifecycle | Create, suspend, activate, delete managed tenants |
| License enforcement | Monitor plan limits, trigger grace period, suspend on overuse |
| Billing management | Stripe webhook handling, billing events, MRR/ARR tracking |
| Impersonation | Log in as any tenant owner for debugging (1-hour JWT) |
| KVKK compliance | Data export trigger, anonymization with "ONAYLA" confirmation |
| Alert management | Payment failures, usage limits, compliance alerts |
| Self-service signup | Manage public signup flow, trial tenants |

PLATFORM_ADMIN credentials are managed entirely within the platform-controller and have no access to tenant-level APIs.

---

## API Key Separation

| Key | Scope | Usage |
|-----|-------|-------|
| `JWT_SECRET` | Tenant services | Signs all tenant user JWTs (SUPERADMIN, OWNER, MANAGER, STAFF, GUEST) |
| `PLATFORM_JWT_SECRET` | Platform Controller | Signs PLATFORM_ADMIN JWTs only — completely separate secret |
| `INTERNAL_SERVICE_KEY` | Inter-service | Used for service-to-service calls (e.g., platform-controller calling auth-service) |
| `CONFIG_ENCRYPTION_KEY` | All services | AES-256 encryption for API keys stored in database |

---

## Full Permission Matrix

Legend: **F** = Full access | **R** = Read only | **L** = Limited | **-** = No access

### Platform Module (Platform Controller only)

| Action | SUPERADMIN | OWNER | MANAGER | STAFF | GUEST |
|--------|-----------|-------|---------|-------|-------|
| View all tenants | F | - | - | - | - |
| Create tenant | F | - | - | - | - |
| Suspend/activate tenant | F | - | - | - | - |
| Impersonate tenant | F | - | - | - | - |
| View MRR/billing | F | - | - | - | - |
| Manage alerts | F | - | - | - | - |
| KVKK export/anonymize | F | - | - | - | - |

### Namespace / Tenant Settings

| Action | SUPERADMIN | OWNER | MANAGER | STAFF | GUEST |
|--------|-----------|-------|---------|-------|-------|
| View tenant settings | F | F | R | - | - |
| Edit tenant settings | F | F | - | - | - |
| Manage API keys (Twilio, Stripe, etc.) | F | F | - | - | - |
| Manage plans/billing | F | F | - | - | - |
| View audit log | F | F | R | - | - |
| White-label settings | F | F | - | - | - |
| Invite users | F | F | L | - | - |

### Reservation Management

| Action | SUPERADMIN | OWNER | MANAGER | STAFF | GUEST |
|--------|-----------|-------|---------|-------|-------|
| View reservations | F | F | F | F | - |
| Create reservation | F | F | F | F | - |
| Update reservation | F | F | F | L | - |
| Cancel reservation | F | F | F | - | - |
| Delete reservation | F | F | - | - | - |
| Walk-in (SEATED) | F | F | F | F | - |
| Manage waitlist | F | F | F | L | - |
| Recurring rules | F | F | F | - | - |
| Deposit management | F | F | F | - | - |
| Confirmation calls | F | F | F | - | - |

### Floor Plan

| Action | SUPERADMIN | OWNER | MANAGER | STAFF | GUEST |
|--------|-----------|-------|---------|-------|-------|
| View floor plan | F | F | F | F | - |
| Edit floor plan | F | F | F | - | - |
| Manage tables | F | F | F | - | - |
| Table merge/split | F | F | F | - | - |
| QR code generation | F | F | F | - | - |
| Table tags | F | F | F | - | - |

### Staff Management

| Action | SUPERADMIN | OWNER | MANAGER | STAFF | GUEST |
|--------|-----------|-------|---------|-------|-------|
| View staff list | F | F | F | L | - |
| Create/edit staff | F | F | F | - | - |
| Manage shifts | F | F | F | - | - |
| Auto-assignment config | F | F | F | - | - |
| Deactivate staff | F | F | - | - | - |
| Performance metrics | F | F | F | - | - |

### Menu & Digital Ordering

| Action | SUPERADMIN | OWNER | MANAGER | STAFF | GUEST |
|--------|-----------|-------|---------|-------|-------|
| View menu | F | F | F | F | F |
| Create/edit menu items | F | F | F | - | - |
| Manage categories | F | F | F | - | - |
| Dynamic pricing rules | F | F | - | - | - |
| Price simulation | F | F | - | - | - |
| View orders | F | F | F | F | - |
| Create order (KDS) | F | F | F | F | - |
| Update order status | F | F | F | F | - |

### Stock Management

| Action | SUPERADMIN | OWNER | MANAGER | STAFF | GUEST |
|--------|-----------|-------|---------|-------|-------|
| View stock levels | F | F | F | R | - |
| Add/edit ingredients | F | F | F | - | - |
| Manage recipes | F | F | F | - | - |
| Stock transactions | F | F | F | - | - |
| Supplier management | F | F | F | - | - |
| Low-stock alerts config | F | F | F | - | - |
| Waste tracking | F | F | F | - | - |
| Cost reports | F | F | F | - | - |

### Finance / POS / Payments

| Action | SUPERADMIN | OWNER | MANAGER | STAFF | GUEST |
|--------|-----------|-------|---------|-------|-------|
| View bills | F | F | F | F | - |
| Close bill (CASH/CARD) | F | F | F | F | - |
| Split payment | F | F | F | F | - |
| Cash register shift | F | F | F | - | - |
| View financial reports | F | F | F | - | - |
| Stripe/iyzico settings | F | F | - | - | - |
| Accounting export | F | F | F | - | - |

### Analytics & Reporting

| Action | SUPERADMIN | OWNER | MANAGER | STAFF | GUEST |
|--------|-----------|-------|---------|-------|-------|
| View dashboards | F | F | F | - | - |
| AI recommendations | F | F | F | - | - |
| CSV/PDF export | F | F | F | - | - |
| Heat maps | F | F | F | - | - |
| Revenue forecast | F | F | R | - | - |
| RevPASH | F | F | R | - | - |
| Voice call analytics | F | F | R | - | - |
| Loyalty distribution | F | F | F | - | - |

### CRM & Loyalty

| Action | SUPERADMIN | OWNER | MANAGER | STAFF | GUEST |
|--------|-----------|-------|---------|-------|-------|
| View customer profiles | F | F | F | L | - |
| Edit customer profiles | F | F | F | - | - |
| Loyalty tier management | F | F | - | - | - |
| View own loyalty points | - | - | - | - | R |
| Birthday automation | F | F | F | - | - |

### Settings & Admin

| Action | SUPERADMIN | OWNER | MANAGER | STAFF | GUEST |
|--------|-----------|-------|---------|-------|-------|
| Superadmin panel (8 tabs) | F | - | - | - | - |
| Setup Wizard | F | F | - | - | - |
| Voice AI settings | F | F | - | - | - |
| Notification templates | F | F | - | - | - |
| i18n language settings | F | F | F | F | - |
| Dark mode toggle | F | F | F | F | F |
| Franchise panel | F | F | R | - | - |
| Compliance dashboard | F | F | - | - | - |
| Impersonation (tenant) | F | - | - | - | - |

### Public Endpoints (No Auth Required)

| Endpoint | Description |
|----------|-------------|
| `POST /auth/login` | User login |
| `POST /auth/register` | User registration (invite-based) |
| `POST /auth/guest-token` | QR-based guest token (4h, no password) |
| `POST /auth/refresh-token` | Token refresh |
| `GET /order/:tableId` | Public QR ordering page |
| `GET /health` | Service health check |
| `GET /api/v1/version` | Version information |
| `POST /platform/signup` | Self-service tenant signup (14-day trial) |
| `POST /platform/webhooks/stripe` | Stripe webhook (signature-verified) |

---

## Notes

1. **SUPERADMIN** inherits all OWNER permissions plus cross-tenant capabilities.
2. **OWNER** inherits all MANAGER permissions plus tenant-wide settings.
3. **MANAGER** inherits most STAFF permissions plus management functions.
4. **STAFF** has the minimum permissions needed for front-desk/waiter operations.
5. **GUEST** has the most restricted access — loyalty read-only and QR ordering only.
6. **OPERATIONS_ADMIN** was removed in v1.21.0 — all its permissions merged into SUPERADMIN across 14 route files.
7. **PLATFORM_ADMIN** operates on a completely separate JWT system and cannot access tenant APIs directly.
8. Dynamic pricing rules in menu-service are restricted to SUPERADMIN/OWNER only; STAFF is explicitly blocked.
9. Stock management (suppliers, recipes, transactions, low-stock) blocks STAFF access as of v1.21.0.

---

*Permission Matrix v1.21.0 — 5 roles + PLATFORM_ADMIN*
