#!/usr/bin/env python3
"""
Simulate real-time event ingestion by sending dummy webhook payloads
to POST /hooks/ingest every 5 seconds.

Usage:
    python scripts/simulate_events.py
    python scripts/simulate_events.py --interval 10  # every 10 seconds
    python scripts/simulate_events.py --url http://localhost:8000
"""

import argparse
import random
import time
from datetime import datetime, timezone

import requests

SOURCES = [
    {"name": "salesforce", "token": "sf-token-dev-123"},
    {"name": "zendesk", "token": "zd-token-dev-456"},
]

CUSTOMERS = [
    "Acme Corp",
    "TechFlow Inc",
    "DataPrime Solutions",
    "CloudNine Systems",
    "QuantumLeap AI",
    "NorthStar Analytics",
    "BlueWave Tech",
    "SilverLine Solutions",
    "EverGreen Digital",
    "RapidScale Inc",
]

EVENT_TEMPLATES = [
    # support_ticket events
    {
        "event_type": "support_ticket",
        "titles": [
            "Login issues reported",
            "API timeout on export endpoint",
            "Dashboard not loading for some users",
            "SSO integration failing intermittently",
            "Data sync delay exceeding SLA",
            "Permission error on admin panel",
            "CSV export generating empty files",
            "Webhook delivery failures",
            "Search returning stale results",
            "Mobile app crashing on launch",
        ],
        "descriptions": [
            "Customer reported the issue affecting multiple users in their org.",
            "Intermittent failures observed during peak hours.",
            "Issue started after the latest platform update.",
            "Affecting a subset of users with specific browser versions.",
            "Customer escalated after initial workaround failed.",
        ],
        "data_variants": [
            {"priority": "high", "status": "open"},
            {"priority": "medium", "status": "open"},
            {"priority": "low", "status": "open"},
            {"priority": "high", "status": "in_progress"},
            {"priority": "critical", "status": "open", "escalated": True},
            {"priority": "medium", "status": "resolved", "resolution_time_hours": 4},
        ],
    },
    # meeting events
    {
        "event_type": "meeting",
        "titles": [
            "Quarterly business review",
            "Product roadmap walkthrough",
            "Onboarding kickoff call",
            "Technical deep-dive session",
            "Executive sponsor check-in",
            "Renewal discussion",
            "Feature request review",
            "Incident post-mortem",
            "Training session for new team members",
            "Integration planning call",
        ],
        "descriptions": [
            "Scheduled meeting with key stakeholders.",
            "Follow-up from previous action items.",
            "Customer requested a walkthrough of new features.",
            "Proactive check-in to discuss adoption progress.",
            "Review of outstanding issues and next steps.",
        ],
        "data_variants": [
            {"attendees": 3, "duration_minutes": 30, "outcome": "positive"},
            {"attendees": 5, "duration_minutes": 60, "outcome": "neutral"},
            {"attendees": 2, "duration_minutes": 15, "outcome": "positive"},
            {"attendees": 8, "duration_minutes": 90, "outcome": "action_items"},
            {"attendees": 4, "duration_minutes": 45, "outcome": "follow_up_needed"},
        ],
    },
    # usage_event events
    {
        "event_type": "usage_event",
        "titles": [
            "Daily active users spike",
            "New feature adopted by team",
            "API call volume increased",
            "Report generation usage up",
            "Dashboard views milestone reached",
            "Integration activated",
            "Bulk data import completed",
            "User invited 5 new team members",
            "Advanced search feature used",
            "Custom workflow created",
        ],
        "descriptions": [
            "Usage metrics recorded from platform telemetry.",
            "Notable change in adoption pattern detected.",
            "Customer expanding usage across departments.",
            "Automated usage tracking event.",
            "Significant engagement milestone.",
        ],
        "data_variants": [
            {"daily_active_users": random.randint(
                10, 200), "feature": "dashboard"},
            {"api_calls": random.randint(100, 5000), "feature": "api"},
            {"reports_generated": random.randint(
                1, 50), "feature": "reporting"},
            {"logins": random.randint(5, 100), "feature": "auth"},
            {"exports": random.randint(1, 20), "feature": "data_export"},
        ],
    },
    # contract_renewal events
    {
        "event_type": "contract_renewal",
        "titles": [
            "Annual contract renewal due",
            "Contract expansion discussion",
            "Renewal approved by procurement",
            "Multi-year deal signed",
            "Downgrade risk flagged",
        ],
        "descriptions": [
            "Contract renewal milestone triggered.",
            "Customer reviewing renewal terms.",
            "Sales team engaged for renewal process.",
        ],
        "data_variants": [
            {"contract_value": 50000, "term_months": 12, "status": "pending"},
            {"contract_value": 120000, "term_months": 24, "status": "approved"},
            {"contract_value": 30000, "term_months": 12, "status": "at_risk"},
            {"contract_value": 200000, "term_months": 36, "status": "signed"},
        ],
    },
    # onboarding events
    {
        "event_type": "onboarding",
        "titles": [
            "Onboarding started",
            "Initial setup completed",
            "First integration connected",
            "Team training completed",
            "Go-live milestone reached",
        ],
        "descriptions": [
            "Customer progressing through onboarding checklist.",
            "Key onboarding milestone achieved.",
            "Onboarding team recorded progress update.",
        ],
        "data_variants": [
            {"step": 1, "total_steps": 5, "completion_pct": 20},
            {"step": 3, "total_steps": 5, "completion_pct": 60},
            {"step": 5, "total_steps": 5, "completion_pct": 100},
        ],
    },
]


def generate_event() -> tuple[dict, str]:
    """Generate a random event payload and return (payload, token)."""
    source = random.choice(SOURCES)
    template = random.choice(EVENT_TEMPLATES)

    payload = {
        "event_type": template["event_type"],
        "customer_identifier": random.choice(CUSTOMERS),
        "title": random.choice(template["titles"]),
        "description": random.choice(template["descriptions"]),
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "data": random.choice(template["data_variants"]),
    }

    return payload, source["token"]


def send_event(base_url: str, payload: dict, token: str) -> None:
    """Send an event to the ingestion endpoint."""
    url = f"{base_url}/hooks/ingest"
    headers = {
        "Content-Type": "application/json",
        "X-Source-Token": token,
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        now = datetime.now().strftime("%H:%M:%S")

        if resp.status_code == 202:
            data = resp.json()
            print(
                f"[{now}] SENT  {payload['event_type']:20s} | "
                f"{payload['customer_identifier']:25s} | "
                f"{payload['title'][:40]:40s} | "
                f"id={data.get('event_id', '?')[:8]}"
            )
        else:
            print(
                f"[{now}] ERROR {resp.status_code} | {resp.text[:80]}"
            )
    except requests.exceptions.ConnectionError:
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] CONNECTION ERROR - is the backend running?")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Simulate real-time event ingestion")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Backend base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Seconds between events (default: 5)",
    )
    args = parser.parse_args()

    print(f"Simulating events -> {args.url}/hooks/ingest")
    print(f"Interval: {args.interval}s | Press Ctrl+C to stop")
    print("-" * 120)

    count = 0
    try:
        while True:
            payload, token = generate_event()
            send_event(args.url, payload, token)
            count += 1
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print(f"\nStopped. Sent {count} events.")


if __name__ == "__main__":
    main()
