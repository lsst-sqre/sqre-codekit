"""Apply autopep8 to the LSST Stack to establish conformance to the
Python coding standard (see RFC-162) and push changes to GitHub branches.

Usage
-----

To run autopep8 in all repos in the 'Data Management' team in the
lsst organization:

   lsst-autopep8 -u shipitsquirrel --org lsst --team 'Data Management' \
        --branch mybranch

Or you can run lsst-bp on just a single repository:

    lsst-autopep8 -u shipitsqurrel --org lsst --repo afw --branch mybranch

Optionally, the script can be run against repositories forked into a
shadow github organization. Use the github-fork-repos script to do this:

   github-fork-repos -u shipitsquirrel --org shadowy-org
   lsst-autopep8 -u shipitsquirrel --org shadowy-org --ignore-teams \
        --branch mybranch

Note that github-fork-repos does not carry over GitHub team assignments,
so the --team option will not use useful in shadow organizations.
Instead use --ignore-teams to avoid filtering by teams.

autopep8 Settings
-----------------

RFC-162 (https://jira.lsstcorp.org/browse/RFC-162) specified a set of
PEP8 exclusions for consistency with the published DM Python Coding style
at http://developer.lsst.io/en/latest/coding/python_style_guide.html.

lsst-autopep8 provides the following arguments to control autopep8, with
default values conforming to the published coding standards:

- --autopep8-ignore (default: E133,E226,E228,E251,N802,N803,W391)
- --autopep8-max-line-length (default: 110)

You may explicitly set these arguments if you need to deviate from DM
standards.

In addition to the above configurable settings, lsst-autopep8 always runs
autopep8 with the following settings:

- --in-place - make changes to files in place
- --recursive - Search and modify Python files throughout a repo

Processing Flow
---------------

1. Clones repositories to disk
2. For each repository, runs autopep8
3. Commit changes.
4. Push changes up to Git remote in a new branch.

Once lsst-autopep8 is run, it shouldn't need to be run again unless
non-compliant code has been added to the stack. However, the results
shouldn't change PEP8 compliant lines of code if run repeatedly.
"""

import sys
import argparse
import textwrap
import os
from .. import codetools
from .. import autopep8


def parse_args():
    """CL arguments for lsst-autopep8."""
    parser = argparse.ArgumentParser(
        prog='lsst-bp',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(sys.modules[__name__].__doc__),
        epilog=textwrap.dedent("""
            See RFC-162 for more information.

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
        help='Apply autopep8 to a single repo, rather than all repos '
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
        '--autopep8-ignore',
        default='E133,E226,E228,E251,N802,N803,W391',
        dest='autopep8_ignore',
        help='PEP8 errors to ignore')
    parser.add_argument(
        '--autopep8-max-line-length',
        type=int,
        default=110,
        dest='autopep8_max_length',
        help='Maximum line length target for autopep8')
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

    if args.repo is None and args.ignore_teams is True:
        repo_iter = org.iter_repos()
    elif args.repo is None and args.ignore_teams is False:
        repo_iter = codetools.repos_for_team(org, args.team)
    else:
        repo_iter = [codetools.open_repo(org, args.repo)]

    for repo in repo_iter:
        print("Applying autopep8 to {0}".format(repo.name))
        with codetools.TempDir() as temp_dir:
            autopep8.autopep8_repo(
                gh, repo, args.branch, temp_dir,
                args.autopep8_ignore, args.autopep8_max_length)
