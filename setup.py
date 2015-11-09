from setuptools import setup, find_packages
import os
import codecs


PACKAGENAME = 'sqre-codekit'
DESCRIPTION = 'LSST Data Management SQuaRE code management tools'
AUTHOR = 'Frossie Economou'
AUTHOR_EMAIL = 'frossie@lsst.org'
URL = 'https://github.com/lsst-sqre/sqre-codekit'
VERSION = '0.0.0.dev0'


def read(filename):
    full_filename = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        filename)
    return codecs.open(full_filename, 'r', 'utf-8').read()

long_description = read('README.md')


setup(
    name=PACKAGENAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    url=URL,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='lsst',
    packages=find_packages(exclude=['docs', 'tests*']),
    install_requires=['github3.py', 'urllib3', 'progress'],
    tests_require=['nose', 'tox'],
    # package_data={},
    entry_points={
        'console_scripts': [
            'github-pull-request = codekit.cli.github_pull_request:main',
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
