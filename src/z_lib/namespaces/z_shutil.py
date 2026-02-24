import shutil
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..core import Z_Lib

class Z_Shutil:
    def __init__(self, z_lib: "Z_Lib"):
        self._z_lib = z_lib

    def copy2(self, src: str, dst: str, **kwargs) -> str:
        real_src = self._z_lib.resolve(src)
        real_dst = self._z_lib.resolve(dst)
        print(f"  📌 [Z_SHUTIL] copy2   {src}  ➜  {dst}")
        real_dst_result = shutil.copy2(real_src, real_dst, **kwargs)
        return str(real_dst_result)

    def move(self, src: str, dst: str, **kwargs) -> str:
        real_src = self._z_lib.resolve(src)
        real_dst = self._z_lib.resolve(dst)
        print(f"  ➡️  [Z_SHUTIL] move   {src}  ➜  {dst}")
        return str(shutil.move(real_src, real_dst, **kwargs))
        
    def copytree(self, src: str, dst: str, **kwargs) -> str:
        real_src = self._z_lib.resolve(src)
        real_dst = self._z_lib.resolve(dst)
        print(f"  🗂  [Z_SHUTIL] copytree   {src}  ➜  {dst}")
        return str(shutil.copytree(real_src, real_dst, **kwargs))

    def rmtree(self, path: str, **kwargs) -> None:
        real_path = self._z_lib.resolve(path)
        print(f"  🗑  [Z_SHUTIL] rmtree   › {path}")
        shutil.rmtree(real_path, **kwargs)
