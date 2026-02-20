from typing import TypedDict, Literal, IO
from pathlib import Path

OpenMode = Literal["r", "rw"]

class ZipHandle(TypedDict):
    path: str              # Original ZIP file path
    temp_dir: str          # Path to the temporary directory where ZIP is extracted
    mode: OpenMode         # "r" or "rw"

