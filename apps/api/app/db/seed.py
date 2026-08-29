"""
Seed script — loads all synthetic dev incidents from data/incidents/dev/*.json
into a SQLite dev database for local development.

Usage: python -m app.db.seed
"""
import json
import sys
from pathlib import Path

from app.schemas.payment import SyntheticIncident

INCIDENTS_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "incidents" / "dev"


def load_incidents() -> list[SyntheticIncident]:
    incidents: list[SyntheticIncident] = []
    files = sorted(INCIDENTS_DIR.glob("*.json"))
    if not files:
        print(f"No JSON files found in {INCIDENTS_DIR}", file=sys.stderr)
        sys.exit(1)
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            incident = SyntheticIncident.model_validate(data)
            incidents.append(incident)
        except Exception as e:
            print(f"ERROR loading {f.name}: {e}", file=sys.stderr)
            sys.exit(1)
    return incidents


def main() -> None:
    incidents = load_incidents()
    print(f"Loaded {len(incidents)} synthetic dev incidents:")
    for inc in incidents:
        print(
            f"  {inc.incident_id} | {inc.scenario:20s} | "
            f"expected={inc.expected_state.value:20s} | action={inc.expected_action.value}"
        )
    print("\nAll incidents validated successfully.")
    print("SYNTHETIC DATA ONLY — no real payment data, UTRs, or customer PII.")


if __name__ == "__main__":
    main()
