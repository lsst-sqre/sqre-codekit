#!/usr/bin/env python3
"""Moves a bunch of Github repos to a team"""
# Technical Debt
# -------------
# - will need updating to be new permissions model aware

from codekit import pygithub
from .. import codetools
from codekit.codetools import info, debug, warn, error
import argparse
import github
import logging
import os
import sys
import textwrap

logger = logging.getLogger('codekit')
logging.basicConfig()


def parse_args():
    """Parse command-line args"""
    parser = argparse.ArgumentParser(
        prog='github-mv-repos-to-team',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""Move repo(s) from one team to another.

            Note that --from and --to are required "options".

            Examples:

            ./github_mv_repos_to_team.py --from test_ext2 \
                --to test_ext pipe_tasks apr_util
        """),
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
        action='store_true',
        default=os.getenv('DM_SQUARE_DEBUG'),
        help='Debug mode')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('-v', '--version', action=codetools.ScmVersionAction)

    return parser.parse_args()


def find_team(teams, name):
    assert isinstance(teams, list)
    assert isinstance(name, str) \
        or isinstance(name, list)

    t = [t for t in teams if t.name in name]
    if not t:
        error("unable to find team {team}".format(team=name))
        sys.exit(1)

    return t


def main():
    """Move the repos"""
    args = parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    g = pygithub.login_github(token_path=args.token_path, token=args.token)
    org = g.organization(args.org)

    # only iterate over all teams once
    teams = list(org.get_teams())
    old_team = find_team(teams, args.oldteam)
    new_team = find_team(teams, args.newteam)

    move_me = args.repos
    debug(len(move_me), 'repos to be moved')

    added = []
    removed = []
    for name in move_me:
        r = org.get_repo(name)

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
            except github.GithubException as e:
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
            except github.GithubException as e:
                debug('  FAILED')

    info('Added:', added)
    info('Removed:', removed)


if __name__ == '__main__':
    main()
