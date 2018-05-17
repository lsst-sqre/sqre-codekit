#!/usr/bin/env python3
"""List repositories on Github belonging to organisations, teams, etc.
"""
# Technical Debt
# --------------

# Known Bugs
# ----------

from .. import codetools
import argparse
import codekit.pygithub as pygithub
import github
import logging
import os
import textwrap

logging.basicConfig()
logger = logging.getLogger('codekit')


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        prog='github-list-repos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""

        List repositories on Github using various criteria

        Examples:

          github_list_repos --org lsst

          github_list_repos --hide 'Data Management' --hide 'Owners' --org lsst

        Note: --mint and --maxt limits are applied after --hide.
        So for example,

          github_list_repos --maxt 0 --hide Owners --org lsst

        returns the list of repos that are owned by no team besides Owners.
        """),
        epilog='Part of codekit: https://github.com/lsst-sqre/sqre-codekit')
    parser.add_argument(
        '-o', '--org',
        dest='organization',
        help='GitHub Organization name',
        required=True)
    parser.add_argument(
        '--hide', action='append',
        help='Hide a specific team from the output')
    parser.add_argument(
        '--mint', type=int, default='0',
        help='Only list repos that have more than MINT teams')
    parser.add_argument(
        '--maxt', type=int,
        help='Only list repos that have fewer than MAXT teams')
    parser.add_argument(
        '--delimiter', default=', ',
        help='Character(s) separating teams in print out')
    parser.add_argument(
        '--token-path',
        default='~/.sq_github_token',
        help='Use a token (made with github-auth) in a non-standard loction')
    parser.add_argument(
        '--token',
        default=None,
        help='Literal github personal access token string')
    parser.add_argument(
        '-d', '--debug',
        action='count',
        default=os.getenv('DM_SQUARE_DEBUG'),
        help='Debug mode')
    parser.add_argument('-v', '--version', action=codetools.ScmVersionAction)
    return parser.parse_args()


def run():
    """List repos and teams"""
    args = parse_args()
    global g
    g = pygithub.login_github(token_path=args.token_path, token=args.token)

    if args.debug:
        logger.setLevel(logging.DEBUG)
    if args.debug > 1:
        github.enable_console_debug_logging()

    if not args.hide:
        args.hide = []

    org = g.get_organization(args.organization)

    for r in org.get_repos():
        teamnames = [t.name for t in r.get_teams()
                     if t.name not in args.hide]
        maxt = args.maxt if (args.maxt is not None and
                             args.maxt >= 0) else len(teamnames)
        if args.debug:
            print("MAXT=", maxt)

        if args.mint <= len(teamnames) <= maxt:
            print(r.name.ljust(40) + args.delimiter.join(teamnames))


def main():
    try:
        run()
    finally:
        if 'g' in globals():
            pygithub.debug_ratelimit(g)


if __name__ == '__main__':
    main()
