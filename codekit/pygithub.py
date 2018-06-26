"""
pygithub based help functions for interacting with the github api.
"""

from codekit.codetools import debug
from github import Github
from public import public
import codekit.codetools as codetools
import collections
import github
import itertools
import textwrap

github.MainClass.DEFAULT_TIMEOUT = 15  # timeouts creating teams w/ many repos


@public
def setup_logging(verbosity=0):
    """Enable pygithub HTTP request tracing if verbosity is 2+."""
    if verbosity and verbosity > 1:
        github.enable_console_debug_logging()


class CaughtRepositoryError(Exception):
    """Simple exception class intended to bundle together a
    github.Repository.Repository object and a thrown exception
    """
    def __init__(self, repo, caught, msg):
        assert isinstance(repo, github.Repository.Repository), type(repo)
        assert isinstance(caught, github.GithubException), type(caught)

        self.repo = repo
        self.caught = caught
        self.msg = msg

    def __str__(self):
        return textwrap.dedent("""\
            Caught: {cls}
              In repo: {repo}
              Message: {msg}
              Exception Message: {e}\
            """.format(
            cls=type(self.caught),
            repo=self.repo.full_name,
            msg=self.msg,
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
    def __init__(self, org, caught, msg):
        assert isinstance(org, github.Organization.Organization), type(org)
        assert isinstance(caught, github.GithubException), type(caught)

        self.org = org
        self.caught = caught
        self.msg = msg

    def __str__(self):
        return textwrap.dedent("""\
            Caught: {cls}
              In org: {org}
              Message: {msg}
              Exception Message: {e}\
            """.format(
            cls=type(self.caught),
            org=self.org.login,
            msg=self.msg,
            e=str(self.caught)
        ))


class RepositoryTeamMembershipError(Exception):
    def __init__(self, repo, repo_team_names, allow_teams, deny_teams):
        assert isinstance(repo, github.Repository.Repository), type(repo)

        self.repo = repo
        self.repo_team_names = repo_team_names
        self.allow_teams = allow_teams
        self.deny_teams = deny_teams

    def __str__(self):
        return textwrap.dedent("""\
            Invalid team membership for {repo}
              has teams:     {repo_teams}
              allowed teams: {allow}
              denied teams:  {deny}\
            """.format(
            repo=self.repo.full_name,
            repo_teams=self.repo_team_names,
            allow=self.allow_teams,
            deny=self.deny_teams,
        ))


class TargetTag(collections.UserDict):
    """Represents an abstract git tag that is independent of a git repository.
    This is an a rough analog of `pygithub`s `github.GitTag.GitTag` class but
    is intended to be directly instantiated while `GitTag` is not.

    Objects of this class may generally be treated as a `dict`.
    """

    def __init__(self, *args, **kwargs):
        """These named parameters are required:
            - `name`
            - `sha`
            - `message`
            - `tagger`

        The value of `tagger` must be a `github.InputGitAuthor`.
        """

        required_keys = ['name', 'sha', 'message', 'tagger']
        for rk in required_keys:
            if rk not in kwargs:
                raise KeyError("missing required key: {rk}".format(rk=rk))

        # pygithub requires that the authorship on a tag be set with a
        # github.InputGitAuthor object
        tagger = kwargs['tagger']
        assert isinstance(tagger, github.InputGitAuthor), type(tagger)

        super(TargetTag, self).__init__(*args, **kwargs)

    def __getattr__(self, item):
        """Allow keys to be looked up as attributes."""
        return self[item]


@public
def login_github(token_path=None, token=None):
    """Log into GitHub using an existing token.

    Parameters
    ----------
    token_path : str, optional
        Path to the token file. The default token is used otherwise.

    token: str, optional
        Literal token string. If specified, this value is used instead of
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
    assert isinstance(org, github.Organization.Organization), type(org)

    try:
        org_teams = list(org.get_teams())
    except github.RateLimitExceededException:
        raise
    except github.GithubException as e:
        msg = 'error getting teams'
        raise CaughtOrganizationError(org, e, msg) from None

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


@public
def check_repo_teams(repo, allow_teams, deny_teams, team_names=None):
    """Check if repo teams match allow/deny lists

    Parameters
    ----------
    repo: github.Repository.Repository
        repo to check for membership

    allow_teams: list(str)
        list of team names that repo MUST belong to at least one of.

    deny_teams: list(str)
        list of team that repo MUST NOT be a member of.

    team_names: list(str)
        list of the team name which the repo is a member of (optional).
        Providing this list saves retrieving the list of teams from the github
        API.

    Raises
    ------
    RepositoryTeamMembershipError
        Upon permission error
    """
    assert isinstance(repo, github.Repository.Repository), type(repo)

    # fetch team names if a list was not passed
    if not team_names:
        try:
            team_names = [t.name for t in repo.get_teams()]
        except github.RateLimitExceededException:
            raise
        except github.GithubException as e:
            msg = 'error getting teams'
            raise CaughtRepositoryError(repo, e, msg) from None

    if not any(x in team_names for x in allow_teams)\
       or any(x in team_names for x in deny_teams):
        raise RepositoryTeamMembershipError(
            repo,
            team_names,
            allow_teams=allow_teams,
            deny_teams=deny_teams
        )


@public
def get_default_ref(repo):
    """Return a `github.GitRef` object for the HEAD of the default branch.

    Parameters
    ----------
    repo: github.Repository.Repository
        repo to get default branch head ref from

    Returns
    -------
    head : :class:`github.GitRef` instance

    Raises
    ------
    github.RateLimitExceededException
    codekit.pygithub.CaughtRepositoryError
    """
    assert isinstance(repo, github.Repository.Repository), type(repo)

    # XXX this probably should be resolved via repos.yaml
    default_branch = repo.default_branch
    default_branch_ref = "heads/{ref}".format(ref=default_branch)

    # if accessing the default branch fails something is seriously wrong...
    try:
        head = repo.get_git_ref(default_branch_ref)
    except github.RateLimitExceededException:
        raise
    except github.GithubException as e:
        msg = "error getting ref: {ref}".format(ref=default_branch_ref)
        raise CaughtRepositoryError(repo, e, msg) from None

    return head
