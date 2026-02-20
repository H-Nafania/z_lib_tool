import pytest
import os
import zipfile
from pathlib import Path
from z_lib.core import Z_Lib
from z_lib.exceptions import ZipNotLoadedError
from z_lib.path_resolver import normalize_path

@pytest.fixture
def z_lib_instance():
    z = Z_Lib()
    yield z
    z._cleanup()

@pytest.fixture
def test_zip(tmp_path):
    p = tmp_path / "test.zip"
    with zipfile.ZipFile(p, "w") as zf:
        zf.writestr("a.txt", "hello")
    return p

def test_load_and_unload(z_lib_instance, test_zip):
    # Load
    z_lib_instance.load_zip(str(test_zip))
    assert normalize_path(str(test_zip)) in z_lib_instance._loaded_zips
    
    # Check internal state
    handle = z_lib_instance._loaded_zips[normalize_path(str(test_zip))]
    assert os.path.exists(handle["temp_dir"])
    
    # Unload
    z_lib_instance.unload_zip(str(test_zip))
    assert normalize_path(str(test_zip)) not in z_lib_instance._loaded_zips
    assert not os.path.exists(handle["temp_dir"])

def test_open_read(z_lib_instance, test_zip):
    z_lib_instance.load_zip(str(test_zip))
    
    # Open file inside zip
    zip_file_path = f"{str(test_zip)}/a.txt"
    with z_lib_instance.open(zip_file_path, "r") as f:
        content = f.read()
        assert content == "hello"

def test_open_write_and_save(z_lib_instance, tmp_path):
    zip_path = tmp_path / "new.zip"
    
    # Create new zip
    z_lib_instance.load_zip(str(zip_path), create=True, mode="rw")
    
    # Write file
    file_path = f"{str(zip_path)}/new.txt"
    with z_lib_instance.open(file_path, "w") as f:
        f.write("new world")
        
    # Unload to save
    z_lib_instance.unload_zip(str(zip_path))
    
    # Verify
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path) as zf:
        assert zf.read("new.txt") == b"new world"

def test_swap_zip(z_lib_instance, tmp_path):
    zip1 = tmp_path / "1.zip"
    zip2 = tmp_path / "2.zip"
    
    z_lib_instance.swap_zip([str(zip1), str(zip2)], create=True)
    assert normalize_path(str(zip1)) in z_lib_instance._loaded_zips
    assert normalize_path(str(zip2)) in z_lib_instance._loaded_zips
    
    # Swap to only zip1
    z_lib_instance.swap_zip([str(zip1)])
    assert normalize_path(str(zip1)) in z_lib_instance._loaded_zips
    assert normalize_path(str(zip2)) not in z_lib_instance._loaded_zips

def test_resolve(z_lib_instance, test_zip):
    z_lib_instance.load_zip(str(test_zip))
    
    path = f"{str(test_zip)}/a.txt"
    real_path = z_lib_instance.resolve(path)
    
    assert isinstance(real_path, Path)
    assert real_path.exists()
    assert real_path.read_text() == "hello"

def test_load_nest(z_lib_instance, tmp_path):
    # Setup nested structure
    # folder/
    #   a.zip
    #   sub/
    #     b.zip
    
    folder = tmp_path / "nest"
    folder.mkdir()
    (folder / "sub").mkdir()
    
    zip1 = folder / "a.zip"
    zip2 = folder / "sub" / "b.zip"
    
    with zipfile.ZipFile(zip1, "w") as zf: zf.writestr("f1", "1")
    with zipfile.ZipFile(zip2, "w") as zf: zf.writestr("f2", "2")
    
    z_lib_instance.load_nest(str(folder), mode="r")
    
    assert normalize_path(str(zip1)) in z_lib_instance._loaded_zips
    assert normalize_path(str(zip2)) in z_lib_instance._loaded_zips
