"""Hebrew speech via the local Piper Noa voice used by Chef Mind."""

import subprocess
from pathlib import Path

CHEF_PYTHON = Path(r"C:\workspace\chef_mind\.venv\Scripts\python.exe")
CHEF_BACKEND = Path(r"C:\workspace\chef_mind\backend")
_CACHE: dict[str, bytes] = {}
_HELPER = """
import sys
sys.path.insert(0, sys.argv[1])
from app.local_speech import LocalSpeech
engine = LocalSpeech()
if not engine.available():
    raise SystemExit(3)
text = sys.stdin.buffer.read().decode("utf-8", errors="ignore").strip()
sys.stdout.buffer.write(engine.create(text))
"""


def synthesize_noa(text: str) -> bytes | None:
    spoken = " ".join((text or "").split())
    if not spoken or not CHEF_PYTHON.exists() or not CHEF_BACKEND.exists():
        return None
    if spoken in _CACHE:
        return _CACHE[spoken]
    try:
        completed = subprocess.run(
            [str(CHEF_PYTHON), "-c", _HELPER, str(CHEF_BACKEND)],
            input=spoken.encode("utf-8"),
            capture_output=True,
            timeout=90,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0 or not completed.stdout.startswith(b"RIFF"):
        return None
    _CACHE[spoken] = completed.stdout
    while len(_CACHE) > 24:
        _CACHE.pop(next(iter(_CACHE)))
    return completed.stdout
