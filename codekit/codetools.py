"""Assorted codetools utility functions."""

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


__all__ = ['login_github', 'eups2git_ref', 'repos_for_team',
           'github_2fa_callback']


def login_github(token_path=None):
    """Log into GitHub using an existing token.

    Parameters
    ----------
    token_path : str, optional
        Path to the token file. The default token is used otherwise.

    Returns
    -------
    gh : :class:`github3.GitHub` instance
        A GitHub login instance.
    """
    if token_path is None:
        # Try the default token
        token_path = '~/.sq_github_token'
    token_path = os.path.expandvars(os.path.expanduser(token_path))

    if not os.path.isfile(token_path):
        print "You don't have a token in {0} ".format(token_path)
        print "Have you run github-auth"
        sys.exit(1)

    with open(token_path, 'r') as fd:
        mytoken = fd.readline().strip()

    gh = login(token=mytoken, two_factor_callback=github_2fa_callback)

    return gh


def github_2fa_callback():
    # http://github3py.readthedocs.org/en/master/examples/two_factor_auth.html
    code = ''
    while not code:
        # The user could accidentally press Enter before being ready,
        # let's protect them from doing that.
        code = input('Enter 2FA code: ')
    return code


def repos_for_team(org, teams=None):
    """Iterate over repos in a GitHub organization that are in the given
    set of teams.

    Parameters
    ----------
    org : class:`github3.github3.orgs.Organization` instance
        The GitHub organization to operate in. Usually created with the
        :meth:`github3.GitHub.organization` method.
    teams : iterable
        A sequence of team names (as strings). If `None` (default) then
        team identity will be ignored and all repos in the organization
        will be iterated over.

    Yields
    ------
    repo : :class:`github3.repos.repo.Repository`
        Yields repositiory instances that pass organization and team criteria.
    """
    if teams is not None:
        teams = set(teams)
    for repo in org.iter_repos():
        repo_teams = set([t.name for t in repo.iter_teams()])
        if teams is None:
            yield repo
        elif repo_teams.isdisjoint(teams) is False:
            yield repo


def open_repo(org, repo_name):
    """Open a :class:`github3.repos.repo.Repository` instance by name
    in a GitHub organization.

    Parameters
    ----------
    org : class:`github3.github3.orgs.Organization` instance
        The GitHub organization to operate in. Usually created with the
        :meth:`github3.GitHub.organization` method.
    repo_name : str
        Name of the repository (without the organization namespace).
        E.g. `'afw'`.

    Returns
    -------
    repo : :class:`github3.repos.repo.Repository`
        The repository instance.
    """
    for repo in org.iter_repos():
        if repo.name == repo_name:
            return repo


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
