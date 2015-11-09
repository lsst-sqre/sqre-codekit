"""Migrate LSST code to use a minimal style of inline boilerplate and
refer to centralzed LICENSE and COPYRIGHT files.

Use lsst-dm to accomplish RFC-45 compliance in the Stack.

Usage
-----

   lsst-bp -u shipitsquirrel --org lsst --team 'Data Management'

Optionally, the script can be run against repositories forked into a
shadow github organization. Use the github-fork-repos script to do this.

   github-fork-repos -u shipitsquirrel --org shadowy-org
   lsst-bp -u shipitsquirrel --org shadowy-org --team 'Data Management'

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
        '--team', action='append',
        default=['Data Management'],
        help='Act on a specific team')
    parser.add_argument(
        '--token-path',
        default='~/.sq_github_token',
        help='Token made with github-auth (set if using non-standard path)')
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        default=os.getenv('DM_SQUARE_DEBUG'),
        help='Debug mode')
    return parser.parse_args()


def main():
    """CLI entrypoint for lsst-bp executable."""
    args = parse_args()

    gh = codetools.login_github(token_path=args.token_path)
    org = gh.organization(args.orgname)
    teams = set(args.team)

    for repo in org.iter_repos():
        repo_teams = set([t.name for t in repo.iter_teams()])
        if repo_teams.isdisjoint(teams) is False:
            # This repo has teams we're interested in for processing
            licensing.process_repo(gh, repo)
