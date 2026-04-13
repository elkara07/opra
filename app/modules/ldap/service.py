"""LDAP synchronization service: user/group sync from Active Directory."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_value, hash_password
from app.models.ldap_config import LDAPConfig
from app.models.user import User
from app.modules.ldap.client import LDAPClient, LDAPUser


async def get_ldap_config(db: AsyncSession, tenant_id: UUID) -> LDAPConfig | None:
    result = await db.execute(
        select(LDAPConfig).where(
            LDAPConfig.tenant_id == tenant_id,
            LDAPConfig.sync_enabled == True,
        )
    )
    return result.scalar_one_or_none()


def sync_users_from_ldap(
    ldap_client: LDAPClient,
    ldap_config: LDAPConfig,
    existing_users: list[User],
    tenant_id: UUID,
) -> dict:
    """Sync users from LDAP to local database.

    This is a pure function that returns changes to apply.
    Called from Celery worker (synchronous context).

    Returns:
        {
            "to_create": [{"email": ..., "name": ..., "ldap_dn": ..., "role": ...}],
            "to_update": [{"user_id": ..., "name": ..., "role": ...}],
            "to_deactivate": [user_id, ...],
        }
    """
    # Search all users in AD
    base_dn = ldap_config.base_dn
    search_filter = ldap_config.user_search_filter or "(&(objectClass=user)(mail=*))"
    ldap_users = ldap_client.search_users(base_dn, search_filter)

    # Build lookup maps
    existing_by_email = {u.email: u for u in existing_users if u.email}
    existing_by_dn = {u.ldap_dn: u for u in existing_users if u.ldap_dn}
    ldap_by_dn = {lu.dn: lu for lu in ldap_users}

    role_mapping = ldap_config.role_mapping or {}

    to_create = []
    to_update = []
    to_deactivate = []

    for lu in ldap_users:
        if lu.is_disabled:
            # If we have this user locally, deactivate
            if lu.dn in existing_by_dn:
                to_deactivate.append(existing_by_dn[lu.dn].id)
            continue

        # Determine role from group membership
        role = _resolve_role(lu.groups, role_mapping)

        existing = existing_by_dn.get(lu.dn) or existing_by_email.get(lu.email)
        if existing:
            # Update if changed
            changes = {}
            if existing.name != lu.display_name:
                changes["name"] = lu.display_name
            if existing.ldap_dn != lu.dn:
                changes["ldap_dn"] = lu.dn
            if role and existing.role != role:
                changes["role"] = role
            if not existing.is_active:
                changes["is_active"] = True
            if changes:
                changes["user_id"] = existing.id
                to_update.append(changes)
        else:
            if lu.email:  # Only create if email exists
                to_create.append({
                    "email": lu.email,
                    "name": lu.display_name or lu.sam_account_name,
                    "ldap_dn": lu.dn,
                    "role": role or "agent_l1",
                    "auth_source": "ldap",
                })

    # Deactivate users removed from AD
    for user in existing_users:
        if user.auth_source == "ldap" and user.ldap_dn and user.ldap_dn not in ldap_by_dn:
            if user.is_active:
                to_deactivate.append(user.id)

    return {
        "to_create": to_create,
        "to_update": to_update,
        "to_deactivate": to_deactivate,
    }


def _resolve_role(groups: list[str], role_mapping: dict) -> str | None:
    """Map AD group membership to local role.

    role_mapping: {"CN=IT-Admins,OU=Groups,...": "tenant_admin", ...}
    Returns the highest-privilege matching role.
    """
    from app.core.dependencies import ROLE_HIERARCHY

    best_role = None
    best_level = -1

    for group_dn in groups:
        role = role_mapping.get(group_dn)
        if role and ROLE_HIERARCHY.get(role, 0) > best_level:
            best_role = role
            best_level = ROLE_HIERARCHY[role]

    return best_role
