# Opra User Guide

**Version:** 1.0 | **Last Updated:** 2026-04-12

> Step-by-step instructions for every feature in Opra, organized by page and role.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard](#dashboard)
3. [Tickets](#tickets)
4. [Contacts](#contacts)
5. [Projects](#projects)
6. [Topology](#topology)
7. [Voice Test](#voice-test)
8. [Settings](#settings)
   - [Voice Settings](#voice-settings)
   - [SLA Configuration](#sla-configuration)
   - [Escalation Rules](#escalation-rules)
   - [Email Settings](#email-settings)
   - [Jira Settings](#jira-settings)
   - [LDAP Settings](#ldap-settings)
9. [Reports](#reports)
10. [System Health](#system-health)
11. [Role Permissions Matrix](#role-permissions-matrix)

---

## Getting Started

### Logging In

1. Navigate to your Opra instance URL (e.g., `https://opra.yourcompany.com`).
2. Enter your email address and password.
3. Click **Sign In**.
4. If this is your first login with LDAP-synced credentials, use your Active Directory email and password.

### First-Time Setup (tenant_admin)

After your tenant is provisioned by the super_admin, complete these steps:

1. **Change your password** — Click your profile icon in the top-right corner, select **Profile**, and change your default password.
2. **Create a project** — Go to **Projects** and create at least one project. Projects are the top-level container for tickets.
3. **Configure SLA** — Go to **Settings > SLA Configuration** and review the default SLA thresholds for each priority level. Adjust for your operations center requirements.
4. **Set up escalation** — Go to **Settings > Escalation** and define escalation rules for your projects.
5. **Add users** — Either configure LDAP sync (**Settings > LDAP**) or invite users manually through the user management interface.
6. **Configure voice** (optional) — If using the voice pipeline, go to **Settings > Voice Settings** and configure your STT, LLM, and TTS providers with API keys.
7. **Configure email** (optional) — If using email intake, go to **Settings > Email Settings** and connect your Microsoft 365 mailbox.

### Navigation

The left sidebar contains all main navigation items. The sidebar collapses on smaller screens and can be toggled with the hamburger menu icon. Items visible in the sidebar depend on your role.

| Menu Item | Icon | Minimum Role |
|-----------|------|-------------|
| Dashboard | Home | viewer |
| Tickets | Ticket | viewer |
| Contacts | People | viewer |
| Projects | Folder | viewer |
| Topology | Network | viewer |
| Voice Test | Microphone | agent_l1 |
| Voice Settings | Gear + Mic | manager |
| SLA Config | Clock | manager |
| Escalation | Arrow Up | manager |
| Email Settings | Mail | manager |
| Jira Settings | Link | manager |
| LDAP Settings | Directory | tenant_admin |
| Reports | Chart | manager |
| System Health | Heart | manager |

---

## Dashboard

The Dashboard is the first page you see after login. It provides an at-a-glance view of your operations center status.

### Global KPI Bar

The top bar shows aggregated KPIs across all your projects:

| KPI | Description |
|-----|-------------|
| **Open Tickets** | Total tickets in `new`, `open`, `in_progress`, or `escalated` status |
| **SLA Compliance** | Percentage of tickets within SLA thresholds (last 30 days) |
| **Avg Response Time** | Average time to first response across all tickets (last 30 days) |
| **Active Calls** | Number of voice calls currently in progress (real-time) |
| **Escalated** | Number of tickets currently in `escalated` status |

### Project Cards

Below the KPI bar, each project you have access to is displayed as a card showing:

| Metric | Description |
|--------|-------------|
| **Project Name** | The project title |
| **Open / Total** | Count of open tickets vs total tickets |
| **P1/P2 Count** | Number of high-priority tickets currently open (highlighted in red/orange) |
| **SLA %** | SLA compliance percentage for this project |
| **Trend Arrow** | Up/down arrow indicating whether ticket volume is increasing or decreasing compared to the previous period |

**Click on a project card** to navigate to the Project Dashboard, which shows detailed metrics for that specific project.

### Project Dashboard

The Project Dashboard shows:

- **Ticket breakdown** by status (bar chart)
- **Ticket breakdown** by priority (donut chart)
- **SLA compliance trend** over the selected period (line chart)
- **Recent tickets** table with quick-action buttons
- **Escalated tickets** section (highlighted) with time-since-escalation

### Escalated Tickets Section

At the bottom of the Dashboard (both global and project), an **Escalated Tickets** panel lists all tickets currently in escalated status, sorted by escalation time (oldest first). Each entry shows:

- Ticket ID and title
- Priority badge (P1-P4)
- Escalation level (L1-L4)
- Time since escalation
- Assigned agent
- Quick action: **Pick Up** (assign to yourself) or **View** (open ticket detail)

---

## Tickets

### Ticket List View

The Tickets page shows all tickets you have access to in a tabular format.

#### Filters

Use the filter bar at the top to narrow results:

| Filter | Options | Description |
|--------|---------|-------------|
| **Status** | All, New, Open, In Progress, Pending, Resolved, Closed, Cancelled, Escalated | Filter by current status |
| **Priority** | All, P1, P2, P3, P4 | Filter by priority level |
| **Type** | All, Incident, Service Request, Problem, Change | Filter by ITIL type |
| **Source** | All, Voice, Email, Web, API | Filter by how the ticket was created |
| **Project** | Dropdown of your projects | Filter by project |
| **Assigned To** | Dropdown of agents | Filter by assigned agent |
| **SLA Status** | All, Within SLA, Breached, At Risk | Filter by SLA compliance |
| **Search** | Free text | Searches title and description |

#### Sorting

Click any column header to sort. Click again to reverse. Default sort is by creation date (newest first).

#### Pagination

Results are paginated at 25 tickets per page. Use the pagination controls at the bottom to navigate.

### Creating a New Ticket

**Minimum role**: agent_l1

1. Click the **+ New Ticket** button in the top-right corner of the Tickets page.
2. Fill in the required fields:

| Field | Required | Description |
|-------|----------|-------------|
| **Title** | Yes | Short summary of the issue (max 200 characters). Be specific: "Exchange server unresponsive" is better than "Server issue". |
| **Description** | Yes | Full description including symptoms, affected users, and any steps already taken. |
| **Type** | Yes | Select the appropriate ITIL type: **Incident** (something is broken), **Service Request** (someone needs something), **Problem** (investigating root cause), **Change** (planned modification). |
| **Priority** | Yes | **P1** - Complete outage, revenue impact. **P2** - Major degradation, no workaround. **P3** - Partial issue, workaround exists. **P4** - Minor, no business impact. |
| **Project** | Yes | Select the project this ticket belongs to. |
| **Contact** | No | The person who reported the issue. Select from existing contacts or leave blank. If a VIP contact is selected, priority is automatically elevated to at least P2. |
| **Assigned To** | No | Optionally assign to a specific agent. If left blank, the ticket stays unassigned in the queue. |
| **Tags** | No | Add freeform tags for categorization (e.g., "network", "database", "vendor-xyz"). |

3. Click **Create Ticket**.
4. The ticket is created with status `new` and SLA timers begin immediately.

### Ticket Detail View

Click any ticket in the list to open its detail view. The detail page has several sections:

#### Header

- Ticket ID (e.g., `#1042`)
- Title (editable by agent_l1+)
- Status badge with dropdown to change status (valid transitions only)
- Priority badge with dropdown to change priority
- Type badge
- Source badge (voice/email/web/api)

#### Information Panel (Left Side)

- **Assigned To** — Current assignee. Click to reassign (agent_l2+).
- **Contact** — Reporting contact with link to contact detail.
- **Project** — Parent project.
- **Created** — Creation timestamp.
- **Updated** — Last update timestamp.
- **Escalation Level** — Current level (L0-L4). Shows "Not Escalated" for L0.
- **Jira Link** — If synced, shows Jira issue key as a clickable link.

#### SLA Panel (Right Side)

Three SLA timers displayed with countdown format:

| Timer | Description | Visual |
|-------|-------------|--------|
| **Response** | Time until first response required | Green (on track), Yellow (>80% elapsed), Red (breached) |
| **Update** | Time until next update required | Same color scheme |
| **Resolution** | Time until resolution required | Same color scheme |

If timers are paused (ticket in pending status), they show "PAUSED" with the elapsed time frozen.

#### Timeline

The timeline shows a chronological history of all ticket events:

| Event Type | Description |
|------------|-------------|
| **Created** | Ticket creation with source information |
| **Status Change** | Status transitions with from/to values |
| **Priority Change** | Priority changes with from/to values |
| **Assignment** | Assignment or reassignment |
| **Comment** | Public or internal comments (see below) |
| **Escalation** | Escalation events with level and reason |
| **SLA Warning** | SLA approaching breach |
| **SLA Breach** | SLA threshold exceeded |
| **Jira Sync** | Jira sync events (created, updated, conflict) |
| **Email** | Inbound/outbound email events |

#### Comments

**Adding a Comment**:

1. Scroll to the comment box at the bottom of the timeline.
2. Type your comment in the text area.
3. Choose comment visibility:
   - **Public** — Visible to all users and included in email notifications to the contact. Use for updates you want the caller/requester to see.
   - **Internal** — Visible only to agents and managers. Use for technical notes, troubleshooting steps, and team communication.
4. Click **Add Comment**.

Comments support basic markdown formatting (bold, italic, code blocks, lists).

#### Changing Ticket Status

1. Click the status badge dropdown in the ticket header.
2. Only valid transitions are shown (see the state machine in the Product Guide).
3. Select the new status.
4. If moving to `resolved`, you may optionally add a resolution comment.
5. The status change is recorded in the timeline and SLA timers adjust accordingly:
   - Moving to `pending` pauses SLA timers.
   - Moving from `pending` to `open` or `in_progress` resumes timers.
   - Moving to `resolved` or `closed` stops timers.

#### Assigning a Ticket

**Minimum role**: agent_l2 (agent_l1 can only self-assign)

1. Click the **Assigned To** field in the information panel.
2. Select an agent from the dropdown. The dropdown shows agents filtered by the ticket's project.
3. The assignment is recorded in the timeline and the assignee receives a notification.

#### Manual Escalation

**Minimum role**: agent_l1

1. Click the **Escalate** button in the ticket header.
2. Select the target escalation level (L2, L3, or L4).
3. Enter a reason for escalation (required).
4. Click **Confirm**.
5. The ticket status changes to `escalated`, the escalation is recorded in the timeline, and notifications are sent to the escalation target group.

#### Jira Sync Status

If Jira integration is configured and the ticket is synced:

- A **Jira badge** appears in the header showing the Jira issue key (e.g., `OPS-123`).
- Clicking the badge opens the Jira issue in a new tab.
- The timeline shows sync events including any conflicts.
- Changes made in Jira are reflected in Opra within the sync interval (typically 1-5 minutes).

---

## Contacts

Contacts represent the people who report issues — callers, email senders, and requesters.

### Contact List

The list displays all contacts for your tenant with:
- Name, email, phone number
- Company/department
- VIP flag (star icon)
- Ticket count

**Search** by name, email, or phone using the search bar.

### Creating a Contact

**Minimum role**: agent_l1

1. Click **+ New Contact**.
2. Fill in the fields:

| Field | Required | Description |
|-------|----------|-------------|
| **Name** | Yes | Full name |
| **Email** | Yes | Email address (must be unique within tenant) |
| **Phone** | No | Phone number in E.164 format (+1234567890) |
| **Company** | No | Company or department name |
| **VIP** | No | Toggle on for VIP contacts. VIP contacts automatically get P2 or higher priority on new tickets. |
| **Notes** | No | Internal notes about this contact |

3. Click **Save**.

### Editing a Contact

1. Click a contact in the list to open the detail view.
2. Click **Edit** to modify fields.
3. Click **Save**.

Changes to VIP status do not retroactively affect existing tickets.

### Deleting a Contact

**Minimum role**: manager

1. Open the contact detail view.
2. Click **Delete**.
3. Confirm the deletion.

Contacts with associated tickets cannot be deleted — they can only be deactivated.

---

## Projects

Projects are the top-level organizational unit. Every ticket belongs to a project. Projects typically map to a team, service, or customer.

### Project List

Displays all projects with:
- Project name and description
- Ticket count (open / total)
- SLA compliance percentage
- Jira project mapping (if configured)
- Created date

### Creating a Project

**Minimum role**: manager

1. Click **+ New Project**.
2. Fill in the fields:

| Field | Required | Description |
|-------|----------|-------------|
| **Name** | Yes | Project name (e.g., "Production Operations", "Network Support") |
| **Description** | No | Description of the project scope |
| **Code** | Yes | Short code used in ticket IDs (e.g., "PROD", "NET"). 2-6 uppercase characters. |

3. Click **Create**.

### Editing a Project

1. Click a project to open its detail view.
2. Click **Edit**.
3. Modify fields and click **Save**.

The project code cannot be changed after creation (it is embedded in ticket references).

### Project Statistics

The project detail view shows:
- Total tickets by status (chart)
- SLA compliance trend
- Top contacts (most tickets filed)
- Agent workload distribution

### Jira Project Mapping

**Minimum role**: manager

1. Open the project detail view.
2. Click the **Jira Mapping** tab.
3. Select the Jira project key to map this Opra project to.
4. The dropdown shows all Jira projects fetched during the last Jira connection test.
5. Click **Save Mapping**.

Once mapped, new tickets in this Opra project can be synced to the mapped Jira project.

### CSV Import

**Minimum role**: manager

To bulk-import tickets from a CSV file:

1. Open the project detail view.
2. Click **Import CSV**.
3. Download the CSV template by clicking **Download Template**.
4. Fill in the CSV with your ticket data. The template columns are:

```
title,description,type,priority,contact_email,tags
"Server down","Exchange server unresponsive since 08:00",incident,P1,john@company.com,"exchange,email"
"VPN access","New employee needs VPN access",service_request,P4,jane@company.com,"onboarding,vpn"
```

5. Upload the completed CSV file.
6. Review the preview (first 10 rows shown with validation status).
7. Click **Import** to create the tickets.
8. Results summary shows: created count, skipped count (with reasons), and error count.

---

## Topology

The Topology page provides a visual map of all Opra system components and their interconnections. This is primarily used for monitoring pipeline health and diagnosing issues.

### Pipeline Map

The map displays nodes (components) connected by edges (data flow). The layout represents the logical architecture:

**Voice Pipeline (top section)**:
```
PBX/SIP ──► LiveKit ──► Pipecat ──► STT ──► Guardrails ──► LLM ──► TTS
                                                                      │
                                                                      ▼
                                                                  LiveKit (audio out)
```

**Ticket Pipeline (middle section)**:
```
Voice Agent ──┐
              ├──► FastAPI ──► PostgreSQL
Email Agent ──┘       │
                      ├──► Redis
                      ├──► Celery/Beat
                      ├──► Jira Sync
                      └──► LDAP Sync
```

**Monitoring (bottom section)**:
```
All Components ──► Prometheus ──► Grafana
                              ──► Loki (logs)
```

### Node Color Indicators

| Color | Meaning | Action Required |
|-------|---------|-----------------|
| **Green** | Healthy — all checks passing | None |
| **Yellow** | Degraded — operational but with warnings | Investigate soon; check node detail for warnings |
| **Red** | Unhealthy — component down or failing | Immediate attention required |
| **Gray** | Unknown — not configured or check pending | Configure the component or wait for first health check |

### Clicking a Node

Click any node to navigate to its **Node Detail** page, which shows:

- **Status**: Current health status with last check timestamp
- **Metrics**: Key metrics for that component (latency, error rate, throughput)
- **Configuration**: Current configuration summary
- **Recent Events**: Last 20 health check results with timestamps
- **Configure Button**: Quick link to the relevant settings page (e.g., clicking Configure on the STT node takes you to Voice Settings > STT tab)

### Node Details by Component

| Node | Key Metrics | Configure Link |
|------|-------------|---------------|
| **PBX/SIP** | Active calls, call quality (MOS) | External PBX admin |
| **LiveKit** | Active rooms, participants, CPU/memory | Voice Settings > LiveKit |
| **Pipecat** | Active agents, pipeline errors | Voice Settings > General |
| **STT** | Latency (p50/p95), error rate, provider status | Voice Settings > STT |
| **Guardrails** | Triggers (injection/off-topic/PII), block rate | Voice Settings > General |
| **LLM** | Latency (TTFT), token usage, error rate | Voice Settings > LLM |
| **TTS** | Latency, character usage, error rate | Voice Settings > TTS |
| **FastAPI** | Request rate, latency (p50/p95), error rate | System config |
| **PostgreSQL** | Connection pool usage, query latency, disk usage | System config |
| **Redis** | Memory usage, hit rate, connected clients | System config |
| **Celery** | Queue depth, active workers, task success rate | System config |
| **Email Webhook** | Subscription status, messages processed | Email Settings |
| **Jira Sync** | Last sync time, sync errors, queue depth | Jira Settings |
| **LDAP Sync** | Last sync time, users synced, errors | LDAP Settings |

---

## Voice Test

The Voice Test page allows you to test the voice pipeline without making a phone call. It simulates a caller conversation through your browser.

**Minimum role**: agent_l1

### Starting a Conversation

1. Navigate to **Voice Test** from the sidebar.
2. Select a **Project** from the dropdown (this determines which voice configuration is used).
3. Choose your input mode:
   - **Microphone Mode** — Uses your browser microphone. You speak and hear the AI agent respond. Requires microphone permission.
   - **Text Mode** — Type messages as if you were the caller. The agent responds with text (TTS audio is optional).
4. Click **Start Conversation**.

### Pipeline Visualization

During an active conversation, the right panel shows the voice pipeline with animated indicators:

```
[Caller Input] ─(animating)─► [STT] ─(animating)─► [Guardrails] ─(animating)─► [LLM] ─(animating)─► [TTS] ─(animating)─► [Audio Out]
```

Each step lights up as it processes:
- **Blue pulse** — Currently processing
- **Green check** — Completed successfully
- **Red X** — Error occurred at this step

### Required Fields Panel

The left panel shows the ticket fields the AI agent is trying to collect:

| Field | Status Indicator |
|-------|-----------------|
| Caller Name | Gray (not collected) / Green (collected) |
| Phone Number | Gray / Green |
| Issue Description | Gray / Green |
| Priority | Gray / Green |
| Affected System | Gray / Green |
| Type | Gray / Green |

As the conversation progresses and the agent extracts information, fields turn green with the extracted value shown.

### Guardrail Indicators

Below the pipeline visualization, guardrail indicators show real-time status:

| Indicator | Meaning |
|-----------|---------|
| **Injection: CLEAR** (green) | No prompt injection detected |
| **Injection: BLOCKED** (red) | Prompt injection attempt detected and blocked |
| **Off-Topic: CLEAR** (green) | Conversation on-topic |
| **Off-Topic: REDIRECT** (yellow) | Off-topic detected, agent redirecting |
| **PII: CLEAR** (green) | No PII detected |
| **PII: REDACTED** (yellow) | PII detected and redacted before LLM |
| **Turns: 5/20** | Current turn count vs maximum |

### Conversation State

The conversation state indicator shows:
- **Greeting** — Agent is delivering the opening greeting
- **Collecting Info** — Agent is asking questions to fill required fields
- **Confirming** — Agent is reading back collected information for confirmation
- **Creating Ticket** — Ticket is being created in the system
- **Complete** — Conversation finished, ticket created (ticket ID shown)

### Ending a Conversation

- Click **End Conversation** at any time.
- If required fields are partially collected, the system will ask if you want to create a ticket with available data or discard.

---

## Settings

Settings pages are accessible to **manager** role and above unless otherwise noted.

### Voice Settings

Voice Settings is organized into seven tabs.

#### General Tab

| Setting | Description | Default |
|---------|-------------|---------|
| **Language** | Primary language for STT and TTS (e.g., en-US, tr-TR, de-DE) | en-US |
| **Greeting Message** | The first thing the AI agent says when answering a call | "Thank you for calling. How can I help you?" |
| **System Prompt** | Instructions for the LLM defining the agent's behavior, personality, and ticket collection goals. Supports template variables: `{company_name}`, `{project_name}`, `{agent_name}`. | Default operations center prompt |
| **Min Silence (ms)** | Minimum silence duration before the system considers the caller has finished speaking. Lower values = faster response but may cut off slow speakers. | 600 |
| **Max Silence (ms)** | Maximum silence before forcing end-of-turn. | 1500 |
| **Interruption Mode** | How the agent handles being interrupted: **Allow** (stops immediately), **Queue** (finishes sentence first), **Ignore** (ignores interruption). | Allow |
| **Backchannel** | Whether the agent produces acknowledgment sounds ("mm-hmm", "I see") during the caller's speech. | Off |
| **Max Turns** | Maximum conversation turns before the agent wraps up. Prevents infinite conversations. | 20 |
| **Guardrails** | Toggle individual guardrails on/off: Injection Detection, Off-Topic Detection, PII Redaction. | All On |

#### STT Tab (Speech-to-Text)

1. **Primary Provider** — Select from: Deepgram, Groq Whisper, Voxtral, OpenAI Whisper.
2. **Fallback Provider** — Select a different provider as fallback. If the primary fails, the system automatically switches.
3. **Provider Details**: Each provider card shows:
   - Provider name and logo
   - Supported languages
   - Streaming support (yes/no)
   - Estimated latency
   - Cost per minute
   - Status indicator (configured/not configured)

To configure a provider, its API key must be set in the **API Keys** tab.

#### LLM Tab (Language Model)

1. **Primary Provider** — Select from: Claude (Anthropic), Mistral, Groq Llama, GPT-4o Mini (OpenAI).
2. Each provider card shows:
   - Model name and version
   - Context window size
   - Estimated latency (time to first token)
   - Cost per 1M tokens (input/output)
   - Quality rating
   - Status indicator

#### TTS Tab (Text-to-Speech)

1. **Primary Provider** — Select from: Edge TTS (free), OpenAI TTS, ElevenLabs, Voxtral TTS.
2. **Voice Selection** — After selecting a provider, choose a specific voice from the available options. A **Preview** button lets you hear a sample.
3. Each provider card shows:
   - Voice quality rating
   - Available voices count
   - Streaming support
   - Cost per 1M characters
   - Status indicator

#### LiveKit Tab

| Setting | Description |
|---------|-------------|
| **LiveKit URL** | WebSocket URL of your LiveKit server (e.g., `wss://livekit.yourcompany.com`) |
| **API Key** | LiveKit API key for authentication |
| **API Secret** | LiveKit API secret (masked after entry) |
| **Test Connection** | Click to verify connectivity. Shows success/failure with latency. |

After entering credentials, click **Test Connection** before saving. A green checkmark confirms the connection is working.

#### DID Tab (Direct Inward Dialing)

DID mappings route incoming phone calls to the correct tenant and project.

1. Click **+ Add DID Mapping**.
2. Enter the phone number in E.164 format (e.g., `+12125551234`).
3. Select the **Project** this number should route to.
4. Click **Save**.

Multiple DIDs can map to the same project. Each DID can only be assigned to one project.

#### API Keys Tab

This tab manages API keys for all voice pipeline providers.

| Provider | Key Name | Description |
|----------|----------|-------------|
| Deepgram | API Key | Deepgram console API key |
| Groq | API Key | Groq console API key |
| OpenAI | API Key | OpenAI platform API key |
| Anthropic | API Key | Anthropic console API key |
| Mistral | API Key | Mistral platform API key |
| ElevenLabs | API Key | ElevenLabs API key |

**Adding/Changing a Key**:

1. Click the **Edit** (pencil) icon next to the provider.
2. Enter the API key in the field.
3. Click **Save**.
4. The key is encrypted with AES-256-GCM before storage. After saving, only the last 3 characters are displayed (e.g., `sk-...abc`).

**Important**: API keys are never transmitted back to the frontend in full. If you need to change a key, you must enter the complete new key.

---

### SLA Configuration

**Minimum role**: manager

SLA configuration defines the response, update, and resolution time targets for each priority level.

#### Understanding SLA Fields

| Field | Description |
|-------|-------------|
| **Response Time** | Maximum time (in minutes) from ticket creation to first agent response or acknowledgment. |
| **Update Time** | Maximum time (in minutes) between ticket status updates. Resets each time the ticket is updated. |
| **Resolution Time** | Maximum time (in minutes) from ticket creation to ticket resolution. |
| **Business Hours Only** | Whether SLA timers only count during business hours (default: Yes). |
| **Business Hours** | Start and end time for business hours (e.g., 09:00 - 17:00). |
| **Business Days** | Which days are business days (default: Monday - Friday). |

#### Default SLA Thresholds

| Priority | Response | Update | Resolution |
|----------|----------|--------|------------|
| P1 - Critical | 15 min | 30 min | 240 min (4h) |
| P2 - High | 30 min | 60 min | 480 min (8h) |
| P3 - Medium | 120 min (2h) | 240 min (4h) | 1440 min (24h) |
| P4 - Low | 480 min (8h) | 1440 min (24h) | 4320 min (72h) |

#### Editing SLA Thresholds

1. Navigate to **Settings > SLA Configuration**.
2. The page shows a table with one row per priority level.
3. Click **Edit** on any row to modify the thresholds.
4. Enter new values in minutes.
5. Click **Save**.

#### Project-Specific SLAs

By default, all projects use the global SLA configuration. To create project-specific SLAs:

1. On the SLA Configuration page, click **+ Project SLA**.
2. Select the project from the dropdown.
3. Configure the thresholds for each priority level.
4. Click **Save**.

Project-specific SLAs override the global defaults for tickets in that project only.

---

### Escalation Rules

**Minimum role**: manager

Escalation rules define when tickets should be automatically escalated and who should be notified.

#### Understanding Escalation Fields

| Field | Description |
|-------|-------------|
| **Project** | Which project this rule applies to |
| **L1 to L2 Threshold** | Minutes without resolution before escalating from L1 to L2 |
| **L2 to L3 Threshold** | Minutes without resolution before escalating from L2 to L3 |
| **L3 to L4 Threshold** | Minutes without resolution before escalating from L3 to Management |
| **Notification Email** | Email address(es) to notify on escalation (comma-separated) |
| **Webhook URL** | Optional URL to POST escalation events to |
| **Enabled** | Whether auto-escalation is active for this rule |

#### Creating an Escalation Rule

1. Navigate to **Settings > Escalation**.
2. Click **+ New Rule**.
3. Select the **Project**.
4. Enter threshold minutes for each escalation level:
   - **L1 -> L2**: Typical value 30-60 minutes. This is the time from ticket creation (or assignment to L1) before it escalates to L2.
   - **L2 -> L3**: Typical value 60-120 minutes.
   - **L3 -> L4 (Management)**: Typical value 120-240 minutes.
5. Enter notification recipients.
6. Optionally enter a webhook URL for external notification delivery.
7. Toggle **Enabled** on.
8. Click **Save**.

#### How Auto-Escalation Works

Every 60 seconds, the SLA breach detection task also evaluates escalation rules:

1. For each open/in-progress ticket, the system checks the elapsed time against the current escalation level threshold.
2. If the threshold is exceeded:
   - The ticket's escalation level is incremented.
   - The ticket status changes to `escalated`.
   - Notifications are sent to the configured recipients.
   - A timeline entry is created with the escalation reason.
3. The ticket can be de-escalated by an L2+ agent changing the status back to `in_progress`.

**Note**: Tickets in `pending` status are excluded from escalation checks (just as SLA timers are paused).

---

### Email Settings

**Minimum role**: manager

Email Settings configure the Microsoft 365 integration for email-based ticket creation.

#### Adding a Mailbox

1. Navigate to **Settings > Email Settings**.
2. Click **+ Add Mailbox**.
3. Enter the mailbox email address (e.g., `ops@company.com`).
4. Enter the Microsoft Graph API credentials:
   - **Client ID** — From your Azure AD app registration
   - **Client Secret** — From your Azure AD app registration
   - **Tenant ID** — Your Azure AD tenant ID
5. Select the **Default Project** — Tickets from this mailbox will be created in this project.
6. Click **Save and Activate**.

#### Microsoft Graph Webhook Setup

After saving the mailbox configuration, Opra automatically:

1. Creates a Graph API subscription for the mailbox (webhook).
2. The subscription notifies Opra whenever a new email arrives.
3. Subscriptions auto-renew before expiration (Graph subscriptions expire after 3 days for mail).

If the webhook setup fails, a warning is displayed with the error message. Common issues:
- Azure AD app lacks `Mail.Read` permission
- App registration not configured for the correct tenant
- Firewall blocking inbound webhooks from Microsoft

#### Project Mapping

You can map specific sender domains or email addresses to specific projects:

1. In the mailbox configuration, click **+ Add Routing Rule**.
2. Enter a pattern:
   - `*@vendor.com` — All emails from vendor.com go to the mapped project.
   - `specific.person@company.com` — Emails from this address go to the mapped project.
3. Select the target project.
4. Click **Save**.

Routing rules are evaluated in order. The first match wins. Unmatched emails go to the default project.

#### How Thread Matching Works

When an email arrives, the system tries to match it to an existing ticket:

1. **Subject line check** — Looks for `[OPRA-{id}]` in the subject. All outbound emails from Opra include this tag.
2. **Email headers** — Checks `In-Reply-To` and `References` headers against stored Message-IDs.
3. **Conversation ID** — Uses Microsoft's `conversationId` as a fallback.

If a match is found, the email is added as a comment on the existing ticket. If no match, a new ticket is created.

---

### Jira Settings

**Minimum role**: manager (tenant_admin for credentials)

#### Configuration

1. Navigate to **Settings > Jira Settings**.
2. Enter your Jira Cloud credentials:
   - **Site URL** — Your Jira Cloud site (e.g., `https://yourcompany.atlassian.net`)
   - **API Email** — The email address of a Jira account with API access
   - **API Token** — An Atlassian API token (generate at https://id.atlassian.com/manage/api-tokens)
3. Click **Test Connection** to verify. A successful test displays the Jira server version and available projects.
4. Click **Save**.

#### Status Mapping

Customize how Opra ticket statuses map to Jira issue statuses:

1. Click the **Status Mapping** tab.
2. For each Opra status, select the corresponding Jira status from the dropdown.
3. Jira statuses are fetched from your Jira instance (they depend on your Jira workflow configuration).
4. Click **Save Mapping**.

#### Priority Mapping

1. Click the **Priority Mapping** tab.
2. For each Opra priority (P1-P4), select the corresponding Jira priority.
3. Click **Save Mapping**.

#### How Bidirectional Sync Works

**Opra to Jira**:
- When a ticket is created or updated in Opra and its project is mapped to a Jira project, a Celery task queues the sync.
- The task creates or updates the Jira issue with mapped fields.
- The Jira issue key is stored on the Opra ticket.

**Jira to Opra**:
- Opra registers a Jira webhook that fires on issue create/update/delete events.
- When a webhook arrives, Opra validates the signature and processes the event.
- If the issue matches an existing Opra ticket (via stored Jira key), the ticket is updated.
- If auto-import is enabled and the issue is in a mapped project, a new Opra ticket is created.

**Conflict Resolution**:
- If both sides update different fields, both changes are merged.
- If both sides update the same field, the most recent change (by timestamp) wins.
- All conflicts are logged in the ticket timeline for audit purposes.
- A 5-second sync lock prevents ping-pong updates.

---

### LDAP Settings

**Minimum role**: tenant_admin

#### Configuration

1. Navigate to **Settings > LDAP Settings**.
2. Enter your LDAP/Active Directory connection details:

| Field | Description | Example |
|-------|-------------|---------|
| **Server URL** | LDAP or LDAPS URL | `ldaps://ad.company.com:636` |
| **Bind DN** | Distinguished name of the service account | `CN=OpraService,OU=Service Accounts,DC=company,DC=com` |
| **Bind Password** | Service account password | (encrypted at rest) |
| **Search Base** | Base DN for user search | `OU=Users,DC=company,DC=com` |
| **Search Filter** | LDAP filter to select users | `(&(objectClass=user)(memberOf=CN=OpsTeam,OU=Groups,DC=company,DC=com))` |
| **Sync Interval** | Minutes between automatic syncs | 60 |

3. Click **Test Connection** to verify. A successful test shows: connection status, number of users matching the filter, and sample user data (first 5).
4. Click **Save**.

#### Role Mapping

1. Click the **Role Mapping** tab.
2. For each Opra role, enter the AD group DN that should map to it:

| Opra Role | AD Group DN |
|-----------|-------------|
| tenant_admin | `CN=Opra-Admins,OU=Groups,DC=company,DC=com` |
| manager | `CN=Opra-Managers,OU=Groups,DC=company,DC=com` |
| agent_l3 | `CN=Opra-L3,OU=Groups,DC=company,DC=com` |
| agent_l2 | `CN=Opra-L2,OU=Groups,DC=company,DC=com` |
| agent_l1 | `CN=Opra-L1,OU=Groups,DC=company,DC=com` |
| viewer | `CN=Opra-Viewers,OU=Groups,DC=company,DC=com` |

3. Click **Save Mapping**.

If a user belongs to multiple mapped groups, the highest role is assigned.

#### Sync Interval

The sync interval determines how often Opra queries AD for changes. Default is 60 minutes. Setting this lower increases AD server load but ensures faster provisioning.

#### Manual Sync Trigger

Click **Sync Now** to trigger an immediate sync. The page shows:
- Sync status (running/completed/failed)
- Last sync timestamp
- Results: users created, updated, deactivated, errors

---

## Reports

**Minimum role**: manager

The Reports page provides analytics across five report types. All reports support a **Period Selector** in the top-right corner:
- Last 24 hours
- Last 7 days
- Last 30 days
- Last 90 days
- Custom date range

### SLA Compliance Report

**What it shows**: Percentage of tickets that met their SLA targets, broken down by priority.

**How to read it**:
- **Bar chart**: Each bar represents a priority level (P1-P4). The bar height is the compliance percentage. Green portion = met, Red portion = breached.
- **Trend line**: Shows compliance over time for the selected period.
- **Table**: Below the chart, a detailed table lists every breached ticket with: ticket ID, title, priority, which SLA was breached (response/update/resolution), and by how much.

**Target**: Most operations centers aim for 95%+ compliance on P1/P2 and 90%+ on P3/P4.

### Ticket Volume Report

**What it shows**: Number of tickets created over time, segmented by various dimensions.

**Breakdown options** (toggle buttons):
- **By Source**: Voice, Email, Web, API — Shows which channel generates the most tickets.
- **By Type**: Incident, Service Request, Problem, Change — Shows the distribution of ITIL types.
- **By Status**: Current status distribution — Identifies bottlenecks (e.g., many tickets stuck in pending).
- **By Priority**: P1-P4 distribution — Shows severity trends.

**Charts**:
- **Stacked area chart**: Volume over time with color-coded segments.
- **Donut chart**: Overall distribution for the selected period.
- **Table**: Raw numbers with totals.

### Escalation Frequency Report

**What it shows**: How often tickets are escalated and to which level.

**Charts**:
- **Bar chart by level**: Shows total escalations to L2, L3, and L4 for the period.
- **Trend line**: Escalation rate over time (escalations per day/week).
- **Top escalation reasons**: Word cloud or ranked list of escalation reasons from comments.

**What to look for**: A high L3/L4 escalation rate may indicate L1/L2 training gaps or unrealistic SLA thresholds.

### Agent Performance Report

**What it shows**: Workload and performance metrics per agent.

**Metrics per agent**:
| Metric | Description |
|--------|-------------|
| **Tickets Assigned** | Total tickets assigned during the period |
| **Tickets Resolved** | Total tickets resolved |
| **Avg Resolution Time** | Average time from assignment to resolution |
| **SLA Compliance** | Percentage of assigned tickets that met SLA |
| **Escalation Rate** | Percentage of assigned tickets that were escalated |
| **Response Time** | Average time to first response after assignment |

**Charts**:
- **Leaderboard table**: Agents ranked by resolution count and SLA compliance.
- **Workload distribution**: Donut chart showing ticket distribution across agents.
- **Trend**: Individual agent performance over time (select an agent).

### Call Analytics Report

**What it shows**: Voice pipeline statistics.

**Metrics**:
| Metric | Description |
|--------|-------------|
| **Total Calls** | Number of voice calls received |
| **Avg Call Duration** | Average call length in minutes |
| **Ticket Conversion Rate** | Percentage of calls that resulted in a ticket |
| **Avg STT Latency** | Average speech-to-text processing time |
| **Avg LLM Latency** | Average LLM response time (TTFT) |
| **Avg TTS Latency** | Average text-to-speech processing time |
| **Guardrail Trigger Rate** | Percentage of turns where a guardrail was activated |
| **Call Abandonment Rate** | Percentage of calls ended by caller before ticket creation |

**Charts**:
- **Call volume over time**: Bar chart with daily/hourly granularity.
- **Duration distribution**: Histogram of call durations.
- **Pipeline latency breakdown**: Stacked bar showing STT + LLM + TTS latency per call.
- **Provider comparison**: If multiple providers are used, side-by-side latency comparison.

---

## System Health

**Minimum role**: manager

The System Health page provides a quick status overview of all system components.

### Service Status Cards

Each component is displayed as a card with:

| Card Element | Description |
|-------------|-------------|
| **Name** | Component name (e.g., PostgreSQL, Redis, Celery) |
| **Status Icon** | Green check (healthy), Yellow warning (degraded), Red X (down) |
| **Uptime** | Time since last restart or failure |
| **Key Metric** | One primary metric (e.g., connection pool usage for PostgreSQL, memory usage for Redis) |
| **Last Check** | Timestamp of the most recent health check |

### Components Shown

| Component | Health Check | Key Metric |
|-----------|-------------|------------|
| FastAPI Backend | HTTP /health endpoint | Request latency (p95) |
| PostgreSQL | Connection test | Active connections / pool size |
| Redis | PING command | Memory usage |
| Celery Workers | Inspector ping | Active tasks / queue depth |
| Celery Beat | Heartbeat check | Last scheduled task time |
| LiveKit | REST API health | Active rooms |
| Email Webhook | Graph subscription status | Last event time |
| Jira Integration | Connection test | Last sync time |
| LDAP Integration | Bind test | Last sync time |

### Link to Topology

A **View Full Topology** button at the top links to the Topology page for the detailed interactive pipeline map.

---

## Role Permissions Matrix

The following table defines what each role can do on each page. Roles are cumulative — each role includes all permissions of the roles below it.

### Page Access

| Page | viewer | agent_l1 | agent_l2 | agent_l3 | manager | tenant_admin | super_admin |
|------|--------|----------|----------|----------|---------|-------------|-------------|
| **Dashboard** | View | View | View | View | View | View | View (all tenants) |
| **Tickets - List** | View | View | View | View | View | View | View (all tenants) |
| **Tickets - Create** | -- | Create | Create | Create | Create | Create | Create |
| **Tickets - Edit** | -- | Edit own | Edit any | Edit any | Edit any | Edit any | Edit any |
| **Tickets - Status Change** | -- | Limited* | All | All | All | All | All |
| **Tickets - Assign** | -- | Self only | Any agent | Any agent | Any agent | Any agent | Any agent |
| **Tickets - Escalate** | -- | Escalate | Escalate | Escalate | Escalate | Escalate | Escalate |
| **Tickets - Delete** | -- | -- | -- | -- | Delete | Delete | Delete |
| **Contacts - List** | View | View | View | View | View | View | View |
| **Contacts - Create/Edit** | -- | Create/Edit | Create/Edit | Create/Edit | Create/Edit | Create/Edit | Create/Edit |
| **Contacts - Delete** | -- | -- | -- | -- | Delete | Delete | Delete |
| **Projects - List** | View | View | View | View | View | View | View |
| **Projects - Create/Edit** | -- | -- | -- | -- | Create/Edit | Create/Edit | Create/Edit |
| **Projects - Delete** | -- | -- | -- | -- | -- | Delete | Delete |
| **Projects - CSV Import** | -- | -- | -- | -- | Import | Import | Import |
| **Topology** | View | View | View | View | View | View | View |
| **Node Detail** | View | View | View | View | View + Configure | View + Configure | View + Configure |
| **Voice Test** | -- | Test | Test | Test | Test | Test | Test |
| **Voice Settings** | -- | -- | -- | -- | Edit | Edit | Edit |
| **SLA Configuration** | -- | -- | -- | View | Edit | Edit | Edit |
| **Escalation Rules** | -- | -- | -- | View | Edit | Edit | Edit |
| **Email Settings** | -- | -- | -- | -- | Edit | Edit | Edit |
| **Jira Settings** | -- | -- | -- | -- | Edit | Edit | Edit |
| **LDAP Settings** | -- | -- | -- | -- | -- | Edit | Edit |
| **Reports** | -- | -- | -- | View | View + Export | View + Export | View + Export |
| **System Health** | -- | -- | -- | -- | View | View | View |

*agent_l1 limited status changes: can move `new` -> `open`, `open` -> `in_progress`, `in_progress` -> `pending`, `in_progress` -> `resolved`. Cannot change to `closed` or `cancelled`.

### Special Permissions

| Permission | Roles |
|-----------|-------|
| **SLA Override** — Manually extend or reset SLA timers | agent_l3, manager, tenant_admin, super_admin |
| **View All Tenants** — See data across tenant boundaries | super_admin only |
| **Create Tenants** — Provision new tenants | super_admin only |
| **Manage Users** — Create/edit/deactivate user accounts | manager (within team), tenant_admin (all tenant users), super_admin (all users) |
| **Export Data** — Export reports and ticket data to CSV | manager, tenant_admin, super_admin |
| **API Key Management** — View/edit encrypted API keys | tenant_admin, super_admin |
| **Audit Log** — View system audit trail | tenant_admin, super_admin |

---

*This guide is maintained by the Opra team. For feature requests or corrections, contact your operations center administrator.*
