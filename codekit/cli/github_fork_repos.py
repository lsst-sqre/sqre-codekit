#!/usr/bin/env python3

from codekit.codetools import debug, error, info, warn
from .. import codetools
import argparse
import codekit.pygithub as pygithub
import datetime
import github
import itertools
import logging
import os
import progressbar
import sys
import textwrap

progressbar.streams.wrap_stderr()
logging.basicConfig()
logger = logging.getLogger('codekit')


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        prog='github-fork-repos',
        description=textwrap.dedent("""
        Fork LSST repos into a showow GitHub organization.
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Part of codekit: https://github.com/lsst-sqre/sqre-codekit')
    parser.add_argument(
        '--src-org',
        dest='src_org',
        required=True,
        help='Organization to fork repos *from*')
    parser.add_argument(
        '--dst-org',
        dest='dst_org',
        required=True,
        help='Organization to fork repos *into*')
    parser.add_argument(
        '--team',
        action='append',
        required=True,
        help='Filter repos to fork by team membership'
             ' (can specify several times')
    parser.add_argument(
        '--token-path',
        default='~/.sq_github_token',
        help='Use a token (made with github-auth) in a non-standard location')
    parser.add_argument(
        '--token',
        default=None,
        help='Literal github personal access token string')
    parser.add_argument(
        '--limit',
        default=None,
        type=int,
        help='Maximum number of repos to fork')
    parser.add_argument(
        '--copy-teams',
        action='store_true',
        help=textwrap.dedent("""\
            Recreate team membership on forked repos.  This will copy *all*
            teams a repo is a member of, reguardless if they were specified as
            a selection "--team" or not.\
        """))
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        default=os.getenv('DM_SQUARE_DEBUG'),
        help='Debug mode')
    parser.add_argument('-v', '--version', action=codetools.ScmVersionAction)
    return parser.parse_args()


def find_teams_by_repo(src_repos):
    assert isinstance(src_repos, list), type(src_repos)

    # length of longest repo name
    max_name_len = len(max([r.full_name for r in src_repos], key=len))

    src_rt = {}
    for r in src_repos:
        teams = r.get_teams()
        team_names = [t.name for t in teams]
        debug("  {repo: >{w}} {teams}".format(
            repo=r.full_name,
            w=max_name_len,
            teams=team_names
        ))
        src_rt[r.full_name] = {'repo': r, 'teams': teams}

    return src_rt


def find_used_teams(src_rt):
    assert isinstance(src_rt, dict), type(src_rt)

    # extract an index of team names from all repos being forked, with the repo
    # objects as value(s)
    used_teams = {}
    for k, v in src_rt.items():
        for name in [t.name for t in v['teams']]:
            if name not in used_teams:
                used_teams[name] = [v['repo']]
            else:
                used_teams[name].append(v['repo'])

    return used_teams


def create_teams(
    org,
    teams,
    with_repos=False,
    ignore_existing=False,
    dry_run=False
):
    assert isinstance(org, github.Organization.Organization), type(org)
    assert isinstance(teams, dict), type(teams)

    # it takes fewer api calls to create team(s) with an explicit list of
    # members after all repos have been forked but this blows up if the team
    # already exists.

    debug("creating teams in {org}".format(org=org.login))

    # dict of dst org teams keyed by name (str) with team object as value
    dst_teams = {}
    for name, repos in teams.items():
        debug("creating team {o}/'{t}'".format(
            o=org.login,
            t=name
        ))

        if dry_run:
            debug('  (noop)')
            continue

        dst_t = None
        try:
            if with_repos:
                # need full qualified list of repos in the new org
                dst_repo_names = ['/'.join([org.login, r.name]) for r in repos]
                debug('  with members:')
                [debug("    {r}".format(r=r)) for r in dst_repo_names]
                dst_t = org.create_team(name, repo_names=dst_repo_names)
            else:
                dst_t = org.create_team(name)
        except github.GithubException as e:
            error("  {m}".format(m=e.data['message']))
            for oops in e.data['errors']:
                msg = oops['message']
                error("    {m}".format(m=msg))
                # if the error is for any cause other than the team already
                # existing, puke.
                if not\
                   (ignore_existing and 'Name has already been taken' in msg):
                    raise e

            dst_t = next(t for t in org.get_teams() if t.name in name)

        dst_teams[dst_t.name] = dst_t

    return dst_teams


def create_forks(dst_org, src_repos, dry_run=False):
    assert isinstance(dst_org, github.Organization.Organization),\
        type(dst_org)
    assert isinstance(src_repos, list), type(src_repos)

    repo_count = len(src_repos)

    widgets = ['Forking: ', progressbar.Bar(), ' ', progressbar.AdaptiveETA()]

    # XXX progressbar is not playing nicely with debug output and the advice in
    # the docs for working with logging don't have any effect.
    with progressbar.ProgressBar(
            widgets=widgets,
            max_value=repo_count) as pbar:

        new_forks = []
        repo_idx = 0
        for r in src_repos:
            pbar.update(repo_idx)
            repo_idx += 1

            # XXX per
            # https://developer.github.com/v3/repos/forks/#create-a-fork
            # fork creation is async and pygithub doesn't appear to wait.
            # https://github.com/PyGithub/PyGithub/blob/c44469965e4ea368b78c4055a8afcfcf08314585/github/Organization.py#L321-L336
            # so its possible that this may fail in some strange way such as
            # not returning all repo data, but it hasn't yet been observed.

            # get current time before API call in case fork creation is slow.
            now = datetime.datetime.now()

            debug("forking {r}".format(r=r.full_name))
            if dry_run:
                debug('  (noop)')
                continue

            fork = dst_org.create_fork(r)
            new_forks.append(fork)
            debug("  -> {r}".format(r=fork.full_name))

            if fork.created_at < now:
                warn("fork of {r} already exists\n  created_at {ctime}".format(
                    r=fork.full_name,
                    ctime=fork.created_at
                ))

        return new_forks


def find_teams_by_name(org, team_names):
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


def main():
    args = parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    g = pygithub.login_github(token_path=args.token_path, token=args.token)

    # protect destination org
    codetools.validate_org(args.dst_org)
    src_org = g.get_organization(args.src_org)
    dst_org = g.get_organization(args.dst_org)
    info("forking repos from: {org}".format(org=src_org.login))
    info("                to: {org}".format(org=dst_org.login))

    debug('looking for repos -- this can take a while for large orgs...')
    if args.team:
        debug('selecting repos by membership in team(s):')
        fork_teams = [t for t in src_org.get_teams() if t.name in args.team]
        [debug("  '{t}'".format(t=t.name)) for t in fork_teams]
        fork_teams = [t for t in src_org.get_teams() if t.name in args.team]
        repos = pygithub.get_repos_by_team(fork_teams)
    else:
        repos = pygithub.get_repos_by_team(fork_teams)

    src_repos = list(itertools.islice(repos, args.limit))

    repo_count = len(src_repos)
    if not repo_count:
        debug('nothing to do -- exiting')
        sys.exit(0)

    debug("found {n} repos to be forked from org {src_org}:".format(
        n=repo_count,
        src_org=src_org.login
    ))
    [debug("  {r}".format(r=r.full_name)) for r in src_repos]

    if args.copy_teams:
        debug('checking source repo team membership...')
        # dict of repo and team objects, keyed by repo name
        src_rt = find_teams_by_repo(src_repos)

        # extract a non-duplicated list of team names from all repos being
        # forked as a dict, keyed by team name
        src_teams = find_used_teams(src_rt)

        debug('found {n} teams in use within org {o}:'.format(
            n=len(src_teams),
            o=src_org.login
        ))
        [debug("  '{t}'".format(t=t)) for t in src_teams.keys()]

        # check for conflicting teams in dst org before attempting to create
        # any forks so its possible to bail out before any resources have been
        # created.
        debug('checking teams in destination org')
        conflicting_teams = find_teams_by_name(dst_org, list(src_teams.keys()))
        if conflicting_teams:
            error("found {n} conflicting teams in {o}:".format(
                n=len(conflicting_teams),
                o=dst_org.login
            ))
            [error("  '{t}'".format(t=t.name)) for t in conflicting_teams]
            sys.exit(1)

    debug('there is no spoon...')
    create_forks(dst_org, src_repos, dry_run=args.dry_run)

    if args.copy_teams:
        create_teams(dst_org, src_teams, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
