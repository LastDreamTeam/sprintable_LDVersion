"""Invoke only Sprintable's native seven-day soft-deleted-asset collector.

No mtime deletion, orphan sweep, model calls, or business-relevance classifier.
The scheduler and this HTTP wrapper are deployment files, not upstream code.
"""
import json
import math
import os
import shutil
import urllib.error
import urllib.request


def main():
    secret = os.environ.get("CRON_SECRET", "").strip()
    if not secret:
        raise RuntimeError("Maintenance credential is missing")
    request = urllib.request.Request(
        "http://127.0.0.1:32800/api/v2/internal/cron/assets-grace-hard-delete",
        headers={"Authorization": "Bearer " + secret},
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"Native asset collector returned HTTP {error.code}") from None
    data = result.get("data")
    if not isinstance(data, dict) or not all(
        isinstance(data.get(k), int) for k in ("hard_deleted", "blob_delete_failed")
    ):
        raise RuntimeError("Unexpected native collector response")
    disk = shutil.disk_usage("/srv/sprintable")
    used_percent = math.ceil(disk.used * 100 / (disk.used + disk.free))
    output = {
        "native_asset_gc": data,
        "filesystem_used_percent": used_percent,
        "filesystem_available_bytes": disk.free,
        "filesystem_warning": disk.free < 8 * 1024**3 or used_percent >= 85,
        "note": "Disk warning is journal-only; not an email or chat notification",
    }
    print(json.dumps(output))
    if data["blob_delete_failed"]:
        raise RuntimeError("Some already-deleted assets could not be reclaimed")


if __name__ == "__main__":
    main()
