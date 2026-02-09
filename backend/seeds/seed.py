"""Database seed script.

Usage: python -m seeds.seed

Seeds the database with:
- 15 permissions
- 5 roles with role-permission mappings
- 6 users (1 admin + 1 per role)
- 2 sources
- 10 customers with varied data
- 50+ events across customers
- 3 metric definitions
- Initial metric values for customers
"""

import asyncio
import hashlib
import random
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_session
from app.infrastructure.models import (
    CustomerMetricHistoryModel,
    CustomerMetricModel,
    CustomerModel,
    EventModel,
    MetricDefinitionModel,
    PermissionModel,
    RoleModel,
    RolePermissionModel,
    SourceModel,
    UserModel,
)
from app.infrastructure.security import hash_password

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALL_PERMISSIONS = [
    ("customers.read", "View customer list and detail profiles"),
    ("customers.manage", "Create, update, and soft-delete customers"),
    ("customers.export", "Export customer data (CSV, reports)"),
    ("events.read", "View customer activity timeline"),
    ("metrics.read", "View computed metrics for customers"),
    ("metrics.catalog.read", "View metrics catalog definitions"),
    ("metrics.catalog.manage", "Add/edit/remove metric definitions"),
    ("sources.read", "View registered sources and their status"),
    ("sources.manage", "Register, deactivate, rotate keys"),
    ("users.read", "View user list and role assignments"),
    ("users.manage", "Create, update, deactivate users and assign roles"),
    ("roles.read", "View roles and their permission assignments"),
    ("roles.manage", "Create, update, delete roles and assign/remove permissions"),
    ("chat.use", "Send messages to the AI agent"),
    ("system.health.read", "View system health and diagnostics"),
]

ROLES_CONFIG = [
    {
        "name": "sales",
        "display_name": "Sales",
        "description": "Customer contracts, activity, and health scores for deals/renewals.",
        "permissions": ["customers.read", "events.read", "metrics.read", "chat.use"],
    },
    {
        "name": "support",
        "display_name": "Support",
        "description": "Tickets and customer context for better service.",
        "permissions": ["customers.read", "events.read", "metrics.read", "chat.use"],
    },
    {
        "name": "cs_manager",
        "display_name": "Customer Success Manager",
        "description": "Full read access to all customer data. Can export.",
        "permissions": [
            "customers.read",
            "customers.export",
            "events.read",
            "metrics.read",
            "metrics.catalog.read",
            "chat.use",
        ],
    },
    {
        "name": "ops",
        "display_name": "Operations",
        "description": "System health, data quality, and ingestion pipeline monitoring.",
        "permissions": [
            "customers.read",
            "events.read",
            "metrics.read",
            "metrics.catalog.read",
            "sources.read",
            "chat.use",
            "system.health.read",
        ],
    },
    {
        "name": "admin",
        "display_name": "Administrator",
        "description": "Full platform access. Only role that can manage users and sources.",
        "permissions": [code for code, _ in ALL_PERMISSIONS],
    },
]

USERS_CONFIG = [
    {"email": "admin@customer360.com", "full_name": "Admin User", "role": "admin"},
    {"email": "sarah.sales@customer360.com",
        "full_name": "Sarah Sales", "role": "sales"},
    {"email": "tom.support@customer360.com",
        "full_name": "Tom Support", "role": "support"},
    {"email": "maria.csm@customer360.com",
        "full_name": "Maria CSM", "role": "cs_manager"},
    {"email": "dave.ops@customer360.com", "full_name": "Dave Ops", "role": "ops"},
    {"email": "alice.admin@customer360.com",
        "full_name": "Alice Admin", "role": "admin"},
]

SOURCES_CONFIG = [
    {
        "name": "salesforce",
        "description": "Salesforce CRM integration",
        "token": "sf-token-dev-123",
    },
    {
        "name": "zendesk",
        "description": "Zendesk support platform integration",
        "token": "zd-token-dev-456",
    },
]

