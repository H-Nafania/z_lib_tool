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
        real_dst_result = shutil.copy2(real_src, real_dst, **kwargs)
        
        # Return virtual path of dst?
        # shutil.copy2 returns the destination file path.
        # It's hard to map back exactly if we don't know if dst was a dir or file.
        # But usually users ignore return value.
        # For correctness, we might try to constructing it, but simple str(real_dst_result) is real path.
        # Let's return the real path for now, or just the input dst string if user wants predictable return.
        # Design choice: Return real path (as it's what local shutil does relative to CWD)
        return str(real_dst_result)

    def move(self, src: str, dst: str, **kwargs) -> str:
        real_src = self._z_lib.resolve(src)
        real_dst = self._z_lib.resolve(dst)
        return str(shutil.move(real_src, real_dst, **kwargs))
        
    def copytree(self, src: str, dst: str, **kwargs) -> str:
        real_src = self._z_lib.resolve(src)
        real_dst = self._z_lib.resolve(dst)
        return str(shutil.copytree(real_src, real_dst, **kwargs))

    def rmtree(self, path: str, **kwargs) -> None:
        real_path = self._z_lib.resolve(path)
        shutil.rmtree(real_path, **kwargs)
