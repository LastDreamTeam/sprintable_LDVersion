"""OpenAI: stdlib-only tests; run in an isolated backend image, never with a live DB."""
import asyncio
from collections import Counter
from datetime import datetime, timezone
import re
import string
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, MagicMock
import uuid

from app.services.agent_onboarding_config import (
    resolve_locale, resolve_locale_from_request, template_locale, build_connector_guidance,
)
from app.services.i18n_catalog import MessageCatalog, UnknownMessageKeyError, t
from app.services.role_template_locale import ROLE_DISPLAY, role_display, role_behaviors
from app.services.agent_recruiter import compose_kit
from app.services.org_locale import resolve_org_locale
from app.services import email_copy, retro_export_i18n as retro


class LocaleTests(unittest.TestCase):
    def test_locale_aliases_and_unknown_fallback(self):
        for value in ("zh", "zh-CN", "zh_Hans", " ZH "):
            self.assertEqual(resolve_locale(value), "zh")
        self.assertEqual(resolve_locale("ko-KR"), "ko")
        for value in (None, "", "fr"):
            self.assertEqual(resolve_locale(value), "en")
        self.assertEqual(template_locale("zh"), "en")

    def test_accept_language_quality_and_explicit_precedence(self):
        self.assertEqual(resolve_locale_from_request(None, "ko;q=0.2,zh-CN;q=0.9,en;q=0.5"), "zh")
        self.assertEqual(resolve_locale_from_request("zh", "ko"), "zh")
        self.assertEqual(resolve_locale_from_request(None, "ko;q=0,en;q=1"), "en")
        self.assertEqual(resolve_locale_from_request(None, "ko;q=bad,zh;q=0.8"), "zh")

    def test_catalog_complete_placeholders_and_no_korean(self):
        entries = MessageCatalog.all_entries()
        self.assertGreaterEqual(len(entries), 192)
        def signature(value):
            return Counter((field, spec, conv) for _, field, spec, conv in string.Formatter().parse(value) if field is not None)
        for key, entry in entries.items():
            with self.subTest(key=key):
                self.assertEqual(set(entry), {"ko", "en", "zh"})
                self.assertEqual(signature(entry["zh"]), signature(entry["en"]))
                self.assertNotRegex(entry["zh"], r"[\uac00-\ud7af]")
                params = {field: "test" for field, _, _ in signature(entry["en"])}
                self.assertIsInstance(t(key, "zh-CN", **params), str)
        self.assertEqual(t("system.publisher_name", "zh"), "系统通知")
        with self.assertRaises(UnknownMessageKeyError):
            t("ld.nonexistent.key", "zh")

    def test_twenty_four_builtin_roles_and_behavior_fallback(self):
        self.assertEqual(len(ROLE_DISPLAY), 24)
        for slug, data in ROLE_DISPLAY.items():
            role = SimpleNamespace(slug=slug, name=data["name"], is_builtin=True,
                description="한국어", description_i18n={}, role_behaviors="한국어",
                role_behaviors_i18n={"en": "Follow verified workflow and tools."},
                default_tool_groups=["chat"], runtime_overrides={}, skills=[])
            with self.subTest(slug=slug):
                name, description = role_display(role, "zh")
                self.assertEqual(name, data["zh"]["name"])
                self.assertNotRegex(description, r"[\uac00-\ud7af]")
                self.assertNotRegex(role_display(role, "en")[1], r"[\uac00-\ud7af]")
                self.assertEqual(role_behaviors(role, "zh"), role.role_behaviors_i18n["en"])
                for runtime in ("hermes", "claude-code", "connector"):
                    kit = compose_kit(role, runtime, "zh")
                    self.assertNotRegex("\n".join(kit.values()), r"[\uac00-\ud7af]")
                    self.assertIn("sprintable_get_workflow_guide", kit["workflow_pointer"])
                    self.assertIn("Don't overwrite your existing identity", kit["integration_prompt"])

    def test_custom_role_and_authored_translation_preserved(self):
        role = SimpleNamespace(slug="backend", name="Custom", is_builtin=False,
            description="User-authored original", description_i18n={"zh": "用户自定义"})
        self.assertEqual(role_display(role, "zh"), ("Custom", "用户自定义"))
        role.is_builtin = True
        self.assertEqual(role_display(role, "zh"), ("Custom", "用户自定义"))
        role.name = "Backend Engineer"
        self.assertEqual(role_display(role, "zh"), ("后端工程师", "用户自定义"))

    def test_real_router_serialization_keeps_permissions(self):
        from app.routers.role_templates import _to_summary_response, _to_detail_response
        role = SimpleNamespace(id=uuid.uuid4(), slug="backend", name="Backend Engineer",
            category="backend", is_builtin=True, description="한국어", description_i18n={},
            role_behaviors="한국어", role_behaviors_i18n={"en": "Keep original permission rules."},
            default_tool_groups=["chat"], tier="free", version=1, division="Engineering",
            emoji=None, skills=[], runtime_overrides={}, created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc))
        for serialize in (_to_summary_response, _to_detail_response):
            result = serialize(role, "zh")
            self.assertEqual(result.name, "后端工程师")
            self.assertEqual(result.division, "研发")
            self.assertEqual(result.default_tool_groups, ["chat"])
            self.assertEqual(result.id, role.id)
        self.assertEqual(_to_detail_response(role, "zh").role_behaviors, "Keep original permission rules.")

    def test_org_uses_earliest_supported_owner_including_zh_cn(self):
        for values, expected in [(["fr", "zh-CN", "en"], "zh"), (["ko", "zh"], "ko"), ([], "en")]:
            result = MagicMock()
            result.scalars.return_value.all.return_value = values
            db = SimpleNamespace(execute=AsyncMock(return_value=result))
            self.assertEqual(asyncio.run(resolve_org_locale(db, uuid.uuid4())), expected)

    def test_legacy_technical_and_mail_copy_safe_english_fallback(self):
        self.assertNotRegex(build_connector_guidance("hermes", "zh"), r"[\uac00-\ud7af]")
        for entry in [*email_copy.TRANSACTIONAL_COPY.values(), email_copy.INVITE_COPY,
                      email_copy.REMINDER_COPY, email_copy.STORAGE_WARN_COPY, email_copy.AU_WARN_COPY]:
            self.assertEqual(entry["zh"], entry["en"])

    def test_retro_export_zh_and_english_unknown(self):
        self.assertEqual(retro.resolve_export_locale("zh-CN"), "zh")
        self.assertEqual(retro.phase_label("collect", "zh"), "收集")
        self.assertEqual(retro.votes_label(2, "zh"), "2 票")
        self.assertEqual(retro.votes_label(2, "fr"), "2 votes")


if __name__ == "__main__":
    unittest.main(verbosity=2)
