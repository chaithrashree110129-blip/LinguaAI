"""
Translation engine router.

Phase 3 only defines the structure: which provider should be used, and
clear errors. Live Sarvam and MyMemory calls are added in Phase 5.
This module never returns hardcoded fake translations.
"""

import config

INDIC_CODES = {"kn", "hi", "ta", "te"}
EURO_CODES = {"es", "fr"}


class TranslationError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ValidationError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def choose_provider(source_code, target_code):
    """
    Decide which service should handle a pair.

    - English <-> Indian languages: Sarvam
    - Indian <-> Indian: Sarvam via English (two calls later)
    - Spanish or French involved: MyMemory
    """
    if source_code == target_code:
        raise ValidationError("Choose two different languages.")

    if source_code not in config.SUPPORTED_LANGUAGES:
        raise ValidationError("That source language is not supported.")
    if target_code not in config.SUPPORTED_LANGUAGES:
        raise ValidationError("That target language is not supported.")

    involved = {source_code, target_code}

    if involved & EURO_CODES:
        return "mymemory"

    if involved <= (INDIC_CODES | {"en"}):
        return "sarvam"

    return "mymemory"


def translate(text, source_code, target_code):
    """
    Translate `text` from source_code to target_code.

    Returns a dictionary with translated_text, provider, and notes.
    """
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValidationError("Please enter some text to translate.")
    if len(cleaned) > config.MAX_INPUT_CHARS:
        raise ValidationError(
            f"Please keep text under {config.MAX_INPUT_CHARS} characters."
        )

    provider = choose_provider(source_code, target_code)

    if provider == "sarvam" and not config.SARVAM_API_KEY:
        raise TranslationError(
            "Sarvam is not configured yet. Add SARVAM_API_KEY to your .env file. "
            "See README.md for steps."
        )

    # Live HTTP calls are added in Phase 5. Do not invent a translation here.
    raise TranslationError(
        "The translation engine is structured but not connected to the APIs yet. "
        "This is expected during project foundation. No fake translation was returned."
    )
