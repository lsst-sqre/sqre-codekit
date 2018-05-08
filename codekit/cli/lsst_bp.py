#!/usr/bin/env python3
"""Migrate LSST code to use a minimal style of inline boilerplate and
refer to centralzed LICENSE and COPYRIGHT files.

Use lsst-dm to accomplish RFC-45 compliance in the Stack.

Usage
-----

To migrate boilerplate in all repos in the 'Data Management' team in the
lsst organization:

   lsst-bp -u shipitsquirrel --org lsst --team 'Data Management' \
        --branch mybranch

Or you can run lsst-bp on just a single repository:

    lsst-bp -u shipitsqurrel --org lsst --repo afw --branch mybranch

Optionally, the script can be run against repositories forked into a
shadow github organization. Use the github-fork-repos script to do this:

   github-fork-repos -u shipitsquirrel --org shadowy-org
   lsst-bp -u shipitsquirrel --org shadowy-org --ignore-teams \
        --branch mybranch

Note that github-fork-repos does not carry over GitHub team assignments,
so the --team option will not use useful in shadow organizations.
Instead use --ignore-teams to avoid filtering by teams.

Processing Flow
---------------

1. Clones repositories to disk
2. For each repository,

   - modify the boilerplate of all source files to new style
   - make a LICENSE file with GPLv3 text
   - Make a COPYRIGHT file with years determined from git history

3. Push changes up to forks in a new branch.
4. Issue pull requests

Once lsst-bp is run, it shouldn't need to be run again unless
non-compliant code has been added to the stack. lsst-bp is designed to
be run multiple times without adverse effects to compliant code.
"""

import sys
import argparse
import textwrap
import os
from .. import codetools
from .. import licensing


def parse_args():
    """CL arguments for lsst-bp."""
    parser = argparse.ArgumentParser(
        prog='lsst-bp',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(sys.modules[__name__].__doc__),
        epilog=textwrap.dedent("""
            See DM-4220 and RFC-45 for more information.

            Part of codekit: https://github.com/lsst-sqre/sqre-codekit
            """))
    parser.add_argument(
        '-u', '--user',
        help='GitHub username',
        required=True)
    parser.add_argument(
        '-o', '--org',
        dest='orgname',
        help='GitHub organization, e.g. lsst or a shadow org setup with '
             'lsst-fork-repos',
        required=True)
    parser.add_argument(
        '--repo',
        default=None,
        help='Upgrade the boilerplate of a single repo, rather than all repos '
             'in the organization matching --team')
    parser.add_argument(
        '--branch',
        help='Branch to create and work on',
        required=True)
    parser.add_argument(
        '--team', action='append', default=['Data Management'],
        help='Act on a specific team')
    parser.add_argument(
        '--ignore-teams', action='store_true', default=False,
        help='Ignore filtering by GitHub teams')
    parser.add_argument(
        '--token-path',
        default='~/.sq_github_token',
        help='Token made with github-auth (set if using non-standard path)')
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        default=os.getenv('DM_SQUARE_DEBUG'),
        help='Debug mode')
    parser.add_argument('-v', '--version', action=codetools.ScmVersionAction)
    return parser.parse_args()


def main():
    """CLI entrypoint for lsst-bp executable."""
    args = parse_args()

    ghb = codetools.login_github(token_path=args.token_path)
    org = ghb.organization(args.orgname)

    if args.repo is None and args.ignore_teams is True:
        repo_iter = org.repositories()
    elif args.repo is None and args.ignore_teams is False:
        repo_iter = codetools.repos_for_team(org, args.team)
    else:
        # This is actually a list
        repo_iter = [codetools.open_repo(org, args.repo)]

    token = ''
    token_path = os.path.expandvars(os.path.expanduser(args.token_path))
    with open(token_path, 'r') as fdo:
        token = fdo.readline().strip()
    git_helper = codetools.get_git_credential_helper(args.user, token)

    for repo in repo_iter:
        print("Upgrading {0}".format(repo.name))
        with codetools.TempDir() as temp_dir:
            licensing.upgrade_repo(repo, args.branch, temp_dir, git_helper)
