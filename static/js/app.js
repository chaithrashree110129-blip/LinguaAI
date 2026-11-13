/**
 * AI Language Translator — Client-side helpers
 * - Theme management & persistence
 * - Welcome screen name entry & validation
 * - Dynamic greeting synchronization
 * - Speech-to-Text (Microphone dictation)
 * - Text-to-Speech pronunciation (Listen)
 * - Clipboard copy helper
 * - Live character counter
 */
(function () {
  const html = document.documentElement;

  // 1. Toast Notification Helper
  function toast(message) {
    const node = document.getElementById("toast");
    if (!node) return;
    node.hidden = false;
    node.textContent = message;
    window.clearTimeout(window._toastTimeout);
    window._toastTimeout = window.setTimeout(function () {
      node.hidden = true;
    }, 2800);
  }

  // 2. Theme Persistence
  const savedTheme = localStorage.getItem("ai_translator_theme") || localStorage.getItem("linguaai-theme");
  if (savedTheme === "light" || savedTheme === "dark") {
    html.setAttribute("data-theme", savedTheme);
  }

  const themeInputs = document.querySelectorAll('input[name="theme"]');
  themeInputs.forEach(function (input) {
    input.addEventListener("change", function () {
      html.setAttribute("data-theme", input.value);
      localStorage.setItem("ai_translator_theme", input.value);
    });
  });

  // 3. Welcome Screen Handler
  const welcomeForm = document.getElementById("welcome-name-form");
  const nameInput = document.getElementById("user-name-input");
  const startBtn = document.getElementById("btn-start-translating");

  function handleStartTranslating() {
    if (!nameInput) return;
    const name = nameInput.value.trim();
    if (!name) {
      nameInput.classList.add("input-error-shake");
      nameInput.focus();
      toast("Please enter your name to start translating.");
      setTimeout(function () {
        nameInput.classList.remove("input-error-shake");
      }, 500);
      return;
    }
    // Save to localStorage & cookie
    localStorage.setItem("ai_translator_username", name);
    document.cookie = "ai_translator_username=" + encodeURIComponent(name) + "; path=/; max-age=31536000; SameSite=Lax";

    // Navigate to homepage
    window.location.href = "/";
  }

  if (welcomeForm) {
    welcomeForm.addEventListener("submit", function (e) {
      e.preventDefault();
      handleStartTranslating();
    });
  }
  if (startBtn) {
    startBtn.addEventListener("click", function (e) {
      e.preventDefault();
      handleStartTranslating();
    });
  }

  // Pre-fill name on welcome screen if revisiting
  if (nameInput && !nameInput.value) {
    const existing = localStorage.getItem("ai_translator_username") || localStorage.getItem("linguaai-username");
    if (existing) {
      nameInput.value = existing;
    }
  }

  // 4. Homepage Greeting Synchronization
  const userGreetingElem = document.getElementById("user-display-name");
  if (userGreetingElem) {
    const localName = localStorage.getItem("ai_translator_username") || localStorage.getItem("linguaai-username");
    if (localName && localName.trim()) {
      userGreetingElem.textContent = localName.trim();
    }
  }

  // 5. Settings Username Sync
  const settingsNameInput = document.getElementById("settings-username-input");
  const settingsForm = document.getElementById("settings-form");
  if (settingsNameInput) {
    const localName = localStorage.getItem("ai_translator_username") || localStorage.getItem("linguaai-username");
    if (localName && !settingsNameInput.value) {
      settingsNameInput.value = localName;
    }
    if (settingsForm) {
      settingsForm.addEventListener("submit", function () {
        const updated = settingsNameInput.value.trim();
        if (updated) {
          localStorage.setItem("ai_translator_username", updated);
          document.cookie = "ai_translator_username=" + encodeURIComponent(updated) + "; path=/; max-age=31536000; SameSite=Lax";
        }
      });
    }
  }

  // 6. Character Count Tracker
  const input = document.getElementById("input_text");
  const used = document.getElementById("char-used");
  const updateCount = function () {
    if (input && used) {
      used.textContent = String(input.value.length);
    }
  };
  if (input && used) {
    updateCount();
    input.addEventListener("input", updateCount);
  }

  // 7. Clear and swap workspace content
  const form = document.getElementById("translate-form");
  const loading = document.getElementById("output-loading");
  const output = document.getElementById("output_text");
  const outputState = document.getElementById("output_text_state");
  const sourceSelect = document.getElementById("source_lang");
  const targetSelect = document.getElementById("target_lang");
  const clearBtn = document.getElementById("btn-clear");
  const swapBtn = document.querySelector(".btn-swap-panels");

  if (clearBtn) {
    clearBtn.addEventListener("click", function () {
      if (input) input.value = "";
      if (output) {
        output.textContent = "";
        output.removeAttribute("data-has-result");
      }
      if (outputState) outputState.value = "";
      const detectedBadge = document.querySelector(".detected-badge");
      if (detectedBadge) detectedBadge.remove();
      updateCount();
      if (input) input.focus();
    });
  }

  if (form && swapBtn) {
    form.addEventListener("submit", function (event) {
      if (event.submitter !== swapBtn) return;
      event.preventDefault();
      if (!sourceSelect || !targetSelect || sourceSelect.value === "auto") {
        toast("Choose a source language before swapping.");
        return;
      }

      const oldSource = sourceSelect.value;
      sourceSelect.value = targetSelect.value;
      targetSelect.value = oldSource;
      // Swap language selections only; never move text between the source and output panels.
      if (output) output.setAttribute("lang", targetSelect.value);
      const listenBtn = document.getElementById("btn-listen");
      if (listenBtn) listenBtn.setAttribute("data-lang", targetSelect.value);
      const detectedBadge = document.querySelector(".detected-badge");
      if (detectedBadge) detectedBadge.remove();
    });
  }

  // 8. Form Submission Loading Overlay
  if (form && loading) {
    form.addEventListener("submit", function (event) {
      const submitter = event.submitter;
      if (submitter && submitter.value === "translate") {
        loading.hidden = false;
      }
    });
  }

  // 9. Clipboard Copy Action
  const copyBtn = document.getElementById("btn-copy");
  if (copyBtn) {
    copyBtn.addEventListener("click", async function () {
      const target = document.getElementById(copyBtn.getAttribute("data-copy-target"));
      const text = target ? target.textContent.trim() : "";
      if (!text) {
        toast("Nothing to copy yet. Translate a sentence first.");
        return;
      }
      try {
        if (navigator.clipboard && window.isSecureContext) {
          await navigator.clipboard.writeText(text);
        } else {
          const temporary = document.createElement("textarea");
          temporary.value = text;
          temporary.setAttribute("readonly", "");
          temporary.style.position = "fixed";
          temporary.style.opacity = "0";
          document.body.appendChild(temporary);
          temporary.select();
          const copied = document.execCommand("copy");
          temporary.remove();
          if (!copied) throw new Error("Clipboard access was denied.");
        }
        toast("Copied translation to clipboard!");
      } catch (error) {
        toast("Copy failed. You can select the text and copy manually.");
      }
    });
  }

  // 9. Speech-to-Text Microphone Dictation
  const micBtn = document.getElementById("btn-mic");
  if (micBtn && input) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;
    let isListening = false;

    const langMap = {
      en: "en-US",
      kn: "kn-IN",
      hi: "hi-IN",
      ta: "ta-IN",
      te: "te-IN",
      es: "es-ES",
      fr: "fr-FR",
      auto: navigator.language || "en-US"
    };

    if (!SpeechRecognition) {
      micBtn.addEventListener("click", function () {
        toast("Voice dictation is not supported in this browser. You can type directly.");
      });
    } else {
      micBtn.addEventListener("click", function () {
        if (isListening) {
          if (recognition) recognition.stop();
          return;
        }

        try {
          recognition = new SpeechRecognition();
          recognition.continuous = false;
          recognition.interimResults = true;

          const sourceSelect = document.getElementById("source_lang");
          const selectedLang = sourceSelect ? sourceSelect.value : "auto";
          recognition.lang = langMap[selectedLang] || "en-US";

          recognition.onstart = function () {
            isListening = true;
            micBtn.classList.add("is-listening");
            micBtn.setAttribute("title", "Listening… Click to stop");
            toast("Listening… Speak clearly now.");
          };

          recognition.onresult = function (event) {
            let transcript = "";
            for (let i = event.resultIndex; i < event.results.length; i++) {
              transcript += event.results[i][0].transcript;
            }
            if (transcript) {
              input.value = transcript;
              if (used) used.textContent = String(input.value.length);
            }
          };

          recognition.onerror = function (event) {
            isListening = false;
            micBtn.classList.remove("is-listening");
            micBtn.setAttribute("title", "Click to dictate (speech input)");
            if (event.error === "not-allowed") {
              toast("Microphone access was denied. Please allow microphone permission in your browser.");
            } else if (event.error === "no-speech") {
              toast("No speech detected. Please try clicking the microphone again.");
            } else {
              toast("Speech recognition encountered a problem (" + event.error + ").");
            }
          };

          recognition.onend = function () {
            isListening = false;
            micBtn.classList.remove("is-listening");
            micBtn.setAttribute("title", "Click to dictate (speech input)");
          };

          recognition.start();
        } catch (err) {
          isListening = false;
          micBtn.classList.remove("is-listening");
          toast("Could not start speech recognition. You can type your text.");
        }
      });
    }
  }

  // 10. Text-to-Speech Pronunciation (Listen)
  const listenBtn = document.getElementById("btn-listen");
  if (listenBtn) {
    listenBtn.addEventListener("click", function () {
      const target = document.getElementById(listenBtn.getAttribute("data-listen-target"));
      const text = target ? target.textContent.trim() : "";
      const lang = listenBtn.getAttribute("data-lang") || "en";
      if (!text) {
        toast("Nothing to read yet. Translate a sentence first.");
        return;
      }
      if (!window.speechSynthesis) {
        toast("This browser does not support speech synthesis.");
        return;
      }
      const voices = window.speechSynthesis.getVoices();
      const match = voices.find(function (voice) {
        return voice.lang.toLowerCase().startsWith(lang.toLowerCase());
      });
      if (voices.length && !match && lang !== "en") {
        toast("No speech voice is installed for this language on your system.");
        return;
      }
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = lang;
      if (match) utterance.voice = match;
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utterance);
    });
  }
})();
