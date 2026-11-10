# AI Language Translator

AI-powered language translation for English, Kannada, Hindi, Tamil, Telugu, Spanish, and French.

A calm, privacy-first translation studio featuring personalized greetings, a 3D rotating multilingual Earth visualization, a two-panel workspace with voice dictation, local SQLite history, and dual Aurora themes.

---

## What You Need

- Windows 10 or 11
- Python 3.10 or newer ([python.org](https://www.python.org/downloads/))  
  During install, tick **Add python.exe to PATH**.

---

## First-Time Setup

Open **PowerShell** in the project directory and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

If Windows blocks the activate script, run this once, then try `Activate.ps1` again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Edit `.env` in Notepad:
1. Set `FLASK_SECRET_KEY` to any long random sentence.
2. (Optional for later API wiring): Add a Sarvam API key.

---

## Run the Website

```powershell
.\.venv\Scripts\Activate.ps1
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

Stop the server with `Ctrl+C` in PowerShell.

---

## User Flow & Key Features

1. **Welcome / Intro Screen (`/welcome`)**:
   - First screen for new visitors featuring the AI Network illustration.
   - Name entry field with instant browser validation.
   - Saves visitor name in browser storage without requiring an account.
2. **Homepage Hero Section**:
   - Personalized greeting dynamically addressing the visitor by name.
   - High-performance animated 3D rotating Earth globe with orbiting characters from all supported languages (`ಕ`, `अ`, `அ`, `అ`, `A`, `ñ`, `ç`).
3. **Two-Panel Translation Workspace**:
   - **Left Panel (Source)**: Language selector (including Auto Detect), large text area, live character counter, and microphone speech dictation button.
   - **Center Swap Control**: Flip source and target languages instantly.
   - **Right Panel (Output)**: Destination language selector, translated output well with neural spinner, plus one-click Copy and Listen (speech synthesis) actions.
   - **Prominent Translate Action**: Centered AI-glowing button below the panels.
4. **Additional Feature Cards**:
   - Automatic language detection.
   - Seven supported languages.
   - Voice input & speech pronunciation.
   - Local on-device SQLite history.
   - Quick clipboard copy.
   - Instant language swap.
5. **Local Privacy Guarantee (`/privacy`)**:
   - Zero cloud accounts, zero tracking cookies. All notes and history reside exclusively on the user's laptop.

---

## Project Map

| Path | Role |
|------|------|
| `app.py` | Web application routes (`/`, `/welcome`, `/history`, `/settings`, `/about`, `/privacy`) |
| `config.py` | Reads `.env`, defines supported language pairs and limits |
| `translator.py` | Translation router (Sarvam vs MyMemory) |
| `detect.py` | Language detection interface |
| `database.py` | SQLite local history and user settings persistence |
| `templates/` | HTML templates (`base.html`, `index.html`, `welcome.html`, etc.) |
| `static/css/` | Aurora Studio styling (`tokens.css`, `layout.css`, `components.css`, `motion.css`) |
| `static/js/app.js` | Speech recognition, TTS, copy, char count, name & theme storage |
| `static/img/` | Brand logos and hero visual assets |
