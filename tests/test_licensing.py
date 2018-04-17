# !/usr/bin/env python3
"""Test the licensing conversion functions"""
from __future__ import print_function
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import pytest

from codekit.licensing import convert_boilerplate

# pylint: disable=redefined-outer-name


def test_py_boilerplate_conversion(py_truth):
    """Test conversion of Python boilerplate"""
    example_input, expected_result = py_truth
    converted_text = convert_boilerplate(StringIO(example_input))
    assert expected_result == converted_text


def test_py_boilerplate_rerun(py_truth):
    """Verify that the conversion doesn't change converted documents"""
    _, expected_result = py_truth
    converted_text = convert_boilerplate(StringIO(expected_result))
    assert expected_result == converted_text


def test_cpp_boilerplate_conversion(cpp_truth):
    """Test conversion of C++ boilerplate"""
    example_input, expected_result = cpp_truth
    converted_text = convert_boilerplate(StringIO(example_input))
    print(converted_text)
    assert expected_result == converted_text


def test_cpp_boilerplate_rerun(cpp_truth):
    """Verify that the conversion doesn't change converted documents"""
    _, expected_result = cpp_truth
    converted_text = convert_boilerplate(StringIO(expected_result))
    print(converted_text)
    assert expected_result == converted_text

# The linter gets confused by the examples.
# pylint: disable=missing-docstring


@pytest.fixture
def py_truth():
    # Note how the Python example includes bad whitespace
    example_input = """from __future__ import absolute_import, division
#
# LSST Data Management System
# Copyright 2015 LSST Corporation.
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.
#
\"\"\"Utilities that should be imported into the lsst.afw.coord namespace when lsst.afw.coord is used
In the case of the assert functions, importing them makes them available in lsst.utils.tests.TestCase
\"\"\"
import lsst.utils.tests
import lsst.afw.geom as afwGeom
"""  # noqa: E501

    # bad whitespace removed in expected output
    expected_result = """from __future__ import absolute_import, division
#
# LSST Data Management System
# See the COPYRIGHT and LICENSE files in the top-level directory of this
# package for notices and licensing terms.
#
\"\"\"Utilities that should be imported into the lsst.afw.coord namespace when lsst.afw.coord is used
In the case of the assert functions, importing them makes them available in lsst.utils.tests.TestCase
\"\"\"
import lsst.utils.tests
import lsst.afw.geom as afwGeom
"""  # noqa: E501
    return example_input, expected_result


@pytest.fixture
def cpp_truth():
    example_input = """/*
 * LSST Data Management System
 * Copyright 2014 LSST Corporation.
 *
 * This product includes software developed by the
 * LSST Project (http://www.lsst.org/).
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the LSST License Statement and
 * the GNU General Public License along with this program.  If not,
 * see <http://www.lsstcorp.org/LegalNotices/>.
 */

#include "lsst/afw/cameraGeom/CameraSys.h"

namespace lsst {
"""

    expected_result = """/*
 * LSST Data Management System
 * See the COPYRIGHT and LICENSE files in the top-level directory of this
 * package for notices and licensing terms.
 */

#include "lsst/afw/cameraGeom/CameraSys.h"

namespace lsst {
"""
    return example_input, expected_result
