"""Automatic language detection. Real detection is wired in a later phase."""

import config


class DetectionError(Exception):
    def __init__(self, message, confidence="none"):
        super().__init__(message)
        self.message = message
        self.confidence = confidence


def detect_language(text):
    """
    Identify the language of `text`.

    Returns a dictionary:
      code: language code such as "en"
      name: display name
      confidence: "high", "low", or "none"
      message: shown to the user when we are not sure
    """
    cleaned = (text or "").strip()
    if not cleaned:
        raise DetectionError("Enter some text before using Auto Detect.")

    # Placeholder until Phase 5 connects langdetect / provider detection.
    raise DetectionError(
        "Language detection is not connected yet. "
        "Choose a source language by hand for now.",
        confidence="none",
    )


def code_to_name(code):
    if code == "auto":
        return "Auto Detect"
    return config.SUPPORTED_LANGUAGES.get(code, code)
