#!/usr/bin/env python3

import os
import codekit.codetools as codetools
import pytest


def test_tempdir():
    """Test temporary directory context manager"""
    with codetools.TempDir() as temp_dir:
        assert os.path.exists(temp_dir)
    assert os.path.exists(temp_dir) is False


def test_debug_lvl_from_env():
    """fetching default debug level from DM_SQUARE_DEBUG env var"""

    # default when unset
    os.environ['DM_SQUARE_DEBUG'] = ''
    assert codetools.debug_lvl_from_env() == 0

    with pytest.raises(RuntimeError):
        os.environ['DM_SQUARE_DEBUG'] = 'foo'
        codetools.debug_lvl_from_env()

    os.environ['DM_SQUARE_DEBUG'] = '42'
    codetools.debug_lvl_from_env() == 42
