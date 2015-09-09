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
import textwrap

gh = codetools.github(authfile='~/.sq_github_token')

# Argument Parsing
# ----------------

parser = argparse.ArgumentParser(
    prog='github_list_repos',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''

    List repositories on Github using various criteria

    Examples:

    github_list_repos.py lsst
    
    '''),
    epilog='Part of codekit: https://github.com/lsst-sqre/sqre-codekit'
)

parser.add_argument('organisation')

opt = parser.parse_args()

# Do Something
# ------------

org = gh.organization(opt.organisation)

for repo in org.iter_repos():
    print repo.name
    








