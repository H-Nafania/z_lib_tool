import pytest
import shutil
import zipfile
import os
from pathlib import Path
from z_lib.core import Z_Lib
from z_lib.path_resolver import normalize_path

@pytest.fixture
def z_lib_instance():
    z = Z_Lib()
    yield z
    z._cleanup()

@pytest.fixture
def test_structure(tmp_path):
    # Setup nested structure
    # root/
    #   normal_file.txt
    #   archive.zip/
    #     inner_file.txt
    #     inner_folder/
    
    root = tmp_path / "root"
    root.mkdir()
    (root / "normal_file.txt").write_text("normal")
    
    archive = root / "archive.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("inner_file.txt", "inner")
        zf.writestr("inner_folder/inner_sub.txt", "sub")
        
    return root

def test_z_os_path_methods(z_lib_instance, test_structure):
    archive_path = str(test_structure / "archive.zip")
    z_lib_instance.load_zip(archive_path)
    
    # Exists
    assert z_lib_instance.os.path.exists(f"{archive_path}/inner_file.txt")
    assert z_lib_instance.os.path.exists(f"{archive_path}")
    assert not z_lib_instance.os.path.exists(f"{archive_path}/nonexistent")
    
    # Isfile/Isdir
    assert z_lib_instance.os.path.isfile(f"{archive_path}/inner_file.txt")
    assert z_lib_instance.os.path.isdir(f"{archive_path}/inner_folder")
    
    # Join
    assert z_lib_instance.os.path.join(archive_path, "folder", "file.txt") == f"{normalize_path(archive_path)}/folder/file.txt"

def test_z_os_methods(z_lib_instance, test_structure):
    archive_path = str(test_structure / "archive.zip")
    z_lib_instance.load_zip(archive_path, mode="rw")
    
    # Listdir
    files = z_lib_instance.os.listdir(archive_path)
    assert "inner_file.txt" in files
    assert "inner_folder" in files
    
    # Mkdir
    new_dir = f"{archive_path}/new_dir"
    z_lib_instance.os.mkdir(new_dir)
    assert z_lib_instance.os.path.isdir(new_dir)
    
    # Remove
    z_lib_instance.os.remove(f"{archive_path}/inner_file.txt")
    assert not z_lib_instance.os.path.exists(f"{archive_path}/inner_file.txt")

def test_z_shutil_methods(z_lib_instance, test_structure, tmp_path):
    archive_path = str(test_structure / "archive.zip")
    z_lib_instance.load_zip(archive_path, mode="rw")
    
    src = f"{archive_path}/inner_folder/inner_sub.txt"
    dst = f"{archive_path}/copied.txt"
    
    # Copy within ZIP
    z_lib_instance.shutil.copy2(src, dst)
    assert z_lib_instance.os.path.exists(dst)
    
    # Copy out of ZIP
    local_dst = tmp_path / "exported.txt"
    z_lib_instance.shutil.copy2(src, str(local_dst))
    assert local_dst.exists()
    assert local_dst.read_text() == "sub"

def test_walk_zip(z_lib_instance, test_structure):
    archive_path = str(test_structure / "archive.zip")
    z_lib_instance.load_zip(archive_path)
    
    # Walk the ZIP
    # Expected:
    # root: archive.zip
    #   dirs: [inner_folder]
    #   files: [inner_file.txt]
    # root: archive.zip/inner_folder
    #   dirs: []
    #   files: [inner_sub.txt]
    
    walk_gen = z_lib_instance.os.walk(archive_path)
    
    root, dirs, files = next(walk_gen)
    # Normalize to compare strings safely
    assert normalize_path(root) == normalize_path(archive_path)
    assert "inner_folder" in dirs
    assert "inner_file.txt" in files
    
    # Next step could be inner_folder (depends on walk order, usually topdown=True)
    # Let's collect all
    all_roots = [normalize_path(root)]
    for root, d, f in walk_gen:
        all_roots.append(normalize_path(root))
        
    assert f"{normalize_path(archive_path)}/inner_folder" in all_roots
