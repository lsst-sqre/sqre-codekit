"""Assorted codetools utility functions."""
# technical debt
# --------------
# - package

from datetime import datetime
from pkg_resources import get_distribution
from public import public
import argparse
import functools
import gitconfig
import logging
import os
import requests
import shutil
import sys
import tempfile


logging.basicConfig()
logger = logging.getLogger('codekit')


# based on _VersionAction() from:
# https://github.com/python/cpython/blob/3.6/Lib/argparse.py
class ScmVersionAction(argparse.Action):
    """Print --version string as `<command> <version>` where `version` is the
    distirubtion version."""
    def __init__(self,
                 option_strings,
                 version=None,
                 dest=argparse.SUPPRESS,
                 default=argparse.SUPPRESS,
                 help="show program's version number and exit"):
        super(ScmVersionAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help)
        self.version = version

    def __call__(self, parser, namespace, values, option_string=None):
        version = get_distribution('sqre-codekit').version
        formatter = parser._get_formatter()
        formatter.add_text("%(prog)s {v}".format(v=version))
        parser._print_message(formatter.format_help(), sys.stdout)
        parser.exit()


@public
def lookup_email(args):
    """Return the email address to use when creating git objects or exit
    program.

    Parameters
    ----------
    args: parser.parse_args()

    Returns
    -------
    email : `string`
        git user email address
    """
    email = args.email
    if email is None:
        email = gituseremail()

    if email is None:
        error('unable to determine a git email')
        sys.exit('Specify --email option')

    debug("email is {email}".format(email=email))

    return email


@public
def lookup_user(args):
    """Return the user name to use when creating git objects or exit
    program.

    Parameters
    ----------
    args: parser.parse_args()

    Returns
    -------
    user: `string`
        git user name
    """
    user = args.user
    if user is None:
        user = gitusername()

    if user is None:
        error('unable to determine a git user name')
        sys.exit("Specify --user option")

    debug("user name is {user}".format(user=user))

    return user


@public
def github_token(token_path=None, token=None):
    """Return a github oauth token as a string.  If `token` is defined, it is
    has precendece.  If `token` and `token_path` are `None`,
    `~/.sq_github_token` looked for as a fallback.

    Parameters
    ----------
    token_path : str, optional
        Path to the token file. The default token is used otherwise.

    token: str, optional
        Literial token string. If specifified, this value is used instead of
        reading from the token_path file.

    Returns
    -------
    token : `string`
        Hopefully, a valid github oauth token.
    """
    if token is None:
        if token_path is None:
            # Try the default token
            token_path = '~/.sq_github_token'
        token_path = os.path.expandvars(os.path.expanduser(token_path))

        if not os.path.isfile(token_path):
            print("You don't have a token in {0} ".format(token_path))
            print("Have you run github-auth?")
            raise EnvironmentError("No token in %s" % token_path)

        with open(token_path, 'r') as fdo:
            token = fdo.readline().strip()

    return token


@public
def gitusername():
    """
    Returns the user's name from .gitconfig if available
    """
    try:
        mygitconfig = gitconfig.GitConfig()
        return mygitconfig['user.name']
    except:
        return None


@public
def gituseremail():
    """
    Returns the user's email from .gitconfig if available
    """

    try:
        mygitconfig = gitconfig.GitConfig()
        return mygitconfig['user.email']
    except:
        return None


@public
def github_2fa_callback():
    """
    Prompt for two-factor code
    """
    code = ''
    while not code:
        # The user could accidentally press Enter before being ready,
        # let's protect them from doing that.
        code = input('Enter 2FA code: ')
    return code


@functools.lru_cache(maxsize=1024)
@public
def fetch_manifest_file(
    build_id,
    versiondb='https://raw.githubusercontent.com'
              '/lsst/versiondb/master/manifests',
    debug=False
):
    # eg. https://raw.githubusercontent.com/lsst/versiondb/master/manifests/b1108.txt  # NOQA
    shafile = versiondb + '/' + build_id + '.txt'
    logger.debug("fetching: {url}".format(url=shafile))

    # Get the file tying shas to eups versions
    r = requests.get(shafile)
    r.raise_for_status()

    return r.text


@functools.lru_cache(maxsize=1024)
@public
def parse_manifest_file(data):
    products = {}

    for line in data.splitlines():
        if not isinstance(line, str):
            line = str(line, 'utf-8')
        # skip commented out and blank lines
        if line.startswith('#'):
            continue
        if line.startswith('BUILD'):
            continue
        if line == '':
            continue

        (product, sha, eups_version) = line.split()[0:3]

        products[product] = {
            'name': product,
            'sha': sha,
            'eups_version': eups_version,
        }

    return products


@functools.lru_cache(maxsize=1024)
@public
def eups2git_ref(
    product,
    eups_version,
    build_id,
    debug=False
):
    """Provide the sha1 for an EUPS product."""

    manifest = fetch_manifest_file(build_id, debug=debug)
    products = parse_manifest_file(manifest)

    entry = products[product]
    if entry['eups_version'] == eups_version:
        return entry['sha']
    else:
        raise RuntimeError(
            "failed to find record in manifest {build_id} for:\n"
            "  {product} {eups_version}".format(
                build_id=build_id,
                product=product,
                eups_version=eups_version
            )
        )


@public
def info(*args):
    logger.info(*args)


@public
def debug(*args):
    logger.debug(*args)


@public
def warn(*args):
    logger.warn(*args)


@public
def error(*args):
    logger.error(*args)


@public
class TempDir(object):
    """ContextManager for temporary directories.

    For example::

        import os
        with TempDir() as temp_dir:
            assert os.path.exists(temp_dir)
        assert os.path.exists(temp_dir) is False
    """

    def __init__(self):
        super(TempDir, self).__init__()
        self._temp_dir = tempfile.mkdtemp()

    def __enter__(self):
        return self._temp_dir

    def __exit__(self, ttype, value, traceback):
        shutil.rmtree(self._temp_dir)
        self._temp_dir = None


@public
def current_timestamp():
    """Returns current time as ISO8601 formatted string in the Zulu TZ"""
    now = datetime.utcnow()
    timestamp = now.isoformat()[0:19] + 'Z'

    debug("generated timestamp: {now}".format(now=timestamp))

    return timestamp


@public
def validate_org(org):
    """Check that organization name is 'safe' to use for possibly destructive
    operations.

    Parameters
    ----------
    org: str
        Name of github organization

    Raises
    ------
    AssertionError
        To chicken out on org name
    """
    assert 'lsst' not in org, '"lsst" not allowed in org name.'
