import os
from typing import Any, Iterator, List, Tuple, TYPE_CHECKING
from pathlib import Path
from ..path_resolver import normalize_path
from .z_os_path import Z_OS_Path

if TYPE_CHECKING:
    from ..core import Z_Lib

class Z_OS:
    def __init__(self, z_lib: "Z_Lib"):
        self._z_lib = z_lib
        self.path = Z_OS_Path(z_lib)

    def listdir(self, path: str) -> List[str]:
        real_path = self._z_lib.resolve(path)
        return os.listdir(real_path)

    def mkdir(self, path: str, mode: int = 0o777) -> None:
        real_path = self._z_lib.resolve(path)
        os.mkdir(real_path, mode)
        
    def makedirs(self, path: str, mode: int = 0o777, exist_ok: bool = False) -> None:
        real_path = self._z_lib.resolve(path)
        os.makedirs(real_path, mode, exist_ok)

    def remove(self, path: str) -> None:
        real_path = self._z_lib.resolve(path)
        os.remove(real_path)
        
    def rmdir(self, path: str) -> None:
        real_path = self._z_lib.resolve(path)
        os.rmdir(real_path)

    def rename(self, src: str, dst: str) -> None:
        real_src = self._z_lib.resolve(src)
        real_dst = self._z_lib.resolve(dst)
        os.rename(real_src, real_dst)

    def walk(self, top: str, topdown: bool = True, onerror: Any = None, followlinks: bool = False) -> Iterator[Tuple[str, List[str], List[str]]]:
        """
        Directory tree generator.
        Yields a 3-tuple (dirpath, dirnames, filenames).
        'dirpath' will be returned as valid z_lib virtual path (if inside zip).
        """
        # Resolve the top path
        try:
            real_top = self._z_lib.resolve(top)
        except Exception:
            if onerror:
                onerror(OSError(f"Path not found: {top}"))
            return
            
        real_top = Path(real_top)
        
        # Iterate using standard os.walk on the real filesystem (temp dir)
        for root, dirs, files in os.walk(real_top, topdown=topdown, onerror=onerror, followlinks=followlinks):
            root_path = Path(root)
            
            # Calculate relative path from the real top
            try:
                rel_path = root_path.relative_to(real_top)
            except ValueError:
                # Should not happen if os.walk works as expected starting from real_top
                continue
                
            # Construct the virtual path
            if str(rel_path) == ".":
                virtual_root = normalize_path(top)
            else:
                virtual_root = normalize_path(os.path.join(top, str(rel_path)))
            
            yield virtual_root, dirs, files