CUSTOMERS_CONFIG = [
    {
        "company_name": "Acme Corp",
        "contact_name": "John Smith",
        "email": "john@acmecorp.com",
        "phone": "+1-555-0101",
        "industry": "Manufacturing",
        "contract_value": Decimal("125000.00"),
        "signup_date": date(2024, 1, 15),
    },
    {
        "company_name": "TechFlow Inc",
        "contact_name": "Emma Wilson",
        "email": "emma@techflow.io",
        "phone": "+1-555-0102",
        "industry": "Technology",
        "contract_value": Decimal("89000.00"),
        "signup_date": date(2024, 3, 22),
    },
    {
        "company_name": "DataPrime Solutions",
        "contact_name": "Michael Chen",
        "email": "m.chen@dataprime.com",
        "phone": "+1-555-0103",
        "industry": "Data Analytics",
        "contract_value": Decimal("210000.00"),
        "signup_date": date(2023, 11, 5),
    },
    {
        "company_name": "CloudNine Systems",
        "contact_name": "Sarah Johnson",
        "email": "sarah.j@cloudnine.dev",
        "phone": "+1-555-0104",
        "industry": "Cloud Infrastructure",
        "contract_value": Decimal("175000.00"),
        "signup_date": date(2024, 6, 10),
    },
    {
        "company_name": "QuantumLeap AI",
        "contact_name": "David Park",
        "email": "dpark@quantumleap.ai",
        "phone": "+1-555-0105",
        "industry": "Artificial Intelligence",
        "contract_value": Decimal("320000.00"),
        "signup_date": date(2024, 2, 28),
    },
    {
        "company_name": "NorthStar Analytics",
        "contact_name": "Lisa Rodriguez",
        "email": "lisa@northstaranalytics.com",
        "phone": "+1-555-0106",
        "industry": "Business Intelligence",
        "contract_value": Decimal("95000.00"),
        "signup_date": date(2024, 5, 1),
    },
    {
        "company_name": "BlueWave Tech",
        "contact_name": "James Lee",
        "email": "jlee@bluewave.tech",
        "phone": "+1-555-0107",
        "industry": "Fintech",
        "contract_value": Decimal("150000.00"),
        "signup_date": date(2023, 9, 18),
    },
    {
        "company_name": "SilverLine Solutions",
        "contact_name": "Anna Kowalski",
        "email": "anna.k@silverline.com",
        "phone": "+1-555-0108",
        "industry": "Consulting",
        "contract_value": Decimal("68000.00"),
        "signup_date": date(2024, 7, 12),
    },
    {
        "company_name": "EverGreen Digital",
        "contact_name": "Robert Taylor",
        "email": "rtaylor@evergreendigital.com",
        "phone": "+1-555-0109",
        "industry": "Digital Marketing",
        "contract_value": Decimal("42000.00"),
        "signup_date": date(2024, 4, 3),
    },
    {
        "company_name": "RapidScale Inc",
        "contact_name": "Jennifer Wu",
        "email": "jwu@rapidscale.io",
        "phone": "+1-555-0110",
        "industry": "E-commerce",
        "contract_value": Decimal("198000.00"),
        "signup_date": date(2023, 12, 20),
    },
]

# Event templates for generating realistic event data
EVENT_TEMPLATES = {
    "support_ticket": [
        ("Login issues reported",
         "Customer reported intermittent login failures affecting multiple users"),
        ("Data export timeout", "Large dataset export timing out after 30 seconds"),
        ("API rate limiting concern",
         "Customer hitting rate limits during peak usage hours"),
        ("Billing discrepancy inquiry",
         "Customer flagged a discrepancy in the latest invoice"),
        ("Feature request: bulk import",
         "Customer requested bulk data import functionality"),
        ("Integration error with Slack",
         "Webhook integration with Slack returning 500 errors"),
        ("Password reset not working", "Password reset emails not being delivered"),
        ("Dashboard loading slowly", "Main dashboard takes over 10 seconds to load"),
        ("Permission configuration help",
         "Need assistance setting up team role-based access"),
        ("Data sync delay", "CRM data synchronization delayed by more than 2 hours"),
    ],
    "meeting": [
        ("Quarterly business review",
         "QBR with key stakeholders to review adoption and ROI metrics"),
        ("Onboarding kickoff call",
         "Initial kickoff meeting to plan onboarding timeline and milestones"),
        ("Feature demo session", "Demonstrated upcoming Q2 features and gathered feedback"),
        ("Escalation review call",
         "Reviewed open escalation tickets and agreed on resolution timelines"),
        ("Renewal discussion", "Discussed contract renewal terms and potential expansion"),
        ("Technical architecture review",
         "Deep dive into integration architecture and data flow"),
        ("Executive sponsor check-in",
         "Monthly check-in with VP of Engineering on strategic alignment"),
        ("Training session follow-up",
         "Follow-up on advanced training topics requested by the team"),
    ],
    "usage_event": [
        ("High API usage spike", "API call volume increased 300% over the past week"),
        ("New team members onboarded", "5 new users added to the platform this month"),
        ("Dashboard customization", "Customer created 12 custom dashboards this quarter"),
        ("Report generation peak", "Generated 45 reports in the last 7 days"),
        ("New integration activated",
         "Customer activated the Salesforce bi-directional sync"),
        ("Feature adoption milestone",
         "80% of licensed users now active on the platform"),
    ],
    "contract_renewal": [
        ("Annual renewal processed", "12-month contract renewed with standard terms"),
        ("Multi-year renewal signed",
         "Customer signed a 24-month renewal with 10% discount"),
        ("Expansion deal closed", "Added 50 additional seats and premium support tier"),
        ("Renewal at risk - pricing concern",
         "Customer expressed concern about pricing increase at renewal"),
    ],
    "onboarding": [
        ("Technical setup completed",
         "SSO, API keys, and webhook endpoints configured successfully"),
        ("Data migration started",
         "Historical data migration from legacy system initiated"),
        ("User training completed", "All 25 initial users completed onboarding training"),
        ("Go-live confirmed", "Production environment validated and customer went live"),
        ("First integration test passed",
         "End-to-end integration test with customer systems passed"),
    ],
}

