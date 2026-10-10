"""LD display overlays for upstream built-in roles; never alter stored permissions.

Technical behavior uses the native English translation when Chinese is unavailable.
Custom roles, identifiers, tool groups and existing explicit translations are preserved.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.services.agent_onboarding_config import resolve_locale

ROLE_DISPLAY = json.loads((Path(__file__).parent / "locales" / "roles.json").read_text(encoding="utf-8"))


def localized_content(translations: dict | None, original: Any, locale: str) -> Any:
    """Requested translation, then English for non-Korean requests, then original."""
    locale = resolve_locale(locale)
    translations = translations or {}
    return (translations.get(locale)
            or (translations.get("en") if locale != "ko" else None)
            or original)


def role_display(role: Any, locale: str) -> tuple[str, str | None]:
    locale = resolve_locale(locale)
    name = role.name
    translations = getattr(role, "description_i18n", None) or {}
    description = localized_content(translations, getattr(role, "description", None), locale)
    preset = ROLE_DISPLAY.get(getattr(role, "slug", ""))
    # An explicitly renamed/custom role must not be silently replaced by our catalog.
    if not getattr(role, "is_builtin", False) or not preset or name != preset["name"]:
        return name, description
    overlay = preset.get(locale) or (preset["en"] if locale != "ko" else {})
    return overlay.get("name", name), translations.get(locale) or overlay.get("description", description)


def role_behaviors(role: Any, locale: str) -> str:
    return localized_content(
        getattr(role, "role_behaviors_i18n", None), role.role_behaviors, locale,
    )

