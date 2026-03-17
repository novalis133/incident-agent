"""Seed Gradient Knowledge Bases with runbooks and incident data.

Usage:
    python -m scripts.seed_kb
    python -m scripts.seed_kb --runbooks-only
    python -m scripts.seed_kb --incidents-only
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from incidentagent.knowledge.seed_data import seed_runbooks, seed_incidents


async def main(runbooks: bool = True, incidents: bool = True) -> None:
    if runbooks:
        count = await seed_runbooks()
        print(f"Uploaded {count} runbook(s)")

    if incidents:
        count = await seed_incidents()
        print(f"Uploaded {count} incident(s)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Gradient Knowledge Bases")
    parser.add_argument("--runbooks-only", action="store_true")
    parser.add_argument("--incidents-only", action="store_true")
    args = parser.parse_args()

    do_runbooks = not args.incidents_only
    do_incidents = not args.runbooks_only

    asyncio.run(main(runbooks=do_runbooks, incidents=do_incidents))
