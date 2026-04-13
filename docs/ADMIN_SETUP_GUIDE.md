# Admin Setup Guide

**Version:** v1.22.0
**Last updated:** 2026-03-23

Complete step-by-step guide for setting up a new Restoran SaaS instance from scratch.

---

## Prerequisites

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Docker | 24+ | 25+ |
| Docker Compose | 2.x | 2.24+ |
| RAM | 4 GB | 8 GB |
| Disk | 10 GB | 20 GB |
| OS | Ubuntu 22.04 / macOS 13+ | Ubuntu 24.04 |

Ensure Docker is running:
```bash
docker --version
docker compose version
```

---

## Step 1: Clone/Extract and Configure .env

```bash
# Option A: Clone from repository
git clone https://github.com/USER/REPO.git
cd restoran-saas

# Option B: Extract from release archive
unzip restoran-saas-1.22.0.zip
cd restoran-saas
```

Copy and edit the environment file:
```bash
cp .env.example .env
```

Edit `.env` with your values. At minimum, change these from defaults:
- `JWT_SECRET` — generate with: `node -e "console.log(require('crypto').randomBytes(64).toString('hex'))"`
- `POSTGRES_PASSWORD` — strong unique password
- `MONGO_PASSWORD` — strong unique password
- `REDIS_PASSWORD` — strong unique password
- `INTERNAL_SERVICE_KEY` — generate with: `openssl rand -hex 32`
- `CONFIG_ENCRYPTION_KEY` — generate with: `openssl rand -hex 16`
- `PLATFORM_JWT_SECRET` — min 32 characters, separate from JWT_SECRET
- `PLATFORM_DB_PASSWORD` — strong unique password
- `APP_URL` — your domain (e.g., `https://yourdomain.com`)

---

## Step 2: Start All Services

```bash
sudo docker compose up -d --build
```

This starts all containers:
- 8 backend services (auth, reservation, floor-plan, staff, notification, analytics, voice-agent, menu)
- Frontend (React SPA)
- nginx reverse proxy
- Platform Controller (backend + frontend)
- Databases (PostgreSQL, MongoDB, Redis, TimescaleDB, platform-db)

Wait approximately 60 seconds for all services to initialize.

---

## Step 3: Wait for Health Checks

Verify all services are healthy:

```bash
# Check container status
sudo docker compose ps

# Individual health endpoints
curl http://localhost:3006/health     # auth-service
curl http://localhost:3001/health     # reservation-service
curl http://localhost:3002/health     # floor-plan-service
curl http://localhost:3003/health     # staff-service
curl http://localhost:3004/health     # notification-service
curl http://localhost:3005/health     # analytics-service
curl http://localhost:3007/health     # voice-agent-service
curl http://localhost:3008/health     # menu-service
curl http://localhost:3009/health     # platform-controller
curl http://localhost:3000            # frontend
curl http://localhost:3010            # platform-frontend
```

All services should return HTTP 200. If any service fails, check logs:
```bash
sudo docker compose logs --tail=50 <service-name>
```

---

## Step 4: Run Setup Wizard (First-Run Auto-Setup)

Open your browser and navigate to:
```
http://localhost (or https://yourdomain.com)
```

On first run, the platform launches a **6-step Setup Wizard**:

1. **Organization details** — restaurant name, address, timezone
2. **Database verification** — confirms all DB connections are healthy
3. **Admin account creation** — creates the first SUPERADMIN user
4. **Integration configuration** — optional Twilio, Stripe, etc. setup
5. **First restaurant/location setup** — initial branch configuration
6. **Confirmation & launch** — review and finalize

The Setup Wizard handles superadmin creation automatically. No manual seed script is needed.

---

## Step 5: Platform Admin Setup

The Platform Controller runs at `http://localhost:3010` (or `admin.yourdomain.com`).

1. Navigate to `http://localhost:3010`
2. Log in with the PLATFORM_ADMIN credentials
3. On first run, create a PLATFORM_ADMIN user:
   - The platform-controller auto-seeds a default admin if no users exist
   - Default: `admin@symvera.ai` / password from PLATFORM_JWT_SECRET context
   - **Change the password immediately after first login**

Platform Admin capabilities:
- View all managed tenants
- Monitor MRR, alerts, usage
- Suspend/activate/impersonate tenants
- Manage billing events
- KVKK data export and anonymization

---

## Step 6: Create First Tenant via Platform Frontend

