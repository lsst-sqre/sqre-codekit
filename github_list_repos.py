#!/usr/bin/env python

"""
List repositories on Github belonging to organisations, teams, etc
"""

# Technical Debt
# --------------

# Known Bugs
# ----------

import argparse
import codetools
import os
import textwrap

debug = os.getenv("DM_SQUARE_DEBUG")

gh = codetools.github(authfile='~/.sq_github_token')

# Argument Parsing
# ----------------

parser = argparse.ArgumentParser(
    prog='github_list_repos',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''

    List repositories on Github using various criteria

    Examples:

    github_list_repos lsst

    github_list_repos --teams --hide 'Data Management' --hide 'Owners' lsst
    
    '''),
    epilog='Part of codekit: https://github.com/lsst-sqre/sqre-codekit'
)

parser.add_argument('organisation')

parser.add_argument('--teams', action='store_true',
                    help='include team ownership info')

parser.add_argument('--hide', action='append',
                    help='hide a specific team from the output (implies --team)')

opt = parser.parse_args()

if opt.hide:
    opt.teams = True

# Do Something
# ------------

org = gh.organization(opt.organisation)

for repo in org.iter_repos():

    if not opt.teams:
        print repo.name
    else:

        teamnames = [t.name for t in repo.iter_teams() if t.name not in opt.hide]
        print repo.name.ljust(40) + " ".join(teamnames)
