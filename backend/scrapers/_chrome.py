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
import tempfile

_CANDIDATE_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]

# Cloudflare shows this interstitial while it runs its JS/browser challenge.
# Checking for it lets scrapers tell "still blocked" apart from "site markup
# changed", which otherwise look identical (both are a missing-element timeout).
_CF_MARKERS = ("just a moment", "cf-chl", "challenges.cloudflare.com", "cf-browser-verification")


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


def chrome_profile_dir(name: str) -> str:
    """
    Persistent user-data-dir so cookies (notably Cloudflare's `cf_clearance`)
    survive across scrape cycles instead of re-triggering the JS challenge
    every single run.

    /app/data is the volume the bot container already mounts (see
    deploy_bot.yml) for seen_jobs/subscribers, so profiles persist across
    container restarts there too. Falls back to the OS temp dir for local
    dev where that mount doesn't exist.
    """
    base = "/app/data" if os.path.isdir("/app/data") else tempfile.gettempdir()
    path = os.path.join(base, f"uc_profile_{name}")
    os.makedirs(path, exist_ok=True)
    return path


def looks_like_cloudflare_challenge(page_source: str) -> bool:
    """Heuristic check for Cloudflare's interstitial in the current page source."""
    lower = (page_source or "").lower()
    return any(marker in lower for marker in _CF_MARKERS)
