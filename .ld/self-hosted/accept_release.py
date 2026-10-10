"""OpenAI: read-only functional acceptance of the existing self-hosted space.

Uses private instance credentials on the server; login/logout creates only its
temporary session. No test messages, model calls, asset overwrites, or deletes.
"""
import argparse
import datetime
import http.cookiejar
import json
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument("--root", required=True)
parser.add_argument("--origin", required=True)
args = parser.parse_args()
root = Path(args.root).resolve()
state = json.loads((root / "secrets/provision.json").read_text())
origin = args.origin.rstrip("/")
host = urllib.parse.urlsplit(origin).netloc
assert urllib.parse.urlsplit(origin).scheme == "https"
cookies = http.cookiejar.CookieJar()
web = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
deployment_path = root / "config/DEPLOYMENT.json"
deployment = json.loads(deployment_path.read_text())
checks = {"deployment": {key: deployment[key] for key in ("web_commit", "backend_commit", "new_image")}}
def request(path, data=None, headers=None):
    url = path if path.startswith("https://") else origin + path
    assert urllib.parse.urlsplit(url).netloc == host
    head = {"Origin": origin, "X-Org-Id": state["organization"]["id"], "X-Project-Id": state["project"]["id"]}
    if headers:
        head.update(headers)
    if data is not None:
        head["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None, headers=head)
    try:
        return web.open(req, timeout=30)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(str(exc.code) + " " + urllib.parse.urlsplit(url).path) from None
def body(path, data=None):
    with request(path, data) as response:
        result = json.load(response)
    return result.get("data", result) if isinstance(result, dict) else result
body("/api/auth/login", {"email": state["email"], "password": state["password"]})
try:
    for locale in ("zh", "en"):
        roles = body("/api/role-templates?locale=" + locale)
        assert len(roles) >= 24
        for role in roles:
            if role["is_builtin"]:
                assert not re.search(r"[\uac00-\ud7af]", role.get("description") or ""), role["slug"]
        if locale == "zh":
            assert next(x for x in roles if x["slug"] == "backend")["name"] == "后端工程师"
        checks["role_catalog_" + locale] = len(roles)
    members = body("/api/team-members?type=agent")
    assert any(x["id"] == state["agents"]["shanghai"]["member_id"] for x in members)
    checks["existing_maid_in_roster"] = True
    assert any(x.get("runtime_type") == "system-publisher" and x["name"] == "系统通知" for x in members)
    checks["existing_system_publisher_localized"] = True
    agent_request = urllib.request.Request("http://127.0.0.1:32800/api/v2/me", headers={
        "Authorization": "Bearer " + state["agents"]["shanghai"]["api_key"],
        "X-Org-Id": state["organization"]["id"], "X-Project-Id": state["project"]["id"],
    })
    with urllib.request.urlopen(agent_request, timeout=10) as response:
        assert response.status == 200
    checks["existing_agent_key_works"] = True
    conversation = state["meeting_conversation"]["id"]
    assert re.fullmatch(r"[0-9a-f-]{36}", conversation)
    query = ("SELECT COALESCE(json_agg(x),'[]'::json) FROM "
             "(SELECT id,attachments FROM conversation_messages WHERE conversation_id='" + conversation +
             "' AND deleted_at IS NULL AND jsonb_array_length(COALESCE(attachments,'[]'::jsonb))>0 ORDER BY created_at DESC LIMIT 3) x")
    raw = subprocess.check_output(["docker", "exec", "ld-sprintable-postgres", "psql", "-p", "35432",
                                   "-U", "sprintable", "-d", "sprintable", "-Atc", query], text=True)
    messages = json.loads(raw)
    previews = []
    for message in messages:
        for attachment in message["attachments"]:
            path = attachment.get("url") or ""
            if not path.startswith("org/") or not str(attachment.get("content_type", "")).startswith("image/"):
                continue
            signed = body("/api/attachments/sign?" + urllib.parse.urlencode({"path": path, "conversation_id": conversation}))["url"]
            with request(signed) as response:
                original = response.read()
                assert response.status == 200 and len(original) > 50
            split = urllib.parse.urlsplit(signed)
            relative = split.path + "?" + split.query
            with request("/_next/image?" + urllib.parse.urlencode({"url": relative, "w": 384, "q": 75}),
                         headers={"Accept": "image/webp,image/*"}) as response:
                optimized = response.read()
                assert response.status == 200 and response.headers["Content-Type"].startswith("image/")
                assert len(optimized) > 30
            query_params = urllib.parse.parse_qs(split.query)
            assert "sig" in query_params
            value = query_params["sig"][0]
            query_params["sig"] = [("0" if value[0] != "0" else "1") + value[1:]]
            tampered = split.path + "?" + urllib.parse.urlencode(query_params, doseq=True)
            try:
                with request(tampered):
                    raise AssertionError("Invalid signature accepted")
            except RuntimeError as exc:
                assert str(exc).startswith("403 "), str(exc)
            previews.append({"message_id": message["id"], "original_bytes": len(original), "preview_bytes": len(optimized)})
    assert len(previews) >= 2, "Need at least two existing images to verify"
    checks["existing_image_previews"] = previews
    checks["invalid_signatures_rejected"] = True
    checks["no_messages_or_models_invoked"] = True
    checks["activation"] = body("/api/activation/checklist")["steps"]
    checks["gateway_pid"] = subprocess.check_output(["systemctl", "show", "hermes-gateway.service", "-p", "MainPID", "--value"], text=True).strip()
    assert json.loads(deployment_path.read_text()) == deployment, "Deployment changed during acceptance"
    checks["accepted_at_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (root / "config/ACCEPTANCE.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2))
    deployment.update({"status": "functional_acceptance_passed", "accepted_at_utc": checks["accepted_at_utc"]})
    deployment_path.write_text(json.dumps(deployment, indent=2))
    print(json.dumps(checks, ensure_ascii=False))
finally:
    body("/api/auth/logout", {})
