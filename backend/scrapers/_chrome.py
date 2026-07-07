"""
Shared Chrome binary/version resolution for undetected-chromedriver scrapers.

Local dev on Windows and the Docker image (Debian + google-chrome-stable) have
Chrome in different places and different versions - hardcoding either breaks
the other. CHROME_BINARY / CHROME_VERSION_MAIN let you pin a specific local
install via .env; with nothing set, uc.Chrome() auto-detects both from
whatever's on the system (which is what the Docker image relies on).
"""
import os
import shutil

_CANDIDATE_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]


def chrome_binary_location() -> str | None:
    """Best-effort Chrome binary path, or None to let uc.Chrome() auto-detect."""
    env_path = os.getenv("CHROME_BINARY")
    if env_path:
        return env_path
    for path in _CANDIDATE_PATHS:
        if os.path.exists(path) or shutil.which(path):
            return path
    return None


def chrome_version_main() -> int | None:
    """Optional pin via CHROME_VERSION_MAIN; None lets uc.Chrome() auto-detect."""
    val = os.getenv("CHROME_VERSION_MAIN")
    return int(val) if val else None
