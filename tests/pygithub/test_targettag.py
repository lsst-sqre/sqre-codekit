#!/usr/bin/env python3

import codekit.pygithub
import github
import itertools
import pytest


@pytest.fixture
def git_author():
    return github.InputGitAuthor(name='foo', email='foo@exmaple.org')


def test_init(git_author):
    """Test TargetTag object instantiation"""

    t_tag = codekit.pygithub.TargetTag(
        name='foo',
        sha='bar',
        message='baz',
        tagger=git_author,
    )

    assert isinstance(t_tag, codekit.pygithub.TargetTag), type(t_tag)


def test_attributes(git_author):
    """Test TargetTag attributes"""

    t_tag = codekit.pygithub.TargetTag(
        name='foo',
        sha='bar',
        message='baz',
        tagger=git_author,
    )
    assert t_tag.name == 'foo'
    assert t_tag.sha == 'bar'
    assert t_tag.message == 'baz'
    assert isinstance(t_tag.tagger, github.InputGitAuthor), type(t_tag.tagger)


def test_init_required_args(git_author):
    """TargetTag requires named args"""

    all_args = dict(
        name='foo',
        sha='bar',
        message='baz',
        tagger=git_author,
    )

    args = {}
    # try all named args but one
    for k, v in itertools.islice(all_args.items(), len(all_args) - 1):
        args[k] = v

        with pytest.raises(KeyError):
            codekit.pygithub.TargetTag(**args)


def test_init_tagger_type():
    """TargetTag tagger named arg must be correct type"""
    with pytest.raises(AssertionError):
        codekit.pygithub.TargetTag(
            name='foo',
            sha='bar',
            message='baz',
            tagger='bonk',
        )
