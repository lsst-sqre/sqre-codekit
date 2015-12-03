import os
import codekit.codetools as codetools


def test_tempdir():
    with codetools.TempDir() as temp_dir:
        assert os.path.exists(temp_dir)
    assert os.path.exists(temp_dir) is False
