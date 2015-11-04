"""Fork github repos"""

# technical debt:
# --------------


from getpass import getuser
import os
import sys
from time import sleep
from github3 import login


def main():
    token = ''
    debug = os.getenv("DM_SQUARE_DEBUG")
    user = getuser()

    if debug:
        print 'You are', user

    # I have cut and pasted code
    # I am a bad person
    # I promise to make a module

    file_credential = os.path.expanduser('~/.sq_github_token')

    if not os.path.isfile(file_credential):
        print "You don't have a token in {0} ".format(file_credential)
        print "Have you run github_auth.py?"
        sys.exit(1)

    with open(file_credential, 'r') as fd:
        token = fd.readline().strip()

    gh = login(token=token)

    # get the organization object
    organization = gh.organization('lsst')

    # list of all LSST repos
    repos = [g for g in organization.iter_repos()]

    if debug:
        print repos

    for repo in repos:
        if debug:
            print repo.name

        forked_repo = repo.create_fork(user + '-shadow')  # NOQA
        sleep(2)

        # forked_name = forked_repo.name
        # Trap previous fork with dm_ prefix
        # if not forked_name.startswith("dm_"):
        #     newname = "dm_" + forked_name
        #     forked_repo.edit(newname)

if __name__ == '__main__':
    main()
