"""OpenAI: download a CI artifact on the server, verify and stage it without activating.

stdin JSON: root, source_commit, artifact_url (short-lived), artifact_sha256.
No credentials, signed URLs or production data are written into the receipt.
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tarfile
import urllib.parse
import urllib.request
import zipfile

data = json.load(sys.stdin)
root = Path(data["root"]).resolve()
assert root != Path("/") and (root / "compose.json").is_file()
commit = data["source_commit"]
assert len(commit) == 40 and all(c in "0123456789abcdef" for c in commit)
url = urllib.parse.urlsplit(data["artifact_url"])
assert url.scheme == "https" and not url.username and not url.password
stage = root / "releases" / ("web-" + commit[:12])
stage.mkdir(parents=True, exist_ok=False)
archive = stage / "artifact.zip"
with urllib.request.urlopen(data["artifact_url"], timeout=45) as response, archive.open("wb") as out:
    shutil.copyfileobj(response, out)
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
assert digest == data["artifact_sha256"].removeprefix("sha256:"), "Artifact digest mismatch"
allowed = {"SOURCE_COMMIT", "SHA256SUMS", "catalog.sha256", "web-standalone.tar.gz"}
with zipfile.ZipFile(archive) as bundle:
    assert set(bundle.namelist()) == allowed
    bundle.extractall(stage)
assert (stage / "SOURCE_COMMIT").read_text().strip() == commit
expected = (stage / "SHA256SUMS").read_text().split()[0]
with (stage / "web-standalone.tar.gz").open("rb") as inp:
    actual = hashlib.file_digest(inp, "sha256").hexdigest() if hasattr(hashlib, "file_digest") else hashlib.sha256(inp.read()).hexdigest()
assert expected == actual, "Runtime digest mismatch"
runtime = stage / "runtime"
runtime.mkdir()
with tarfile.open(stage / "web-standalone.tar.gz") as tar:
    for member in tar.getmembers():
        target = (runtime / member.name).resolve()
        assert target.is_relative_to(runtime), "Archive escapes staging"
        assert not (member.isdev() or member.isfifo())
        if member.issym():
            assert (target.parent / member.linkname).resolve().is_relative_to(runtime)
        if member.islnk():
            assert (runtime / member.linkname).resolve().is_relative_to(runtime)
    tar.extractall(runtime)
assert (runtime / "apps/web/server.js").is_file()
record = {"web_commit": commit, "archive_sha256": actual, "artifact_sha256": digest, "runtime": str(runtime)}
(stage / "STAGED.json").write_text(json.dumps(record, indent=2))
print(json.dumps(record))
