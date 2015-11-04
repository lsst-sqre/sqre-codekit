#!/usr/bin/env python

"""
List repositories on Github belonging to organisations, teams, etc
"""

# Technical Debt
# --------------

# Known Bugs
# ----------

import argparse
import os
import textwrap
from .. import codetools


def parse_args():
    parser = argparse.ArgumentParser(
        prog='github-list-repos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''

        List repositories on Github using various criteria

        Examples:

        github_list_repos lsst

        github_list_repos --hide 'Data Management' --hide 'Owners' lsst

        Note:

        --mint and --maxt limits are applied after --hide

        So for example,

        github_list_repos --maxt 0 --hide Owners lsst

        returns the list of repos that are owned by no team besides Owners.
        '''),
        epilog='Part of codekit: https://github.com/lsst-sqre/sqre-codekit'
    )

    parser.add_argument('organisation')

    parser.add_argument('--hide', action='append',
                        help='hide a specific team from the output')

    parser.add_argument('--mint', type=int, default='0',
                        help='only list repos that have more than MINT teams')

    parser.add_argument('--maxt', type=int,
                        help='only list repos that have fewer than MAXT teams')

    return parser.parse_args()


def main():
    debug = os.getenv("DM_SQUARE_DEBUG")

    gh = codetools.github(authfile='~/.sq_github_token')

    opt = parse_args()

    if not opt.hide:
        opt.hide = []

    # Do Something
    # ------------

    org = gh.organization(opt.organisation)

    for repo in org.iter_repos():
        teamnames = [t.name for t in repo.iter_teams()
                     if t.name not in opt.hide]
        maxt = opt.maxt if (opt.maxt >= 0) else len(teamnames)
        if debug:
            print "MAXT=", maxt

        if (opt.mint <= len(teamnames) <= maxt):
            print repo.name.ljust(40) + " ".join(teamnames)


if __name__ == '__main__':
    main()
