"""Delete all repos in the Github <user>-shadow org."""

# (the -u in the commandline unbuffers output so the countdown works)

import sys
from getpass import getuser
import os
from time import sleep
from github3 import login


def main():
    token = ''
    debug = os.getenv("DM_SQUARE_DEBUG")
    # Deliberately hardcoding the -shadow part due to cowardice
    orgname = getuser() + '-shadow'

    if debug:
        print 'org:', orgname

    # yes, yes, module

    file_credential = os.path.expanduser('~/.sq_github_token_delete')

    if not os.path.isfile(file_credential):
        print "You don't have a token in {0} ".format(file_credential)
        print "Have you run github_auth.py?"
        sys.exit(1)

    with open(file_credential, 'r') as fd:
        token = fd.readline().strip()

    gh = login(token=token)

    # get the organization object
    organization = gh.organization(orgname)

    # get all the repos
    repos = [g for g in organization.iter_repos()]

    print 'Deleting all repos in', orgname
    print 'Now is the time to panic and Ctrl-C'

    secs = 10
    while secs >= 0:
        print secs, '...',
        sleep(2)
        secs -= 1

    print 'Here goes:'

    if debug:
        delay = 5;
        print delay, 'second gap between deletions'
        work = 0
        nowork = 0
        
    for repo in repos:

        if debug:
            print 'Next deleting:', repo.name,'...',
            sleep(delay)

        status = repo.delete()


        if status:
            print 'ok'
            work += 1
        else:
            print 'FAILED - does your token have delete_repo scope?'
            nowork +=1

    print 'Done - Succeed:', work, 'Failed:', nowork
    if work: print 'Consider deleting your privileged auth token', file_credential


if __name__ == '__main__':
    main()
