"""LDAP/Active Directory client wrapper.

Uses python-ldap for bind and search operations.
Designed for LDAP sync pattern: periodic sync + local JWT (no LDAP bind per request).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LDAPUser:
    dn: str
    sam_account_name: str
    email: str
    display_name: str
    groups: list[str] = field(default_factory=list)
    is_disabled: bool = False


class LDAPClient:
    """Wrapper around python-ldap for AD operations.

    Note: python-ldap is synchronous. This is acceptable because LDAP sync
    runs in Celery workers (not in async FastAPI request handlers).
    """

    def __init__(self, server_url: str, bind_dn: str, bind_password: str):
        self.server_url = server_url
        self.bind_dn = bind_dn
        self.bind_password = bind_password
        self._conn = None

    def connect(self):
        """Establish LDAP connection and bind."""
        import ldap

        self._conn = ldap.initialize(self.server_url)
        self._conn.set_option(ldap.OPT_REFERRALS, 0)
        self._conn.set_option(ldap.OPT_PROTOCOL_VERSION, 3)

        if self.server_url.startswith("ldaps://"):
            self._conn.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

        self._conn.simple_bind_s(self.bind_dn, self.bind_password)

    def close(self):
        if self._conn:
            self._conn.unbind_s()
            self._conn = None

    def authenticate_user(self, user_dn: str, password: str) -> bool:
        """Attempt LDAP bind with user credentials. Returns True if successful."""
        import ldap

        try:
            conn = ldap.initialize(self.server_url)
            conn.set_option(ldap.OPT_REFERRALS, 0)
            conn.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
            conn.simple_bind_s(user_dn, password)
            conn.unbind_s()
            return True
        except ldap.INVALID_CREDENTIALS:
            return False
        except ldap.LDAPError:
            return False

    def search_users(self, base_dn: str, search_filter: str) -> list[LDAPUser]:
        """Search for users in AD."""
        import ldap

        if not self._conn:
            self.connect()

        attrs = [
            "distinguishedName", "sAMAccountName", "mail",
            "displayName", "memberOf", "userAccountControl",
        ]

        try:
            results = self._conn.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter, attrs)
        except ldap.LDAPError:
            return []

        users = []
        for dn, entry in results:
            if not dn or not isinstance(entry, dict):
                continue

            # Check if account is disabled (bit 2 of userAccountControl)
            uac = int(entry.get("userAccountControl", [b"0"])[0])
            is_disabled = bool(uac & 0x2)

            groups = [
                g.decode("utf-8") if isinstance(g, bytes) else g
                for g in entry.get("memberOf", [])
            ]

            users.append(LDAPUser(
                dn=dn,
                sam_account_name=_decode(entry.get("sAMAccountName", [b""])[0]),
                email=_decode(entry.get("mail", [b""])[0]),
                display_name=_decode(entry.get("displayName", [b""])[0]),
                groups=groups,
                is_disabled=is_disabled,
            ))

        return users

    def get_user_groups(self, user_dn: str, base_dn: str) -> list[str]:
        """Get all groups a user belongs to."""
        import ldap

        if not self._conn:
            self.connect()

        search_filter = f"(&(objectClass=group)(member={user_dn}))"
        try:
            results = self._conn.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter, ["distinguishedName"])
            return [dn for dn, _ in results if dn]
        except ldap.LDAPError:
            return []


def _decode(value) -> str:
    """Decode LDAP attribute value."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value) if value else ""
