-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Enums (IF NOT EXISTS ile uyumlu format)
DO $$ BEGIN CREATE TYPE "Plan" AS ENUM ('STARTER', 'GROWTH', 'CHAIN', 'ENTERPRISE');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Add new enum values if type already exists
DO $$ BEGIN ALTER TYPE "Plan" ADD VALUE IF NOT EXISTS 'GROWTH'; EXCEPTION WHEN others THEN NULL; END $$;
DO $$ BEGIN ALTER TYPE "Plan" ADD VALUE IF NOT EXISTS 'CHAIN'; EXCEPTION WHEN others THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE "Role" AS ENUM ('SUPERADMIN', 'OWNER', 'MANAGER', 'STAFF', 'GUEST');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE "Channel" AS ENUM ('PHONE', 'APP', 'VOICE_AI');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE "ReservationStatus" AS ENUM ('CONFIRMED', 'SEATED', 'COMPLETED', 'CANCELLED', 'NO_SHOW');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Tables
CREATE TABLE IF NOT EXISTS tenants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(100) NOT NULL,
  slug VARCHAR(50) UNIQUE NOT NULL,
  phone VARCHAR(20),
  email VARCHAR(100) UNIQUE NOT NULL,
  address VARCHAR(255),
  timezone VARCHAR(50) DEFAULT 'Europe/Istanbul',
  "isActive" BOOLEAN DEFAULT true,
  plan "Plan" DEFAULT 'STARTER',
  "stripeCustomerId" VARCHAR(50),
  "logoUrl"          VARCHAR(500),
  "primaryColor"     VARCHAR(7),
  "secondaryColor"   VARCHAR(7),
  "language"         VARCHAR(5) DEFAULT 'tr',
  "googleCalendarRefreshToken" VARCHAR(500),
  "googleCalendarEmail"        VARCHAR(100),
  "googleCalendarSyncEnabled"  BOOLEAN DEFAULT false,
  "whatsappPhoneId"           VARCHAR(50),
  "whatsappVerifyToken"       VARCHAR(100),
  "notifyChannels"            JSONB DEFAULT '{"sms":true,"email":false,"whatsapp":false,"calendar":false}',
  "sendgridFromEmail"         VARCHAR(100),
  "createdAt" TIMESTAMPTZ DEFAULT NOW(),
  "updatedAt" TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "tenantId" UUID REFERENCES tenants(id) ON DELETE CASCADE,
  email VARCHAR(100) NOT NULL,
  "passwordHash" VARCHAR(255) NOT NULL,
  name VARCHAR(100) NOT NULL,
  role "Role" DEFAULT 'STAFF',
  "locationId" UUID,
  "isActive" BOOLEAN DEFAULT true,
  "lastLoginAt" TIMESTAMPTZ,
  "createdAt" TIMESTAMPTZ DEFAULT NOW(),
  "updatedAt" TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE("tenantId", email)
);

