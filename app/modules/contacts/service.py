"""Contact business logic."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.contact import Contact


async def create_contact(
    db: AsyncSession, tenant_id: UUID, **kwargs,
) -> Contact:
    contact = Contact(tenant_id=tenant_id, **kwargs)
    db.add(contact)
    await db.flush()
    return contact


async def get_contact(db: AsyncSession, tenant_id: UUID, contact_id: UUID) -> Contact:
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.tenant_id == tenant_id)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise NotFoundError("Contact")
    return contact


async def find_contact_by_email(
    db: AsyncSession, tenant_id: UUID, email: str,
) -> Contact | None:
    result = await db.execute(
        select(Contact).where(Contact.tenant_id == tenant_id, Contact.email == email)
    )
    return result.scalar_one_or_none()


async def find_contact_by_phone(
    db: AsyncSession, tenant_id: UUID, phone: str,
) -> Contact | None:
    result = await db.execute(
        select(Contact).where(Contact.tenant_id == tenant_id, Contact.phone == phone)
    )
    return result.scalar_one_or_none()


async def list_contacts(
    db: AsyncSession, tenant_id: UUID, page: int = 1, size: int = 50,
) -> tuple[list[Contact], int]:
    count_result = await db.execute(
        select(func.count(Contact.id)).where(Contact.tenant_id == tenant_id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Contact)
        .where(Contact.tenant_id == tenant_id)
        .order_by(Contact.name)
        .offset((page - 1) * size)
        .limit(size)
    )
    return list(result.scalars().all()), total


async def update_contact(
    db: AsyncSession, tenant_id: UUID, contact_id: UUID, **updates,
) -> Contact:
    contact = await get_contact(db, tenant_id, contact_id)
    for field, value in updates.items():
        if value is not None and hasattr(contact, field):
            setattr(contact, field, value)
    await db.flush()
    return contact
