"""OpenAI: verified Git checkout via codeload when GitHub's Git TLS route is unavailable.

stdin: destination, repository HTTPS URL, commit SHA, raw_commit_base64, tree SHA.
Rebuilds Git objects from the public archive, requires an exact original tree AND
commit hash match, then marks the commit as a shallow boundary. Origin stays normal
GitHub; future fetch/deepen uses ordinary Git. Never runs source or changes services.
"""
import base64
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import urllib.request

data = json.load(sys.stdin)
destination = Path(data["destination"]).resolve()
assert destination.name == "source" and destination.parent.name == "sprintable"
assert not destination.exists(), "Never overwrite an existing checkout"
repository = data["repository"]
assert repository == "https://github.com/LastDreamTeam/sprintable_LDVersion.git"
commit = data["commit"]
assert len(commit) == 40 and all(c in "0123456789abcdef" for c in commit)
url = "https://codeload.github.com/LastDreamTeam/sprintable_LDVersion/tar.gz/" + commit
archive = destination.parent / "transfer" / ("source-" + commit + ".tar.gz")
archive.parent.mkdir(parents=True, exist_ok=True)
with urllib.request.urlopen(url, timeout=45) as response, archive.open("wb") as out:
    shutil.copyfileobj(response, out)
destination.mkdir(mode=0o755)
with tarfile.open(archive) as tar:
    links = []
    for member in tar.getmembers():
        parts = Path(member.name).parts
        if len(parts) == 1:
            continue
        member.name = str(Path(*parts[1:]))
        target = (destination / member.name).resolve()
        assert target.is_relative_to(destination) and ".git" not in Path(member.name).parts
        assert member.isfile() or member.isdir() or member.issym()
        if member.issym():
            links.append((target, member.linkname))
        else:
            tar.extract(member, destination)
    # Native Git repositories may contain intentionally external symlinks. Create
    # them only after extracting regular files; never follow them for extraction.
    for target, link in links:
        assert not target.exists() and not target.is_symlink()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(link)
def git(*args, raw=None):
    return subprocess.check_output(["git", "-C", str(destination), *args], input=raw).decode().strip()
git("init", "--initial-branch=main_1")
git("-c", "core.autocrlf=false", "-c", "core.filemode=true", "add", "--force", "--all")
assert git("write-tree") == data["tree"], "Source archive does not match Git tree"
raw = base64.b64decode(data["raw_commit_base64"])
assert raw.startswith(("tree " + data["tree"] + "\n").encode())
assert git("hash-object", "-t", "commit", "-w", "--stdin", raw=raw) == commit
(destination / ".git/shallow").write_text(commit + "\n")
git("update-ref", "refs/heads/main_1", commit)
git("remote", "add", "origin", repository)
git("config", "branch.main_1.remote", "origin")
git("config", "branch.main_1.merge", "refs/heads/main_1")
assert git("status", "--porcelain") == ""
print(json.dumps({"source_commit": commit, "tree_verified": True, "git_clean": True, "shallow": True}))
