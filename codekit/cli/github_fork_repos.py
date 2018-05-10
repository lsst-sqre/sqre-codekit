#!/usr/bin/env python3
"""Fork LSST repos into a showow GitHub organization."""

from codekit.codetools import debug
from .. import codetools
import argparse
import codekit.pygithub as pygithub
import logging
import os
import progressbar
import textwrap

progressbar.streams.wrap_stderr()
logging.basicConfig()
logger = logging.getLogger('codekit')


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        prog='github-fork-repos',
        description=textwrap.dedent("""
        Fork LSST into a shadow GitHub organization.
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Part of codekit: https://github.com/lsst-sqre/sqre-codekit')
    parser.add_argument(
        '-o', '--org',
        dest='shadow_org',
        required=True,
        help='Organization to fork repos into')
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
    parser.add_argument('-v', '--version', action=codetools.ScmVersionAction)
    return parser.parse_args()


def main():
    """Fork all repos into shadow org"""
    args = parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    g = pygithub.login_github(token_path=args.token_path, token=args.token)

    src_org = g.get_organization('lsst')
    dst_org = g.get_organization(args.shadow_org)
    debug("forking repos from: {org}".format(org=src_org))
    debug("                to: {org}".format(org=dst_org))

    src_repos = list(src_org.get_repos())
    repo_count = len(src_repos)
    debug("found {n} repos in {src_org}".format(n=repo_count, src_org=src_org))

    debug('repos to be forked:')
    [debug("  {r}".format(r=r.full_name)) for r in src_repos]

    widgets = ['Forking: ', progressbar.Bar(), ' ', progressbar.AdaptiveETA()]

    # XXX progressbar is not playing nicely with debug output and the advice in
    # the docs for working with logging don't have any effect.
    with progressbar.ProgressBar(
            widgets=widgets,
            max_value=repo_count) as pbar:

        repo_idx = 0
        for r in src_repos:
            debug("forking {r}".format(r=r.full_name))

            dst_org.create_fork(r)
            pbar.update(repo_idx)
            repo_idx += 1


if __name__ == '__main__':
    main()
