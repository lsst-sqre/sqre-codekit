"""Assorted codetools utility functions."""
from __future__ import print_function
# technical debt
# --------------
# - package
# - check explictly for github3 version

import os
import shutil
import tempfile
# import re # Only used in SHA-sanity-check unreachable code
import urllib3
from github3 import login
import gitconfig


__all__ = ['login_github', 'eups2git_ref', 'repos_for_team',
           'github_2fa_callback', 'TempDir', 'gitusername', 'gituseremail',
           'get_team_id_by_name', 'get_git_credential_helper']


def login_github(token_path=None, token=None):
    """Log into GitHub using an existing token.

    Parameters
    ----------
    token_path : str, optional
        Path to the token file. The default token is used otherwise.

    token: str, optional
        Literial token string. If specifified, this value is used instead of
        reading from the token_path file.

    Returns
    -------
    gh : :class:`github3.GitHub` instance
        A GitHub login instance.
    """
    if token is None:
        if token_path is None:
            # Try the default token
            token_path = '~/.sq_github_token'
        token_path = os.path.expandvars(os.path.expanduser(token_path))

        if not os.path.isfile(token_path):
            print("You don't have a token in {0} ".format(token_path))
            print("Have you run github-auth?")
            raise EnvironmentError("No token in %s" % token_path)

        with open(token_path, 'r') as fdo:
            token = fdo.readline().strip()

    ghb = login(token=token, two_factor_callback=github_2fa_callback)

    return ghb


def gitusername():
    """
    Returns the user's name from .gitconfig if available
    """
    # pylint: disable=bare-except
    try:
        mygitconfig = gitconfig.GitConfig()
        return mygitconfig['user.name']
    except:
        return None


def gituseremail():
    """
    Returns the user's email from .gitconfig if available
    """

    # pylint: disable=bare-except
    try:
        mygitconfig = gitconfig.GitConfig()
        return mygitconfig['user.email']
    except:
        return None


def github_2fa_callback():
    """
    Prompt for two-factor code
    """
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
    for repo in org.repositories():
        repo_teams = set([t.name for t in repo.teams()])
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
    for repo in org.repositories():
        if repo.name == repo_name:
            return repo


def get_team_id_by_name(org, team_name, debug=False):
    """Get the ID of a team in a GitHub organization.

    Parameters
    ----------
    org : class:`github3.github3.orgs.Organization` instance
        The GitHub organization to operate in. Usually created with the
        :meth:`github3.GitHub.organization` method.
    team_name : `str`
        Name of the team to find
    debug : `bool`, optional
        Enable debug output.

    Returns
    -------
    team_id : `int` or `None`
        The team ID as an integer, or `None` if `team_name` is the empty string.

    Raises
    ------
    `NameError`
        If there is no team with the given name in the supplied organization.
    """

    if team_name == '':
        if debug:
            print("Searching for empty teamname -> None")
        return None  # Special case for empty teams
    teams = org.teams()
    try:
        while True:
            team = teams.next()
            if debug:
                print("Considering team %s with ID %i" % (team.name, team.id))
            if team.name == team_name:
                if debug:
                    print("Match found.")
                return team.id
    except StopIteration:
        raise NameError("No team '%s' in organization '%s'" % (team_name,
                                                               org.login))


def get_git_credential_helper(username, token):
    """Get a string suitable for inclusion in a git config as a credential
    helper, allowing authenticated access without prompting for a password.

    Useful for, e.g., doing a push to Github from a local repo.

    Parameters
    ----------
    username: `str`
        The GitHub username for the authenticated action.
    token: `str`
        The corresponding access token.

    Returns
    -------
    helper : `str`
        A string which is a runnable shell fragment for use in a git config.
    """
    # The initial bang tells git it's about to run a shell fragment.
    #  The rest is a string, which will be evaluated in the shell (so don't
    #  take unsanitized input from the outside world!)
    # It defines a function to swallow any input and put username and password
    #  on separate lines: it substitutes its parameter values into the
    #  username/password values.
    # This means it will work under `git credential fill`, which is the
    #  entire point.
    helper = '!"f() { cat > /dev/null ; echo username=' + username
    helper += ' ; echo password=' + token + ' ; } ; f"'
    return helper


def eups2git_ref(eups_ref,
                 repo,
                 eupsbuild,
                 versiondb='https://raw.githubusercontent.com/lsst/versiondb/master/manifests',  # NOQA pylint: disable=line-too-long
                 debug=None):
    """Provide the eups tag given a git SHA."""
    # Thought of trying to parse the eups tag for the ref, but given
    # that doesn't help with the tag-based versions, might as well
    # look up versiondb for everything

    # eg. https://raw.githubusercontent.com/lsst/versiondb/master/manifests/b1108.txt  # NOQA
    shafile = versiondb + '/' + eupsbuild + '.txt'
    if debug:
        print(shafile)

    # Get the file tying shas to eups versions
    http = urllib3.poolmanager.PoolManager()
    refs = http.request('GET', shafile)
    if refs.status >= 300:
        raise RuntimeError('Failed GET with HTTP code', refs.status)
    reflines = refs.data.splitlines()

    for entry in reflines:
        # Python 2/3 accomodation
        if not isinstance(entry, str):
            entry = str(entry, 'utf-8')
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
            print(eupspkg, sha, eupsver)

        break

        # We never reach this sanity check, so I am commenting it out.

        # sanity check that our digest looks like a sha1
        # pat = re.compile('\b[0-9a-f]{5,40}\b')
        # mat = pat.match(sha)
        # if not mat:
        #    raise RuntimeError('does not appear to be a sha1 digest', sha)

    return sha


class TempDir(object):
    """ContextManager for temporary directories.

    For example::

        import os
        with TempDir() as temp_dir:
            assert os.path.exists(temp_dir)
        assert os.path.exists(temp_dir) is False
    """

    # pylint: disable=too-few-public-methods
    def __init__(self):
        super(TempDir, self).__init__()
        self._temp_dir = tempfile.mkdtemp()

    def __enter__(self):
        return self._temp_dir

    def __exit__(self, ttype, value, traceback):
        shutil.rmtree(self._temp_dir)
        self._temp_dir = None
