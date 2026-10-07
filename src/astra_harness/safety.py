"""Credential-class path protection and symlink rejection before I/O."""
import os
from pathlib import Path

class BoundaryError(ValueError):
    pass

def protected_read(path):
    """Password stores and credential locations stay outside general read access."""
    for part in Path(path).parts:
        name=part.casefold()
        if (name in {'.ssh','.aws','.gnupg','keychains','1password','1password.app',
                     'credentials.json','.credentials.json','auth.json','id_rsa','id_ed25519'}
            or name.startswith(('com.1password','com.agilebits')) or name.endswith(('.kdbx','.keychain-db'))
            or (name=='.env' or name.startswith('.env.')) and name not in {'.env.example','.env.template'}):
            return True
    return False


def safe_path(path, *, follow_final=True):
    """Reject credential classes and every existing symlink component.

    The caller supplies the path; this core has no ambient host configuration.
    This is a local library boundary, not an authorization server or OS sandbox.
    """
    raw = Path(os.path.abspath(Path(path).expanduser()))
    if protected_read(raw):
        raise BoundaryError('Credential-class path; not accessed')
    current = Path(raw.anchor)
    for part in raw.parts[1:]:
        current /= part
        if current.is_symlink():
            raise BoundaryError('Symlink path; not accessed')
    return raw


def safe_read_path(path):
    return safe_path(path)
