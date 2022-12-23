import sys
import pytest

@pytest.fixture()
def tmpsyspath():
    orig_paths = sys.path.copy()
    yield sys.path
    sys.path = orig_paths