import re
import string

import pytest

from messages import MESSAGES, SUPPORTED_LANGS, msg, normalize_lang


def placeholders(template):
    return {name for _, name, _, _ in string.Formatter().parse(template) if name}


@pytest.mark.parametrize("key", sorted(MESSAGES))
def test_message_exists_in_every_language_with_same_placeholders(key):
    variants = MESSAGES[key]
    assert set(variants) == set(SUPPORTED_LANGS)
    assert all(variants[lang].strip() for lang in SUPPORTED_LANGS)
    assert len({frozenset(placeholders(v)) for v in variants.values()}) == 1


@pytest.mark.parametrize(
    "key", ["rate_limited", "server_busy", "ai_quota", "ai_failed", "text_too_short", "pdf_encrypted"]
)
def test_new_keys_exist(key):
    assert key in MESSAGES


def test_russian_and_kazakh_messages_use_cyrillic():
    for key, variants in MESSAGES.items():
        for lang in ("ru", "kk"):
            assert re.search("[а-яА-ЯәғқңөұүһіӘҒҚҢӨҰҮҺІ]", variants[lang]), (key, lang)


@pytest.mark.parametrize(
    "raw,expected",
    [("en", "en"), ("RU", "ru"), ("kk-KZ", "kk"), ("ru_RU", "ru"),
     ("de", "en"), ("", "en"), (None, "en"), ("  kk ", "kk")],
)
def test_normalize_lang(raw, expected):
    assert normalize_lang(raw) == expected


def test_rate_limited_message_has_no_seconds_placeholder():
    for lang in SUPPORTED_LANGS:
        assert placeholders(MESSAGES["rate_limited"][lang]) == set()


def test_msg_fills_placeholders():
    assert "1,000" in msg("too_long", "en", length=5, limit=1000)


def test_missing_api_key_message_does_not_leak_setup_details():
    for lang in SUPPORTED_LANGS:
        text = MESSAGES["missing_api_key"][lang]
        assert ".env" not in text and "GEMINI" not in text and "README" not in text


def test_msg_unknown_language_falls_back_to_english():
    assert msg("no_input", "xx") == msg("no_input", "en")


def test_msg_returns_translation():
    assert msg("no_input", "ru") != msg("no_input", "en")
