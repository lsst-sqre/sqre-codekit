"""Moves a bunch of Github repos to a team"""

# Technical Debt
# -------------
# - will need updating to be new permissions model aware
# - warn if repo and teams do not exist

import os
import logging
import argparse
import textwrap
from time import sleep
from .. import codetools


def parse_args():
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
        'repos', nargs='+',
        help='Names of repos to move')
    parser.add_argument(
        '--from', required=True, dest='oldteam',
        help='Original team name')
    parser.add_argument(
        '--to', required=True, dest='newteam',
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
        '-d', '--debug',
        action='store_true',
        default=os.getenv('DM_SQUARE_DEBUG'),
        help='Debug mode')
    parser.add_argument('--dry-run', action='store_true')

    return parser.parse_args()


def main():
    args = parse_args()

    if args.debug:
        print args

    if args.debug:
        urllib3 = logging.getLogger('requests.packages.urllib3')  # NOQA
        stream_handler = logging.StreamHandler()
        logger = logging.getLogger('github3')
        logger.addHandler(stream_handler)
        logger.setLevel(logging.DEBUG)

    gh = codetools.login_github(token_path=args.token_path)
    if args.debug:
        print(type(gh))

    org = gh.organization(args.org)

    move_me = args.repos
    if args.debug:
        print len(move_me), 'repos to me moved'

    # FIXME unused
    # teams = [g for g in org.iter_teams()]

    status = 0
    status2 = 0

    for r in move_me:
        repo = args.org + '/' + r.rstrip()

        # Add team to the repo
        if args.debug or args.dry_run:
            print 'Adding', repo, 'to', args.newteam, '...',

        if not args.dry_run:
            status += org.add_repo(repo, args.newteam)
            if status:
                print 'ok'
            else:
                print 'FAILED'

        # remove repo from old team
        # you cannot move out of Owners

        if args.oldteam != 'Owners':
            if args.debug or args.dry_run:
                print 'Removing', repo, 'from', args.oldteam, '...',

            if not args.dry_run:
                status2 += org.remove_repo(repo, args.oldteam)

                if status2:
                    print 'ok'
                else:
                    print 'FAILED'

        # give the API a rest (*snicker*) we don't want to get throttled
        sleep(1)

    if args.debug:
        print ' '
        print 'Added:', status
        print 'Removed:', status2


if __name__ == '__main__':
    main()
