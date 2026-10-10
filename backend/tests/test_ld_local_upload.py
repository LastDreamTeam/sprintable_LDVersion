"""LD local-upload regression suite. No database/network/production writes.

Run with the locked backend runtime: python -m unittest discover -s tests
 -p test_ld_local_upload.py -v. Images are tiny synthetic test fixtures.
"""
import asyncio
import importlib
import io
import os
import tempfile
import unittest
import uuid
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

import httpx
from fastapi import FastAPI, HTTPException
from PIL import Image
from app.routers.local_storage import router
from app.services.storage.local import LocalStorageProvider, _resolve_safe


class LocalUploadTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ld-local-upload-test-")
        self.env = patch.dict(os.environ, {
            "STORAGE_PROVIDER": "local", "STORAGE_LOCAL_ROOT": self.tmp.name,
            "STORAGE_LOCAL_SIGNING_SECRET": "isolated-test-not-a-real-secret",
            "STORAGE_LOCAL_SERVE_BASE_URL": "http://test", "GCS_AVATARS_BUCKET": "test-avatars",
        })
        self.env.start()
        import app.services.avatar_upload as avatar
        self.avatar = importlib.reload(avatar)
        app = FastAPI()
        app.include_router(router)
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test")
        self.provider = LocalStorageProvider()
        self.org, self.member = uuid.uuid4(), uuid.uuid4()

    async def asyncTearDown(self):
        await self.client.aclose()
        self.env.stop()
        importlib.reload(self.avatar)
        self.tmp.cleanup()

    async def url(self, path="manual/file.txt", **kwargs):
        return await self.provider.signed_write_url("private", path,
            ttl=kwargs.pop("ttl", timedelta(minutes=1)), content_type="text/plain", create_only=True, **kwargs)

    @staticmethod
    def mutate(url, **changes):
        p = urlsplit(url)
        q = {k: v[0] for k, v in parse_qs(p.query).items()}
        q.update(changes)
        return urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), ""))

    async def test_create_read_and_atomic_replay_rejected(self):
        url = await self.url()
        first = await self.client.put(url, content=b"original", headers={"content-type": "text/plain"})
        self.assertEqual(first.status_code, 204)
        replay = await self.client.put(url, content=b"replacement", headers={"content-type": "text/plain"})
        self.assertEqual(replay.status_code, 412)
        self.assertEqual(await self.provider.download_object("private", "manual/file.txt"), b"original")
        self.assertEqual(list(Path(self.tmp.name).rglob(".upload-*")), [])

    async def test_concurrent_create_only_one_winner(self):
        url = await self.url()
        responses = await asyncio.gather(*(self.client.put(url, content=str(i), headers={"content-type": "text/plain"}) for i in range(5)))
        self.assertEqual(sorted(r.status_code for r in responses), [204, 412, 412, 412, 412])

    async def test_constraints_cannot_be_tampered_or_read_signature_reused(self):
        url = await self.url()
        for changes in ({"create": "0"}, {"max": "99999999"}, {"type": "image/png"}, {"sig": "bad"}):
            r = await self.client.put(self.mutate(url, **changes), content=b"x", headers={"content-type": "text/plain"})
            self.assertEqual(r.status_code, 403)
        read = await self.provider.signed_read_url("private", "manual/file.txt", ttl=timedelta(minutes=1))
        r = await self.client.put(self.mutate(url, sig=parse_qs(urlsplit(read).query)["sig"][0]), content=b"x", headers={"content-type": "text/plain"})
        self.assertEqual(r.status_code, 403)
        r = await self.client.put(url.replace("file.txt", "other.txt"), content=b"x", headers={"content-type": "text/plain"})
        self.assertEqual(r.status_code, 403)

    async def test_expired_wrong_mime_empty_and_no_secret_fail_closed(self):
        url = await self.url(ttl=timedelta(seconds=-1))
        self.assertEqual((await self.client.put(url, content=b"x")).status_code, 403)
        url = await self.url()
        self.assertEqual((await self.client.put(url, content=b"x", headers={"content-type": "image/png"})).status_code, 403)
        self.assertEqual((await self.client.put(url, content=b"", headers={"content-type": "text/plain"})).status_code, 422)
        with patch.dict(os.environ, {"STORAGE_LOCAL_SIGNING_SECRET": "", "APP_ENV": "production"}):
            self.assertEqual((await self.client.put(url, content=b"x")).status_code, 503)

    async def test_path_and_provider_isolation(self):
        for container, path in (("..", "outside"), ("/tmp", "outside"), ("private", "../../outside"), ("private", "dir\\outside")):
            with self.assertRaises(ValueError):
                _resolve_safe(container, path)
        with patch.dict(os.environ, {"STORAGE_PROVIDER": "gcs"}):
            self.assertEqual((await self.client.put("/api/v2/storage/local-upload/private/a")).status_code, 404)
        self.assertEqual((await self.client.get("/api/v2/storage/local-avatars/private/file.txt")).status_code, 404)

    async def test_avatar_three_formats_replace_delete_and_public_preview(self):
        previous = None
        for fmt, mime in (("PNG", "image/png"), ("JPEG", "image/jpeg"), ("WEBP", "image/webp")):
            data = io.BytesIO()
            Image.new("RGB", (2, 2), (50, 80, 100)).save(data, format=fmt)
            raw = data.getvalue()
            issued = await self.avatar.create_upload_url(org_id=self.org, member_id=self.member, content_type=mime)
            self.assertEqual((await self.client.put(issued["upload_url"], content=raw, headers={"content-type": mime})).status_code, 204)
            public = await self.avatar.confirm_upload(org_id=self.org, member_id=self.member,
                object_path=issued["object_path"], previous_avatar_url=previous)
            r = await self.client.get(public)
            self.assertEqual(r.content, raw)
            self.assertEqual(r.headers["content-type"], mime)
            if previous:
                self.assertEqual((await self.client.get(previous)).status_code, 404)
            previous = public
        await self.avatar.delete_avatar(current_avatar_url=previous)
        self.assertEqual((await self.client.get(previous)).status_code, 404)

    async def test_invalid_oversized_avatar_and_foreign_confirm_rejected(self):
        issued = await self.avatar.create_upload_url(org_id=self.org, member_id=self.member, content_type="image/png")
        r = await self.client.put(issued["upload_url"], content=b"<html>bad</html>", headers={"content-type": "image/png"})
        self.assertEqual(r.status_code, 422)
        r = await self.client.put(issued["upload_url"], content=b"x" * (5 * 1024 * 1024 + 1), headers={"content-type": "image/png"})
        self.assertEqual(r.status_code, 413)
        with self.assertRaises(self.avatar.AvatarUploadError) as cm:
            await self.avatar.confirm_upload(org_id=self.org, member_id=uuid.uuid4(), object_path=issued["object_path"], previous_avatar_url=None)
        self.assertEqual(cm.exception.status_code, 403)
        self.assertEqual(list(Path(self.tmp.name).rglob(".upload-*")), [])

    async def test_gcs_avatar_url_contract_unchanged(self):
        with patch.dict(os.environ, {"STORAGE_PROVIDER": "gcs"}):
            mod = importlib.reload(self.avatar)
            provider = MagicMock(signed_write_url=AsyncMock(return_value="https://signed.example/upload"))
            with patch.object(mod, "get_storage_provider", return_value=provider):
                issued = await mod.create_upload_url(org_id=self.org, member_id=self.member, content_type="image/png")
                self.assertTrue(issued["public_url"].startswith("https://storage.googleapis.com/test-avatars/"))


if __name__ == "__main__":
    unittest.main()
