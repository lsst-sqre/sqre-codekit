"""
pygithub based help functions for interacting with the github api.
"""

from codekit.codetools import debug
from github import Github
from public import public
import codekit.codetools as codetools
import github
import itertools
import logging
import textwrap

logging.basicConfig()
logger = logging.getLogger('codekit')
github.MainClass.DEFAULT_TIMEOUT = 15  # timeouts creating teams w/ many repos


class CaughtRepositoryError(Exception):
    """Simple exception class intended to bundle together a
    github.Repository.Repository object and a thrown exception
    """
    def __init__(self, repo, caught):
        assert isinstance(repo, github.Repository.Repository), type(repo)
        assert isinstance(caught, github.GithubException), type(caught)

        self.repo = repo
        self.caught = caught

    def __str__(self):
        return textwrap.dedent("""\
            Caught: {cls}
              In repo: {repo}
              Message: {e}\
            """.format(
            cls=type(self.caught),
            repo=self.repo.full_name,
            e=str(self.caught)
        ))


class CaughtTeamError(Exception):
    """Simple exception class intended to bundle together a github.Team.Team
    object and a thrown exception
    """
    def __init__(self, team, caught):
        assert isinstance(team, github.Team.Team), type(team)
        assert isinstance(caught, github.GithubException), type(caught)

        self.team = team
        self.caught = caught

    def __str__(self):
        return textwrap.dedent("""\
            Caught: {cls}
              In team: {team}@{org}
              Message: {e}\
            """.format(
            cls=type(self.caught),
            team=self.team.slug,
            org=self.team.organization.login,
            e=str(self.caught)
        ))


class CaughtOrganizationError(Exception):
    """Simple exception class intended to bundle together a
    github.Organization.Organization object and a thrown exception
    """
    def __init__(self, org, caught):
        assert isinstance(org, github.Organization.Organization), type(org)
        assert isinstance(caught, github.GithubException), type(caught)

        self.org = org
        self.caught = caught

    def __str__(self):
        return textwrap.dedent("""\
            Caught: {cls}
              In org: {org}
              Message: {e}\
            """.format(
            cls=type(self.caught),
            org=self.org.login,
            e=str(self.caught)
        ))


@public
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
    gh : :class:`github.GitHub` instance
        A GitHub login instance.
    """

    token = codetools.github_token(token_path=token_path, token=token)
    g = Github(token)
    debug_ratelimit(g)
    return g


@public
def find_tag_by_name(repo, tag_name, safe=True):
    """Find tag by name in a github Repository

    Parameters
    ----------
    repo: :class:`github.Repository` instance

    tag_name: str
        Short name of tag (not a fully qualified ref).

    safe: bool, optional
        Defaults to `True`. When `True`, `None` is returned on failure. When
        `False`, an exception will be raised upon failure.

    Returns
    -------
    gh : :class:`github.GitRef` instance or `None`

    Raises
    ------
    github.UnknownObjectException
        If git tag name does not exist in repo.
    """
    tagfmt = 'tags/{ref}'.format(ref=tag_name)

    try:
        ref = repo.get_git_ref(tagfmt)
        if ref and ref.ref:
            return ref
    except github.UnknownObjectException:
        if not safe:
            raise

    return None


@public
def get_repos_by_team(teams):
    """Find repos by membership in github team(s).

    Parameters
    ----------
    teams: list(github.Team.Team)
        list of Team objects

    Returns
    -------
    generator of github.Repository.Repository objects

    Raises
    ------
    github.GithubException
        Upon error from github api
    """
    return itertools.chain.from_iterable(
        t.get_repos() for t in teams
    )


@public
def get_teams_by_name(org, team_names):
    """Find team(s) in org by name(s).

    Parameters
    ----------
    org: github.Organization.Organization
        org to search for team(s)

    teams: list(str)
        list of team names to search for

    Returns
    -------
    list of github.Team.Team objects

    Raises
    ------
    github.GithubException
        Upon error from github api
    """
    assert isinstance(org, github.Organization.Organization),\
        type(org)
    assert isinstance(team_names, list), type(team_names)

    org_teams = list(org.get_teams())

    found_teams = []
    for name in team_names:
        debug("looking for team: {o}/'{t}'".format(
            o=org.login,
            t=name
        ))

        t = next((t for t in org_teams if t.name == name), None)
        if t:
            debug('  found')
            found_teams.append(t)
        else:
            debug('  not found')

    return found_teams


@public
def debug_ratelimit(g):
    """Log debug of github ratelimit information from last API call

    Parameters
    ----------
    org: github.MainClass.Github
        github object
    """
    assert isinstance(g, github.MainClass.Github), type(g)

    debug("github ratelimit: {rl}".format(rl=g.rate_limiting))
