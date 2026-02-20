import pytest
from PIL import Image
from z_lib.core import Z_Lib
from z_lib.path_resolver import normalize_path

def test_pillow_integration(z_lib_instance, tmp_path):
    zip_path = tmp_path / "images.zip"
    zip_str = str(zip_path)
    
    # 1. Create image in memory and save to ZIP
    z_lib_instance.load_zip(zip_str, create=True, mode="rw")
    
    img = Image.new('RGB', (100, 100), color = 'red')
    
    # Write using z_lib.open
    with z_lib_instance.open(f"{zip_str}/test.png", "wb") as f:
        img.save(f, format="PNG")
        
    z_lib_instance.unload_zip(zip_str)
    
    # 2. Re-load and Read image
    z_lib_instance.load_zip(zip_str, mode="r")
    
    # Read using z_lib.open
    with z_lib_instance.open(f"{zip_str}/test.png", "rb") as f:
        loaded_img = Image.open(f)
        assert loaded_img.size == (100, 100)
        assert loaded_img.getpixel((50, 50)) == (255, 0, 0)
        
    # 3. Use resolve() for direct path access
    real_path = z_lib_instance.resolve(f"{zip_str}/test.png")
    loaded_img_direct = Image.open(real_path)
    assert loaded_img_direct.size == (100, 100)
    assert loaded_img_direct.getpixel((50, 50)) == (255, 0, 0)
