import unittest
from unittest.mock import patch

import app as app_module
import config
import detect
import translator


class FakeResponse:
    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code
        self.ok = 200 <= status_code < 400

    def json(self):
        return self.data


class DetectionTests(unittest.TestCase):
    def test_detects_each_supported_language(self):
        samples = {
            "en": "Good morning, how are you today?",
            "es": "Buenos d\u00edas, \u00bfc\u00f3mo est\u00e1s hoy?",
            "fr": "Bonjour, comment allez-vous aujourd'hui?",
            "kn": "\u0ca8\u0cae\u0cb8\u0ccd\u0c95\u0cbe\u0cb0, \u0ca8\u0cc0\u0cb5\u0cc1",
            "hi": "\u0928\u092e\u0938\u094d\u0924\u0947, \u0906\u092a \u0915\u0948\u0938\u0947",
            "ta": "\u0bb5\u0ba3\u0b95\u0bcd\u0b95\u0bae\u0bcd, \u0ba8\u0bc0\u0b99\u0bcd\u0b95\u0bb3\u0bcd",
            "te": "\u0c39\u0c32\u0c4b, \u0c2e\u0c40\u0c30\u0c41 \u0c0e\u0c32\u0c3e",
        }
        for expected, text in samples.items():
            with self.subTest(language=expected):
                result = detect.detect_language(text)
                self.assertEqual(result["code"], expected)

    def test_rejects_empty_and_unsupported_text(self):
        with self.assertRaises(detect.DetectionError):
            detect.detect_language("   ")
        with self.assertRaises(detect.DetectionError):
            detect.detect_language(
                "Bom dia, como voce esta? Voce gostaria de uma traducao?"
            )


class TranslationTests(unittest.TestCase):
    def test_provider_selection_covers_all_supported_pairs(self):
        for source in config.SUPPORTED_LANGUAGES:
            for target in config.SUPPORTED_LANGUAGES:
                if source == target:
                    with self.assertRaises(translator.ValidationError):
                        translator.choose_provider(source, target)
                else:
                    expected = (
                        "mymemory"
                        if {source, target} & {"es", "fr"}
                        else "sarvam"
                    )
                    self.assertEqual(
                        translator.choose_provider(source, target), expected
                    )

    def test_sarvam_request_uses_configured_key_and_real_response(self):
        response = FakeResponse(
            {"translated_text": "\u0928\u092e\u0938\u094d\u0924\u0947"}
        )
        with patch.object(config, "SARVAM_API_KEY", "unit-test-key"), patch(
            "translator.requests.post", return_value=response
        ) as post:
            result = translator.translate("Hello", "en", "hi")

        self.assertEqual(result["translated_text"], "\u0928\u092e\u0938\u094d\u0924\u0947")
        self.assertEqual(result["provider"], "sarvam")
        self.assertEqual(post.call_args.kwargs["headers"]["api-subscription-key"], "unit-test-key")
        self.assertEqual(
            post.call_args.kwargs["json"]["target_language_code"], "hi-IN"
        )

    def test_sarvam_maps_all_supported_language_codes(self):
        response = FakeResponse({"translated_text": "provider result"})
        with patch.object(config, "SARVAM_API_KEY", "unit-test-key"), patch(
            "translator.requests.post", return_value=response
        ) as post:
            for source_code in config.SARVAM_LANGUAGE_CODES:
                target_code = "kn" if source_code == "en" else "en"
                with self.subTest(source=source_code, target=target_code):
                    translator.translate("Hello", source_code, target_code)
                    payload = post.call_args.kwargs["json"]
                    self.assertEqual(
                        payload["source_language_code"],
                        config.SARVAM_LANGUAGE_CODES[source_code],
                    )
                    self.assertEqual(
                        payload["target_language_code"],
                        config.SARVAM_LANGUAGE_CODES[target_code],
                    )

    def test_missing_sarvam_key_is_reported_without_request(self):
        with patch.object(config, "SARVAM_API_KEY", ""), patch(
            "translator.requests.post"
        ) as post:
            with self.assertRaisesRegex(translator.TranslationError, "SARVAM_API_KEY"):
                translator.translate("Hello", "en", "kn")
        post.assert_not_called()

    def test_mymemory_request_decodes_provider_response(self):
        response = FakeResponse(
            {
                "responseStatus": 200,
                "responseData": {"translatedText": "Bonjour &amp; salut"},
            }
        )
        with patch("translator.requests.get", return_value=response) as get:
            result = translator.translate("Hello and hi", "en", "fr")

        self.assertEqual(result["translated_text"], "Bonjour & salut")
        self.assertEqual(result["provider"], "mymemory")
        self.assertEqual(get.call_args.kwargs["params"]["langpair"], "en|fr")

    def test_mymemory_chunks_requests_to_provider_byte_limit(self):
        response = FakeResponse(
            {
                "responseStatus": 200,
                "responseData": {"translatedText": "resultado"},
            }
        )
        text = "palabra " * 100
        with patch("translator.requests.get", return_value=response) as get:
            translator.translate(text, "es", "fr")

        self.assertGreater(get.call_count, 1)
        self.assertTrue(
            all(
                len(call.kwargs["params"]["q"].encode("utf-8"))
                <= translator.MYMEMORY_MAX_BYTES
                for call in get.call_args_list
            )
        )

    def test_provider_error_is_not_replaced_with_a_fake_translation(self):
        response = FakeResponse(
            {"error": {"message": "invalid API key"}}, status_code=403
        )
        with patch.object(config, "SARVAM_API_KEY", "unit-test-key"), patch(
            "translator.requests.post", return_value=response
        ):
            with self.assertRaisesRegex(translator.TranslationError, "rejected"):
                translator.translate("Hello", "en", "kn")


class WebsiteIntegrationTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config["TESTING"] = True
        self.client = app_module.app.test_client()

    def test_homepage_auto_detection_translates_and_records_history(self):
        with (
            patch.object(app_module.database, "init_db"),
            patch.object(
                app_module.database,
                "get_setting",
                side_effect=lambda key, default=None: default,
            ),
            patch.object(
                app_module,
                "detect_language",
                return_value={
                    "code": "en",
                    "name": "English",
                    "confidence": "high",
                    "message": "",
                },
            ),
            patch.object(
                app_module.translator,
                "translate",
                return_value={"translated_text": "\u0ca8\u0cae\u0cb8\u0ccd\u0c95\u0cbe\u0cb0"},
            ),
            patch.object(app_module.database, "save_translation") as save_translation,
        ):
            response = self.client.post(
                "/",
                data={
                    "source_lang": "auto",
                    "target_lang": "kn",
                    "input_text": "Hello",
                    "action": "translate",
                },
            )

        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Detected: English (high confidence)", body)
        self.assertIn("\u0ca8\u0cae\u0cb8\u0ccd\u0c95\u0cbe\u0cb0", body)
        save_translation.assert_called_once()

    def test_swap_moves_output_back_to_input(self):
        with (
            patch.object(app_module.database, "init_db"),
            patch.object(
                app_module.database,
                "get_setting",
                side_effect=lambda key, default=None: default,
            ),
        ):
            response = self.client.post(
                "/",
                data={
                    "source_lang": "en",
                    "target_lang": "fr",
                    "input_text": "Hello",
                    "output_text": "Bonjour",
                    "action": "swap",
                },
            )

        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="input_text"', body)
        self.assertIn(">Bonjour</textarea>", body)
        self.assertIn(">Hello</div>", body)


if __name__ == "__main__":
    unittest.main()
