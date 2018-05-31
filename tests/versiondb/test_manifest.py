#!/usr/bin/env python3

from codekit import codetools, versiondb
import codecs
import os
import pytest
import responses

codetools.setup_logging()


@pytest.fixture
def fixture_dir():
    d = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(d, 'data')


@pytest.fixture
def b3504(fixture_dir):
    filename = os.path.join(fixture_dir, 'b3504.txt')
    with codecs.open(filename, 'r', encoding='utf8') as file:
        return file.read()


@responses.activate
def test_init():
    # should not make any http requests
    m = versiondb.Manifest('b1234')
    assert isinstance(m, versiondb.Manifest)


@responses.activate
def test_b3504(b3504):
    responses.add(
        responses.Response(
            method='GET',
            url='https://raw.githubusercontent.com/lsst/versiondb'
                '/master/manifests/b3504.txt',
            body=b3504,
        ),
    )
    m = versiondb.Manifest(name='b3504')
    assert m.name == 'b3504'

    # spot check a couple of products
    products = m.products
    assert products['apr']['name'] == 'apr'
    assert products['apr']['sha'] == '39b3212aa46217e4f485b02496381907da8b8d7a'
    assert products['apr']['eups_version'] == '1.5.2'
    assert products['apr']['dependencies'] == []

    assert products['skymap']['name'] == 'skymap'
    assert products['skymap']['sha'] == \
        '3609236c8b3caebe32fc9b619541bb650e33f4f1'
    assert products['skymap']['eups_version'] == '14.0-4-g3609236+6'
    assert products['skymap']['dependencies'] == ['numpy', 'afw', 'healpy']
