#!/usr/bin/env python3

from codekit.codetools import debug, error, info
from codekit import codetools, pygithub
import argparse
import datetime
import sys
import textwrap


def parse_args():
    """Parse command-line arguments"""
    prog = 'github-get-ratelimit'

    parser = argparse.ArgumentParser(
        prog=prog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""
            Display the current github ReST API request ratelimit.

            Examples:

                {prog}
        """).format(prog=prog),
        epilog='Part of codekit: https://github.com/lsst-sqre/sqre-codekit'
    )

    parser.add_argument(
        '--token-path',
        default='~/.sq_github_token_delete',
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
    parser.add_argument('-v', '--version', action=codetools.ScmVersionAction)

    return parser.parse_args()


def run():
    args = parse_args()

    codetools.setup_logging(args.debug)

    global g
    g = pygithub.login_github(token_path=args.token_path, token=args.token)
    info("github ratelimit: {rl}".format(rl=g.rate_limiting))

    reset = datetime.datetime.fromtimestamp(int(g.rate_limiting_resettime))
    info("github ratelimit reset: {time}".format(time=reset))


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
