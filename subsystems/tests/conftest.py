import sys
import pytest

@pytest.fixture()
def tmpsyspath(tmpdir):
    orig_paths = sys.path.copy()
    orig_paths.append(str(tmpdir))
    yield sys.path
    sys.path = orig_paths