#!/usr/bin/env python3
"""Fork LSST repos into a showow GitHub organization."""

from .. import codetools
import argparse
import codekit.pygithub as pygithub
import os
import progressbar
import textwrap


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

    g = pygithub.login_github(token_path=args.token_path, token=args.token)

    src_org = g.get_organization('lsst')
    dst_org = g.get_organization(args.shadow_org)

    # list of all LSST repos
    src_repos = list(src_org.get_repos())
    repo_count = len(src_repos)

    if args.debug:
        print(src_repos)

    widgets = ['Forking: ', progressbar.Bar(), ' ', progressbar.AdaptiveETA()]
    pbar = progressbar.ProgressBar(
        widgets=widgets, max_value=repo_count).start()
    repo_idx = 0
    for r in src_repos:
        if args.debug:
            print(r.name)

        dst_org.create_fork(r)
        pbar.update(repo_idx)
        repo_idx += 1


if __name__ == '__main__':
    main()
