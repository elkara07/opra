# Opra

### 24/7 Operations Call Center Ticket Management

<!-- ![Opra Logo](docs/assets/opra-logo.png) -->

> **AI-powered, multi-tenant ticket management for operations centers that never sleep.**

---

## What is Opra?

Opra is a multi-tenant SaaS platform built for 24/7 operations centers. It unifies voice, email, and web-based ticket intake into a single ITIL v4-compliant system with SLA tracking, multi-level escalation, and enterprise integrations. Instead of juggling separate phone systems, email inboxes, and ticketing tools, operations teams use Opra as their single pane of glass.

The platform's standout feature is its **Voice AI Pipeline**: callers dial in and speak with an AI agent that collects structured ticket information through natural conversation. The agent uses configurable STT, LLM, and TTS providers with real-time guardrails for prompt injection, off-topic detection, and PII redaction. Email intake works through Microsoft Graph API webhooks with automatic thread matching, and the bidirectional Jira sync keeps operations and engineering teams aligned without manual data entry.

## Key Features

- **Voice AI Agent** — Phone calls answered by an AI that creates tickets through structured conversation (LiveKit + Pipecat + multi-provider STT/LLM/TTS)
- **Email Intake** — Microsoft 365 integration via Graph API webhooks with auto-threading and ticket creation
- **ITIL v4 Tickets** — 4 types (incident, service request, problem, change), 8 statuses, P1-P4 priority
- **SLA Engine** — Business-hours-aware timers with pause/resume, 60-second breach detection
- **4-Level Escalation** — L1 through Management, threshold-based auto-escalation with notifications
- **Jira Cloud Sync** — Bidirectional sync with field-level conflict resolution
- **LDAP/Active Directory** — Automated user provisioning with AD group to role mapping
- **Pipeline Topology** — Real-time visual map of all system components with health monitoring
- **7-Level RBAC** — From viewer to super_admin, with page-level and action-level permissions
- **Multi-Tenant** — Per-tenant configuration, data isolation, AES-256 API key encryption
- **Reports** — SLA compliance, ticket volume, escalation frequency, agent performance, call analytics
- **Real-Time Updates** — Server-Sent Events (SSE) for live dashboard updates

## Architecture

```
              VOICE                              EMAIL
         ┌───────────┐                    ┌───────────────┐
         │  PBX/SIP  │                    │ Microsoft 365 │
         └─────┬─────┘                    └───────┬───────┘
               │                                  │
         ┌─────▼─────┐                    ┌───────▼───────┐
         │  LiveKit   │                    │  Graph API    │
         │  (WebRTC)  │                    │  Webhooks     │
         └─────┬─────┘                    └───────┬───────┘
               │                                  │
         ┌─────▼─────┐                            │
         │  Pipecat   │                            │
         │ STT → LLM  │                            │
         │   → TTS    │                            │
         └─────┬─────┘                            │
               │                                  │
               └──────────┬───────────────────────┘
                          │
                ┌─────────▼─────────┐
                │   FastAPI Backend  │──── React Frontend
                │   (48 endpoints)  │     (17 pages)
                └─────────┬─────────┘
                          │
            ┌─────────────┼─────────────┐
            │             │             │
      ┌─────▼────┐  ┌────▼────┐  ┌─────▼─────┐
      │PostgreSQL│  │  Redis  │  │  Celery   │
      │          │  │         │  │  + Beat   │
      └──────────┘  └─────────┘  └─────┬─────┘
                                       │
                          ┌────────────┼────────────┐
                          │            │            │
                    ┌─────▼────┐ ┌────▼─────┐ ┌───▼────┐
                    │Jira Cloud│ │  LDAP/AD │ │Promethe│
                    │  Sync    │ │  Sync    │ │us+Graf.│
                    └──────────┘ └──────────┘ └────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose v2
- At least 4GB RAM available

### Run

```bash
git clone https://github.com/your-org/opra.git
cd opra

cp .env.example .env
# Edit .env — at minimum set:
#   DATABASE_URL, REDIS_URL, SECRET_KEY, ENCRYPTION_KEY

docker compose up -d
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Grafana**: http://localhost:3001

### Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Tenant Admin | `admin@opra.local` | `OpraAdmin2026!` |
| Manager | `manager@opra.local` | `OpraManager2026!` |
| Agent L1 | `agent@opra.local` | `OpraAgent2026!` |
| Viewer | `viewer@opra.local` | `OpraViewer2026!` |

<!-- ## Screenshots

### Dashboard
![Dashboard](docs/assets/screenshots/dashboard.png)

