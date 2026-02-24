import atexit
from typing import Dict, List, Optional, Union, IO
from pathlib import Path

from ._types import ZipHandle, OpenMode
from .exceptions import ZipNotLoadedError, ZipAlreadyLoadedError, ZipPathError
from .path_resolver import normalize_path, resolve_to_real_path
from .backend.zipfile_backend import ZipFileBackend
from .namespaces.z_os import Z_OS
from .namespaces.z_shutil import Z_Shutil

class Z_Lib:
    def __init__(self):
        self._loaded_zips: Dict[str, ZipHandle] = {}
        self._backend = ZipFileBackend()
        
        # Ensure cleanup on exit
        atexit.register(self._cleanup)
        
        self.os = Z_OS(self)
        self.shutil = Z_Shutil(self)

    def load_zip(self, *paths: str, create: bool = False, mode: OpenMode = "rw") -> None:
        """
        Load one or more ZIP files.
        """
        for path in paths:
            # 正規化だけでなく、絶対パスに解決して一貫性を持たせる
            abs_path = Path(path).resolve()
            norm_path = normalize_path(str(abs_path))
            
            if norm_path in self._loaded_zips:
                print(f"  📦 [Z_Lib] LOAD  ⚡ already loaded — skipped   › {norm_path}")
                continue

            action = "create" if create else "open"
            print(f"  📦 [Z_Lib] LOAD  ▶  mode={mode!r}  [{action}]   › {norm_path}")
            handle = self._backend.open(path, create=create, mode=mode)
            self._loaded_zips[norm_path] = handle
            print(f"     └─ ✅ mounted   temp_dir={handle['temp_dir']}")

    def unload_zip(self, *paths: str) -> None:
        """
        Unload one or more ZIP files, saving changes if mode is "rw".
        """
        for path in paths:
            abs_path = Path(path).resolve()
            norm_path = normalize_path(str(abs_path))
            
            if norm_path not in self._loaded_zips:
                continue

            handle = self._loaded_zips[norm_path]
            will_save = handle.get("mode", "rw") == "rw"
            save_label = "💾 saving" if will_save else "🚫 discarding"
            print(f"  📦 [Z_Lib] UNLOAD  ◀  {save_label}   › {norm_path}")
            self._backend.close(handle, save=True)
            del self._loaded_zips[norm_path]
            print(f"     └─ ✅ closed")

    def swap_zip(self, target_zips: List[str], create: bool = False, mode: OpenMode = "rw") -> None:
        """
        Synchronize loaded ZIPs with the target list.
        Unloads ZIPs not in target_zips, loads ZIPs in target_zips that aren't loaded.
        """
        target_norm_set = {normalize_path(p) for p in target_zips}
        current_norm_set = set(self._loaded_zips.keys())

        to_unload = current_norm_set - target_norm_set
        to_load   = target_norm_set   - current_norm_set
        unchanged = current_norm_set  & target_norm_set

        print(
            f"  🔄 [Z_Lib] SWAP"
            f"  │  +load={len(to_load)}  -unload={len(to_unload)}  =keep={len(unchanged)}"
        )

        # Unload
        if to_unload:
            self.unload_zip(*to_unload)

        # Load
        if to_load:
            zips_to_load_args = [
                raw for raw in target_zips
                if normalize_path(raw) in to_load
            ]
            if zips_to_load_args:
                self.load_zip(*zips_to_load_args, create=create, mode=mode)

        loaded_count = len(self._loaded_zips)
        print(f"     └─ ✅ swap complete   loaded={loaded_count} ZIP(s)")

    def load_nest(self, folder: str, create: bool = False, mode: OpenMode = "r") -> None:
        """
        Recursively find and load all .zip files in a folder.
        Default mode is "r" as per requirements.
        """
        folder_path = Path(folder)
        print(f"  🔍 [Z_Lib] LOAD_NEST  ▶  scanning   › {normalize_path(str(folder_path.resolve()))}")

        if not folder_path.exists():
            if create:
                folder_path.mkdir(parents=True, exist_ok=True)
                print(f"     └─ 📁 folder created")
            else:
                raise FileNotFoundError(f"Folder not found: {folder}")

        zip_files = list(folder_path.rglob("*.zip"))
        print(f"     └─ 🗂  found {len(zip_files)} ZIP file(s)")
        for zip_file in zip_files:
            self.load_zip(str(zip_file), create=create, mode=mode)

    def open(self, path: str, mode: str = "r", **kwargs) -> IO:
        """
        Open a file (local or inside ZIP) seamlessly.
        """
        real_path = resolve_to_real_path(path, self._loaded_zips)
        print(f"  📂 [Z_Lib] OPEN   mode={mode!r}   › {path}")
        return open(real_path, mode, **kwargs)

    def resolve(self, path: str) -> Path:
        """
        Resolve a virtual path to a real filesystem path (Path object).
        Useful for integration with libraries like Polars, Pillow, xlwings.
        """
        return resolve_to_real_path(path, self._loaded_zips)

    def _cleanup(self) -> None:
        """
        Force unload all ZIPS (cleanup).
        """
        remaining = list(self._loaded_zips)
        if remaining:
            print(f"  🧹 [Z_Lib] CLEANUP  ▶  unloading {len(remaining)} ZIP(s) ...")
            for zip_path in remaining:
                self.unload_zip(zip_path)
            print(f"     └─ ✅ all ZIPs closed")

    def __del__(self) -> None:
        self._cleanup()
