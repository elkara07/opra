"""LDAP synchronization tasks."""

from __future__ import annotations

from workers.celery_app import app


@app.task(name="workers.tasks.ldap_tasks.ldap_sync_all", bind=True)
def ldap_sync_all(self):
    """Sync users and groups from LDAP/AD for all tenants with sync_enabled=True.

    1. For each tenant with ldap_config.sync_enabled:
    2. Bind to LDAP server
    3. Search users with configured filter
    4. Create/update local user records
    5. Map AD groups to local roles
    6. Deactivate users removed from AD
    7. Update ldap_config.last_sync_at
    """
    # TODO: Implement in Faz 3
    pass