### Ticket Detail
![Ticket Detail](docs/assets/screenshots/ticket-detail.png)

### Pipeline Topology
![Topology](docs/assets/screenshots/topology.png)

### Voice Test
![Voice Test](docs/assets/screenshots/voice-test.png)

### Reports
![Reports](docs/assets/screenshots/reports.png)
-->

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, Vite, Tailwind CSS, Zustand |
| **Backend** | Python FastAPI, SQLAlchemy 2.0 (async), Pydantic v2 |
| **Database** | PostgreSQL 16 |
| **Cache / Broker** | Redis 7 |
| **Task Queue** | Celery + Celery Beat |
| **Voice Gateway** | LiveKit (WebRTC / SIP) |
| **Voice Pipeline** | Pipecat framework |
| **STT Providers** | Deepgram, Groq Whisper, Voxtral, OpenAI Whisper |
| **LLM Providers** | Claude (Anthropic), Mistral, Groq Llama, GPT-4o Mini |
| **TTS Providers** | Edge TTS, OpenAI TTS, ElevenLabs, Voxtral TTS |
| **Email** | Microsoft Graph API |
| **Issue Tracking** | Jira Cloud (bidirectional sync) |
| **Directory** | LDAP / Active Directory |
| **Monitoring** | Prometheus, Grafana, Loki, OpenTelemetry |
| **Auth** | JWT (RS256), bcrypt, AES-256-GCM |
| **Deployment** | Docker Compose, Helm / Kubernetes |

## API Overview

48 endpoints across 12 groups:

| Group | Endpoints | Description |
|-------|-----------|-------------|
| Auth | 5 | Login, register, refresh, logout, me |
| Tickets | 6 | CRUD, status change, assign, comments, timeline |
| Contacts | 4 | CRUD |
| Projects | 6 | CRUD, stats, Jira mapping, CSV import |
| SLA | 2 | Configuration CRUD |
| Escalation | 2 | Rule CRUD |
| Email | 4 | Graph webhook, mailbox CRUD |
| Voice | 15 | Config, providers, API keys, LiveKit, DID, calls, SIP |
| Jira | 5 | Config, test, webhook, sync, sync status |
| LDAP | 4 | Config, test, sync, sync status |
| Reports | 5 | SLA, volume, escalation, performance, calls |
| System | 5 | Health, topology, readiness, SSE events |

Full API reference: [docs/API_REFERENCE.md](docs/API_REFERENCE.md)

## Roles

| Role | Level | Scope |
|------|-------|-------|
| `super_admin` | 7 | Platform-wide, all tenants |
| `tenant_admin` | 6 | Full tenant configuration |
| `manager` | 5 | Settings, team management, reports |
| `agent_l3` | 4 | Advanced support, SLA override |
| `agent_l2` | 3 | Technical support, reassign tickets |
| `agent_l1` | 2 | Basic support, create/update tickets |
| `viewer` | 1 | Read-only dashboard access |

## Documentation

| Document | Description |
|----------|-------------|
| [docs/PRODUCT_GUIDE.md](docs/PRODUCT_GUIDE.md) | Architecture, voice pipeline, SLA engine, integrations, deployment, cost estimation |
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | Step-by-step instructions for every page, organized by role |
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | Detailed API endpoint documentation |
| [docs/VOICE_PIPELINE_ARCHITECTURE.md](docs/VOICE_PIPELINE_ARCHITECTURE.md) | Voice pipeline technical architecture |
| [docs/SECURITY_AUDIT.md](docs/SECURITY_AUDIT.md) | Security audit findings and remediations |
| [docs/PERMISSION_MATRIX.md](docs/PERMISSION_MATRIX.md) | Full role-permission matrix |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `SECRET_KEY` | Yes | JWT signing key |
| `ENCRYPTION_KEY` | Yes | AES-256 key for API key encryption |
| `ALLOWED_ORIGINS` | Yes | CORS allowed origins |
| `LIVEKIT_URL` | No | LiveKit server URL |
| `LIVEKIT_API_KEY` | No | LiveKit API key |
| `LIVEKIT_API_SECRET` | No | LiveKit API secret |
| `GRAPH_CLIENT_ID` | No | Azure AD app ID |
| `GRAPH_CLIENT_SECRET` | No | Azure AD app secret |

See [docs/PRODUCT_GUIDE.md](docs/PRODUCT_GUIDE.md#environment-variables-reference) for the complete reference.

## License

MIT License. See [LICENSE](LICENSE) for details.

---

Built for operations teams that keep the world running, 24/7.
