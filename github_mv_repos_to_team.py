#!/usr/bin/env python

"""
Moves a bunch of Github repos to a team
"""

# Technical Debt
# -------------
# - will need updating to be new permissions model aware
# - warn if repo and teams do not exist

import codetools
import os
import sys
import argparse
import textwrap
from time import sleep
from getpass import getuser

debug = os.getenv("DM_SQUARE_DEBUG")
trace = False
user = getuser()

# argument parsing and default options

parser = argparse.ArgumentParser(
    prog='github_mv_repos_to_team',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''

    Move repo(s) from one team to another. 

    Examples:

    ./github_mv_repos_to_team.py 

    '''),
    epilog='Part of codekit: https://github.com/lsst-sqre/sqre-codekit'
)

parser.add_argument('repos', nargs='+')

# because opt.from seems to mean something else
parser.add_argument('--from', required=True, dest='oldteam')

parser.add_argument('--to', required=True, dest='newteam')

parser.add_argument('--org',
                    default=user+'-shadow')

parser.add_argument('--dry-run', action='store_true')

opt = parser.parse_args()

if debug: print opt

if trace:
    import logging
    urllib3 = logging.getLogger('requests.packages.urllib3')
    stream_handler = logging.StreamHandler()
    logger = logging.getLogger('github3')
    logger.addHandler(stream_handler)
    logger.setLevel(logging.DEBUG)

debug = os.getenv("DM_SQUARE_DEBUG")

gh = codetools.github(authfile='~/.sq_github_token_delete')
if debug: print(type(gh))

org = gh.organization(opt.org)

move_me = opt.repos
if debug: print len(move_me),'repos to me moved'

teams = [g for g in org.iter_teams()]

work = nowork = status = status2 = 0

for r in move_me:
    repo = opt.org + '/' + r.rstrip()

    # Add team to the repo
    if debug or opt.dry_run:
        print 'Adding', repo, 'to', opt.newteam, '...',   

    if not opt.dry_run:
        status += org.add_repo(repo,opt.newteam)
        if status:
            print 'ok'
        else:
            print 'FAILED'
   
    # remove repo from old team
    # you cannot move out of Owners

    if opt.oldteam != 'Owners':
        if debug or opt.dry_run:
            print 'Removing', repo, 'from', opt.oldteam, '...',

        if not opt.dry_run:
            status2 += org.remove_repo(repo,opt.oldteam)

            if status2:
                print 'ok'
            else:
                print 'FAILED'

    # give the API a rest (*snicker*) we don't want to get throttled
    sleep(1)

if debug:
    print ' '
    print 'Added:', status
    print 'Removed:', status2






