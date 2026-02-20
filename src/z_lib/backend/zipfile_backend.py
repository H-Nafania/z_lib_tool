import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from .._types import ZipHandle, OpenMode
from ..exceptions import ZipPathError

class ZipFileBackend:
    def open(self, path: str, create: bool, mode: OpenMode = "rw") -> ZipHandle:
        path_obj = Path(path).resolve()
        
        if not path_obj.exists():
            if not create:
                raise FileNotFoundError(f"ZIP file not found: {path}")
            # If creating, just ensure parent dir exists? 
            # Ideally verify it ends with .zip or similar, but we trust caller.
        
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp(prefix="z_lib_")
        
        if path_obj.exists() and zipfile.is_zipfile(path_obj):
            # Extract existing ZIP
            with zipfile.ZipFile(path_obj, 'r') as zf:
                zf.extractall(temp_dir)
        elif path_obj.exists() and not zipfile.is_zipfile(path_obj):
             # File exists but is not a ZIP
             shutil.rmtree(temp_dir)
             raise ZipPathError(f"File exists but is not a valid ZIP file: {path}")

        # If creating new and file doesn't exist, temp_dir is already empty, which is correct.
        
        return ZipHandle(
            path=str(path_obj),
            temp_dir=temp_dir,
            mode=mode
        )

    def close(self, handle: ZipHandle, save: bool) -> None:
        temp_dir = Path(handle["temp_dir"])
        original_path = Path(handle["path"])
        mode = handle["mode"]

        try:
            # Save if required and allowed
            if save and mode == "rw" and temp_dir.exists():
                # Re-compress
                # We write to a temporary file first to avoid corruption if process is interrupted
                # But zipfile.ZipFile(path, 'w') truncates, so it's relatively safe if we don't crash mid-write.
                # For robustness, let's write to a temp file next to original then rename.
                
                # Check if original directory exists, if not create it (for new files)
                if not original_path.parent.exists():
                    original_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Create a temporary zip file
                fd, temp_zip_path = tempfile.mkstemp(dir=original_path.parent, suffix=".tmp_zip")
                os.close(fd)
                
                try:
                    with zipfile.ZipFile(temp_zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                        # os.walk ensures we visit all files
                        for root, dirs, files in os.walk(temp_dir):
                            for file in files:
                                file_path = Path(root) / file
                                arcname = file_path.relative_to(temp_dir)
                                zf.write(file_path, arcname)
                    
                    # Atomic replace
                    shutil.move(temp_zip_path, original_path)
                    
                except Exception:
                    # Clean up temp zip if failed
                    if os.path.exists(temp_zip_path):
                        os.remove(temp_zip_path)
                    raise

        finally:
            # Always clean up the temp directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
