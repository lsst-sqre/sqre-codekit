#!/usr/bin/env python3
"""Generate a github auth token"""
# technical debt:
# --------------
# - add command line option to override default user
# - add command line option for delete scope

from getpass import getpass
import argparse
import textwrap
import os
import platform
import sys
import github3
from .. import codetools


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        prog='github-auth',
        description=textwrap.dedent("""Generate a GitHub auth token.

           By default this token will not allow you to delete repositories.
           Use the --delete-role flag to create a delete-enabled token.

           By default, regular and delete-enabled tokens will be stored
           in separate locations (~/.sq_github_token vs
           ~/.sq_github_token_delete).
           """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Part of codekit: https://github.com/lsst-sqre/sqre-codekit')
    parser.add_argument(
        '-u', '--user',
        help='GitHub username',
        dest='user',
        required=True)
    parser.add_argument(
        '--delete-role',
        default=False,
        action='store_true',
        help='Add the delete role to this token')
    parser.add_argument(
        '--token-path',
        default=None,
        help='Save this token to a non-standard path')
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        default=os.getenv('DM_SQUARE_DEBUG'),
        help='Debug mode')
    parser.add_argument('-v', '--version', action=codetools.ScmVersionAction)
    return parser.parse_args()


def main():
    """Log in and store credentials"""
    args = parse_args()

    appname = sys.argv[0]
    hostname = platform.node()

    if args.debug:
        print(args.user)
    password = ''

    if args.token_path is None and args.delete_role is True:
        cred_path = os.path.expanduser('~/.sq_github_token_delete')
    elif args.token_path is None and args.delete_role is False:
        cred_path = os.path.expanduser('~/.sq_github_token')
    else:
        cred_path = os.path.expandvars(os.path.expanduser(args.token_path))

    if not os.path.isfile(cred_path):
        print("""
        Type in your password to get an auth token from github
        It will be stored in {0}
        and used in subsequent occasions.
        """.format(cred_path))

        while not password:
            password = getpass('Password for {0}: '.format(args.user))

        note_template = '{app} via github3 on {host} by {user} {creds}'
        note = note_template.format(app=appname,
                                    host=hostname,
                                    user=args.user,
                                    creds=cred_path)
        note_url = 'https://lsst.org/'

        if args.delete_role:
            scopes = ['repo', 'user', 'delete_repo', 'admin:org']
        else:
            scopes = ['repo', 'user']

        auth = github3.authorize(
            args.user, password, scopes, note, note_url,
            two_factor_callback=codetools.github_2fa_callback)

        with open(cred_path, 'w') as fdo:
            fdo.write(auth.token + '\n')
            fdo.write(str(auth.id))

        print('Token written to {0}'.format(cred_path))

    else:
        print("You already have an auth file: {0} ".format(cred_path))
        print("Delete it if you want a new one and run again")
        print("Remember to also remove the corresponding token on Github")


if __name__ == '__main__':
    main()
