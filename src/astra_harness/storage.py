"""Atomic JSON storage within an explicit caller-supplied research root."""
import json
import os
import tempfile
from .safety import safe_path

def read_json(path):
    return json.loads(safe_path(path).read_text())

def atomic_bytes(path, content, mode=0o600):
    path = safe_path(path, follow_final=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.harness-', dir=path.parent)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, 'wb') as out:
            out.write(content); out.flush(); os.fsync(out.fileno())
        os.replace(tmp, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.lexists(tmp):
            os.unlink(tmp)

def write_json(path, value):
    atomic_bytes(path, (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode())
