# Opra Product Guide

**Version:** 1.0 | **Last Updated:** 2026-04-12

> Comprehensive technical and product documentation for Opra, a 24/7 operations call center ticket management platform.

---

## Table of Contents

1. [Product Overview](#product-overview)
2. [Architecture](#architecture)
3. [Voice Pipeline](#voice-pipeline)
4. [Email Pipeline](#email-pipeline)
5. [Ticket Engine](#ticket-engine)
6. [SLA Engine](#sla-engine)
7. [Escalation System](#escalation-system)
8. [Integrations](#integrations)
9. [Topology and Monitoring](#topology-and-monitoring)
10. [Multi-Tenancy](#multi-tenancy)
11. [Security](#security)
12. [Deployment](#deployment)
13. [Cost Estimation](#cost-estimation)

---

## Product Overview

Opra is a multi-tenant SaaS platform purpose-built for 24/7 operations centers. It replaces fragmented tooling — separate phone systems, email ticketing, escalation spreadsheets, and monitoring dashboards — with a single unified platform that handles the entire lifecycle of an operations ticket from first contact to resolution.

The platform accepts inbound communications through two primary channels: **voice** (phone calls handled by an AI agent) and **email** (Microsoft 365 integration). Both channels feed into an ITIL v4-compliant ticket management engine with SLA tracking, multi-level escalation, and bidirectional sync to enterprise tools like Jira and Active Directory.

### Key Capabilities

- **Voice AI Pipeline** — Callers speak to an AI agent that collects structured ticket information through natural conversation, with guardrails for safety, PII handling, and prompt injection prevention.
- **Email Intake** — Microsoft Graph API webhooks detect incoming emails, auto-create tickets or thread replies to existing ones, and send acknowledgment responses.
- **ITIL v4 Tickets** — Four ticket types (incident, service request, problem, change), eight statuses, four priority levels (P1-P4), with a strict state machine governing transitions.
- **SLA Engine** — Business-hours-aware timers for response, update, and resolution targets. Timers pause automatically when tickets enter pending states and resume on reactivation. Breach detection runs every 60 seconds.
- **4-Level Escalation** — L1 through L3 technical escalation plus management escalation, with configurable thresholds and automatic notification delivery.
- **Enterprise Integrations** — Bidirectional Jira Cloud sync, LDAP/Active Directory user provisioning, Microsoft Graph email.
- **Pipeline Topology** — Real-time visual map of all system components with health status indicators and drill-down diagnostics.
- **Multi-Tenant Isolation** — Per-tenant configuration, data isolation via tenant_id, encrypted API keys (AES-256-GCM), and role-based access control across seven role levels.

---

## Architecture

```
                            INBOUND CHANNELS
                    ┌──────────────────────────────┐
                    │                              │
              ┌─────▼─────┐              ┌─────────▼─────────┐
              │   PBX/SIP │              │  Microsoft 365    │
              │  Trunking  │              │  (Graph API)      │
              └─────┬─────┘              └─────────┬─────────┘
                    │                              │
              ┌─────▼─────┐              ┌─────────▼─────────┐
              │  LiveKit   │              │  Graph Webhook    │
              │  (WebRTC/  │              │  Listener         │
              │   SIP)     │              │  (FastAPI)        │
              └─────┬─────┘              └─────────┬─────────┘
                    │                              │
              ┌─────▼─────┐                        │
              │  Pipecat   │                        │
              │  Agent     │                        │
              │ ┌────────┐ │                        │
              │ │  STT   │ │                        │
              │ ├────────┤ │                        │
              │ │Guards  │ │                        │
              │ ├────────┤ │                        │
              │ │  LLM   │ │                        │
              │ ├────────┤ │                        │
              │ │  TTS   │ │                        │
              │ └────────┘ │                        │
              └─────┬─────┘                        │
                    │                              │
                    └──────────┬───────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   FastAPI Backend    │
                    │   (REST + SSE)      │
                    │                     │
                    │  ┌───────────────┐  │
                    │  │ Ticket Engine │  │
                    │  │ SLA Engine    │  │
                    │  │ Escalation    │  │
                    │  │ RBAC / Auth   │  │
                    │  └───────────────┘  │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
        ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
        │ PostgreSQL │   │   Redis   │   │  Celery   │
        │ (primary)  │   │ (cache +  │   │ + Beat    │
        │            │   │  broker)  │   │ (tasks)   │
        └────────────┘   └───────────┘   └─────┬─────┘
                                               │
              ┌────────────────┬───────────────┤
              │                │               │
        ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
        │ Jira Cloud │   │   LDAP/   │   │ Prometheus│
        │ (bidir     │   │   AD      │   │ + Grafana │
        │  sync)     │   │ (user     │   │ + Loki    │
        │            │   │  sync)    │   │           │
        └───────────┘   └───────────┘   └───────────┘

                    ┌──────────────────────┐
                    │    React Frontend    │
                    │  (Vite + Tailwind)   │
                    │                     │
                    │  Dashboard          │
                    │  Tickets            │
                    │  Topology Map       │
                    │  Voice Test         │
                    │  Settings           │
                    │  Reports            │
                    └──────────────────────┘
```

### Component Summary

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | React 19, Vite, Tailwind CSS, Zustand | SPA with 17 pages, SSE real-time updates |
| **Backend API** | Python FastAPI, SQLAlchemy 2.0 async | 48 REST endpoints, JWT auth, RBAC |
| **Database** | PostgreSQL | Primary data store, tenant-isolated |
| **Cache/Broker** | Redis | Session cache, Celery task broker, SSE pub/sub |
| **Task Queue** | Celery + Celery Beat | Async tasks, SLA breach checks (60s), Jira sync, LDAP sync |
| **Voice Gateway** | LiveKit (WebRTC/SIP) | SIP termination, WebRTC rooms, audio routing |
| **Voice Agent** | Pipecat framework | Orchestrates STT -> Guardrails -> LLM -> TTS pipeline |
| **Email Intake** | Microsoft Graph API | Webhook-driven email reception and threading |
| **Monitoring** | Prometheus, Grafana, Loki, OpenTelemetry | Metrics, dashboards, log aggregation, distributed tracing |

---

## Voice Pipeline

The voice pipeline is Opra's primary intake channel. When a caller dials in, the system connects them to an AI agent that conducts a structured conversation to collect ticket information.

### Pipeline Flow

```
Caller (Phone)
    │
    ▼
PBX/SIP Trunk ─── PSTN termination, DID routing
    │
    ▼
LiveKit Server ─── SIP-to-WebRTC bridge, room management
    │
    ▼
Pipecat Agent ─── Pipeline orchestrator
    │
    ├──► STT (Speech-to-Text) ─── Converts audio to transcript
    │         │
    │         ▼
    ├──► Guardrails ─── Validates transcript before LLM
    │    │ - Prompt injection detection
    │    │ - Off-topic filtering
    │    │ - PII redaction
    │    │ - Max turn enforcement
    │         │
    │         ▼
    ├──► LLM (Language Model) ─── Generates contextual response
    │    │ - System prompt with ticket schema
    │    │ - Conversation history
    │    │ - Field extraction
    │    │ - Structured output (JSON)
    │         │
    │         ▼
    └──► TTS (Text-to-Speech) ─── Converts response to audio
              │
              ▼
         LiveKit ─── Streams audio back to caller
              │
              ▼
         Caller hears response
```

### LiveKit Configuration

LiveKit serves as the WebRTC/SIP bridge. It receives SIP calls from the PBX, creates a room for each call, and connects the Pipecat agent to that room.

| Setting | Description | Default |
|---------|-------------|---------|
| `LIVEKIT_URL` | WebSocket URL for LiveKit server | `ws://localhost:7880` |
| `LIVEKIT_API_KEY` | API key for authentication | — |
| `LIVEKIT_API_SECRET` | API secret for authentication | — |
| SIP Trunk Config | Inbound SIP trunk pointing to LiveKit | Per deployment |
| DID Mapping | Maps phone numbers (DIDs) to tenants | Per tenant |

**DID Mapping**: Each tenant can have one or more Direct Inward Dialing (DID) numbers assigned. When a call arrives at a DID, the system looks up the tenant mapping and loads that tenant's voice configuration (language, STT provider, LLM provider, TTS provider, system prompt, guardrail settings).

### Pipecat Agent

Pipecat is the pipeline orchestration framework. It manages the flow of data between STT, guardrails, LLM, and TTS, handling:

- **Turn detection** — Determines when the caller has finished speaking
- **Interruption handling** — What happens when the caller speaks while TTS is playing
- **Pipeline state** — Tracks conversation progress and required fields
- **Ticket creation** — Extracts structured data from conversation and creates tickets via the API

### STT Providers

| Provider | Model | Latency | Accuracy | Cost (per hour) | Languages | Streaming |
|----------|-------|---------|----------|-----------------|-----------|-----------|
| **Deepgram** | Nova-2 | ~200ms | Excellent | $0.0043/min (~$0.26/hr) | 36+ | Yes |
| **Groq Whisper** | Whisper Large v3 | ~300ms | Excellent | $0.0028/min (~$0.17/hr) | 99+ | No (chunked) |
| **Voxtral** | Voxtral | ~250ms | Very Good | ~$0.30/hr | 20+ | Yes |
| **OpenAI Whisper** | Whisper-1 | ~500ms | Excellent | $0.006/min (~$0.36/hr) | 57+ | No |

**Provider Selection Strategy**: Configure a primary and fallback provider per tenant. If the primary fails or times out, the system automatically switches to the fallback. Deepgram is recommended as primary for its low latency and streaming support. Groq Whisper offers the best cost-to-accuracy ratio for non-streaming use cases.

### LLM Providers

| Provider | Model | Latency (TTFT) | Quality | Cost (input/output per 1M tokens) | Context Window |
|----------|-------|-----------------|---------|-----------------------------------|----------------|
| **Claude** | Claude 3.5 Sonnet | ~800ms | Excellent | $3.00 / $15.00 | 200K |
| **Mistral** | Mistral Large | ~600ms | Very Good | $2.00 / $6.00 | 128K |
| **Groq Llama** | Llama 3.1 70B | ~200ms | Good | $0.59 / $0.79 | 128K |
| **GPT-4o Mini** | GPT-4o Mini | ~400ms | Very Good | $0.15 / $0.60 | 128K |

**Provider Selection Strategy**: For voice applications, latency matters more than in text-based use. Groq Llama offers the fastest time-to-first-token. Claude provides the highest quality for complex ticket classification. GPT-4o Mini offers an excellent balance of cost, speed, and quality for most operations center use cases.

### TTS Providers

| Provider | Voice Quality | Latency | Cost (per 1M chars) | Streaming | Voices |
|----------|--------------|---------|---------------------|-----------|--------|
| **Edge TTS** | Good | ~150ms | Free | Yes | 300+ |
| **OpenAI TTS** | Excellent | ~300ms | $15.00 | Yes | 6 |
| **ElevenLabs** | Excellent | ~250ms | $30.00+ | Yes | 1000+ / custom |
| **Voxtral TTS** | Very Good | ~200ms | ~$10.00 | Yes | 20+ |

**Provider Selection Strategy**: Edge TTS is free and sufficient for most operations centers. OpenAI TTS provides natural-sounding voices at moderate cost. ElevenLabs is recommended only when brand-specific voice cloning or premium voice quality is required.

### Turn Detection

Turn detection determines when the caller has stopped speaking and it is the agent's turn to respond.

| Setting | Description | Range | Default |
|---------|-------------|-------|---------|
| `min_silence_ms` | Minimum silence before end-of-turn | 200-2000ms | 600ms |
| `max_silence_ms` | Maximum silence before forced end-of-turn | 500-5000ms | 1500ms |
| `interruption_mode` | How to handle caller interrupting agent | `allow`, `queue`, `ignore` | `allow` |
| `backchannel_enabled` | Whether agent produces "mm-hmm" sounds | true/false | false |
| `vad_threshold` | Voice Activity Detection sensitivity | 0.0-1.0 | 0.5 |

**Interruption Modes**:
- `allow` — Agent immediately stops speaking and processes the caller's new input. Best for natural conversation flow.
- `queue` — Agent finishes current sentence, then processes the interruption. Prevents partial responses.
- `ignore` — Agent ignores interruptions until it finishes speaking. Use for critical instructions.

### Guardrails

Guardrails are applied to the caller's transcript before it reaches the LLM, and to the LLM's output before it reaches TTS.

#### Input Guardrails (Transcript -> LLM)

| Guardrail | Description | Action on Trigger |
|-----------|-------------|-------------------|
| **Prompt Injection** | Detects attempts to override system prompt ("ignore previous instructions", "you are now...") | Blocks input, responds with redirect |
| **Off-Topic Detection** | Identifies conversation that strays from ticket creation purpose | Gentle redirect to ticket topic |
| **PII Redaction** | Detects and masks SSN, credit card numbers, passwords in transcript before sending to LLM | Masks with `[REDACTED]`, stores original securely |
| **Max Turns** | Limits conversation length to prevent infinite loops | After N turns, summarizes and creates ticket with available data |

#### Output Guardrails (LLM -> TTS)

| Guardrail | Description | Action on Trigger |
|-----------|-------------|-------------------|
| **Content Safety** | Prevents agent from generating inappropriate content | Replaces with safe alternative |
| **Hallucination Check** | Prevents agent from inventing ticket numbers or referencing nonexistent data | Strips fabricated references |
| **Length Limit** | Prevents excessively long responses that are unnatural in voice | Truncates to natural sentence boundary |

### Voice Configuration Per Tenant

Each tenant has an independent voice configuration stored in the database:

```
tenant_voice_config:
  language: "en-US"
  stt_provider: "deepgram"
  stt_fallback_provider: "groq_whisper"
  llm_provider: "gpt4o_mini"
  tts_provider: "edge"
  system_prompt: "You are an operations center agent for {company_name}..."
  greeting: "Thank you for calling {company_name} operations..."
  turn_detection:
    min_silence_ms: 600
    max_silence_ms: 1500
    interruption_mode: "allow"
    vad_threshold: 0.5
  guardrails:
    injection_detection: true
    off_topic_detection: true
    pii_redaction: true
    max_turns: 20
  required_fields:
    - caller_name
    - caller_phone
    - issue_description
    - priority_hint
    - affected_system
```

---

## Email Pipeline

### Microsoft Graph Integration Flow

```
Incoming Email (Microsoft 365 mailbox)
    │
    ▼
Microsoft Graph ─── Webhook notification (POST /api/v1/email/webhook)
    │
    ▼
Webhook Listener ─── Validates subscription, fetches full message
    │
    ▼
Thread Matching ─── Checks if email is reply to existing ticket
    │
    ├── Match found ──► Add as comment to existing ticket
    │                   Update ticket status if needed
    │                   Send threaded auto-reply
    │
    └── No match ──► Create new ticket
                     Extract priority from subject/body
                     Map sender to contact
                     Assign to project via mailbox mapping
                     Send acknowledgment email with ticket ID
```

### Thread Matching Strategies

Opra uses three strategies to match incoming emails to existing tickets, applied in order:

1. **Ticket ID in Subject** — Scans subject line for pattern `[OPRA-{ticket_id}]`. This is injected into all outbound emails and auto-replies.
2. **Message-ID / In-Reply-To Headers** — Standard email threading headers. The system stores the Message-ID of every outbound email and matches against In-Reply-To and References headers of incoming messages.
3. **Conversation ID** — Microsoft Graph provides a `conversationId` that groups related messages. Used as a fallback when headers are stripped.

### Email Configuration

| Setting | Description |
|---------|-------------|
| Mailbox Address | The monitored email address (e.g., ops@company.com) |
| Graph Client ID | Azure AD application ID |
| Graph Client Secret | Azure AD application secret |
| Graph Tenant ID | Azure AD tenant ID |
| Project Mapping | Which project receives tickets from this mailbox |
| Auto-Reply Template | Template for acknowledgment emails |
| Thread Prefix | Prefix for subject line ticket IDs (default: `OPRA`) |

### Attachment Handling

- Attachments up to 25MB are downloaded and stored
- Supported formats: images, PDFs, Office documents, text files, logs
- Attachments are linked to the ticket and available in the ticket detail view
- Inline images in HTML emails are preserved in the ticket comment

---

## Ticket Engine

### ITIL v4 Ticket Types

| Type | Code | Description | Typical Use |
|------|------|-------------|-------------|
| **Incident** | `incident` | Unplanned interruption or reduction in quality of a service | "Server is down", "Application error", "Network outage" |
| **Service Request** | `service_request` | Formal request for something to be provided | "Need VPN access", "Password reset", "New account" |
| **Problem** | `problem` | Root cause of one or more incidents | "Recurring database timeouts", "Memory leak investigation" |
| **Change** | `change` | Addition, modification, or removal of a service component | "Deploy patch", "Upgrade firmware", "Config change" |

### Priority Levels

| Priority | Code | Response SLA | Update SLA | Resolution SLA | Description |
|----------|------|-------------|------------|----------------|-------------|
| **P1 - Critical** | `P1` | 15 min | 30 min | 4 hours | Complete service outage, revenue impact |
| **P2 - High** | `P2` | 30 min | 60 min | 8 hours | Major degradation, workaround unavailable |
| **P3 - Medium** | `P3` | 2 hours | 4 hours | 24 hours | Partial degradation, workaround available |
| **P4 - Low** | `P4` | 8 hours | 24 hours | 72 hours | Minor issue, no business impact |

**VIP Contacts**: Contacts flagged as VIP automatically escalate ticket priority to at least P2 upon creation.

### Status State Machine

```
                    ┌──────────┐
         ┌─────────│   new    │──────────┐
         │         └────┬─────┘          │
         │              │                │
         │         acknowledge           │
         │              │                │
         │         ┌────▼─────┐          │
         │    ┌────│   open   │────┐     │
         │    │    └────┬─────┘    │     │
         │    │         │          │     │
         │  assign   investigate  wait   │
         │    │         │          │     │
         │    │    ┌────▼─────┐   │     │
         │    │    │in_progress│   │     │
         │    │    └────┬─────┘   │     │
         │    │         │         │     │
         │    │    ┌────┤    ┌────▼─────┐
         │    │    │    │    │ pending  │
         │    │    │    │    └────┬─────┘
         │    │    │    │         │
         │    │    │    │    reactivate
         │    │    │    │         │
         │    │    │    └────◄────┘
         │    │    │
         │    │  resolve
         │    │    │
         │    │    ┌────▼─────┐
         │    │    │ resolved │
         │    │    └────┬─────┘
         │    │         │
         │    │    ┌────┤
         │    │    │    │
         │    │  close  reopen
         │    │    │    │
         │    │    │    └──────► open
         │    │    │
         │    │    ┌────▼─────┐
         │    └──►│  closed  │
         │         └──────────┘
         │
         │         ┌──────────┐
         └────────►│cancelled │
                   └──────────┘
```

**Eight Statuses**: `new`, `open`, `in_progress`, `pending`, `resolved`, `closed`, `cancelled`, `escalated`

#### Valid Transitions

| From | To | Trigger |
|------|----|---------|
| `new` | `open` | Agent acknowledges ticket |
| `new` | `cancelled` | Duplicate or invalid |
| `open` | `in_progress` | Agent begins work |
| `open` | `pending` | Waiting on caller/vendor |
| `open` | `escalated` | Manual or auto escalation |
| `open` | `closed` | Resolved immediately |
| `in_progress` | `pending` | Waiting on external party |
| `in_progress` | `resolved` | Fix applied |
| `in_progress` | `escalated` | Needs higher-level support |
| `pending` | `open` | Caller responds / info received |
| `pending` | `in_progress` | Reactivated with new info |
| `resolved` | `closed` | Confirmed by caller or auto-close after 48h |
| `resolved` | `open` | Caller reports issue persists |
| `escalated` | `in_progress` | Escalation team picks up |
| `escalated` | `pending` | Escalation team waiting on info |

### Ticket Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Short description (max 200 chars) |
| `description` | text | Yes | Full description of the issue |
| `type` | enum | Yes | incident, service_request, problem, change |
| `priority` | enum | Yes | P1, P2, P3, P4 |
| `status` | enum | Auto | Managed by state machine |
| `source` | enum | Auto | voice, email, web, api |
| `project_id` | FK | Yes | Parent project |
| `contact_id` | FK | No | Reporting contact |
| `assigned_to` | FK | No | Assigned agent |
| `escalation_level` | int | Auto | Current escalation level (0-4) |
| `sla_response_at` | datetime | Auto | SLA response deadline |
| `sla_update_at` | datetime | Auto | SLA update deadline |
| `sla_resolution_at` | datetime | Auto | SLA resolution deadline |
| `sla_paused` | boolean | Auto | Whether SLA timers are paused |
| `jira_issue_key` | string | Auto | Linked Jira issue (e.g., OPS-123) |
| `tags` | array | No | Freeform tags |

---

## SLA Engine

The SLA engine enforces service level agreements by tracking response, update, and resolution timers for every ticket.

### How SLA Timers Work

When a ticket is created, the system looks up the SLA configuration for the ticket's project and priority combination. If no project-specific SLA exists, the global default for that priority is used.

Three independent timers are started:

1. **Response Timer** — Time until first agent response or acknowledgment
2. **Update Timer** — Time between status updates (resets on each update)
3. **Resolution Timer** — Total time from creation to resolution

### Business Hours Calculation

SLA timers only count time during configured business hours. Default business hours are Monday-Friday, 09:00-17:00 in the tenant's timezone, but can be customized per project.

**Example**: A P3 ticket created Friday at 16:00 with a 2-hour response SLA. Only 1 hour counts on Friday (16:00-17:00). The remaining 1 hour counts starting Monday 09:00. The response SLA deadline is Monday 10:00.

```
Friday:    |=========|X|  (16:00-17:00 = 1 hour counted)
Saturday:  |XXXXXXXXXXX|  (not counted)
Sunday:    |XXXXXXXXXXX|  (not counted)
Monday:    |X|=========|  (09:00-10:00 = 1 hour counted, SLA deadline reached)
```

### Pause and Resume

When a ticket enters `pending` status (waiting on caller or external party), all SLA timers are paused. The elapsed time is recorded, and when the ticket is reactivated (moves back to `open` or `in_progress`), timers resume from where they left off.

```
Timeline:
  Created (P3, 2h response SLA)    ─── Timer starts
  00:30   Agent responds           ─── Response SLA met (0:30 < 2:00)
  01:00   Moves to pending         ─── Timer pauses at 1:00 elapsed
  ...     (3 days pass)            ─── Timer still at 1:00
  01:00   Caller responds          ─── Timer resumes from 1:00
  01:45   Resolved                 ─── Resolution at 1:45 elapsed
```

### Breach Detection

A Celery Beat task runs every **60 seconds** and performs the following:

1. Queries all tickets where `status NOT IN ('closed', 'cancelled', 'resolved')` and `sla_paused = false`
2. For each ticket, calculates elapsed business-hours time
3. Compares against SLA thresholds
4. If breached:
   - Sets `sla_breached = true` on the ticket
   - Creates an SLA breach event in the timeline
   - Triggers notification to assigned agent, team lead, and tenant admin
   - If escalation rules are configured, may auto-escalate the ticket
5. If approaching breach (within 80% of threshold):
   - Sends warning notification to assigned agent

### SLA Configuration Defaults

| Priority | Response | Update | Resolution |
|----------|----------|--------|------------|
| P1 | 15 min | 30 min | 4 hours |
| P2 | 30 min | 60 min | 8 hours |
| P3 | 2 hours | 4 hours | 24 hours |
| P4 | 8 hours | 24 hours | 72 hours |

These defaults can be overridden per project and per priority.

---

## Escalation System

### Escalation Levels

| Level | Name | Typical Role | Description |
|-------|------|-------------|-------------|
| **L1** | First Line | agent_l1 | Initial triage, basic troubleshooting, ticket creation |
| **L2** | Technical | agent_l2 | Advanced troubleshooting, can reassign tickets |
| **L3** | Expert | agent_l3 | Deep technical expertise, can override SLAs |
| **L4** | Management | manager | Management awareness, resource allocation, customer communication |

### Auto-Escalation

Escalation rules are configured per project with threshold minutes for each level:

```
Example Escalation Rule:
  Project: "Production Ops"
  L1 → L2:  30 minutes without resolution
  L2 → L3:  60 minutes without resolution
  L3 → L4: 120 minutes without resolution (management notification)
```

The escalation check runs as part of the SLA breach detection cycle (every 60 seconds). When a ticket exceeds the threshold for its current level:

1. Ticket `escalation_level` is incremented
2. Ticket status changes to `escalated`
3. Notifications are sent to the escalation target:
   - **Email** notification to the escalation group
   - **SSE event** pushed to connected dashboards
   - **Webhook** (if configured) to external systems
4. Timeline entry records the escalation with reason

### Manual Escalation

Agents can manually escalate tickets at any time. Manual escalation:
- Requires a reason (comment)
- Jumps directly to the specified level (does not need to go L1 -> L2 -> L3 sequentially)
- Sends the same notifications as auto-escalation

### Notification Channels

| Channel | Delivery | Latency | Configuration |
|---------|----------|---------|---------------|
| In-app (SSE) | Real-time push to dashboard | <1s | Always enabled |
| Email | SMTP or Graph API | 5-30s | Per-user preference |
| Webhook | HTTP POST to configured URL | <5s | Per-project |

---

## Integrations

### Jira Cloud (Bidirectional Sync)

Opra syncs tickets bidirectionally with Jira Cloud, allowing operations teams to use Opra while engineering teams use Jira.

#### Configuration

| Setting | Description |
|---------|-------------|
| Site URL | Jira Cloud site (e.g., `https://company.atlassian.net`) |
| API Email | Atlassian account email |
| API Token | Atlassian API token |
| Project Mapping | Opra project -> Jira project key |
| Status Mapping | Opra status -> Jira status (customizable) |
| Priority Mapping | Opra priority -> Jira priority (customizable) |
| Sync Direction | `bidirectional`, `opra_to_jira`, `jira_to_opra` |

#### Sync Flow

```
Opra Ticket Created/Updated
    │
    ▼
Celery Task: sync_to_jira
    │
    ├── New ticket ──► Jira API: Create Issue
    │                  Store jira_issue_key on ticket
    │
    └── Updated ticket ──► Jira API: Update Issue
                           Map status/priority per config

Jira Issue Created/Updated
    │
    ▼
Jira Webhook ──► POST /api/v1/jira/webhook
    │
    ▼
Validate webhook signature
    │
    ▼
    ├── New issue ──► Create Opra ticket (if auto-import enabled)
    │
    └── Updated issue ──► Update matching Opra ticket
                          Map status/priority per config
```

#### Conflict Resolution

When both sides update the same ticket simultaneously:

1. **Last-write-wins with field-level merge** — If Opra updated status and Jira updated assignee, both changes are applied.
2. **Same-field conflict** — The most recent change (by timestamp) wins. A conflict event is logged in the ticket timeline.
3. **Sync lock** — A 5-second lock prevents rapid ping-pong updates between systems.

#### Default Status Mapping

| Opra Status | Jira Status |
|-------------|-------------|
| new | To Do |
| open | To Do |
| in_progress | In Progress |
| pending | Waiting for Customer |
| escalated | In Progress |
| resolved | Done |
| closed | Done |
| cancelled | Cancelled |

#### Default Priority Mapping

| Opra Priority | Jira Priority |
|---------------|---------------|
| P1 | Highest |
| P2 | High |
| P3 | Medium |
| P4 | Low |

### LDAP / Active Directory

Opra syncs users from LDAP/Active Directory to maintain an up-to-date user directory without manual account management.

#### Configuration

| Setting | Description |
|---------|-------------|
| Server URL | LDAP server (e.g., `ldap://ad.company.com:389` or `ldaps://...`) |
| Bind DN | Service account DN for binding |
| Bind Password | Service account password (AES-256 encrypted at rest) |
| Search Base | Base DN for user search (e.g., `OU=Users,DC=company,DC=com`) |
| Search Filter | LDAP filter (e.g., `(&(objectClass=user)(memberOf=CN=OpsTeam,...))`) |
| Sync Interval | Minutes between automatic syncs (default: 60) |
| Role Mapping | AD group -> Opra role mapping |

#### Role Mapping Example

```
AD Group                          Opra Role
─────────────────────────────     ─────────────
CN=Opra-Admins,OU=Groups,...  →   tenant_admin
CN=Opra-Managers,OU=Groups,...→   manager
CN=Opra-L3,OU=Groups,...      →   agent_l3
CN=Opra-L2,OU=Groups,...      →   agent_l2
CN=Opra-L1,OU=Groups,...      →   agent_l1
CN=Opra-Viewers,OU=Groups,... →   viewer
```

#### Sync Behavior

- **New users** in AD that match the filter are created in Opra with the mapped role
- **Removed users** (no longer matching filter) are deactivated in Opra (not deleted, to preserve ticket history)
- **Changed attributes** (name, email, phone) are updated in Opra
- **Group changes** (user moved to different AD group) update the Opra role
- Sync can be triggered manually or runs on the configured interval via Celery Beat

### Microsoft Graph (Email)

See [Email Pipeline](#email-pipeline) above. Additional Graph API capabilities:

- **Calendar integration** (future) — Schedule maintenance windows
- **Teams notifications** (future) — Post to Teams channels on escalation
- **SharePoint** (future) — Attach documents from SharePoint

---

## Topology and Monitoring

### Pipeline Topology Map

The Topology page provides a visual map of all system components and their connections. Each component is represented as a node with a health indicator.

#### Node Types

| Node | Category | Description | Health Check |
|------|----------|-------------|-------------|
| **PBX/SIP** | Voice | External SIP trunk | SIP OPTIONS ping |
| **LiveKit** | Voice | WebRTC/SIP bridge | REST API /health |
| **Pipecat** | Voice | Pipeline orchestrator | Process heartbeat |
| **STT Provider** | Voice | Speech-to-text service | API ping with test audio |
| **LLM Provider** | Voice | Language model | API ping with test prompt |
| **TTS Provider** | Voice | Text-to-speech service | API ping with test text |
| **Guardrails** | Voice | Input/output safety | Internal health check |
| **FastAPI** | Core | Backend API server | /api/v1/system/health |
| **PostgreSQL** | Core | Primary database | Connection pool check |
| **Redis** | Core | Cache and broker | PING command |
| **Celery** | Core | Task workers | Inspector ping |
| **Celery Beat** | Core | Scheduler | Last heartbeat check |
| **Email Webhook** | Email | Graph API listener | Subscription status |
| **Jira Sync** | Integration | Jira connector | API connectivity test |
| **LDAP Sync** | Integration | AD connector | Bind test |
| **Prometheus** | Monitoring | Metrics collector | /api/v1/status |
| **Grafana** | Monitoring | Dashboards | /api/health |

#### Health Status Colors

| Color | Status | Meaning |
|-------|--------|---------|
| Green | healthy | Component operational, all checks passing |
| Yellow | degraded | Component operational but with warnings (high latency, high error rate) |
| Red | unhealthy | Component down or failing health checks |
| Gray | unknown | Health check not yet run or component not configured |

### Prometheus Metrics

Opra exposes the following Prometheus metrics at `/metrics`:

| Metric | Type | Description |
|--------|------|-------------|
| `opra_tickets_created_total` | Counter | Total tickets created, labeled by type, source, priority |
| `opra_tickets_resolved_total` | Counter | Total tickets resolved |
| `opra_sla_breaches_total` | Counter | Total SLA breaches, labeled by type (response/update/resolution) |
| `opra_escalations_total` | Counter | Total escalations, labeled by level |
| `opra_voice_calls_total` | Counter | Total voice calls received |
| `opra_voice_call_duration_seconds` | Histogram | Call duration distribution |
| `opra_voice_stt_latency_seconds` | Histogram | STT processing latency |
| `opra_voice_llm_latency_seconds` | Histogram | LLM response latency (TTFT) |
| `opra_voice_tts_latency_seconds` | Histogram | TTS processing latency |
| `opra_email_received_total` | Counter | Total emails received |
| `opra_email_processing_seconds` | Histogram | Email processing time |
| `opra_jira_sync_total` | Counter | Jira sync operations, labeled by direction |
| `opra_jira_sync_errors_total` | Counter | Jira sync failures |
| `opra_api_request_duration_seconds` | Histogram | API endpoint latency |
| `opra_api_requests_total` | Counter | API requests, labeled by method, endpoint, status |
| `opra_active_users` | Gauge | Currently active users (by SSE connections) |

### Grafana Dashboards

Pre-built dashboards included:

1. **Operations Overview** — Ticket volume, SLA compliance rate, escalation count, active calls
2. **Voice Pipeline** — Call volume, average call duration, STT/LLM/TTS latency percentiles, guardrail trigger rates
3. **SLA Performance** — Compliance by priority, breach trends, average resolution time
4. **System Health** — API latency, error rates, database connections, Redis memory, Celery queue depth

### OpenTelemetry Tracing

Distributed traces are collected via OpenTelemetry and exported to Grafana Tempo (or any OTLP-compatible backend). Key traced operations:

- Voice call lifecycle (SIP connect -> STT -> LLM -> TTS -> ticket creation)
- Email processing (webhook receive -> thread match -> ticket create/update)
- Jira sync (detect change -> API call -> conflict resolution)
- API requests (auth -> RBAC check -> handler -> database -> response)

---

## Multi-Tenancy

### Isolation Model

Every data record in Opra includes a `tenant_id` foreign key. All database queries are scoped to the authenticated user's tenant, enforced at the SQLAlchemy query layer.

```
┌─────────────────────────────────────────────────┐
│                  PostgreSQL                      │
│                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐│
│  │ Tenant A    │  │ Tenant B    │  │ Tenant C ││
│  │ tickets     │  │ tickets     │  │ tickets  ││
│  │ contacts    │  │ contacts    │  │ contacts ││
│  │ projects    │  │ projects    │  │ projects ││
│  │ users       │  │ users       │  │ users    ││
│  │ voice_cfg   │  │ voice_cfg   │  │ voice_cfg││
│  │ sla_cfg     │  │ sla_cfg     │  │ sla_cfg  ││
│  │ ...         │  │ ...         │  │ ...      ││
│  └─────────────┘  └─────────────┘  └──────────┘│
│                                                  │
│  Row-level isolation via tenant_id column        │
│  Enforced at ORM query layer                     │
└─────────────────────────────────────────────────┘
```

### Per-Tenant Configuration

Each tenant has independent configuration for:

| Configuration | Scope | Description |
|--------------|-------|-------------|
| Voice Config | Tenant | STT/LLM/TTS providers, language, system prompt, guardrails |
| SLA Config | Tenant + Project | SLA thresholds per priority, business hours |
| Escalation Rules | Tenant + Project | Escalation thresholds and notification targets |
| Email Settings | Tenant | Mailbox config, Graph API credentials, thread prefix |
| Jira Settings | Tenant | Jira site, credentials, field mappings |
| LDAP Settings | Tenant | AD server, bind credentials, sync config |
| DID Mappings | Tenant | Phone number to tenant routing |
| API Keys | Tenant | Provider API keys (encrypted) |

### API Key Encryption

All third-party API keys (STT, LLM, TTS, Jira, LDAP, Graph) are encrypted at rest using AES-256-GCM:

```
Storage Flow:
  User enters API key in UI
      │
      ▼
  Frontend sends key via HTTPS (TLS 1.3)
      │
      ▼
  Backend encrypts with AES-256-GCM:
    - Key: derived from ENCRYPTION_KEY env var via PBKDF2
    - IV: random 12 bytes per encryption
    - Output: base64(iv + ciphertext + tag)
      │
      ▼
  Encrypted value stored in PostgreSQL

Retrieval Flow:
  API key needed for provider call
      │
      ▼
  Backend decrypts from database
      │
      ▼
  Used in memory only, never logged
      │
      ▼
  Frontend displays masked: "sk-...abc" (last 3 chars only)
```

---

## Security

### Authentication

| Mechanism | Details |
|-----------|---------|
| **JWT Tokens** | RS256 signed, 15-minute access token, 7-day refresh token |
| **Token Refresh** | Automatic refresh via `/api/v1/auth/refresh` with rotation |
| **Password Hashing** | bcrypt with cost factor 12 |
| **Session Management** | Redis-backed session store, invalidation on logout |

### Role-Based Access Control (RBAC)

Seven roles with hierarchical permissions:

| Role | Level | Description |
|------|-------|-------------|
| `super_admin` | 7 | Platform-wide access across all tenants |
| `tenant_admin` | 6 | Full tenant configuration and management |
| `manager` | 5 | Settings, team management, reports |
| `agent_l3` | 4 | Advanced support, SLA override capability |
| `agent_l2` | 3 | Technical support, ticket reassignment |
| `agent_l1` | 2 | Basic support, ticket creation and updates |
| `viewer` | 1 | Read-only dashboard access |

RBAC is enforced at two levels:
1. **API middleware** — FastAPI dependency checks role before handler execution
2. **Frontend routing** — React router hides inaccessible pages, Zustand store filters UI elements by role

### Input Validation

- All API inputs validated via Pydantic v2 models with strict typing
- SQL injection prevented by SQLAlchemy parameterized queries
- XSS prevented by React's default escaping and CSP headers
- CSRF protection via SameSite cookies and Origin header validation
- Rate limiting: 100 requests/minute per IP, 1000/minute per authenticated user

### Guardrails (Voice)

See [Guardrails](#guardrails) in the Voice Pipeline section.

---

## Deployment

### Docker Compose (Development / Small Production)

```yaml
# docker-compose.yml (simplified)
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [postgres, redis]

  frontend:
    build: ./frontend
    ports: ["3000:80"]
    depends_on: [backend]

  celery-worker:
    build: ./backend
    command: celery -A app.celery worker -l info -c 4
    env_file: .env
    depends_on: [postgres, redis]

  celery-beat:
    build: ./backend
    command: celery -A app.celery beat -l info
    env_file: .env
    depends_on: [redis]

  livekit:
    image: livekit/livekit-server:latest
    ports: ["7880:7880", "7881:7881", "7882:7882/udp"]
    volumes: ["./livekit.yaml:/etc/livekit.yaml"]

  postgres:
    image: postgres:16
    volumes: ["pgdata:/var/lib/postgresql/data"]
    environment:
      POSTGRES_DB: opra
      POSTGRES_USER: opra
      POSTGRES_PASSWORD: ${DB_PASSWORD}

  redis:
    image: redis:7-alpine
    volumes: ["redisdata:/data"]

  prometheus:
    image: prom/prometheus:latest
    volumes: ["./prometheus.yml:/etc/prometheus/prometheus.yml"]
    ports: ["9090:9090"]

  grafana:
    image: grafana/grafana:latest
    ports: ["3001:3000"]
    volumes: ["grafana-data:/var/lib/grafana"]
```

### Quick Start

```bash
git clone https://github.com/your-org/opra.git
cd opra
cp .env.example .env
# Edit .env with your configuration (see Environment Variables below)
docker compose up -d
```

Default login: `admin@opra.local` / `OpraAdmin2026!`

### Kubernetes / Helm (Production)

Opra ships with a Helm chart for Kubernetes deployment:

```bash
helm repo add opra https://charts.opra.io
helm install opra opra/opra \
  --namespace opra \
  --create-namespace \
  --values values.yaml
```

Key Kubernetes considerations:
- Backend runs as a Deployment with HPA (2-10 replicas)
- Celery workers run as a separate Deployment with HPA (2-8 replicas)
- Celery Beat runs as a single-replica Deployment (leader election via Redis)
- PostgreSQL should use a managed service (RDS, Cloud SQL) or a StatefulSet with PVCs
- Redis should use a managed service (ElastiCache, Memorystore) or a StatefulSet
- LiveKit requires UDP port exposure (NodePort or dedicated load balancer)
- Ingress with TLS termination (cert-manager recommended)

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `REDIS_URL` | Yes | `redis://localhost:6379/0` | Redis connection string |
| `SECRET_KEY` | Yes | — | JWT signing key (RS256 private key or secret) |
| `ENCRYPTION_KEY` | Yes | — | AES-256 key for API key encryption (32-byte hex) |
| `ALLOWED_ORIGINS` | Yes | — | CORS allowed origins (comma-separated) |
| `LIVEKIT_URL` | No | — | LiveKit server WebSocket URL |
| `LIVEKIT_API_KEY` | No | — | LiveKit API key |
| `LIVEKIT_API_SECRET` | No | — | LiveKit API secret |
| `GRAPH_CLIENT_ID` | No | — | Azure AD application ID for Graph API |
| `GRAPH_CLIENT_SECRET` | No | — | Azure AD application secret |
| `GRAPH_TENANT_ID` | No | — | Azure AD tenant ID |
| `SMTP_HOST` | No | — | SMTP server for email notifications |
| `SMTP_PORT` | No | `587` | SMTP port |
| `SMTP_USER` | No | — | SMTP username |
| `SMTP_PASSWORD` | No | — | SMTP password |
| `PROMETHEUS_ENABLED` | No | `true` | Enable Prometheus metrics endpoint |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | No | — | OpenTelemetry collector endpoint |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `CELERY_CONCURRENCY` | No | `4` | Number of Celery worker processes |
| `SLA_CHECK_INTERVAL` | No | `60` | SLA breach check interval in seconds |

---

## Cost Estimation

### Per-Tenant Monthly Costs (Voice Pipeline)

Assumptions: 500 calls/month, average 4 minutes/call, ~2000 minutes total voice time.

| Provider Combination | STT Cost | LLM Cost | TTS Cost | Total/Month |
|---------------------|----------|----------|----------|-------------|
| **Budget** (Groq Whisper + GPT-4o Mini + Edge TTS) | $5.60 | $2.00 | $0.00 | **~$7.60** |
| **Balanced** (Deepgram + GPT-4o Mini + Edge TTS) | $8.60 | $2.00 | $0.00 | **~$10.60** |
| **Quality** (Deepgram + Claude Sonnet + OpenAI TTS) | $8.60 | $15.00 | $6.00 | **~$29.60** |
| **Premium** (Deepgram + Claude Sonnet + ElevenLabs) | $8.60 | $15.00 | $12.00 | **~$35.60** |

*LLM costs assume ~500 tokens input + 200 tokens output per turn, ~8 turns per call.*
*TTS costs assume ~100 characters per response, ~8 responses per call.*

### Infrastructure Costs (Self-Hosted)

| Component | Minimum Spec | Estimated Monthly Cost (Cloud) |
|-----------|-------------|-------------------------------|
| Backend (FastAPI) | 2 vCPU, 4GB RAM | $30-50 |
| Celery Workers (x2) | 2 vCPU, 4GB RAM each | $60-100 |
| PostgreSQL | 2 vCPU, 8GB RAM, 100GB SSD | $50-100 |
| Redis | 1 vCPU, 2GB RAM | $15-30 |
| LiveKit | 2 vCPU, 4GB RAM | $30-50 |
| Monitoring Stack | 2 vCPU, 4GB RAM | $30-50 |
| **Total Infrastructure** | | **$215-380/month** |

### Infrastructure Costs (Managed Services)

| Component | Service | Estimated Monthly Cost |
|-----------|---------|----------------------|
| Backend + Workers | AWS ECS / GCP Cloud Run | $80-150 |
| PostgreSQL | RDS / Cloud SQL | $50-120 |
| Redis | ElastiCache / Memorystore | $25-50 |
| LiveKit | LiveKit Cloud | $0.01/participant-minute |
| Load Balancer | ALB / Cloud LB | $20-30 |
| Monitoring | Grafana Cloud (free tier) | $0-50 |
| **Total Infrastructure** | | **$175-400/month** |

### Cost Scaling Notes

- Voice pipeline costs scale linearly with call volume
- Infrastructure costs remain relatively flat up to ~50 concurrent users / ~5000 tickets per month
- Beyond that, horizontal scaling of backend and Celery workers is the primary cost driver
- PostgreSQL is typically the bottleneck; connection pooling (PgBouncer) extends single-instance capacity significantly
- LiveKit Cloud pricing eliminates the need to manage WebRTC infrastructure but adds per-minute costs

---

*This document is maintained by the Opra engineering team. For questions or corrections, contact the platform team.*
