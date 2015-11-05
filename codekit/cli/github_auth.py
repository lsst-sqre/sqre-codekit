"""Generate a github auth token"""

# technical debt:
# --------------
# - add command line option to override default user
# - add command line option for delete scope

from getpass import getuser, getpass
import argparse
import os
import platform
import sys
from github3 import authorize
from .. import codetools


def parse_args():
    parser = argparse.ArgumentParser(
        prog='github-auth',
        description='Generate a GitHub auth token.')
    parser.add_argument('-u', '--user',
                        help='GitHub username',
                        dest='user',
                        default=getuser())
    return parser.parse_args()


def main():
    args = parse_args()

    appname = sys.argv[0]
    debug = os.getenv("DM_SQUARE_DEBUG")
    delete_scope = os.getenv("DM_SQUARE_ADMIN")
    hostname = platform.node()

    user = args.user
    if debug:
        print user
    password = ''

    if delete_scope:
        file_credential = os.path.expanduser('~/.sq_github_token_delete')
        if debug:
            print 'Token with delete scope will be generated:', file_credential
    else:
        file_credential = os.path.expanduser('~/.sq_github_token')
        if debug:
            print 'Token with user scope will be generated:', file_credential

    if not os.path.isfile(file_credential):

        print """
        Type in your password to get an auth token from github
        It will be stored in {0}
        and used in subsequent occasions.
        """.format(file_credential)

        while not password:
            password = getpass('Password for {0}: '.format(user))

        note_template = '{app} via github3 on {host} by {user} {creds}'
        note = note_template.format(app=appname,
                                    host=hostname,
                                    user=user,
                                    creds=file_credential)
        note_url = 'https://lsst.org/'

        if delete_scope:
            scopes = ['repo', 'user', 'delete_repo', 'admin:org']
        else:
            scopes = ['repo', 'user']

        auth = authorize(user, password, scopes, note, note_url,
                         two_factor_callback=codetools.github_2fa_callback)

        with open(file_credential, 'w') as fd:
            fd.write(auth.token + '\n')
            fd.write(str(auth.id))

        print 'Token written to {0}'.format(file_credential)

    else:
        print "You already have an auth file: {0} ".format(file_credential)
        print "Delete it if you want a new one and run again"
        print "Remember to also remove the corresponding token on Github"


if __name__ == '__main__':
    main()
