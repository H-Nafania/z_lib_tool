import pytest
import shutil
import zipfile
import os
from pathlib import Path
from z_lib.backend.zipfile_backend import ZipFileBackend
from z_lib._types import ZipHandle

@pytest.fixture
def sample_zip(tmp_path):
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("file1.txt", "content1")
        zf.writestr("folder/file2.txt", "content2")
    return zip_path

def test_open_existing_zip(sample_zip):
    backend = ZipFileBackend()
    # Assuming sample_zip is a Path object, resolve ensures we pass absolute path if needed
    handle = backend.open(str(sample_zip), create=False, mode="r")
    
    # Compare standardized paths
    assert Path(handle["path"]).resolve() == sample_zip.resolve()
    assert os.path.isdir(handle["temp_dir"])
    assert (Path(handle["temp_dir"]) / "file1.txt").exists()
    assert (Path(handle["temp_dir"]) / "folder/file2.txt").exists()
    
    # Cleanup (read-only, save=False)
    backend.close(handle, save=False)
    assert not os.path.exists(handle["temp_dir"])
    # Original should be untouched
    assert sample_zip.exists()

def test_create_new_zip(tmp_path):
    zip_path = tmp_path / "new.zip"
    backend = ZipFileBackend()
    
    # Create new
    handle = backend.open(str(zip_path), create=True, mode="rw")
    assert os.path.isdir(handle["temp_dir"])
    assert not os.listdir(handle["temp_dir"]) # Empty
    
    # Add file
    (Path(handle["temp_dir"]) / "new_file.txt").write_text("new content", encoding="utf-8")
    
    # Save
    backend.close(handle, save=True)
    
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path) as zf:
        assert "new_file.txt" in zf.namelist()
        assert zf.read("new_file.txt") == b"new content"

def test_modify_existing_zip(sample_zip):
    backend = ZipFileBackend()
    handle = backend.open(str(sample_zip), create=False, mode="rw")
    
    # Modify file
    (Path(handle["temp_dir"]) / "file1.txt").write_text("modified", encoding="utf-8")
    # Delete file
    os.remove(Path(handle["temp_dir"]) / "folder/file2.txt")
    
    # Save
    backend.close(handle, save=True)
    
    with zipfile.ZipFile(sample_zip) as zf:
        assert zf.read("file1.txt") == b"modified"
        assert "folder/file2.txt" not in zf.namelist()

def test_close_without_save(sample_zip):
    backend = ZipFileBackend()
    handle = backend.open(str(sample_zip), create=False, mode="rw")
    
    # Modify file but don't save
    (Path(handle["temp_dir"]) / "file1.txt").write_text("modified", encoding="utf-8")
    
    backend.close(handle, save=False)
    
    # Verify original is valid and UNCHANGED
    with zipfile.ZipFile(sample_zip) as zf:
        assert zf.read("file1.txt") == b"content1"
