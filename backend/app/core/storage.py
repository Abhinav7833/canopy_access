from pathlib import Path
from typing import Protocol

from app.core.config import get_settings


class Storage(Protocol):
    def save(self, key: str, data: bytes) -> str: ...
    def url_for(self, key: str) -> str: ...
    def path_for(self, key: str) -> Path: ...


class LocalStorage:
    def __init__(self, root: Path, mount: str) -> None:
        self._root = root
        self._mount = mount.rstrip("/")

    def path_for(self, key: str) -> Path:
        return self._root / key

    def save(self, key: str, data: bytes) -> str:
        dest = self.path_for(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return self.url_for(key)

    def url_for(self, key: str) -> str:
        # Append the file mtime so a re-seeded asset gets a fresh URL (busts the
        # browser cache); the /static mount ignores the query string.
        url = f"{self._mount}/{key}"
        try:
            return f"{url}?v={int(self.path_for(key).stat().st_mtime)}"
        except OSError:
            return url


def get_storage() -> Storage:
    s = get_settings()
    return LocalStorage(s.assets_dir, s.static_mount)
