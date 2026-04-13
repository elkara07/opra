"""Import all models so Alembic can discover them."""

from app.models.tenant import Tenant
from app.models.user import User, RefreshToken
from app.models.team import Team, TeamMember
from app.models.project import Project
from app.models.contact import Contact
from app.models.ticket import Ticket, TicketEvent
from app.models.sla import SLAConfig
from app.models.escalation import EscalationRule
from app.models.email_message import EmailMailbox, EmailMessage, Attachment
from app.models.call_record import CallRecord
from app.models.notification import NotificationLog
from app.models.jira_config import JiraConfig, JiraSyncLog
from app.models.ldap_config import LDAPConfig
from app.models.audit import AuditLog, DIDMapping

__all__ = [
    "Tenant", "User", "RefreshToken",
    "Team", "TeamMember", "Project", "Contact",
    "Ticket", "TicketEvent",
    "SLAConfig", "EscalationRule",
    "EmailMailbox", "EmailMessage", "Attachment",
    "CallRecord", "NotificationLog",
    "JiraConfig", "JiraSyncLog",
    "LDAPConfig", "AuditLog", "DIDMapping",
]
