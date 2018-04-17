#!/usr/bin/env python3
"""Test temporary directory context manager"""
import os
import codekit.codetools as codetools


def test_tempdir():
    """Test temporary directory context manager"""
    with codetools.TempDir() as temp_dir:
        assert os.path.exists(temp_dir)
    assert os.path.exists(temp_dir) is False
