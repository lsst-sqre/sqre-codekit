#!/usr/bin/env python3

from codekit.codetools import debug, error, info, warn
from codekit import codetools, pygithub
import argparse
import codekit.progressbar as pbar
import datetime
import github
import itertools
import sys
import textwrap


class TeamError(Exception):
    pass


def parse_args():
    """Parse command-line arguments"""
    prog = 'github-fork-org'

    parser = argparse.ArgumentParser(
        prog=prog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""
        Fork repositories from one GitHub organization to another.

        Example:

            {prog} \\
                --dry-run \\
                --debug \\
                --src-org 'lsst' \\
                --dst-org 'example' \\
                --token "$GITHUB_TOKEN" \\
                --team 'DM Auxilliaries' \\
                --team 'DM Externals' \\
                --team 'Data Management' \\
                --copy-teams
        """).format(prog=prog),
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
    parser.add_argument(
        '--fail-fast',
        action='store_true',
        help='Fail immediately on github API errors.')
    parser.add_argument(
        '--no-fail-fast',
        action='store_const',
        const=False,
        dest='fail_fast',
        help='DO NOT Fail immediately on github API errors. (default)')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument(
        '-d', '--debug',
        action='count',
        default=codetools.debug_lvl_from_env(),
        help='Debug mode (can specify several times)')
    parser.add_argument('-v', '--version', action=codetools.ScmVersionAction)
    return parser.parse_args()


def find_teams_by_repo(src_repos):
    assert isinstance(src_repos, list), type(src_repos)

    # length of longest repo name
    max_name_len = len(max([r.full_name for r in src_repos], key=len))

    src_rt = {}
    for r in src_repos:
        try:
            teams = r.get_teams()
        except github.RateLimitExceededException:
            raise
        except github.GithubException as e:
            msg = 'error getting teams'
            raise pygithub.CaughtRepositoryError(r, e, msg) from None

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
    fail_fast=False,
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
    problems = []
    batch_repos = 50
    for name, repos in teams.items():
        pygithub.debug_ratelimit(g)
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
                debug("  with {n} member repos:".format(n=len(repos)))
                [debug("    {r}".format(r=r.full_name)) for r in repos]

                leftover_repos = repos[batch_repos:]
                if leftover_repos:
                    debug("  creating team with first {b} of {n} repos"
                          .format(
                              b=batch_repos,
                              n=len(repos)
                          ))
                dst_t = org.create_team(name, repo_names=repos[:batch_repos])
                if leftover_repos:
                    # add any repos over the batch limit individually to team
                    for r in leftover_repos:
                        debug("  adding repo {r}".format(r=r.full_name))
                        dst_t.add_to_repos(r)
            else:
                dst_t = org.create_team(name)
        except github.RateLimitExceededException:
            raise
        except github.GithubException as e:
            # if the error is for any cause other than the team already
            # existing, puke.
            team_exists = False
            if ignore_existing and 'errors' in e.data:
                for oops in e.data['errors']:
                    msg = oops['message']
                    if 'Name has already been taken' in msg:
                        # find existing team
                        dst_t = pygithub.get_teams_by_name(org, name)[0]
                        team_exists = True
            if not (ignore_existing and team_exists):
                msg = "error creating team: {t}".format(t=name)
                yikes = pygithub.CaughtOrganizationError(org, e, msg)
                if fail_fast:
                    raise yikes from None
                problems.append(yikes)
                error(yikes)
                break
        else:
            dst_teams[dst_t.name] = dst_t

    return dst_teams, problems


def create_forks(
    dst_org,
    src_repos,
    fail_fast=False,
    dry_run=False
):
    assert isinstance(dst_org, github.Organization.Organization),\
        type(dst_org)
    assert isinstance(src_repos, list), type(src_repos)

    repo_count = len(src_repos)

    dst_repos = []
    skipped_repos = []
    problems = []
    with pbar.eta_bar(msg='forking', max_value=repo_count) as progress:
        repo_idx = 0
        for r in src_repos:
            progress.update(repo_idx)
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

            try:
                fork = dst_org.create_fork(r)
                dst_repos.append(fork)
                debug("  -> {r}".format(r=fork.full_name))
            except github.RateLimitExceededException:
                raise
            except github.GithubException as e:
                if 'Empty repositories cannot be forked.' in e.data['message']:
                    warn("{r} is empty and can not be forked".format(
                        r=r.full_name
                    ))
                    skipped_repos.append(r)
                    continue

                msg = "error forking repo {r}".format(r=r.full_name)
                yikes = pygithub.CaughtOrganizationError(dst_org, e, msg)
                if fail_fast:
                    raise yikes from None
                problems.append(yikes)
                error(yikes)

            if fork.created_at < now:
                warn("fork of {r} already exists\n  created_at {ctime}".format(
                    r=fork.full_name,
                    ctime=fork.created_at
                ))

    return dst_repos, skipped_repos, problems


def run():
    args = parse_args()

    codetools.setup_logging(args.debug)

    global g
    g = pygithub.login_github(token_path=args.token_path, token=args.token)

    # protect destination org
    codetools.validate_org(args.dst_org)
    src_org = g.get_organization(args.src_org)
    dst_org = g.get_organization(args.dst_org)
    info("forking repos from: {org}".format(org=src_org.login))
    info("                to: {org}".format(org=dst_org.login))

    debug('looking for repos -- this can take a while for large orgs...')
    if args.team:
        debug('checking that selection team(s) exist')
        try:
            org_teams = list(src_org.get_teams())
        except github.RateLimitExceededException:
            raise
        except github.GithubException as e:
            msg = 'error getting teams'
            raise pygithub.CaughtOrganizationError(src_org, e, msg) from None

        missing_teams = [n for n in args.team if n not in
                         [t.name for t in org_teams]]
        if missing_teams:
            error("{n} team(s) do not exist:".format(n=len(missing_teams)))
            [error("  '{t}'".format(t=n)) for n in missing_teams]
            return
        fork_teams = [t for t in org_teams if t.name in args.team]
        repos = pygithub.get_repos_by_team(fork_teams)
        debug('selecting repos by membership in team(s):')
        [debug("  '{t}'".format(t=t.name)) for t in fork_teams]
    else:
        repos = pygithub.get_repos_by_team(fork_teams)

    src_repos = list(itertools.islice(repos, args.limit))

    repo_count = len(src_repos)
    if not repo_count:
        debug('nothing to do -- exiting')
        return

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
        conflicting_teams = pygithub.get_teams_by_name(
            dst_org,
            list(src_teams.keys())
        )
        if conflicting_teams:
            raise TeamError(
                "found {n} conflicting teams in {o}: {teams}".format(
                    n=len(conflicting_teams),
                    o=dst_org.login,
                    teams=[t.name for t in conflicting_teams]
                ))

    debug('there is no spoon...')
    problems = []
    pygithub.debug_ratelimit(g)
    dst_repos, skipped_repos, err = create_forks(
        dst_org,
        src_repos,
        fail_fast=args.fail_fast,
        dry_run=args.dry_run
    )
    if err:
        problems += err

    if args.copy_teams:
        # filter out repos which were skipped
        # dict of str(fork_repo.name): fork_repo
        dst_forks = dict((r.name, r) for r in dst_repos)
        bad_repos = dict((r.name, r) for r in skipped_repos)
        # dict of str(team.name): [repos] to be created
        dst_teams = {}
        for name, repos in src_teams.items():
            dst_teams[name] = [dst_forks[r.name] for r in repos
                               if r.name not in bad_repos]

        _, err = create_teams(
            dst_org,
            dst_teams,
            with_repos=True,
            fail_fast=args.fail_fast,
            dry_run=args.dry_run
        )
        if err:
            problems += err

    if problems:
        msg = "{n} errors forking repo(s)/teams(s)".format(
            n=len(problems))
        raise codetools.DogpileError(problems, msg)


def main():
    try:
        try:
            run()
        except codetools.DogpileError as e:
            error(e)
            n = len(e.errors)
            sys.exit(n if n < 256 else 255)
        else:
            sys.exit(0)
        finally:
            if 'g' in globals():
                pygithub.debug_ratelimit(g)
    except SystemExit as e:
        debug("exit {status}".format(status=str(e)))
        raise e


if __name__ == '__main__':
    main()
