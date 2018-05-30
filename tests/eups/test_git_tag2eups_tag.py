#!/usr/bin/env python3

from codekit import eups


def test_git_tag2eups_tag_prefix():
    """Numeric tags should be prefixed with 'v'"""

    eups_tag = eups.git_tag2eups_tag('15')
    assert eups_tag == 'v15'

    # one `v` is enough
    eups_tag = eups.git_tag2eups_tag('v15')
    assert eups_tag == 'v15'


def test_git_tag2eups_tag_dots():
    """Dots `.` should be converted to underscores `_`"""

    eups_tag = eups.git_tag2eups_tag('a.b')
    assert eups_tag == 'a_b'


def test_git_tag2eups_tag_dashes():
    """Dashes `-` should be converted to underscores `_`"""

    eups_tag = eups.git_tag2eups_tag('a-b')
    assert eups_tag == 'a_b'


def test_git_tag2eups_tag_official():
    """Check mangling of official format git tags"""

    eups_tag = eups.git_tag2eups_tag('16.0.0')
    assert eups_tag == 'v16_0_0'


def test_git_tag2eups_tag_weekly():
    """Check mangling of weekly format git tags"""

    eups_tag = eups.git_tag2eups_tag('w.2018.19')
    assert eups_tag == 'w_2018_19'


def test_git_tag2eups_tag_daily():
    """Check mangling of daily format git tags"""

    eups_tag = eups.git_tag2eups_tag('d.2018.05.30')
    assert eups_tag == 'd_2018_05_30'
