from typing import Protocol, runtime_checkable
from .._types import ZipHandle, OpenMode

@runtime_checkable
class ZipBackend(Protocol):
    def open(self, path: str, create: bool, mode: OpenMode) -> ZipHandle:
        """
        Open (mount) a ZIP file.
        
        Args:
            path: Path to the ZIP file.
            create: If True, allow creating a new ZIP if it doesn't exist.
            mode: "r" (read-only) or "rw" (read-write).
            
        Returns:
            A ZipHandle dictionary containing the temp directory and metadata.
        """
        ...

    def close(self, handle: ZipHandle, save: bool) -> None:
        """
        Close (unmount) a ZIP file.
        
        Args:
            handle: The ZipHandle to close.
            save: If True and mode is "rw", save changes back to the original ZIP file.
        """
        ...
