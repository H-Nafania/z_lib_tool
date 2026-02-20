import os
from typing import Any, TYPE_CHECKING
from ..path_resolver import normalize_path

if TYPE_CHECKING:
    from ..core import Z_Lib

class Z_OS_Path:
    def __init__(self, z_lib: "Z_Lib"):
        self._z_lib = z_lib

    def exists(self, path: str) -> bool:
        try:
            real_path = self._z_lib.resolve(path)
            return real_path.exists()
        except Exception:
            return False

    def isfile(self, path: str) -> bool:
        try:
            real_path = self._z_lib.resolve(path)
            return real_path.is_file()
        except Exception:
            return False

    def isdir(self, path: str) -> bool:
        try:
            real_path = self._z_lib.resolve(path)
            return real_path.is_dir()
        except Exception:
            return False

    def join(self, *paths: str) -> str:
        # Use simple string join but normalized
        # We don't use os.path.join because it might use backslashes on Windows
        # and we want to keep consistent / separators for z_lib paths
        
        # Filter empty paths
        non_empty_paths = [p for p in paths if p]
        
        if not non_empty_paths:
            return ""
            
        # If absolute path is encountered, it resets the join (os.path.join behavior)
        # But for z_lib virtual paths, "absolute" concept is vague.
        # "C:/foo" is absolute local. "a.zip/foo" is relative/absolute in zip context.
        # Let's rely on standard os.path.join but normalize result.
        joined = os.path.join(*paths)
        return normalize_path(joined)

    def basename(self, path: str) -> str:
        return os.path.basename(normalize_path(path))

    def dirname(self, path: str) -> str:
        return os.path.dirname(normalize_path(path))
        
    def splitext(self, path: str) -> tuple[str, str]:
        return os.path.splitext(normalize_path(path))
        
    def getsize(self, path: str) -> int:
        real_path = self._z_lib.resolve(path)
        return os.path.getsize(real_path)
