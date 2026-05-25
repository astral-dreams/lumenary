from __future__ import annotations

import subprocess
from threading import Lock


_LOCK = Lock()
_CURRENT_CHILD: subprocess.Popen[str] | None = None


def register_child(process: subprocess.Popen[str]) -> None:
    global _CURRENT_CHILD
    with _LOCK:
        _CURRENT_CHILD = process


def unregister_child(process: subprocess.Popen[str]) -> None:
    global _CURRENT_CHILD
    with _LOCK:
        if _CURRENT_CHILD is process:
            _CURRENT_CHILD = None


def terminate_current_child() -> None:
    with _LOCK:
        process = _CURRENT_CHILD
    if process is not None and process.poll() is None:
        process.terminate()
