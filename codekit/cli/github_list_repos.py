#!/usr/bin/env python3

from codekit.codetools import debug, error
from codekit import codetools, pygithub
import argparse
import github
import sys
import textwrap


def parse_args():
    """Parse command-line arguments"""
    prog = 'github-list-repos'

    parser = argparse.ArgumentParser(
        prog=prog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""
        List repositories on Github using various criteria.

        Examples:

            {prog} --org lsst

            {prog} \\
                    --hide 'Data Management' \\
                    --hide 'Owners' \\
                    --org lsst

        Note: --mint and --maxt limits are applied after --hide.

        So for example,

            {prog} --maxt 0 --hide Owners --org lsst

        returns the list of repos that are owned by no team besides Owners.
        """).format(prog=prog),
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
        default=codetools.debug_lvl_from_env(),
        help='Debug mode (can specify several times)')
    parser.add_argument('-v', '--version', action=codetools.ScmVersionAction)
    return parser.parse_args()


def run():
    """List repos and teams"""
    args = parse_args()

    codetools.setup_logging(args.debug)

    global g
    g = pygithub.login_github(token_path=args.token_path, token=args.token)

    if not args.hide:
        args.hide = []

    org = g.get_organization(args.organization)

    try:
        repos = list(org.get_repos())
    except github.RateLimitExceededException:
        raise
    except github.GithubException as e:
        msg = 'error getting repos'
        raise pygithub.CaughtOrganizationError(org, e, msg) from None

    for r in repos:
        try:
            teamnames = [t.name for t in r.get_teams()
                         if t.name not in args.hide]
        except github.RateLimitExceededException:
            raise
        except github.GithubException as e:
            msg = 'error getting teams'
            raise pygithub.CaughtRepositoryError(r, e, msg) from None

        maxt = args.maxt if (args.maxt is not None and
                             args.maxt >= 0) else len(teamnames)
        if args.debug:
            print("MAXT=", maxt)

        if args.mint <= len(teamnames) <= maxt:
            print(r.name.ljust(40) + args.delimiter.join(teamnames))


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
