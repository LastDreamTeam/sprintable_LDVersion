"""OpenAI: explicit, reversible activation of one self-hosted Sprintable release.

Only touches compose.json's backend image and runtime/web. No schema migration,
data deletion, global Docker prune, proxy changes, Hermes or MCP restarts.
Requires an independently verified DB backup. See README for options/rollback.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import pwd
import shutil
import subprocess
import time
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument("--root", required=True)
parser.add_argument("--image")
parser.add_argument("--expected-current-image-id")
parser.add_argument("--backend-commit")
parser.add_argument("--web-stage")
parser.add_argument("--backup-verified")
parser.add_argument("--rollback")
args = parser.parse_args()
root = Path(args.root).resolve()
assert root != Path("/") and (root / "compose.json").is_file()
if not args.rollback:
    assert (root / "runtime/web/apps/web/server.js").is_file()
os.umask(0o077)
def output(command):
    return subprocess.check_output(command, text=True).strip()
def run(command):
    subprocess.run(command, check=True)
def healthy():
    for _ in range(45):
        try:
            for url in ("http://127.0.0.1:32800/api/v2/health", "http://127.0.0.1:33108/login"):
                with urllib.request.urlopen(url, timeout=2) as response:
                    assert response.status == 200
            return
        except Exception:
            time.sleep(1)
    raise RuntimeError("Release health failed")
def backend_up():
    run(["docker", "compose", "-f", str(root / "compose.json"), "up", "-d", "--no-deps", "backend"])
def protected_state():
    return {
        "hermes_pid": output(["systemctl", "show", "hermes-gateway.service", "-p", "MainPID", "--value"]),
        "mcp_id": output(["docker", "inspect", "-f", "{{.Id}}", "ld-sprintable-mcp"]),
        "edge_id": output(["docker", "inspect", "-f", "{{.Id}}", "ld-sprintable-edge"]),
        "postgres_id": output(["docker", "inspect", "-f", "{{.Id}}", "ld-sprintable-postgres"]),
    }
def rollback(backup):
    assert backup.parent == root / "backups" and backup.name.startswith("release-")
    record = json.loads((backup / "BEFORE.json").read_text())
    run(["systemctl", "stop", "ld-sprintable-web.service"])
    if (backup / "web").exists():
        failed = backup / ("failed-web-" + str(time.time_ns()))
        if (root / "runtime/web").exists():
            (root / "runtime/web").rename(failed)
        (backup / "web").rename(root / "runtime/web")
    shutil.copy2(backup / "compose.json", root / "compose.json")
    backend_up()
    run(["systemctl", "start", "ld-sprintable-web.service"])
    healthy()
    assert protected_state() == record["protected"]
    restored = record.get("previous_deployment") or {
        "new_image": record["previous_image"], "source_commits": "not_recorded_for_legacy_release",
    }
    restored.update({"status": "rolled_back_health_ok", "rollback_receipt": str(backup)})
    (root / "config/DEPLOYMENT.json").write_text(json.dumps(restored, indent=2))
    print(json.dumps({"rolled_back": str(backup), "database_and_uploads_untouched": True}))
if args.rollback:
    rollback(Path(args.rollback).resolve())
    raise SystemExit(0)
assert all((args.image, args.expected_current_image_id, args.backend_commit, args.web_stage, args.backup_verified))
verified = Path(args.backup_verified).resolve()
assert verified.is_relative_to(root / "backups")
assert json.loads((verified / "VALIDATION.json").read_text())["db_restore_verified"] is True
stage = Path(args.web_stage).resolve()
assert stage.is_relative_to(root / "releases") and stage.is_dir()
staged = json.loads((stage / "STAGED.json").read_text())
assert Path(staged["runtime"]).resolve() == stage / "runtime"
assert output(["docker", "inspect", "-f", "{{.Image}}", "ld-sprintable-backend"]) == args.expected_current_image_id
image = json.loads(output(["docker", "image", "inspect", args.image]))[0]
assert image["Config"]["Labels"]["org.opencontainers.image.revision"] == args.backend_commit
compose = json.loads((root / "compose.json").read_text())
assert compose["services"]["backend"]["container_name"] == "ld-sprintable-backend"
stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backup = root / "backups" / ("release-" + stamp)
backup.mkdir(mode=0o700)
shutil.copy2(root / "compose.json", backup / "compose.json")
record = {"protected": protected_state(), "previous_image": args.expected_current_image_id,
          "web_commit": staged["web_commit"], "backend_commit": args.backend_commit,
          "new_image": image["Id"], "db_backup": str(verified)}
deployment = root / "config/DEPLOYMENT.json"
record["previous_deployment"] = json.loads(deployment.read_text()) if deployment.exists() else None
(backup / "BEFORE.json").write_text(json.dumps(record, indent=2))
account = pwd.getpwnam("sprintable-web")
# OpenAI: systemd ReadWritePaths must exist before the sandbox is created.
# Standalone CI archives need not contain Next's lazily created runtime cache.
cache = stage / "runtime/apps/web/.next/cache"
assert cache.resolve().is_relative_to(stage / "runtime")
cache.mkdir(mode=0o750, parents=True, exist_ok=True)
run(["chown", "-R", str(account.pw_uid) + ":" + str(account.pw_gid), str(stage / "runtime")])
try:
    compose["services"]["backend"]["image"] = args.image
    compose["services"]["backend"]["pull_policy"] = "never"
    (root / "compose.json").write_text(json.dumps(compose, indent=2))
    backend_up()
    run(["systemctl", "stop", "ld-sprintable-web.service"])
    (root / "runtime/web").rename(backup / "web")
    (stage / "runtime").rename(root / "runtime/web")
    run(["systemctl", "start", "ld-sprintable-web.service"])
    healthy()
    assert protected_state() == record["protected"]
    record["backup"] = str(backup)
    record["status"] = "activated_health_ok_pending_functional_acceptance"
    (backup / "APPLIED.json").write_text(json.dumps(record, indent=2))
    (root / "config/DEPLOYMENT.json").write_text(json.dumps(record, indent=2))
    print(json.dumps(record))
except Exception:
    rollback(backup)
    raise
