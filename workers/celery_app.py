"""Celery application configuration with priority queues and Beat schedule."""

from __future__ import annotations

import os

from celery import Celery
from celery.schedules import crontab

broker_url = os.getenv("CELERY_BROKER_URL", "redis://:callcenter_pass@localhost:6379/1")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://:callcenter_pass@localhost:6379/2")

app = Celery(
    "callcenter",
    broker=broker_url,
    backend=result_backend,
)

app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Priority queues
    task_queues={
        "critical": {"exchange": "critical", "routing_key": "critical"},
        "high": {"exchange": "high", "routing_key": "high"},
        "default": {"exchange": "default", "routing_key": "default"},
        "low": {"exchange": "low", "routing_key": "low"},
    },
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",

    # Retry policy
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,

    # Result expiry
    result_expires=3600,

    # Beat schedule — periodic tasks
    beat_schedule={
        "sla-check-all-active-tickets": {
            "task": "workers.tasks.sla_tasks.sla_check_all",
            "schedule": 60.0,  # Every 60 seconds
            "options": {"queue": "critical"},
        },
        "escalation-threshold-check": {
            "task": "workers.tasks.sla_tasks.escalation_check",
            "schedule": 60.0,
            "options": {"queue": "critical"},
        },
        "graph-subscription-renewal": {
            "task": "workers.tasks.email_tasks.renew_graph_subscriptions",
            "schedule": 6 * 3600,  # Every 6 hours
            "options": {"queue": "low"},
        },
        "ldap-sync": {
            "task": "workers.tasks.ldap_tasks.ldap_sync_all",
            "schedule": 3600.0,  # Every 60 minutes
            "options": {"queue": "low"},
        },
        "jira-retry-failed-syncs": {
            "task": "workers.tasks.jira_tasks.retry_failed_syncs",
            "schedule": 300.0,  # Every 5 minutes
            "options": {"queue": "default"},
        },
        "stale-ticket-notification": {
            "task": "workers.tasks.notification_tasks.notify_stale_tickets",
            "schedule": 1800.0,  # Every 30 minutes
            "options": {"queue": "default"},
        },
    },
)

# Auto-discover tasks from workers/tasks/ package
app.autodiscover_tasks(["workers.tasks"])
