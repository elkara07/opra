"""Seed script: create demo tenant, users, projects, SLA configs, and sample tickets."""

import asyncio
import sys
sys.path.insert(0, '.')

from app.core.database import async_session_factory, engine
from app.core.security import hash_password
from app.models.tenant import Tenant
from app.models.user import User
from app.models.team import Team, TeamMember
from app.models.project import Project
from app.models.contact import Contact
from app.models.sla import SLAConfig
from app.models.escalation import EscalationRule
from app.models.ticket import Ticket, TicketEvent


async def seed():
    async with async_session_factory() as db:
        # --- Tenant ---
        tenant = Tenant(
            name="Acme Operations",
            slug="acme",
            timezone="Europe/Istanbul",
            business_hours={
                "mon": {"start": "00:00", "end": "23:59"},
                "tue": {"start": "00:00", "end": "23:59"},
                "wed": {"start": "00:00", "end": "23:59"},
                "thu": {"start": "00:00", "end": "23:59"},
                "fri": {"start": "00:00", "end": "23:59"},
                "sat": {"start": "00:00", "end": "23:59"},
                "sun": {"start": "00:00", "end": "23:59"},
            },
            holidays=[],
        )
        db.add(tenant)
        await db.flush()
        print(f"Tenant: {tenant.name} (id={tenant.id})")

        # --- Users ---
        users_data = [
            ("admin@acme.com", "Admin User", "tenant_admin", "admin123"),
            ("manager@acme.com", "Ops Manager", "manager", "manager123"),
            ("agent1@acme.com", "Agent L1 - Ayse", "agent_l1", "agent123"),
            ("agent2@acme.com", "Agent L2 - Mehmet", "agent_l2", "agent123"),
            ("agent3@acme.com", "Agent L3 - Fatma", "agent_l3", "agent123"),
            ("viewer@acme.com", "Dashboard Viewer", "viewer", "viewer123"),
        ]
        users = {}
        for email, name, role, password in users_data:
            u = User(
                tenant_id=tenant.id, email=email, name=name,
                role=role, password_hash=hash_password(password),
            )
            db.add(u)
            await db.flush()
            users[role] = u
            print(f"  User: {email} / {password} (role={role})")

        # --- Teams ---
        team_l1 = Team(tenant_id=tenant.id, name="L1 Support", escalation_level=1, manager_id=users["manager"].id)
        team_l2 = Team(tenant_id=tenant.id, name="L2 Technical", escalation_level=2, manager_id=users["manager"].id)
        team_l3 = Team(tenant_id=tenant.id, name="L3 Expert", escalation_level=3, manager_id=users["manager"].id)
        team_mgmt = Team(tenant_id=tenant.id, name="Management", escalation_level=4, manager_id=users["tenant_admin"].id)
        db.add_all([team_l1, team_l2, team_l3, team_mgmt])
        await db.flush()

        db.add_all([
            TeamMember(team_id=team_l1.id, user_id=users["agent_l1"].id, is_primary=True),
            TeamMember(team_id=team_l2.id, user_id=users["agent_l2"].id, is_primary=True),
            TeamMember(team_id=team_l3.id, user_id=users["agent_l3"].id, is_primary=True),
            TeamMember(team_id=team_mgmt.id, user_id=users["manager"].id, is_primary=True),
        ])
        await db.flush()
        print(f"  Teams: L1, L2, L3, Management")

        # --- Projects ---
        projects = {}
        for code, name in [("INFRA", "Infrastructure"), ("APP", "Application"), ("NET", "Network"), ("SEC", "Security")]:
            p = Project(tenant_id=tenant.id, name=name, code=code, default_team_id=team_l1.id, default_priority="P3")
            db.add(p)
            await db.flush()
            projects[code] = p
        print(f"  Projects: {', '.join(projects.keys())}")

        # --- Contacts ---
        contacts = {}
        for name, email, phone, company, vip in [
            ("Ali Yilmaz", "ali@customer.com", "+905321234567", "TechCorp", True),
            ("Zeynep Kaya", "zeynep@bigco.com", "+905329876543", "BigCo", False),
            ("Emre Demir", "emre@startup.io", "+905551112233", "Startup.io", False),
        ]:
            c = Contact(tenant_id=tenant.id, name=name, email=email, phone=phone, company=company, vip=vip)
            db.add(c)
            await db.flush()
            contacts[name] = c
        print(f"  Contacts: {len(contacts)}")

        # --- SLA Configs ---
        sla_defaults = {
            "P1": (15, 60, 240, [30, 60, 120]),
            "P2": (30, 120, 480, [60, 120, 240]),
            "P3": (60, 480, 1440, [120, 480, 720]),
            "P4": (480, 1440, 5760, [1440, 2880, 4320]),
        }
        sla_configs = {}
        for priority, (resp, upd, res, esc) in sla_defaults.items():
            s = SLAConfig(
                tenant_id=tenant.id, name=f"Default {priority}", priority=priority,
                response_minutes=resp, update_minutes=upd, resolution_minutes=res,
                escalation_thresholds=esc, is_default=True,
            )
            db.add(s)
            await db.flush()
            sla_configs[priority] = s
        print(f"  SLA Configs: P1-P4")

        # --- Escalation Rules ---
        for priority, sla in sla_configs.items():
            for level, (team, threshold) in enumerate(
                [(team_l2, sla.escalation_thresholds[0]),
                 (team_l3, sla.escalation_thresholds[1]),
                 (team_mgmt, sla.escalation_thresholds[2])], start=2
            ):
                r = EscalationRule(
                    tenant_id=tenant.id, sla_config_id=sla.id,
                    level=level, threshold_minutes=threshold,
                    notify_team_id=team.id, notification_channels=["email"],
                )
                db.add(r)
        await db.flush()
        print(f"  Escalation Rules: 12 (4 priorities x 3 levels)")

        # --- Sample Tickets ---
        from datetime import datetime, timezone, timedelta
        from app.modules.sla.engine import calculate_due_date

        now = datetime.now(timezone.utc)
        bh = tenant.business_hours

        tickets_data = [
            ("Production DB unresponsive", "incident", "P1", "phone", "Ali Yilmaz", "INFRA", "in_progress", 2),
            ("Cannot deploy to staging", "incident", "P2", "email", "Zeynep Kaya", "APP", "assigned", 1),
            ("VPN connection dropping", "incident", "P2", "phone", "Emre Demir", "NET", "new", 0),
            ("Request new AWS account", "service_request", "P3", "email", "Ali Yilmaz", "INFRA", "in_progress", 0),
            ("SSL certificate expiring in 7 days", "incident", "P3", "web", "Zeynep Kaya", "SEC", "new", 0),
            ("Add monitoring for new service", "service_request", "P4", "email", "Emre Demir", "INFRA", "assigned", 0),
            ("Network latency investigation", "problem", "P2", "phone", "Ali Yilmaz", "NET", "pending_customer", 0),
            ("Firewall rule change request", "change", "P3", "web", "Zeynep Kaya", "SEC", "resolved", 0),
        ]

        for i, (subject, ttype, priority, source, contact_name, proj_code, status, esc_level) in enumerate(tickets_data):
            contact = contacts[contact_name]
            project = projects[proj_code]
            sla = sla_configs[priority]

            created_at = now - timedelta(hours=(len(tickets_data) - i) * 3)
            resp_due = calculate_due_date(created_at, sla.response_minutes, bh, tz="Europe/Istanbul")
            res_due = calculate_due_date(created_at, sla.resolution_minutes, bh, tz="Europe/Istanbul")

            t = Ticket(
                tenant_id=tenant.id,
                ticket_number=f"TKT-{i+1:05d}",
                type=ttype, status=status, priority=priority,
                subject=subject, source=source,
                project_id=project.id, contact_id=contact.id,
                assigned_team_id=team_l1.id,
                assigned_user_id=users["agent_l1"].id if status != "new" else None,
                sla_config_id=sla.id,
                sla_response_due=resp_due,
                sla_resolution_due=res_due,
                sla_responded_at=created_at + timedelta(minutes=10) if status not in ("new",) else None,
                current_escalation_level=esc_level,
                created_at=created_at,
            )
            db.add(t)
            await db.flush()

            # Add creation event
            ev = TicketEvent(
                tenant_id=tenant.id, ticket_id=t.id,
                event_type="created", new_value=status,
                metadata_={"source": source}, created_at=created_at,
            )
            db.add(ev)

            # Add a comment for some tickets
            if status in ("in_progress", "assigned", "pending_customer"):
                comment_ev = TicketEvent(
                    tenant_id=tenant.id, ticket_id=t.id,
                    event_type="comment",
                    comment=f"Investigating {subject.lower()}. Will update shortly.",
                    is_public=True, user_id=users["agent_l1"].id,
                    created_at=created_at + timedelta(minutes=15),
                )
                db.add(comment_ev)

        await db.flush()
        print(f"  Tickets: {len(tickets_data)} sample tickets")

        await db.commit()
        print()
        print("=" * 50)
        print("SEED COMPLETE")
        print("=" * 50)
        print()
        print("Login credentials:")
        print("  admin@acme.com / admin123 (tenant_admin)")
        print("  manager@acme.com / manager123 (manager)")
        print("  agent1@acme.com / agent123 (agent_l1)")
        print("  viewer@acme.com / viewer123 (viewer)")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
