import argparse
import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from tortoise import Tortoise

from app.models.admin import AuditLog
from app.settings import settings


def serialize(value):
    return value.isoformat() if isinstance(value, datetime) else value


async def main() -> None:
    parser = argparse.ArgumentParser(description="Back up and delete old audit logs; dry-run by default.")
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup-dir")
    args = parser.parse_args()
    if args.days < 1:
        raise ValueError("--days must be at least 1")
    if args.apply and not args.backup_dir:
        raise ValueError("--backup-dir is required with --apply")

    await Tortoise.init(config=settings.TORTOISE_ORM)
    try:
        query = AuditLog.filter(created_at__lt=datetime.now() - timedelta(days=args.days))
        count = await query.count()
        print(f"Audit logs eligible for cleanup: {count}")
        if not args.apply or not count:
            print("Dry-run only; no rows deleted.")
            return

        backup_dir = Path(args.backup_dir).resolve()
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"audit-log-{datetime.now():%Y%m%d-%H%M%S}.jsonl"
        with os.fdopen(
            os.open(backup_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w", encoding="utf-8"
        ) as backup_file:
            for row in await query.order_by("id").values():
                backup_file.write(json.dumps(row, ensure_ascii=False, default=serialize) + "\n")
        deleted = await query.delete()
        print(f"Backed up to {backup_path}; deleted {deleted} rows.")
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