1. In the Platform Frontend (`http://localhost:3010`), go to **Tenants** page
2. Click **Create Tenant**
3. Fill in:
   - Tenant name (restaurant name)
   - Slug (subdomain, e.g., `demo-restaurant`)
   - Plan (STARTER / GROWTH / CHAIN)
   - Owner email and name
4. The system creates:
   - A ManagedTenant record in platform-db
   - An owner account in auth-service
   - Plan-specific limits applied

Alternatively, tenants can self-register via the public signup page at `/signup`.

---

## Step 7: Tenant Owner Login and Initial Configuration

1. Navigate to the main application: `http://localhost` (or `slug.yourdomain.com`)
2. Log in with the owner credentials created in Step 6
3. Complete initial configuration:
   - Restaurant details (name, address, phone, timezone)
   - Floor plan setup (add tables, sections)
   - Menu configuration (categories, items, pricing)
   - Staff accounts (invite managers, waiters)
   - Notification preferences (SMS, WhatsApp, Telegram, email)
   - Integration keys (Twilio, Stripe, etc. — optional)

---

## Step 8: Verify All Services

Run the automated test suite:

```bash
./scripts/test.sh
```

Expected output: 390+ tests passing. All tests should show green checkmarks.

Check the version endpoint:
```bash
curl http://localhost/api/v1/version
```

This returns all service versions and the last deployment timestamp.

---

## Step 9: Configure Integrations (Optional)

### Stripe (Payments)
1. Get API keys from https://dashboard.stripe.com/apikeys
2. Set `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` in `.env`
3. Create Price IDs for Professional and Enterprise plans
4. Set `STRIPE_PRICE_PROFESSIONAL`, `STRIPE_PRICE_ENTERPRISE`

### Twilio (Voice & SMS)
1. Get Account SID and Auth Token from Twilio Console
2. Set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`
3. Configure webhook URLs pointing to your domain
4. See `docs/TWILIO_KURULUM.md` for detailed setup

### AI Providers
1. Get API key from Anthropic (Claude): set `ANTHROPIC_API_KEY`
2. Optional: DeepSeek (`DEEPSEEK_API_KEY`), OpenAI Whisper (`OPENAI_API_KEY`)
3. Set `AI_PROVIDER` to your preferred provider (`anthropic`, `deepseek`, `openai`)

### ElevenLabs (TTS)
1. Get API key and voice IDs from ElevenLabs
2. Set `ELEVENLABS_API_KEY` and voice IDs per language

### Google Calendar
1. Create OAuth2 credentials in Google Cloud Console
2. Set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`

All integrations work in **mock mode** when API keys are not configured — no errors, just simulated responses.

---

## Troubleshooting

### Container won't start
```bash
sudo docker compose logs --tail=50 <service-name>
```
Common causes:
- Missing required env var (service exits with validation error)
- Port conflict (another process using the same port)
- Insufficient memory (increase Docker RAM allocation)

### Prisma client mismatch
```bash
sudo docker compose down -v
sudo docker compose up -d --build
```
This happens when the schema changed but the container image is stale.

### 429 Too Many Requests during testing
```bash
sudo docker compose exec redis redis-cli -a $REDIS_PASSWORD DEL "login_lock:owner@test.com" "login_attempts:owner@test.com"
```

### Database connection errors
```bash
# Check database containers are running
sudo docker compose ps postgres mongo redis timescaledb platform-db

# Check database logs
sudo docker compose logs --tail=30 postgres
```

### Voice agent 502
```bash
sudo docker compose logs --tail=50 voice-agent-service
```
Usually a startup crash — check Python dependencies and API keys.

### Platform Controller not accessible
```bash
sudo docker compose logs --tail=30 platform-controller
sudo docker compose logs --tail=30 platform-frontend
```
Ensure `PLATFORM_DATABASE_URL` is correct and platform-db is healthy.

### nginx returns 502 for a service
The backend service is likely still starting up. Wait 30 seconds and retry, or check service logs.

---

## Test User Credentials

For development and testing, the following accounts are available after running the Setup Wizard or seed scripts:

| Role | Email | Password | Notes |
|------|-------|----------|-------|
| OWNER | owner@test.com | Test1234 | Full tenant admin access |
| SUPERADMIN | superadmin@test.com | Test1234 | Cross-tenant superadmin |
| MANAGER | manager@test.com | Test1234 | Branch-level management |
| STAFF | staff@test.com | Test1234 | Waiter/front-desk access |

**Warning:** These credentials are for development only. Never use them in production. The Setup Wizard creates a real admin account with a strong password.

---

*Restoran SaaS Admin Setup Guide v1.21.0*
