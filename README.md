# VocaDesk 🎤

> A modern, fully local Windows desktop voice assistant built with Python and PySide6.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![PySide6](https://img.shields.io/badge/GUI-PySide6-green)
![Windows](https://img.shields.io/badge/Platform-Windows-lightblue)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Features

| Category | Capabilities |
|----------|-------------|
| 🗣 Voice Input | Microphone capture with noise adjustment |
| 💬 Text Input | Keyboard fallback for all commands |
| 🔊 Voice Output | Offline text-to-speech (no API key needed) |
| 🌐 Websites | Open YouTube, Google, GitHub, Gmail, LinkedIn and 10+ more |
| 🔍 Search | Google search by voice or text |
| 💻 Apps | Open Calculator, Notepad, VS Code, Explorer and more |
| 🔒 System | Lock computer, show desktop, volume control |
| 📝 Notes | Create, view, delete notes — stored in SQLite |
| ⏰ Reminders | Set reminders by time — desktop notifications |
| 🤖 AI Mode | Optional Gemini / OpenAI backend for general questions |
| ⚙ Settings | Configurable voice rate, volume, microphone, AI mode |

---

## Technology Stack

- **Python 3.11+**
- **PySide6** — Qt6-based desktop GUI
- **SpeechRecognition** — Microphone capture + Google Web Speech API
- **pyttsx3** — Fully offline text-to-speech (Windows SAPI5)
- **PyAudio** — Audio I/O
- **pycaw** — Windows system volume control
- **SQLite** — Local persistence (notes & reminders)
- **python-dotenv** — Environment variable loading
- **pytest** — Automated tests

---

## Project Structure

```
VocaDesk/
│
├── main.py                  # Entry point — run this
├── requirements.txt         # Python dependencies
├── README.md
├── .env.example             # Template for API keys
│
├── app/
│   ├── __init__.py
│   ├── gui.py               # Main window (PySide6)
│   ├── widgets.py           # ChatBubble, MicButton, StatusBadge
│   ├── assistant.py         # QThread orchestrators (voice + text)
│   ├── speech_to_text.py    # Microphone → text
│   ├── text_to_speech.py    # Text → speech (pyttsx3, threaded)
│   ├── command_processor.py # Pattern-matching command router
│   ├── system_actions.py    # Safe OS actions
│   ├── database.py          # SQLite notes & reminders
│   ├── reminders.py         # Background reminder checker
│   ├── settings.py          # QSettings-backed preferences
│   ├── ai_client.py         # Optional Gemini / OpenAI integration
│   └── utils.py             # Logger, date/time helpers
│
├── data/                    # Auto-created: SQLite DB + log file
├── assets/                  # Icons and resources
│
└── tests/
    └── test_commands.py     # pytest unit tests
```

---

## Installation

### Requirements

- Windows 10 / 11
- Python 3.11 or newer
- A working microphone (for voice mode)
- Internet connection (for speech recognition and optional AI mode)

### Step 1 — Create a virtual environment

```powershell
python -m venv venv
venv\Scripts\activate
```

### Step 2 — Install dependencies

```powershell
pip install -r requirements.txt
```

> **Note:** `pyaudio` sometimes requires a pre-built wheel on Windows.
> If `pip install pyaudio` fails, try:
> ```powershell
> pip install pipwin
> pipwin install pyaudio
> ```
> Or download the wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

### Step 3 — Microphone setup

1. Open **Windows Settings → System → Sound → Input**.
2. Make sure your microphone is listed and set as the default device.
3. Allow microphone access for apps if prompted.

### Step 4 — Run the application

```powershell
python main.py
```

---

## Configuring Optional AI Mode

AI mode lets VocaDesk answer general knowledge questions.

1. Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Edit `.env` and add your key:
   ```
   VOCADESK_GEMINI_API_KEY=your_actual_key_here
   ```

3. Install the AI package:
   ```powershell
   # For Google Gemini (free tier):
   pip install google-generativeai

   # For OpenAI:
   pip install openai
   ```

4. In VocaDesk, open **Settings** and enable **AI mode**.

> The basic assistant works without any API key. AI mode is fully optional.

---

## Supported Commands

### Time & Date
| Say | Response |
|-----|----------|
| "What time is it?" | "It is 9:30 PM." |
| "What's the date?" | "Today is Wednesday, September 17, 2026." |

### Open Websites
| Say | Action |
|-----|--------|
| "Open YouTube" | Opens youtube.com |
| "Open Google" | Opens google.com |
| "Open GitHub" | Opens github.com |
| "Open Gmail" | Opens mail.google.com |
| "Open LinkedIn" | Opens linkedin.com |
| "Open Reddit" | Opens reddit.com |
| "Open Stack Overflow" | Opens stackoverflow.com |

### Search the Web
| Say | Action |
|-----|--------|
| "Search for Python decorators" | Google search |
| "Search Google for recursion" | Google search |
| "Google what is a linked list" | Google search |

### Open Applications
| Say | App Launched |
|-----|-------------|
| "Open Calculator" | Windows Calculator |
| "Open Notepad" | Notepad |
| "Open Command Prompt" | CMD |
| "Open PowerShell" | PowerShell |
| "Open File Explorer" | Explorer |
| "Open VS Code" | Visual Studio Code |
| "Open Paint" | MS Paint |
| "Open Task Manager" | Task Manager |

### System
| Say | Action |
|-----|--------|
| "Lock my computer" | Locks the screen |
| "Show my desktop" | Minimises all windows |
| "Increase volume" | +10% system volume |
| "Decrease volume" | -10% system volume |
| "Mute volume" | Toggle mute |

### Notes
| Say | Action |
|-----|--------|
| "Take a note: buy milk" | Saves note |
| "Note: finish assignment" | Saves note |
| "Show my notes" | Lists all notes |
| "Delete note 3" | Deletes note #3 |

### Reminders
| Say | Action |
|-----|--------|
| "Remind me at 7 PM to study" | Creates reminder |
| "Remind me in 30 minutes to drink water" | Creates reminder |
| "Show my reminders" | Lists all reminders |

### AI Mode (requires API key)
Just ask anything:
- "Explain polymorphism in Java"
- "What is the difference between C and C++?"
- "Give me a Python code example of a decorator"

---

## Troubleshooting

### "Microphone not found"
- Check Windows Sound settings — ensure mic is set as default input.
- Try a different microphone index in **Settings → Microphone**.
- Run `python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"` to list devices.

### "Speech recognition service unavailable"
- This uses Google's free Web Speech API — internet is required.
- Check your internet connection.

### "pyaudio install fails"
- See the PyAudio installation note in Step 2 above.

### "pycaw import error / volume control unavailable"
- `pycaw` is Windows-only. Make sure you're on Windows.
- Try: `pip install pycaw comtypes`

### App starts but TTS doesn't speak
- Make sure Windows SAPI5 is installed (it is by default on Windows 10/11).
- Check **Settings → Enable voice output** is ticked.

### VS Code not found
- Make sure `code` is in your PATH (VS Code installer option: "Add to PATH").

---

## Running Tests

```powershell
python -m pytest tests/ -v
```

---

## Future Improvements

- [ ] Weather queries (OpenWeatherMap API)
- [ ] Music playback control (Spotify / VLC)
- [ ] "Read my notes" — TTS reads back saved notes
- [ ] Translation ("Translate hello to French")
- [ ] Pomodoro / study timer
- [ ] Custom wake word ("Hey VocaDesk") using Porcupine
- [ ] Multiple language support
- [ ] Command history / conversation context
- [ ] Offline STT using Whisper (no internet needed)
- [ ] System tray mini-mode

---

## License

MIT — free to use, modify, and distribute.