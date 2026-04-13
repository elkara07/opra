"""Voice agent definition for ticket intake via phone.

Uses function calling to interact with the ticket system during conversation.
Designed for Pipecat pipeline integration with LiveKit SIP bridge.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Conversation State Machine
# ---------------------------------------------------------------------------

VOICE_STATES = [
    "greeting",       # Initial greeting, identify caller
    "identify",       # Caller ID lookup, confirm identity
    "collect",        # Open-ended issue description
    "classify",       # LLM classifies type, priority, project
    "confirm",        # Summarize and get caller confirmation
    "create",         # Create ticket via function call
    "closing",        # Provide ticket number, ask if anything else
    "transfer",       # Transfer to human agent
    "hangup",         # End call
]


# ---------------------------------------------------------------------------
# Function Definitions (for LLM function calling)
# ---------------------------------------------------------------------------

AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_caller",
            "description": "Look up a caller in the contact database by phone number. Returns name, company, VIP status, and previous ticket history.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Caller's phone number in E.164 format (e.g., +905321234567)",
                    },
                },
                "required": ["phone"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_projects",
            "description": "Get the list of available projects/services for ticket routing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tenant_id": {
                        "type": "string",
                        "description": "Tenant UUID",
                    },
                },
                "required": ["tenant_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_ticket",
            "description": "Create a new support ticket in the system. Call this after collecting and confirming all information from the caller.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {
                        "type": "string",
                        "description": "Brief summary of the issue (max 100 chars)",
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the issue as described by the caller",
                    },
                    "type": {
                        "type": "string",
                        "enum": ["incident", "service_request", "problem", "change"],
                        "description": "ITIL ticket type",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["P1", "P2", "P3", "P4"],
                        "description": "Priority based on impact and urgency",
                    },
                    "project_code": {
                        "type": "string",
                        "description": "Project code for routing (e.g., INFRA, APP, NET)",
                    },
                    "contact_id": {
                        "type": "string",
                        "description": "Contact UUID from lookup_caller result",
                    },
                },
                "required": ["subject", "description", "type", "priority"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_to_human",
            "description": "Transfer the call to a human agent. Use when the caller requests it, the issue is too complex, or after 3 misunderstandings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Why the call is being transferred",
                    },
                },
                "required": ["reason"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# System Prompt Builder
# ---------------------------------------------------------------------------

def build_system_prompt(
    tenant_name: str,
    language: str = "tr",
    projects: list[dict] | None = None,
    caller_info: dict | None = None,
) -> str:
    """Build the system prompt for the voice agent LLM.

    Args:
        tenant_name: Name of the company/tenant
        language: Conversation language
        projects: Available projects for routing
        caller_info: Known caller info from lookup
    """
    project_list = ""
    if projects:
        project_list = "\n".join(
            f"  - {p['code']}: {p['name']}" for p in projects
        )
    else:
        project_list = "  (No specific projects configured)"

    caller_context = ""
    if caller_info:
        caller_context = f"""
Known caller information:
  - Name: {caller_info.get('name', 'Unknown')}
  - Company: {caller_info.get('company', 'Unknown')}
  - VIP: {'Yes' if caller_info.get('vip') else 'No'}
  - Previous tickets: {caller_info.get('ticket_count', 0)}
"""

    lang_instruction = {
        "tr": "Konuşmayı Türkçe olarak yürüt.",
        "en": "Conduct the conversation in English.",
    }.get(language, "Conduct the conversation in English.")

    return f"""You are an AI support agent for {tenant_name}'s 24/7 operations center.
{lang_instruction}

Your job is to:
1. Greet the caller professionally
2. Identify who they are (use lookup_caller if you have their phone number)
3. Understand their issue through conversation (ask clarifying questions)
4. Classify the issue (type: incident/service_request/problem/change, priority: P1-P4)
5. Confirm the summary with the caller
6. Create a ticket using create_ticket function
7. Provide the ticket number and close the call

Available projects for routing:
{project_list}

{caller_context}

Priority guidelines:
- P1: Critical — Service completely down, major business impact, affects many users
- P2: High — Significant degradation, workaround possible but difficult
- P3: Medium — Limited impact, workaround available
- P4: Low — Minor issue, cosmetic, feature request

Rules:
- Be concise and professional. Avoid long monologues.
- Ask ONE question at a time, wait for response.
- If the caller says "transfer" or "human" or presses 0, use transfer_to_human immediately.
- If you don't understand 3 times in a row, transfer to human.
- Maximum 20 conversation turns, then transfer.
- For P1 issues, mention that the ticket will be immediately escalated.
- Always confirm the summary before creating the ticket.
- After ticket creation, provide the ticket number clearly.
"""
