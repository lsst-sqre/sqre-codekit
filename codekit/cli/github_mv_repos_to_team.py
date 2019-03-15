#!/usr/bin/env python3

# Technical Debt
# -------------
# - will need updating to be new permissions model aware

from codekit.codetools import debug, error, info, warn
from codekit import codetools, pygithub
import argparse
import github
import sys
import textwrap


class TeamError(Exception):
    pass


def parse_args():
    """Parse command-line args"""
    prog = 'github-mv-repos-to-team'

    parser = argparse.ArgumentParser(
        prog=prog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""
            Move repo(s) from one team to another.

            Note that --from and --to are required "options".

            Example:

                {prog} \\
                    --from test_ext2 \\
                    --to test_ext \\
                    pipe_tasks apr_util
        """).format(prog=prog),
        epilog='Part of codekit: https://github.com/lsst-sqre/sqre-codekit'
    )

    parser.add_argument(
        'repos',
        nargs='+',
        help='Names of repos to move')
    parser.add_argument(
        '--from',
        required=True,
        dest='oldteam',
        help='Original team name')
    parser.add_argument(
        '--to',
        required=True,
        dest='newteam',
        help='Destination team name')
    parser.add_argument(
        '-o', '--org',
        default=None,
        required=True,
        help='Organization to work in')
    parser.add_argument(
        '--token-path',
        default='~/.sq_github_token',
        help='Use a token (made with github-auth) in a non-standard location')
    parser.add_argument(
        '--token',
        default=None,
        help='Literal github personal access token string')
    parser.add_argument(
        '-d', '--debug',
        action='count',
        default=codetools.debug_lvl_from_env(),
        help='Debug mode (can specify several times)')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('-v', '--version', action=codetools.ScmVersionAction)

    return parser.parse_args()


def find_team(teams, name):
    assert isinstance(teams, list)
    assert isinstance(name, str) \
        or isinstance(name, list)

    t = [t for t in teams if t.name in name]
    if not t:
        raise TeamError("unable to find team {team}".format(team=name))

    return t


def run():
    """Move the repos"""
    args = parse_args()

    codetools.setup_logging(args.debug)

    global g
    g = pygithub.login_github(token_path=args.token_path, token=args.token)
    org = g.get_organization(args.org)

    # only iterate over all teams once
    try:
        teams = list(org.get_teams())
    except github.RateLimitExceededException:
        raise
    except github.GithubException as e:
        msg = 'error getting teams'
        raise pygithub.CaughtOrganizationError(org, e, msg) from None

    old_team = find_team(teams, args.oldteam)
    new_team = find_team(teams, args.newteam)

    move_me = args.repos
    debug(len(move_me), 'repos to be moved')

    added = []
    removed = []
    for name in move_me:
        try:
            r = org.get_repo(name)
        except github.RateLimitExceededException:
            raise
        except github.GithubException as e:
            msg = "error getting repo by name: {r}".format(r=name)
            raise pygithub.CaughtOrganizationError(org, e, msg) from None

        # Add team to the repo
        debug("Adding {repo} to '{team}' ...".format(
            repo=r.full_name,
            team=args.newteam
        ))

        if not args.dry_run:
            try:
                new_team.add_to_repos(r)
                added += r.full_name
                debug('  ok')
            except github.RateLimitExceededException:
                raise
            except github.GithubException:
                debug('  FAILED')

        if old_team.name in 'Owners':
            warn("Removing repo {repo} from team 'Owners' is not allowed"
                 .format(repo=r.full_name))

        debug("Removing {repo} from '{team}' ...".format(
            repo=r.full_name,
            team=args.oldteam
        ))

        if not args.dry_run:
            try:
                old_team.remove_from_repos(r)
                removed += r.full_name
                debug('  ok')
            except github.RateLimitExceededException:
                raise
            except github.GithubException:
                debug('  FAILED')

    info('Added:', added)
    info('Removed:', removed)


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
