#!/usr/bin/env python
"""Setup Tools Script"""
import os
import codecs
from setuptools import setup, find_packages

PACKAGENAME = 'sqre-codekit'
DESCRIPTION = 'LSST Data Management SQuaRE code management tools'
AUTHOR = 'Frossie Economou'
AUTHOR_EMAIL = 'frossie@lsst.org'
URL = 'https://github.com/lsst-sqre/sqre-codekit'
VERSION = '3.1.0'
LICENSE = 'MIT'


def read(filename):
    """Convenience function for includes"""
    full_filename = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        filename)
    return codecs.open(full_filename, 'r', 'utf-8').read()


long_description = read('README.md')  # pylint:disable=invalid-name


setup(
    name=PACKAGENAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    url=URL,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license=LICENSE,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: MIT License',
    ],
    keywords='lsst',
    packages=find_packages(exclude=['docs', 'tests*']),
    install_requires=[
        'sqre-codekit-github3.py==1.0.0a4',
        'uritemplate.py==2.0.0',
        'requests>=2.8.1,<3.0.0',
        'urllib3==1.22',
        'progressbar2==3.11.0',
        'GitPython==1.0.1',
        'MapGitConfig==1.1'
    ],
    setup_requires=[
        'pytest-runner>=2.11.1,<3'
    ],
    tests_require=[
        'pytest>=3,<4',
        'pytest-flake8>=0.8.1,<1'
    ],
    # package_data={},
    entry_points={
        'console_scripts': [
            'github-auth = codekit.cli.github_auth:main',
            'github-delete-shadow = codekit.cli.github_delete_shadow:main',
            'github-fork-repos = codekit.cli.github_fork_repos:main',
            'github-list-repos = codekit.cli.github_list_repos:main',
            'github-mv-repos-to-team = codekit.cli.github_mv_repos_to_team:main',  # NOQA
            'github-tag-version = codekit.cli.github_tag_version:main',
            'lsst-bp = codekit.cli.lsst_bp:main',
        ]
    }
)
