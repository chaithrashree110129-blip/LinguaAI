"""
AI Language Translator — Flask application.

Run with:  python app.py
Pages work. Live translation APIs are connected in a later phase.
"""

from flask import Flask, flash, make_response, redirect, render_template, request, session, url_for

import config
import database
import translator
from detect import DetectionError, detect_language

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024  # 32 KB form posts

EXAMPLE_SENTENCES = [
    {"text": "Good morning, how are you?", "source": "en", "target": "kn"},
    {"text": "Where is the railway station?", "source": "en", "target": "hi"},
    {"text": "Thank you for your help.", "source": "en", "target": "ta"},
]


def _workspace_defaults():
    return {
        "source_lang": database.get_setting("default_source", "auto"),
        "target_lang": database.get_setting("default_target", "kn"),
        "input_text": "",
        "output_text": "",
        "detected_label": "",
        "listen_enabled": database.get_setting("listen_enabled", "1") == "1",
    }


@app.context_processor
def inject_globals():
    return {
        "product_name": "AI Language Translator",
        "supported_languages": config.SUPPORTED_LANGUAGES,
        "source_languages": config.SOURCE_LANGUAGES,
        "max_input_chars": config.MAX_INPUT_CHARS,
        "current_year": __import__("datetime").datetime.now().year,
        "appearance_theme": database.get_setting("theme", "dark"),
    }


@app.before_request
def ensure_database():
    database.init_db()


@app.route("/welcome")
def welcome():
    user_name = request.cookies.get("ai_translator_username", "")
    return render_template("welcome.html", user_name=user_name)


@app.route("/", methods=["GET", "POST"])
def home():
    state = _workspace_defaults()
    reused = session.pop("reuse_item", None)
    if reused:
        state.update(reused)

    user_name = request.cookies.get("ai_translator_username", "")

    if request.method == "POST":
        state["source_lang"] = request.form.get("source_lang", "auto")
        state["target_lang"] = request.form.get("target_lang", "kn")
        state["input_text"] = request.form.get("input_text", "")
        action = request.form.get("action", "translate")

        if action == "swap":
            return _handle_swap(state, user_name)
        return _handle_translate(state, user_name)

    example_id = request.args.get("example")
    if example_id and example_id.isdigit():
        index = int(example_id)
        if 0 <= index < len(EXAMPLE_SENTENCES):
            sample = EXAMPLE_SENTENCES[index]
            state["input_text"] = sample["text"]
            state["source_lang"] = sample["source"]
            state["target_lang"] = sample["target"]

    return render_template(
        "index.html",
        **state,
        user_name=user_name,
        examples=EXAMPLE_SENTENCES,
    )


def _handle_swap(state, user_name=""):
    source = state["source_lang"]
    target = state["target_lang"]
    input_text = state["input_text"]
    output_text = state.get("output_text", "")

    if source == "auto":
        flash(
            "Swap needs a real source language. Auto Detect cannot be swapped. "
            "Choose English (or another language) first.",
            "error",
        )
        return render_template(
            "index.html",
            **state,
            user_name=user_name,
            examples=EXAMPLE_SENTENCES,
        )

    state["source_lang"] = target
    state["target_lang"] = source
    # Move translated text into the input box when we have any.
    if output_text:
        state["input_text"] = output_text
        state["output_text"] = input_text
    return render_template(
        "index.html",
        **state,
        user_name=user_name,
        examples=EXAMPLE_SENTENCES,
    )


def _handle_translate(state, user_name=""):
    source = state["source_lang"]
    target = state["target_lang"]
    text = state["input_text"]
    detected_code = None

    try:
        if source == "auto":
            result = detect_language(text)
            detected_code = result["code"]
            state["detected_label"] = (
                f"Detected: {result['name']} ({result['confidence']} confidence)"
            )
            if result["confidence"] == "low":
                flash(result.get("message") or "Detection confidence is low.", "warning")
            source = detected_code

        translated = translator.translate(text, source, target)
        state["output_text"] = translated["translated_text"]
        database.save_translation(
            original_text=text.strip(),
            source_language=source,
            target_language=target,
            translated_text=translated["translated_text"],
            detected_language=detected_code,
        )
        flash("Translation complete.", "success")
    except (translator.ValidationError, translator.TranslationError, DetectionError) as error:
        flash(error.message, "error")
        state["output_text"] = ""
    except Exception:
        flash(
            "Something went wrong while translating. Please try again in a moment.",
            "error",
        )
        state["output_text"] = ""

    return render_template(
        "index.html",
        **state,
        user_name=user_name,
        examples=EXAMPLE_SENTENCES,
    )


@app.route("/history")
def history():
    items = database.list_translations()
    return render_template("history.html", items=items)


@app.route("/history/<int:item_id>/reuse", methods=["POST"])
def reuse_history(item_id):
    item = database.get_translation(item_id)
    if not item:
        flash("That history item was not found.", "error")
        return redirect(url_for("history"))
    session["reuse_item"] = {
        "source_lang": item["source_language"],
        "target_lang": item["target_language"],
        "input_text": item["original_text"],
        "output_text": item["translated_text"],
        "detected_label": "",
        "listen_enabled": database.get_setting("listen_enabled", "1") == "1",
    }
    return redirect(url_for("home"))


@app.route("/history/<int:item_id>/delete", methods=["POST"])
def delete_history_item(item_id):
    database.delete_translation(item_id)
    flash("Translation removed from history.", "success")
    return redirect(url_for("history"))


@app.route("/history/clear", methods=["POST"])
def clear_history():
    database.clear_translations()
    flash("All translation history was deleted from this laptop.", "success")
    return redirect(url_for("history"))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        source = request.form.get("default_source", "auto")
        target = request.form.get("default_target", "kn")
        listen = "1" if request.form.get("listen_enabled") else "0"
        theme = request.form.get("theme", "dark")
        new_name = request.form.get("user_name", "").strip()

        if source != "auto" and source not in config.SUPPORTED_LANGUAGES:
            flash("That default source language is not supported.", "error")
        elif target not in config.SUPPORTED_LANGUAGES:
            flash("That default target language is not supported.", "error")
        elif source == target:
            flash("Default source and target should be different.", "error")
        else:
            database.set_setting("default_source", source)
            database.set_setting("default_target", target)
            database.set_setting("listen_enabled", listen)
            database.set_setting("theme", theme)
            flash("Settings saved on this laptop.", "success")

            resp = make_response(redirect(url_for("settings")))
            if new_name:
                resp.set_cookie("ai_translator_username", new_name, max_age=31536000, samesite="Lax")
            return resp

        return redirect(url_for("settings"))

    current_name = request.cookies.get("ai_translator_username", "")
    return render_template(
        "settings.html",
        default_source=database.get_setting("default_source", "auto"),
        default_target=database.get_setting("default_target", "kn"),
        listen_enabled=database.get_setting("listen_enabled", "1") == "1",
        theme=database.get_setting("theme", "dark"),
        user_name=current_name,
    )


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", code=404, message="Page not found."), 404


@app.errorhandler(500)
def server_error(_error):
    return (
        render_template(
            "error.html",
            code=500,
            message="The server hit an unexpected problem.",
        ),
        500,
    )


if __name__ == "__main__":
    database.init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