CREATE TABLE IF NOT EXISTS staff (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "tenantId" UUID NOT NULL,
  name VARCHAR(100) NOT NULL,
  phone VARCHAR(20),
  zone VARCHAR(50),
  "isActive" BOOLEAN DEFAULT true,
  "currentLoad" INT DEFAULT 0,
  "maxLoad" INT DEFAULT 5,
  color VARCHAR(7),
  "shiftStart" VARCHAR(5),
  "shiftEnd" VARCHAR(5),
  "createdAt" TIMESTAMPTZ DEFAULT NOW(),
  "updatedAt" TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS staff_assignments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "staffId" UUID NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
  "tenantId" UUID NOT NULL,
  "tableId" VARCHAR(50) NOT NULL,
  date DATE NOT NULL,
  "startTime" TIME NOT NULL,
  "endTime" TIME,
  active BOOLEAN DEFAULT true,
  "createdAt" TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reservations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "tenantId" UUID NOT NULL,
  "tableId" VARCHAR(50) NOT NULL,
  "guestName" VARCHAR(100) NOT NULL,
  phone VARCHAR(20),
  "guestEmail" VARCHAR(100),
  "partySize" SMALLINT NOT NULL,
  date DATE NOT NULL,
  "startTime" TIME NOT NULL,
  "endTime" TIME,
  channel "Channel" DEFAULT 'APP',
  source VARCHAR(20) DEFAULT 'APP',
  "staffId" UUID REFERENCES staff(id),
  status "ReservationStatus" DEFAULT 'CONFIRMED',
  note TEXT,
  "capacityScore" SMALLINT,
  "voiceSessionId" VARCHAR(80),
  "calendarEventId" VARCHAR(200),
  "depositAmount" INT,
  "depositStatus" VARCHAR(20),
  "depositPaymentId" VARCHAR(100),
  "confirmationStatus" VARCHAR(20),
  "createdAt" TIMESTAMPTZ DEFAULT NOW(),
  "updatedAt" TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Locations (Şubeler) ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS locations (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "tenantId"      UUID NOT NULL REFERENCES tenants(id),
  name            VARCHAR(200) NOT NULL,
  address         VARCHAR(500),
  phone           VARCHAR(20),
  timezone        VARCHAR(50) DEFAULT 'Europe/Istanbul',
  "logoUrl"       VARCHAR(500),
  "primaryColor"  VARCHAR(7) DEFAULT '#1a6b5c',
  "isActive"      BOOLEAN DEFAULT true,
  "isDefault"     BOOLEAN DEFAULT false,
  "createdAt"     TIMESTAMPTZ DEFAULT NOW(),
  "updatedAt"     TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_locations_tenant ON locations("tenantId");

-- Add locationId to users if not exists
DO $$ BEGIN
  ALTER TABLE users ADD COLUMN IF NOT EXISTS "locationId" UUID;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_tenant ON users("tenantId");
CREATE INDEX IF NOT EXISTS idx_staff_tenant ON staff("tenantId");
CREATE INDEX IF NOT EXISTS idx_reservations_tenant_date ON reservations("tenantId", date);
CREATE INDEX IF NOT EXISTS idx_assignments_tenant_date ON staff_assignments("tenantId", date);
CREATE INDEX IF NOT EXISTS idx_assignments_staff_date ON staff_assignments("staffId", date);

-- ─── Audit Log ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "tenantId"   UUID,
  "userId"     UUID,
  "userEmail"  VARCHAR(100),
  "userRole"   VARCHAR(30),
  action       VARCHAR(100) NOT NULL,
  resource     VARCHAR(50)  NOT NULL,
  "resourceId" VARCHAR(100),
  details      JSONB,
  "ipAddress"  VARCHAR(45),
  "userAgent"  VARCHAR(255),
  status       VARCHAR(20)  DEFAULT 'success',
  "createdAt"  TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_tenant_date ON audit_logs("tenantId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS idx_audit_user_date   ON audit_logs("userId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS idx_audit_resource    ON audit_logs(resource, action);

-- ─── Davet Tokenları ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS invite_tokens (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "tenantId"   UUID NOT NULL,
  email        VARCHAR(100),
  role         VARCHAR(20) DEFAULT 'STAFF',
  token        VARCHAR(64) UNIQUE NOT NULL,
  "usedAt"     TIMESTAMPTZ,
  "expiresAt"  TIMESTAMPTZ NOT NULL,
  "createdBy"  UUID NOT NULL,
  "createdAt"  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_invite_token ON invite_tokens(token);
CREATE INDEX IF NOT EXISTS idx_invite_tenant ON invite_tokens("tenantId");

-- ─── Arayan Profilleri ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS caller_profiles (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "tenantId"           UUID NOT NULL,
  phone                VARCHAR(20) NOT NULL,
  name                 VARCHAR(100),
  "callCount"          INTEGER DEFAULT 1,
  "lastCallAt"         TIMESTAMPTZ DEFAULT NOW(),
  "lastReservationId"  UUID,
  "preferredZone"      VARCHAR(50),
  "preferredTags"      TEXT[] DEFAULT '{}',
  "preferredTime"      VARCHAR(10),
  notes                TEXT,
  "createdAt"          TIMESTAMPTZ DEFAULT NOW(),
  "updatedAt"          TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE("tenantId", phone)
);
CREATE INDEX IF NOT EXISTS idx_caller_tenant_phone ON caller_profiles("tenantId", phone);

-- ─── İletişim Logları ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS communication_logs (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "tenantId"       UUID NOT NULL,
  type             VARCHAR(20) NOT NULL,
  subtype          VARCHAR(30),
  phone            VARCHAR(20),
  "reservationId"  UUID,
  direction        VARCHAR(10),
  status           VARCHAR(20) NOT NULL DEFAULT 'success',
  duration         INTEGER,
  message          TEXT,
  metadata         JSONB,
  "createdAt"      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_commlog_tenant_date ON communication_logs("tenantId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS idx_commlog_type        ON communication_logs("tenantId", type);
CREATE INDEX IF NOT EXISTS idx_commlog_phone       ON communication_logs(phone);

-- ─── Recurring Rules ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS recurring_rules (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "tenantId"    UUID NOT NULL,
  "tableId"     VARCHAR(50) NOT NULL,
  "guestName"   VARCHAR(100) NOT NULL,
  phone         VARCHAR(20),
  "partySize"   INTEGER NOT NULL,
  "startTime"   VARCHAR(5) NOT NULL,
  "endTime"     VARCHAR(5),
  channel       VARCHAR(20) DEFAULT 'APP',
  note          TEXT,
  frequency     VARCHAR(10) NOT NULL,
  "dayOfWeek"   INTEGER,
  "dayOfMonth"  INTEGER,
  "startDate"   DATE NOT NULL,
  "endDate"     DATE,
  "isActive"    BOOLEAN DEFAULT true,
  "createdAt"   TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_recurring_tenant ON recurring_rules("tenantId", "isActive");

-- ─── Waitlist ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS waitlist (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "tenantId"   UUID NOT NULL,
  "tableId"    VARCHAR(50) NOT NULL,
  "guestName"  VARCHAR(100) NOT NULL,
  phone        VARCHAR(20),
  "partySize"  INTEGER NOT NULL,
  date         DATE NOT NULL,
  "startTime"  TIMESTAMPTZ NOT NULL,
  notified     BOOLEAN DEFAULT false,
  "notifiedAt" TIMESTAMPTZ,
  status       VARCHAR(20) DEFAULT 'WAITING',
  "createdAt"  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_waitlist_tenant_date ON waitlist("tenantId", date);

-- ─── Loyalty Points ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS loyalty_points (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "tenantId"      UUID NOT NULL,
  phone           VARCHAR(20) NOT NULL,
  "guestName"     VARCHAR(100),
  points          INTEGER DEFAULT 0,
  "totalEarned"   INTEGER DEFAULT 0,
  "totalSpent"    INTEGER DEFAULT 0,
  tier            VARCHAR(20) DEFAULT 'STANDARD',
  "birthDate"     DATE,
  "lastVisit"     TIMESTAMPTZ,
  "visitCount"    INTEGER DEFAULT 0,
  "noShowCount"   INTEGER DEFAULT 0,
  notes           TEXT,
  "isBlacklisted" BOOLEAN DEFAULT false,
  "createdAt"     TIMESTAMPTZ DEFAULT NOW(),
  "updatedAt"     TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE("tenantId", phone)
);
CREATE INDEX IF NOT EXISTS idx_loyalty_tenant_phone ON loyalty_points("tenantId", phone);
CREATE INDEX IF NOT EXISTS idx_loyalty_tier ON loyalty_points("tenantId", tier);

-- ─── Loyalty Transactions ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS loyalty_transactions (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "tenantId"       UUID NOT NULL,
  phone            VARCHAR(20) NOT NULL,
  "reservationId"  UUID,
  type             VARCHAR(20) NOT NULL,
  points           INTEGER NOT NULL,
  description      VARCHAR(200),
  "createdAt"      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_loyalty_tx_tenant ON loyalty_transactions("tenantId", phone);
CREATE INDEX IF NOT EXISTS idx_loyalty_tx_date   ON loyalty_transactions("tenantId", "createdAt" DESC);

-- ─── S25: Deposit & Confirmation kolonları ──────────────────────────────────
ALTER TABLE reservations ADD COLUMN IF NOT EXISTS "depositAmount" INTEGER;
ALTER TABLE reservations ADD COLUMN IF NOT EXISTS "depositStatus" VARCHAR(20);
ALTER TABLE reservations ADD COLUMN IF NOT EXISTS "depositPaymentId" VARCHAR(100);
ALTER TABLE reservations ADD COLUMN IF NOT EXISTS "confirmationStatus" VARCHAR(20);

-- ─── #75: avgSittingMinutes kolonu ─────────────────────────────────────────────
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS "avgSittingMinutes" INTEGER DEFAULT 90;

-- ─── #77: weeklyShifts kolonu ──────────────────────────────────────────────────
ALTER TABLE staff ADD COLUMN IF NOT EXISTS "weeklyShifts" JSONB;

-- ─── S22.5: KVKK Compliance kolonları ─────────────────────────────────────────
ALTER TABLE users ADD COLUMN IF NOT EXISTS "kvkkConsentAt" TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS "kvkkConsentText" TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS "dataDeletedAt" TIMESTAMPTZ;

-- ─── S23: App Configs (Encrypted API Key Storage) ───────────────────────────
CREATE TABLE IF NOT EXISTS app_configs (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "tenantId"   UUID,
  service      VARCHAR(50) NOT NULL,
  key          VARCHAR(100) NOT NULL,
  value        TEXT NOT NULL,
  "isActive"   BOOLEAN DEFAULT true,
  "testedAt"   TIMESTAMPTZ,
  "testResult" VARCHAR(20),
  "createdAt"  TIMESTAMPTZ DEFAULT NOW(),
  "updatedAt"  TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE("tenantId", service, key)
);
CREATE INDEX IF NOT EXISTS idx_app_configs_service ON app_configs(service);
CREATE INDEX IF NOT EXISTS idx_app_configs_tenant ON app_configs("tenantId");

-- ─── S23: Plan Configs (DB-driven plan limits) ──────────────────────────────
CREATE TABLE IF NOT EXISTS plan_configs (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name              VARCHAR(50) UNIQUE NOT NULL,
  "displayName"     VARCHAR(100) NOT NULL,
  "maxReservations" INTEGER DEFAULT 50,
  "maxStaff"        INTEGER DEFAULT 3,
  "maxLocations"    INTEGER DEFAULT 1,
  "priceMonthly"    DECIMAL(10,2) DEFAULT 0,
  "priceYearly"     DECIMAL(10,2) DEFAULT 0,
  features          JSONB,
  "isActive"        BOOLEAN DEFAULT true,
  "createdAt"       TIMESTAMPTZ DEFAULT NOW(),
  "updatedAt"       TIMESTAMPTZ DEFAULT NOW()
);

-- Seed default plans (Symvera Lisans Planlama Raporu)
INSERT INTO plan_configs (id, name, "displayName", "maxReservations", "maxStaff", "maxLocations", "priceMonthly", "priceYearly", features, "isActive")
VALUES
  (gen_random_uuid(), 'STARTER', 'Symvera Starter', 500, 5, 1, 49, 490, '{"voiceMinutes":120,"priceEUR":49,"priceTL":2490,"overagePerMinTL":18,"modules":["Voice","Desk","Pulse"],"addOns":{"extraLangPack":890,"extraLocation":4200,"whiteLabel":2500,"smsPack":490}}', true),
  (gen_random_uuid(), 'GROWTH', 'Symvera Growth', 2000, 15, 1, 117, 1170, '{"voiceMinutes":400,"priceEUR":117,"priceTL":5990,"overagePerMinTL":14,"modules":["Voice","Desk","Pulse","Guest","Reach"],"addOns":{"extraLangPack":890,"extraLocation":4200,"whiteLabel":2500,"smsPack":490}}', true),
  (gen_random_uuid(), 'CHAIN', 'Symvera Chain', 10000, 50, 10, 290, 2900, '{"voiceMinutesPerBranch":300,"priceEUR":290,"priceTL":14900,"overagePerMinTL":12,"modules":["Voice","Desk","Pulse","Guest","Reach","Chain"],"addOns":{"extraLangPack":890,"extraLocation":4200,"whiteLabel":2500,"smsPack":490}}', true),
  (gen_random_uuid(), 'ENTERPRISE', 'Symvera Enterprise', -1, -1, -1, 0, 0, '{"custom":true,"priceTL":0,"priceEUR":0,"modules":["all"],"addOns":{"extraLangPack":890,"extraLocation":4200,"whiteLabel":2500,"smsPack":490}}', true)
ON CONFLICT (name) DO UPDATE SET "displayName"=EXCLUDED."displayName", "priceMonthly"=EXCLUDED."priceMonthly", "priceYearly"=EXCLUDED."priceYearly", features=EXCLUDED.features, "maxReservations"=EXCLUDED."maxReservations", "maxStaff"=EXCLUDED."maxStaff", "maxLocations"=EXCLUDED."maxLocations";

-- ─── S22.1: Platform Config (First-Run Setup Wizard) ────────────
CREATE TABLE IF NOT EXISTS platform_config (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  key          VARCHAR(200) UNIQUE NOT NULL,
  value        TEXT NOT NULL,
  "createdAt"  TIMESTAMPTZ DEFAULT NOW(),
  "updatedAt"  TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-complete setup for existing installations (skip wizard)
INSERT INTO platform_config (key, value) VALUES ('setup_completed', 'true')
ON CONFLICT (key) DO NOTHING;
INSERT INTO platform_config (key, value) VALUES ('setup_version', '1.0')
ON CONFLICT (key) DO NOTHING;
INSERT INTO platform_config (key, value) VALUES ('setup_at', NOW()::TEXT)
ON CONFLICT (key) DO NOTHING;

-- ─── S22.8: Refresh Tokens ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS refresh_tokens (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "userId"     UUID NOT NULL REFERENCES users(id),
  token        TEXT UNIQUE NOT NULL,
  "expiresAt"  TIMESTAMPTZ NOT NULL,
  "createdAt"  TIMESTAMPTZ DEFAULT NOW(),
  "revokedAt"  TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens("userId");
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token ON refresh_tokens(token);

-- ─── S26: White-label kolonları ──────────────────────────────────
-- ─── C-9: MFA kolonları ──────────────────────────────────────────────────────
ALTER TABLE users ADD COLUMN IF NOT EXISTS "mfaSecret" VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS "mfaEnabled" BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS "mfaBackupCodes" TEXT;

ALTER TABLE tenants ADD COLUMN IF NOT EXISTS "customDomain" VARCHAR(200);
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS "faviconUrl" VARCHAR(500);
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS "loginBgUrl" VARCHAR(500);
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS "hidePoweredBy" BOOLEAN DEFAULT false;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS "workingHours" JSONB DEFAULT '{}';
CREATE INDEX IF NOT EXISTS idx_tenant_custom_domain ON tenants("customDomain") WHERE "customDomain" IS NOT NULL;
