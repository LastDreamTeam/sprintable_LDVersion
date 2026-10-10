"""LD self-host local storage: bounded signed PUT and public avatar-only GET.

Uploads are authorized by existing avatar/assets routes before capability issuance.
Only the dedicated avatar container is public; chat/document files remain signed.
No database schema, auth bypass, cloud SDK, background service or FE rebuild needed.
"""
from __future__ import annotations

import asyncio
import hmac
import os
import re
import tempfile
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import FileResponse

from app.services.storage.local import _resolve_safe, _signing_secret, write_signature

router = APIRouter(prefix="/api/v2/storage", tags=["local-storage"])


def _require_local() -> None:
    if (os.environ.get("STORAGE_PROVIDER", "").strip().lower() or "local") != "local":
        raise HTTPException(404)


def _valid_avatar(path: Path, content_type: str) -> None:
    # Pillow is already a locked backend dependency. Never serve SVG/HTML as an avatar.
    from PIL import Image
    try:
        with Image.open(path) as image:
            if Image.MIME.get(image.format) != content_type or image.width * image.height > 25_000_000:
                raise ValueError("invalid avatar")
            if getattr(image, "n_frames", 1) != 1:
                raise ValueError("animated avatar")
            image.verify()
    except Exception as exc:
        raise HTTPException(422, "Invalid or animated avatar image") from exc


@router.put("/local-upload/{container}/{object_path:path}", status_code=204)
async def put_local_object(container: str, object_path: str, request: Request) -> Response:
    _require_local()
    query = request.query_params
    try:
        exp = int(query["exp"])
        max_bytes = int(query["max"])
        if query["create"] not in ("0", "1"):
            raise ValueError()
        create_only = query["create"] == "1"
        content_type = query["type"]
        target = _resolve_safe(container, object_path)
        expected = write_signature(_signing_secret(), container, object_path, exp,
                                   content_type, max_bytes, create_only)
        if (exp <= time.time() * 1000 or not 0 < max_bytes <= 100 * 1024 * 1024
                or not re.fullmatch(r"[0-9a-f]{64}", query.get("sig", ""))
                or not hmac.compare_digest(expected, query.get("sig", ""))):
            raise ValueError()
    except (KeyError, ValueError):
        raise HTTPException(403, "Invalid or expired upload signature") from None
    except RuntimeError:
        raise HTTPException(503, "Local storage signing not configured") from None
    if request.headers.get("content-type", "").split(";", 1)[0].strip() != content_type:
        raise HTTPException(403, "Content type does not match upload signature")
    try:
        if int(request.headers.get("content-length", "0")) > max_bytes:
            raise HTTPException(413, "Upload too large")
    except ValueError:
        raise HTTPException(400, "Invalid content length") from None

    avatar_bucket = os.environ.get("GCS_AVATARS_BUCKET")
    if container == avatar_bucket:
        if (not create_only or max_bytes > 5 * 1024 * 1024
                or content_type not in ("image/png", "image/jpeg", "image/webp")
                or not re.fullmatch(r"avatar/[0-9a-f-]{36}/[0-9a-f-]{36}/[0-9a-f]{32}\.(png|jpg|webp)", object_path)):
            raise HTTPException(403, "Invalid avatar upload capability")

    await asyncio.to_thread(target.parent.mkdir, parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".upload-", dir=target.parent)
    temporary = Path(name)
    try:
        # fdopen owns the descriptor immediately; every failure removes the temporary blob.
        with os.fdopen(fd, "wb") as stream:
            size = 0
            async for chunk in request.stream():
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(413, "Upload too large")
                await asyncio.to_thread(stream.write, chunk)
            if not size:
                raise HTTPException(422, "Empty upload")
            await asyncio.to_thread(stream.flush)
        if container == avatar_bucket:
            await asyncio.to_thread(_valid_avatar, temporary, content_type)
        # Shared backend/web group; no access granted to other local services.
        await asyncio.to_thread(temporary.chmod, 0o660)
        if create_only:
            try:
                await asyncio.to_thread(os.link, temporary, target)
            except FileExistsError:
                raise HTTPException(412, "Object already exists") from None
        else:
            await asyncio.to_thread(os.replace, temporary, target)
    finally:
        await asyncio.to_thread(temporary.unlink, missing_ok=True)
    return Response(status_code=204)


@router.get("/local-avatars/avatar/{org_id}/{member_id}/{filename}")
async def get_local_avatar(org_id: uuid.UUID, member_id: uuid.UUID, filename: str) -> FileResponse:
    _require_local()
    bucket = os.environ.get("GCS_AVATARS_BUCKET")
    match = re.fullmatch(r"[0-9a-f]{32}\.(png|jpg|webp)", filename)
    if not bucket or not match:
        raise HTTPException(404)
    path = _resolve_safe(bucket, f"avatar/{org_id}/{member_id}/{filename}")
    if not await asyncio.to_thread(path.is_file):
        raise HTTPException(404)
    return FileResponse(path, media_type={"png": "image/png", "jpg": "image/jpeg", "webp": "image/webp"}[match[1]],
                        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "public, max-age=300"})
