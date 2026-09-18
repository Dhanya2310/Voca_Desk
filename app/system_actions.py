"""
system_actions.py - Safe OS-level actions for Windows.

All actions are explicitly whitelisted — no arbitrary shell execution.
"""

import os
import subprocess
import webbrowser
from app.utils import get_logger

logger = get_logger(__name__)

# ── Known websites ────────────────────────────────────────────────────────────

WEBSITES: dict[str, str] = {
    "youtube":       "https://www.youtube.com",
    "google":        "https://www.google.com",
    "github":        "https://www.github.com",
    "gmail":         "https://mail.google.com",
    "linkedin":      "https://www.linkedin.com",
    "reddit":        "https://www.reddit.com",
    "twitter":       "https://www.twitter.com",
    "x":             "https://www.x.com",
    "stackoverflow": "https://stackoverflow.com",
    "stack overflow":"https://stackoverflow.com",
    "wikipedia":     "https://www.wikipedia.org",
    "netflix":       "https://www.netflix.com",
    "amazon":        "https://www.amazon.com",
    "chatgpt":       "https://chat.openai.com",
    "openai":        "https://www.openai.com",
}

# ── Known Windows applications ────────────────────────────────────────────────

APPS: dict[str, list[str]] = {
    "calculator":     ["calc.exe"],
    "notepad":        ["notepad.exe"],
    "command prompt": ["cmd.exe"],
    "cmd":            ["cmd.exe"],
    "powershell":     ["powershell.exe"],
    "file explorer":  ["explorer.exe"],
    "explorer":       ["explorer.exe"],
    "paint":          ["mspaint.exe"],
    "task manager":   ["taskmgr.exe"],
    "vs code":        ["code.exe", "code"],
    "visual studio code": ["code.exe", "code"],
    "word":           ["winword.exe"],
    "excel":          ["excel.exe"],
    "chrome":         [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                       r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"],
    "firefox":        [r"C:\Program Files\Mozilla Firefox\firefox.exe"],
    "edge":           ["msedge.exe"],
    "spotify":        ["spotify.exe"],
    "discord":        ["discord.exe"],
    "slack":          ["slack.exe"],
    "zoom":           ["zoom.exe"],
    "snipping tool":  ["SnippingTool.exe", "SnipSketch.exe"],
    "clock":          ["ms-clock:"],   # UWP app URI
    "photos":         ["ms-photos:"],
    "settings":       ["ms-settings:"],
    "store":          ["ms-windows-store:"],
}


def open_website(name: str) -> str:
    """Open a known website in the default browser. Returns response message."""
    key = name.strip().lower()
    url = WEBSITES.get(key)
    if url is None:
        # Try partial match
        for k, v in WEBSITES.items():
            if key in k or k in key:
                url = v
                break

    if url is None:
        return f"I don't have a shortcut for '{name}'. Try 'search for {name}' instead."

    try:
        webbrowser.open(url)
        logger.info("Opened website: %s", url)
        return f"Opening {name.title()}."
    except Exception as e:
        logger.error("Failed to open website %s: %s", url, e)
        return f"I couldn't open {name}. Please try manually."


def search_web(query: str) -> str:
    """Perform a Google search in the default browser."""
    import urllib.parse
    url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
    try:
        webbrowser.open(url)
        logger.info("Searching for: %s", query)
        return f"Searching for '{query}'."
    except Exception as e:
        logger.error("Search failed: %s", e)
        return "I couldn't open the browser. Please try manually."


def open_application(name: str) -> str:
    """Launch a known Windows application. Returns response message."""
    key = name.strip().lower()
    candidates = APPS.get(key)

    if candidates is None:
        # Partial match
        for k, v in APPS.items():
            if key in k or k in key:
                candidates = v
                break

    if candidates is None:
        return (
            f"I don't know how to open '{name}'. "
            "You can ask me to search for it instead."
        )

    for exe in candidates:
        try:
            if exe.startswith("ms-"):
                # UWP app URI
                os.startfile(exe)
            else:
                subprocess.Popen(
                    [exe],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    shell=False,
                )
            logger.info("Opened application: %s via %s", name, exe)
            return f"Opening {name.title()}."
        except FileNotFoundError:
            continue
        except Exception as e:
            logger.warning("Could not launch %s: %s", exe, e)
            continue

    return f"I couldn't find '{name}' on your computer. Make sure it's installed."


def lock_computer() -> str:
    """Lock the Windows workstation."""
    try:
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        return "Locking your computer."
    except Exception as e:
        logger.error("Lock failed: %s", e)
        return "I couldn't lock the computer."


def show_desktop() -> str:
    """Minimise all windows to show the desktop."""
    try:
        import ctypes
        # Send Win+D via keybd_event
        VK_LWIN = 0x5B
        VK_D    = 0x44
        KEYEVENTF_KEYUP = 0x0002
        ctypes.windll.user32.keybd_event(VK_LWIN, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_D,    0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_D,    0, KEYEVENTF_KEYUP, 0)
        ctypes.windll.user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)
        return "Showing the desktop."
    except Exception as e:
        logger.error("Show desktop failed: %s", e)
        return "I couldn't show the desktop."


# ── Volume control (uses pycaw on Windows) ────────────────────────────────────

def _get_volume_interface():
    """Return the pycaw ISimpleAudioVolume interface, or None if unavailable."""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
    except Exception as e:
        logger.warning("pycaw unavailable: %s", e)
        return None


def increase_volume(step: float = 0.1) -> str:
    vol = _get_volume_interface()
    if vol is None:
        return "Volume control isn't available on this system."
    try:
        current = vol.GetMasterVolumeLevelScalar()
        vol.SetMasterVolumeLevelScalar(min(1.0, current + step), None)
        return f"Volume increased to {int((current + step) * 100)}%."
    except Exception as e:
        logger.error("Volume increase failed: %s", e)
        return "Couldn't change the volume."


def decrease_volume(step: float = 0.1) -> str:
    vol = _get_volume_interface()
    if vol is None:
        return "Volume control isn't available on this system."
    try:
        current = vol.GetMasterVolumeLevelScalar()
        vol.SetMasterVolumeLevelScalar(max(0.0, current - step), None)
        return f"Volume decreased to {int((current - step) * 100)}%."
    except Exception as e:
        logger.error("Volume decrease failed: %s", e)
        return "Couldn't change the volume."


def mute_volume() -> str:
    vol = _get_volume_interface()
    if vol is None:
        return "Volume control isn't available on this system."
    try:
        muted = vol.GetMute()
        vol.SetMute(not muted, None)
        return "Volume unmuted." if muted else "Volume muted."
    except Exception as e:
        logger.error("Mute failed: %s", e)
        return "Couldn't toggle mute."
