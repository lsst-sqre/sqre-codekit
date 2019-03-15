#!/usr/bin/env python3

# technical debt:
# --------------
# - add command line option for delete scope

from codekit.codetools import debug, error
from codekit import codetools, pygithub
from getpass import getpass
import argparse
import github
import os
import platform
import sys
import textwrap


def parse_args():
    """Parse command line arguments"""
    prog = 'github-auth'

    parser = argparse.ArgumentParser(
        prog=prog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""
            Generate a GitHub authentication token.

            By default this token will not allow you to delete repositories.
            Use the --delete-role flag to create a delete-enabled token.

            By default, regular and delete-enabled tokens will be stored in
            separate locations (~/.sq_github_token vs
            ~/.sq_github_token_delete).

            Example:

                {prog} \\
                    --debug \\
                    --user sqreadmin
        """).format(prog=prog),
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
        action='count',
        default=codetools.debug_lvl_from_env(),
        help='Debug mode (can specify several times)')
    parser.add_argument('-v', '--version', action=codetools.ScmVersionAction)
    return parser.parse_args()


def run():
    """Log in and store credentials"""
    args = parse_args()

    appname = sys.argv[0]
    hostname = platform.node()

    codetools.setup_logging(args.debug)

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

        note = textwrap.dedent("""\
            {app} via bored^H^H^H^H^H terrified opossums[1]
            on {host}
            by {user} {creds}
            [1] https://youtu.be/ZtLrn2zPTxQ?t=1m10s
            """).format(
            app=appname,
            host=hostname,
            user=args.user,
            creds=cred_path
        )
        note_url = 'https://www.youtube.com/watch?v=cFvijBpzD_Y'

        if args.delete_role:
            scopes = ['repo', 'user', 'delete_repo', 'admin:org']
        else:
            scopes = ['repo', 'user']

        global g
        g = github.Github(args.user, password)
        u = g.get_user()

        try:
            auth = u.create_authorization(
                scopes=scopes,
                note=note,
                note_url=note_url,
            )
        except github.TwoFactorException:
            auth = u.create_authorization(
                scopes=scopes,
                note=note,
                note_url=note_url,
                # not a callback
                onetime_password=codetools.github_2fa_callback()
            )
        g = github.Github(auth.token)

        with open(cred_path, 'w') as fdo:
            fdo.write(auth.token + '\n')
            fdo.write(str(auth.id))

        print('Token written to {0}'.format(cred_path))

    else:
        print("You already have an auth file: {0} ".format(cred_path))
        print("Delete it if you want a new one and run again")
        print("Remember to also remove the corresponding token on Github")


def main():
    try:
        try:
            run()
        except codetools.DogpileError as e:
            error(e)
            n = len(e.errors)
            sys.exit(n if n < 256 else 255)
        else:
            sys.exit(0)
        finally:
            if 'g' in globals():
                pygithub.debug_ratelimit(g)
    except SystemExit as e:
        debug("exit {status}".format(status=str(e)))
        raise e


if __name__ == '__main__':
    main()
