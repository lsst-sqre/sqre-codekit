#!/usr/bin/env python

"""
Moves a bunch of repos to a team
"""

# Technical Debt
# -------------
# - remove all hardcoding

import codetools
import os, sys
from time import sleep

orgname = 'lsst'
oldteam = 'Data Management'
newteam = 'DM Externals'

trace = 0

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

org = gh.organization(orgname)

# pipe list through for now
move_me = sys.stdin.readlines()
if debug: print len(move_me),'repos to me moved'

teams = [g for g in org.iter_teams()]

work = nowork = status = status2 = 0

for r in move_me:
   repo = orgname + '/' + r.rstrip()

   # Add team to the repo

   print 'Adding', repo, 'to', newteam, '...',   
   status += org.add_repo(repo,newteam)

   if status: print 'ok'
   else: print 'FAILED'
   
   # remove repo from old team
   if debug: print 'Removing', repo, 'from', oldteam, '...',
   status2 += org.remove_repo(repo,oldteam)

   if status2: print 'ok'
   else: print 'FAILED'

   # give the API a rest (*snicker*) we don't want to get throttled
   sleep(1)


if debug: print 'Added:', status
if debug: print 'Removed:', status2






