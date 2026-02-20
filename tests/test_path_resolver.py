import pytest
import os
from pathlib import Path
from z_lib.path_resolver import normalize_path, split_zip_path, resolve_to_real_path, find_longest_match_handle
from z_lib.exceptions import ZipNotLoadedError
from z_lib._types import ZipHandle

def test_normalize_path():
    assert normalize_path("a\\b\\c") == "a/b/c"
    assert normalize_path("a/b/c") == "a/b/c"

def test_split_zip_path():
    assert split_zip_path("a/b.zip/c/d.txt") == ("a/b.zip", "c/d.txt")
    assert split_zip_path("archive.zip") == ("archive.zip", "")
    assert split_zip_path("folder/file.txt") == (None, "folder/file.txt")
    # Windows style input
    assert split_zip_path("data\\test.zip\\file.txt") == ("data/test.zip", "file.txt")

def test_resolve_to_real_path_simple():
    temp_dir_str = "/tmp/uuid1"
    # Ensure we treat temp_dir as a proper Path object for comparison
    # On Windows, "/tmp/uuid1" might be interpreted relative to current drive root.
    # To be safe, we rely on pathlib's behavior for the platform.
    temp_dir = Path(temp_dir_str)
    
    loaded_zips = {
        "data/test.zip": ZipHandle(path="data/test.zip", temp_dir=temp_dir_str, mode="r")
    }
    
    # Case 1: File inside zip
    real_path = resolve_to_real_path("data/test.zip/folder/file.txt", loaded_zips)
    expected = temp_dir / "folder/file.txt"
    assert real_path == expected

    # Case 2: Root of zip
    real_path = resolve_to_real_path("data/test.zip", loaded_zips)
    assert real_path == temp_dir

def test_resolve_to_real_path_nested_concept():
    # Attempting to verify longest match logic
    temp_dir_a = Path("/tmp/uuid_a")
    temp_dir_b = Path("/tmp/uuid_b")
    
    loaded_zips = {
        "a.zip": ZipHandle(path="a.zip", temp_dir=str(temp_dir_a), mode="r"),
        "a.zip/b.zip": ZipHandle(path="a.zip/b.zip", temp_dir=str(temp_dir_b), mode="r")
    }
    
    # Path targeting inside b.zip (which is loaded as a separate entity)
    real_path = resolve_to_real_path("a.zip/b.zip/content.txt", loaded_zips)
    expected = temp_dir_b / "content.txt"
    assert real_path == expected
    
    # Path targeting inside a.zip but NOT inside b.zip
    real_path = resolve_to_real_path("a.zip/other.txt", loaded_zips)
    expected = temp_dir_a / "other.txt"
    assert real_path == expected

def test_resolve_not_loaded_error():
    loaded_zips = {}
    with pytest.raises(ZipNotLoadedError):
        resolve_to_real_path("unloaded.zip/file.txt", loaded_zips)

def test_resolve_normal_path():
    loaded_zips = {}
    # Use resolve() to compare absolute paths
    p = resolve_to_real_path("some/local/file.txt", loaded_zips)
    expected = Path("some/local/file.txt").resolve()
    assert p == expected
