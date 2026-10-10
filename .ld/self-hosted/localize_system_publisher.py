"""OpenAI: opt-in maintenance of one legacy built-in system publisher name.

The normal member API intentionally protects system identities. This operator-only
script changes no permissions or identity: exact org/id/runtime/default-name guards,
verified DB backup, private before/after receipt, and compare-and-set update.
Custom names are never overwritten. Without --apply this only inspects the target.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import uuid

parser = argparse.ArgumentParser()
parser.add_argument("--root", required=True)
parser.add_argument("--org-id", required=True, type=uuid.UUID)
parser.add_argument("--member-id", required=True, type=uuid.UUID)
parser.add_argument("--locale", required=True, choices=("zh", "en"))
parser.add_argument("--backup-verified")
parser.add_argument("--apply", action="store_true")
args = parser.parse_args()
root = Path(args.root).resolve()
assert root != Path("/") and (root / "compose.json").is_file()
names = {"zh": "系统通知", "en": "System notifications"}
target_name = names[args.locale]
predicate = (f"id='{args.member_id}' AND org_id='{args.org_id}' "
             "AND type='agent' AND runtime_type='system-publisher' "
             "AND deleted_at IS NULL AND is_active=true")

def query(sql):
    result = subprocess.check_output([
        "docker", "exec", "ld-sprintable-postgres", "psql", "-X", "-p", "35432",
        "-U", "sprintable", "-d", "sprintable", "-v", "ON_ERROR_STOP=1", "-Atc", sql,
    ], text=True)
    return json.loads(result)

before = query("SELECT coalesce(json_agg(x),'[]'::json) FROM "
               "(SELECT id,org_id,name,runtime_type,updated_at FROM members WHERE " + predicate + ") x")
assert len(before) == 1, "Expected exactly one active built-in publisher"
if before[0]["name"] == target_name:
    print(json.dumps({"changed": False, "already_localized": True}))
    raise SystemExit(0)
assert before[0]["name"] == "시스템 발행", "Preserve custom or already localized names"
if not args.apply:
    print(json.dumps({"dry_run": True, "before": before, "new_name": target_name}, ensure_ascii=False))
    raise SystemExit(0)
verified = Path(args.backup_verified or "").resolve()
assert verified.is_relative_to(root / "backups")
assert json.loads((verified / "VALIDATION.json").read_text())["db_restore_verified"] is True
os.umask(0o077)
stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
receipt = root / "backups" / ("publisher-locale-" + stamp + ".json")
record = {"before": before, "target_name": target_name, "db_backup": str(verified), "status": "prepared"}
with receipt.open("x", encoding="utf-8") as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
after = query("WITH changed AS (UPDATE members SET name='" + target_name +
              "',updated_at=now() WHERE " + predicate + " AND name='시스템 발행' "
              "RETURNING id,org_id,name,runtime_type,updated_at) SELECT coalesce(json_agg(changed),'[]'::json) FROM changed")
assert len(after) == 1, "Concurrent change: no matching default-name row was updated"
record.update({"after": after, "status": "applied"})
receipt.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"changed": True, "name": target_name, "receipt": str(receipt)}, ensure_ascii=False))
