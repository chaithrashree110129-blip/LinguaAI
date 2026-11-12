"""Local automatic language detection for the supported languages."""

import config
from langdetect import DetectorFactory, LangDetectException, detect_langs

DetectorFactory.seed = 0

INDIC_SCRIPTS = {
    "kn": (0x0C80, 0x0CFF),
    "hi": (0x0900, 0x097F),
    "ta": (0x0B80, 0x0BFF),
    "te": (0x0C00, 0x0C7F),
}


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

    if len(cleaned) > config.MAX_INPUT_CHARS:
        raise DetectionError(
            f"Please keep text under {config.MAX_INPUT_CHARS} characters."
        )

    letters = [character for character in cleaned if character.isalpha()]
    if not letters:
        raise DetectionError("Enter some words so the source language can be detected.")

    script_counts = {
        code: sum(start <= ord(character) <= end for character in letters)
        for code, (start, end) in INDIC_SCRIPTS.items()
    }
    script_code, script_count = max(script_counts.items(), key=lambda item: item[1])
    if script_count:
        share = script_count / len(letters)
        if share >= 0.2 or script_count >= 3:
            confidence = "high" if share >= 0.65 else "low"
            return {
                "code": script_code,
                "name": config.SUPPORTED_LANGUAGES[script_code],
                "confidence": confidence,
                "message": (
                    "The text contains more than one script; please verify the "
                    "detected language."
                    if confidence == "low"
                    else ""
                ),
            }

    try:
        candidates = detect_langs(cleaned)
    except LangDetectException as error:
        raise DetectionError(
            "The source language could not be detected. Choose it manually."
        ) from error

    if not candidates or candidates[0].lang not in {"en", "es", "fr"}:
        raise DetectionError(
            "The text does not appear to be one of the supported languages. "
            "Choose the source language manually."
        )

    best = candidates[0]
    runner_up = candidates[1].prob if len(candidates) > 1 else 0.0
    if best.prob < 0.5:
        raise DetectionError(
            "The source language is uncertain. Add more text or choose it manually."
        )

    confidence = (
        "high" if best.prob >= 0.8 and best.prob - runner_up >= 0.2 else "low"
    )
    return {
        "code": best.lang,
        "name": config.SUPPORTED_LANGUAGES[best.lang],
        "confidence": confidence,
        "message": (
            "The text is short or ambiguous; please verify the detected language."
            if confidence == "low"
            else ""
        ),
    }


def code_to_name(code):
    if code == "auto":
        return "Auto Detect"
    return config.SUPPORTED_LANGUAGES.get(code, code)
