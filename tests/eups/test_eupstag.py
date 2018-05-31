#!/usr/bin/env python3

from codekit import codetools, eups
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
def v15_0(fixture_dir):
    filename = os.path.join(fixture_dir, 'v15_0.list')
    with codecs.open(filename, 'r', encoding='utf8') as file:
        return file.read()


@pytest.fixture
def d_2018_05_08(fixture_dir):
    filename = os.path.join(fixture_dir, 'd_2018_05_08.list')
    with codecs.open(filename, 'r', encoding='utf8') as file:
        return file.read()


@responses.activate
def test_init():
    # should not make any http requests
    et = eups.EupsTag('v42')
    assert isinstance(et, eups.EupsTag)


@responses.activate
def test_v15_0(v15_0):
    responses.add(
        responses.Response(
            method='GET',
            url='https://eups.lsst.codes/stack/src/tags/v15_0.list',
            body=v15_0,
        ),
    )
    et = eups.EupsTag(name='v15_0')
    assert et.name == 'v15_0'
    # v15_0 is prior to d_2018_05_08, when the BUILD= comment was introduced
    assert et.manifest is None

    # spot check a couple of products
    products = et.products
    assert products['apr']['name'] == 'apr'
    assert products['apr']['flavor'] == 'generic'
    assert products['apr']['eups_version'] == '1.5.2'

    assert products['skymap']['name'] == 'skymap'
    assert products['skymap']['flavor'] == 'generic'
    assert products['skymap']['eups_version'] == '15.0'


@responses.activate
def test_d_2018_05_08(d_2018_05_08):
    responses.add(
        responses.Response(
            method='GET',
            url='https://eups.lsst.codes/stack/src/tags/d_2018_05_08.list',
            body=d_2018_05_08,
        ),
    )
    et = eups.EupsTag(name='d_2018_05_08')
    assert et.name == 'd_2018_05_08'
    # d_2018_05_08 is when the BUILD= comment was introduced
    assert et.manifest == 'b3601'

    # spot check a couple of products
    products = et.products
    assert products['apr']['name'] == 'apr'
    assert products['apr']['flavor'] == 'generic'
    assert products['apr']['eups_version'] == '1.5.2'

    assert products['skymap']['name'] == 'skymap'
    assert products['skymap']['flavor'] == 'generic'
    assert products['skymap']['eups_version'] == '15.0-4-g5589a47+3'
