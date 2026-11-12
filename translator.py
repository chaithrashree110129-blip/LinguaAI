"""Route translation requests to real provider APIs."""

import html
import re

import config
import requests

EURO_CODES = {"es", "fr"}
SARVAM_URL = "https://api.sarvam.ai/translate"
MYMEMORY_URL = "https://api.mymemory.translated.net/get"
MYMEMORY_MAX_BYTES = 500
REQUEST_TIMEOUT = (5, 30)


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

    - English and Indian languages: Sarvam
    - Spanish or French: MyMemory
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

    if involved <= set(config.SARVAM_LANGUAGE_CODES):
        return "sarvam"

    raise ValidationError("That language pair is not supported.")


def _request_error(provider, error):
    if isinstance(error, requests.Timeout):
        return TranslationError(
            f"{provider} did not respond in time. Please try again."
        )
    return TranslationError(
        f"Could not connect to {provider}. Check your internet connection and try again."
    )


def _translate_sarvam(text, source_code, target_code):
    if not config.SARVAM_API_KEY:
        raise TranslationError(
            "Sarvam AI is not configured. Add a valid SARVAM_API_KEY to your .env "
            "file to translate English, Kannada, Hindi, Tamil, or Telugu."
        )

    payload = {
        "input": text,
        "source_language_code": config.SARVAM_LANGUAGE_CODES[source_code],
        "target_language_code": config.SARVAM_LANGUAGE_CODES[target_code],
        "model": "sarvam-translate:v1",
        "mode": "formal",
    }
    try:
        response = requests.post(
            SARVAM_URL,
            json=payload,
            headers={
                "api-subscription-key": config.SARVAM_API_KEY,
                "Content-Type": "application/json",
            },
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as error:
        raise _request_error("Sarvam AI", error) from error

    if response.status_code in {401, 403}:
        raise TranslationError(
            "Sarvam AI rejected the API key. Check SARVAM_API_KEY in your .env file."
        )
    if response.status_code == 429:
        raise TranslationError(
            "Sarvam AI quota or rate limit reached. Check your Sarvam account and try later."
        )
    if not response.ok:
        detail = _response_error_detail(response)
        raise TranslationError(f"Sarvam AI could not translate this text. {detail}")

    try:
        data = response.json()
    except ValueError as error:
        raise TranslationError("Sarvam AI returned an unreadable response.") from error

    translated_text = data.get("translated_text") if isinstance(data, dict) else None
    if not isinstance(translated_text, str) or not translated_text.strip():
        raise TranslationError("Sarvam AI returned no translation.")
    return {
        "translated_text": translated_text.strip(),
        "provider": "sarvam",
        "notes": [],
    }


def _response_error_detail(response):
    try:
        data = response.json()
    except ValueError:
        return f"Provider returned HTTP {response.status_code}."

    if isinstance(data, dict):
        error = data.get("error")
        if isinstance(error, dict) and isinstance(error.get("message"), str):
            return error["message"]
        details = data.get("responseDetails")
        if isinstance(details, str) and details:
            return details
    return f"Provider returned HTTP {response.status_code}."


def _split_mymemory_text(text):
    chunks = []
    current = ""
    for word in re.findall(r"\S+", text):
        if len(word.encode("utf-8")) > MYMEMORY_MAX_BYTES:
            raise ValidationError(
                "A single word is too long for the MyMemory translation service."
            )
        candidate = f"{current} {word}".strip()
        if current and len(candidate.encode("utf-8")) > MYMEMORY_MAX_BYTES:
            chunks.append(current)
            current = word
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def _translate_mymemory(text, source_code, target_code):
    translated_chunks = []
    for chunk in _split_mymemory_text(text):
        params = {
            "q": chunk,
            "langpair": f"{source_code}|{target_code}",
        }
        if config.MYMEMORY_EMAIL:
            params["de"] = config.MYMEMORY_EMAIL
        try:
            response = requests.get(
                MYMEMORY_URL, params=params, timeout=REQUEST_TIMEOUT
            )
        except requests.RequestException as error:
            raise _request_error("MyMemory", error) from error

        if not response.ok:
            detail = _response_error_detail(response)
            raise TranslationError(f"MyMemory could not translate this text. {detail}")
        try:
            data = response.json()
        except ValueError as error:
            raise TranslationError("MyMemory returned an unreadable response.") from error

        status = data.get("responseStatus") if isinstance(data, dict) else None
        result = data.get("responseData") if isinstance(data, dict) else None
        translated = result.get("translatedText") if isinstance(result, dict) else None
        if str(status) != "200":
            detail = _response_error_detail(response)
            raise TranslationError(f"MyMemory could not translate this text. {detail}")
        if not isinstance(translated, str) or not translated.strip():
            raise TranslationError("MyMemory returned no translation.")
        translated_chunks.append(html.unescape(translated).strip())

    return {
        "translated_text": " ".join(translated_chunks),
        "provider": "mymemory",
        "notes": [],
    }


def translate(text, source_code, target_code):
    """
    Translate `text` from source_code to target_code.

    Returns a dictionary with translated_text, provider, and notes.
    """
    if not isinstance(text, str):
        raise ValidationError("Please enter text to translate.")
    cleaned = text.strip()
    if not cleaned:
        raise ValidationError("Please enter some text to translate.")
    if len(cleaned) > config.MAX_INPUT_CHARS:
        raise ValidationError(
            f"Please keep text under {config.MAX_INPUT_CHARS} characters."
        )

    provider = choose_provider(source_code, target_code)

    if provider == "sarvam":
        return _translate_sarvam(cleaned, source_code, target_code)
    return _translate_mymemory(cleaned, source_code, target_code)
