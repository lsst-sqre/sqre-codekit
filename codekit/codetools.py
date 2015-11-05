"""
Module for assorted codetools scripts
"""

# technical debt
# --------------
# - package
# - exception rather than sysexit
# - check explictly for github3 version
# major API breakage between
# github3.py Python wrapper for the GitHub API(http://developer.github.com/v3)
#  INSTALLED: 0.9.4
#  LATEST:    1.0.0a1

import os
import sys
import urllib3
from github3 import login


__all__ = ['github', 'eups2git_ref', 'github_2fa_callback']


def github(authfile='~/.github_token'):
    """Return a github login token."""
    mytoken = None
    file_credential = os.path.expanduser(authfile)

    if not os.path.isfile(file_credential):
        print "You don't have a token in {0} ".format(file_credential)
        print "Have you run github-auth"
        sys.exit(1)

    with open(file_credential, 'r') as fd:
        mytoken = fd.readline().strip()

    gh = login(token=mytoken)

    return gh


def github_2fa_callback():
    # http://github3py.readthedocs.org/en/master/examples/two_factor_auth.html
    code = ''
    while not code:
        # The user could accidentally press Enter before being ready,
        # let's protect them from doing that.
        code = input('Enter 2FA code: ')
    return code


def eups2git_ref(eups_ref,
                 repo,
                 eupsbuild,
                 versiondb='https://raw.githubusercontent.com/lsst/versiondb/master/manifests',  # NOQA
                 debug=None):
    """Provide the eups tag given a git SHA."""
    # Thought of trying to parse the eups tag for the ref, but given
    # that doesn't help with the tag-based versions, might as well
    # look up versiondb for everything

    # eg. https://raw.githubusercontent.com/lsst/versiondb/master/manifests/b1108.txt  # NOQA
    shafile = versiondb + '/' + eupsbuild + '.txt'
    if debug:
        print shafile

    # Get the file tying shas to eups versions
    http = urllib3.PoolManager()
    refs = http.request('GET', shafile)
    if refs.status >= 300:
        raise RuntimeError('Failed GET with HTTP code', refs.status)
    reflines = refs.data.splitlines()

    for entry in reflines:
        # skip commented out and blank lines
        if entry.startswith('#'):
            continue
        if entry.startswith('BUILD'):
            continue
        if entry == '':
            continue

        elements = entry.split()
        eupspkg, sha, eupsver = elements[0:3]
        if eupspkg != repo:
            continue
        # sanity check
        if eupsver != eups_ref:
            raise RuntimeError('Something has gone wrong, release file does '
                               'not match manifest', eups_ref, eupsver)
        # get out if we find it
        if debug:
            print eupspkg, sha, eupsver
        break

    return sha