METRIC_DEFINITIONS = [
    {
        "name": "support_tickets_last_30d",
        "display_name": "Support Tickets (Last 30 Days)",
        "description": "Number of support tickets created in the last 30 days",
        "unit": "count",
        "value_type": "integer",
    },
    {
        "name": "health_score",
        "display_name": "Health Score",
        "description": "Composite customer health score from 0 to 100",
        "unit": "score",
        "value_type": "integer",
    },
    {
        "name": "days_since_last_contact",
        "display_name": "Days Since Last Contact",
        "description": "Number of days since the last interaction with the customer",
        "unit": "days",
        "value_type": "integer",
    },
]


# ---------------------------------------------------------------------------
# Seed Functions
# ---------------------------------------------------------------------------


def _hash_source_token(token: str) -> str:
    """Hash a source API token using SHA256 (consistent with ingestion service)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _random_dt_in_last_n_days(n: int) -> datetime:
    """Return a timezone-aware datetime randomly placed within the last n days."""
    offset_seconds = random.randint(0, n * 86400)
    return datetime.now(UTC) - timedelta(seconds=offset_seconds)


async def _seed_permissions(session: AsyncSession) -> dict[str, PermissionModel]:
    """Seed the 15 permissions. Returns a code->model mapping."""
    perm_map: dict[str, PermissionModel] = {}
    for code, description in ALL_PERMISSIONS:
        perm = PermissionModel(id=uuid4(), code=code, description=description)
        session.add(perm)
        perm_map[code] = perm
    await session.flush()
    print(f"  [+] Seeded {len(perm_map)} permissions")
    return perm_map


async def _seed_roles(
    session: AsyncSession,
    perm_map: dict[str, PermissionModel],
) -> dict[str, RoleModel]:
    """Seed the 5 roles and their permission mappings."""
    role_map: dict[str, RoleModel] = {}
    rp_count = 0

    for cfg in ROLES_CONFIG:
        role = RoleModel(
            id=uuid4(),
            name=cfg["name"],
            display_name=cfg["display_name"],
            description=cfg["description"],
            is_system=True,
        )
        session.add(role)
        role_map[cfg["name"]] = role
        await session.flush()

        for perm_code in cfg["permissions"]:
            rp = RolePermissionModel(
                role_id=role.id,
                permission_id=perm_map[perm_code].id,
            )
            session.add(rp)
            rp_count += 1

    await session.flush()
    print(
        f"  [+] Seeded {len(role_map)} roles with {rp_count} role-permission mappings")
    return role_map


async def _seed_users(
    session: AsyncSession,
    role_map: dict[str, RoleModel],
) -> list[UserModel]:
    """Seed the 6 users (password: 'Password123' for all)."""
    pw_hash = hash_password("Password123")
    users: list[UserModel] = []

    for cfg in USERS_CONFIG:
        user = UserModel(
            id=uuid4(),
            email=cfg["email"],
            full_name=cfg["full_name"],
            password_hash=pw_hash,
            role_id=role_map[cfg["role"]].id,
            is_active=True,
        )
        session.add(user)
        users.append(user)

    await session.flush()
    print(f"  [+] Seeded {len(users)} users")
    return users


async def _seed_sources(session: AsyncSession) -> dict[str, SourceModel]:
    """Seed the 2 external data sources."""
    source_map: dict[str, SourceModel] = {}

    for cfg in SOURCES_CONFIG:
        source = SourceModel(
            id=uuid4(),
            name=cfg["name"],
            description=cfg["description"],
            api_token_hash=_hash_source_token(cfg["token"]),
            is_active=True,
        )
        session.add(source)
        source_map[cfg["name"]] = source

    await session.flush()
    print(f"  [+] Seeded {len(source_map)} sources")
    print("      Salesforce token: sf-token-dev-123")
    print("      Zendesk token:    zd-token-dev-456")
    return source_map


async def _seed_customers(
    session: AsyncSession,
    source_map: dict[str, SourceModel],
) -> list[CustomerModel]:
    """Seed 10 customers with realistic company data."""
    customers: list[CustomerModel] = []
    source_names = list(source_map.keys())

    for i, cfg in enumerate(CUSTOMERS_CONFIG):
        # Alternate source assignment: first 5 from salesforce, next 5 from zendesk
        source_name = source_names[0] if i < 5 else source_names[1]
        customer = CustomerModel(
            id=uuid4(),
            company_name=cfg["company_name"],
            contact_name=cfg["contact_name"],
            email=cfg["email"],
            phone=cfg["phone"],
            industry=cfg["industry"],
            contract_value=cfg["contract_value"],
            currency_code="USD",
            signup_date=cfg["signup_date"],
            source_id=source_map[source_name].id,
        )
        session.add(customer)
        customers.append(customer)

    await session.flush()
    print(f"  [+] Seeded {len(customers)} customers")
    return customers


async def _seed_events(
    session: AsyncSession,
    customers: list[CustomerModel],
    source_map: dict[str, SourceModel],
) -> list[EventModel]:
    """Seed 50+ events spread across customers and the last 90 days."""
    events: list[EventModel] = []
    source_ids = [s.id for s in source_map.values()]

    # Distribute events: 5-8 events per customer to hit 50+
    for customer in customers:
        num_events = random.randint(5, 8)
        event_types = list(EVENT_TEMPLATES.keys())

        for _ in range(num_events):
            event_type = random.choice(event_types)
            templates = EVENT_TEMPLATES[event_type]
            title, description = random.choice(templates)

            event = EventModel(
                id=uuid4(),
                customer_id=customer.id,
                source_id=random.choice(source_ids),
                event_type=event_type,
                title=title,
                description=description,
                occurred_at=_random_dt_in_last_n_days(90),
                data={"source": "seed", "auto_generated": True},
            )
            session.add(event)
            events.append(event)

    await session.flush()
    print(
        f"  [+] Seeded {len(events)} events across {len(customers)} customers")
    return events


async def _seed_metric_definitions(
    session: AsyncSession,
) -> dict[str, MetricDefinitionModel]:
    """Seed the 3 metric definitions."""
    metric_def_map: dict[str, MetricDefinitionModel] = {}

    for cfg in METRIC_DEFINITIONS:
        md = MetricDefinitionModel(
            id=uuid4(),
            name=cfg["name"],
            display_name=cfg["display_name"],
            description=cfg["description"],
            unit=cfg["unit"],
            value_type=cfg["value_type"],
        )
        session.add(md)
        metric_def_map[cfg["name"]] = md

    await session.flush()
    print(f"  [+] Seeded {len(metric_def_map)} metric definitions")
    return metric_def_map


async def _seed_customer_metrics(
    session: AsyncSession,
    customers: list[CustomerModel],
    events: list[EventModel],
    metric_def_map: dict[str, MetricDefinitionModel],
) -> int:
    """Compute and seed initial metric values for each customer.

    - support_tickets_last_30d: count of support_ticket events in last 30 days
    - health_score: composite 0-100 based on engagement signals
    - days_since_last_contact: days since most recent event
    """
    now = datetime.now(UTC)
    thirty_days_ago = now - timedelta(days=30)
    metric_count = 0

    for customer in customers:
        # Gather this customer's events
        customer_events = [e for e in events if e.customer_id == customer.id]

        # --- support_tickets_last_30d ---
        recent_tickets = sum(
            1 for e in customer_events if e.event_type == "support_ticket" and e.occurred_at >= thirty_days_ago
        )
        cm_tickets = CustomerMetricModel(
            id=uuid4(),
            customer_id=customer.id,
            metric_definition_id=metric_def_map["support_tickets_last_30d"].id,
            metric_value=Decimal(recent_tickets),
            note="Seeded: auto-computed from seed events",
        )
        session.add(cm_tickets)
        metric_count += 1

        # Also add a history entry
        session.add(
            CustomerMetricHistoryModel(
                id=uuid4(),
                customer_id=customer.id,
                metric_definition_id=metric_def_map["support_tickets_last_30d"].id,
                metric_value=Decimal(recent_tickets),
                recorded_at=now,
            )
        )

        # --- health_score ---
        # Simple heuristic:
        #   base score = 70
        #   + 10 if meetings in last 30d
        #   + 10 if usage_events in last 30d
        #   - 5 per support ticket in last 30d (floor 0)
        #   - 10 if no events in last 14d
        base = 70
        has_meetings = any(e.event_type == "meeting" and e.occurred_at >=
                           thirty_days_ago for e in customer_events)
        has_usage = any(e.event_type == "usage_event" and e.occurred_at >=
                        thirty_days_ago for e in customer_events)
        fourteen_days_ago = now - timedelta(days=14)
        has_recent = any(
            e.occurred_at >= fourteen_days_ago for e in customer_events)

        health = base
        if has_meetings:
            health += 10
        if has_usage:
            health += 10
        health -= recent_tickets * 5
        if not has_recent:
            health -= 10
        health = max(0, min(100, health))

        cm_health = CustomerMetricModel(
            id=uuid4(),
            customer_id=customer.id,
            metric_definition_id=metric_def_map["health_score"].id,
            metric_value=Decimal(health),
            note="Seeded: heuristic from seed events",
        )
        session.add(cm_health)
        metric_count += 1

        session.add(
            CustomerMetricHistoryModel(
                id=uuid4(),
                customer_id=customer.id,
                metric_definition_id=metric_def_map["health_score"].id,
                metric_value=Decimal(health),
                recorded_at=now,
            )
        )

        # --- days_since_last_contact ---
        if customer_events:
            latest = max(e.occurred_at for e in customer_events)
            days_since = (now - latest).days
        else:
            days_since = 999

        cm_days = CustomerMetricModel(
            id=uuid4(),
            customer_id=customer.id,
            metric_definition_id=metric_def_map["days_since_last_contact"].id,
            metric_value=Decimal(days_since),
            note="Seeded: computed from most recent seed event",
        )
        session.add(cm_days)
        metric_count += 1

        session.add(
            CustomerMetricHistoryModel(
                id=uuid4(),
                customer_id=customer.id,
                metric_definition_id=metric_def_map["days_since_last_contact"].id,
                metric_value=Decimal(days_since),
                recorded_at=now,
            )
        )

    await session.flush()
    print(
        f"  [+] Seeded {metric_count} customer metric values (3 per customer)")
    print(f"  [+] Seeded {metric_count} customer metric history entries")
    return metric_count


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def seed_database() -> None:
    """Run the full seed process inside a single transaction.

    Idempotent: skips if permissions are already present.
    """
    print("=" * 60)
    print("  Customer 360 - Database Seed")
    print("=" * 60)

    async for session in get_session():
        # Idempotency check: if any permissions exist, skip
        result = await session.execute(select(PermissionModel).limit(1))
        existing = result.scalar_one_or_none()
        if existing is not None:
            print(
                "\n  [!] Database already seeded (permissions exist). Skipping.")
            print("=" * 60)
            return

        print("\n  Seeding database...\n")

        # 1. Permissions
        perm_map = await _seed_permissions(session)

        # 2. Roles + role-permission mappings
        role_map = await _seed_roles(session, perm_map)

        # 3. Users
        users = await _seed_users(session, role_map)

        # 4. Sources
        source_map = await _seed_sources(session)

        # 5. Customers
        customers = await _seed_customers(session, source_map)

        # 6. Events
        events = await _seed_events(session, customers, source_map)

        # 7. Metric definitions
        metric_def_map = await _seed_metric_definitions(session)

        # 8. Customer metrics (computed from events)
        await _seed_customer_metrics(session, customers, events, metric_def_map)

        # The session context manager in get_session() will commit
        print("\n  Seed Summary:")
        print(f"    Permissions:         {len(perm_map)}")
        print(f"    Roles:               {len(role_map)}")
        print(f"    Users:               {len(users)}")
        print(f"    Sources:             {len(source_map)}")
        print(f"    Customers:           {len(customers)}")
        print(f"    Events:              {len(events)}")
        print(f"    Metric definitions:  {len(metric_def_map)}")
        print(f"    Customer metrics:    {len(customers) * 3}")
        print(f"    Metric history:      {len(customers) * 3}")
        print("\n  Database seeded successfully!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_database())
