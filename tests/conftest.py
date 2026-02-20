import pytest
from z_lib.core import Z_Lib

@pytest.fixture
def z_lib_instance():
    z = Z_Lib()
    yield z
    z._cleanup()
