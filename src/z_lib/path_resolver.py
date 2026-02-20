import os
import re
from pathlib import Path
from typing import Tuple, Optional, Any, Dict
from .exceptions import ZipPathError, ZipNotLoadedError
from ._types import ZipHandle

def normalize_path(path: str) -> str:
    """
    Normalize path separators to forward slashes for internal consistency.
    """
    return path.replace("\\", "/")

def split_zip_path(path: str) -> Tuple[Optional[str], str]:
    """
    Split a path into the ZIP file path and the internal path.
    Use simple heuristic: first component ending with .zip is the ZIP path.
    """
    norm_path = normalize_path(path)
    parts = norm_path.split("/")
    
    current_path_parts = []
    for i, part in enumerate(parts):
        current_path_parts.append(part)
        if part.lower().endswith(".zip"):
            zip_path = "/".join(current_path_parts)
            internal_parts = parts[i+1:]
            internal_path = "/".join(internal_parts)
            return zip_path, internal_path
            
    return None, path

def find_longest_match_handle(path: str, loaded_zips: Dict[str, ZipHandle]) -> Tuple[Optional[ZipHandle], str]:
    """
    Find the best matching loaded ZIP handle for the given path using longest match.
    
    Args:
        path: The virtual path to resolve.
        loaded_zips: Dictionary of loaded ZIP handles. Keys must be normalized strings.
        
    Returns:
        Tuple (handle, internal_path). Handle is None if no match found.
    """
    norm_path = normalize_path(path)
    
    # Sort keys by length descending to ensure we match nested zips (a.zip/b.zip) before parent (a.zip)
    # We assume verify keys in loaded_zips are already normalized.
    sorted_keys = sorted(loaded_zips.keys(), key=len, reverse=True)
    
    for zip_key in sorted_keys:
        # Check if path is exactly the zip_key or starts with zip_key + "/"
        if norm_path == zip_key or norm_path.startswith(zip_key + "/"):
            handle = loaded_zips[zip_key]
            internal_path = norm_path[len(zip_key):].lstrip("/")
            return handle, internal_path
            
    return None, path

def resolve_to_real_path(path: str, loaded_zips: Dict[str, ZipHandle]) -> Path:
    """
    Resolve a virtual path to a real temporary filesystem path.
    
    Args:
        path: The virtual path string.
        loaded_zips: A dictionary mapping resolved ZIP paths to ZipHandle.
        
    Returns:
        A pathlib.Path object pointing to the real file on disk.
        If path corresponds to a loaded ZIP root, returns the temp_dir.
        
    Raises:
        ZipNotLoadedError: If the ZIP file part of the path is not loaded.
    """
    handle, internal_path = find_longest_match_handle(path, loaded_zips)
    
    if handle:
        return Path(handle["temp_dir"]) / internal_path
    
    # If no handle matched, check if it looks like a zip path to give a better error
    potential_zip, _ = split_zip_path(path)
    if potential_zip:
        raise ZipNotLoadedError(f"ZIP file '{potential_zip}' is not loaded (or path '{path}' is invalid).")
    
    # Not a zip path, return absolute path
    return Path(path).resolve()
