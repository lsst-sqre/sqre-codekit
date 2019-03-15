"""Assorted codetools utility functions."""
# technical debt
# --------------
# - package


from datetime import datetime
from pkg_resources import get_distribution
from public import public
import argparse
import gitconfig
import os
import shutil
import sys
import tempfile
import textwrap

# configured by setup_logging() -- this is declared only as a friendly reminder
# that something unusual is going on this with this var.
logger = None


@public
def setup_logging(verbosity=0):
    """Configure python `logging`.  This is required before the `debug()`,
    `info()`, etc. functions may be used.

    If any other `codekit.*` modules, which are not a "package", have been
    imported, and they have a `setup_logging()` function, that is called before
    `logging` is configured.  This gives other modules a chance to configure
    their own logging.

    As an example, if `progressbar2` is being used, it needs to be configure a
    `sys.stderr` wrapper before `logging` is configured.  Thus, some gymnastics
    are being done to delay `logging` setup while simultanously not requiring
    that `progressbar2` be imported unless it is actually being used.

    Parameters
    ----------
    verbosity: int
        Logging / output verbosity level. 1 is useful for more purposes while
        2+ is generaly TMI.
    """
    import pkgutil
    import logging
    import codekit

    # https://packaging.python.org/guides/creating-and-discovering-plugins/#using-namespace-packages
    def iter_namespace(ns_pkg):
        # Specifying the second argument (prefix) to iter_modules makes the
        # returned name an absolute name instead of a relative one. This allows
        # import_module to work without having to do additional modification to
        # the name.
        return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")

    # find codekit modules that are not a package
    codekit_mods = [name for finder, name, ispkg in iter_namespace(codekit)
                    if ispkg is False]

    # filter out the current module
    # XXX `is not` doesn't work here but `!=` does... why???
    codekit_mods = [m for m in codekit_mods
                    if m != __name__]

    # filter out modules that have not been imported
    codekit_mods = [m for m in codekit_mods
                    if m in sys.modules]

    # record funcs successfully called
    logging_funcs = []
    for m in codekit_mods:
        try:
            lsetup = getattr(sys.modules[m], 'setup_logging')
            lsetup(verbosity=verbosity)
            logging_funcs.append(lsetup)
        except AttributeError:
            # ignore modules that do have a setup_logging()
            pass

    logging.basicConfig()
    # configure `logger` for the entire module
    global logger
    logger = logging.getLogger('codekit')

    if verbosity:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    [debug("{m}.{f}()".format(m=f.__module__, f=f.__name__))
        for f in logging_funcs]


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


class DogpileError(Exception):
    """Aggregate list of exceptions"""
    def __init__(self, errors, msg):
        self.errors = errors
        self.msg = msg

    def __str__(self):
        return self.msg + "\n" + "\n".join([str(e) for e in self.errors])


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
        raise RuntimeError(textwrap.dedent("""\
            unable to determine a git email
            Specify --email option\
        """))

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
        raise RuntimeError(textwrap.dedent("""\
            unable to determine a git user name
            Specify --user option\
        """))

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


@public
def info(*args):
    if logger:
        logger.info(*args)


@public
def debug(*args):
    if logger:
        logger.debug(*args)


@public
def warn(*args):
    if logger:
        logger.warn(*args)


@public
def error(*args):
    if logger:
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


@public
def debug_lvl_from_env():
    """Read and return `DM_SQUARE_DEBUG` env var, if defined.

    Raises
    ------
    RuntimeError
        If DM_SQUARE_DEBUG is not an int convertable value
    """
    debug_lvl = os.environ.get('DM_SQUARE_DEBUG')
    if not debug_lvl:
        return 0

    try:
        debug_lvl = int(debug_lvl)
    except ValueError:
        # ensure that logging is configured as this method is likely to be
        # called prior to configuring logging.
        setup_logging(verbosity=1)
        raise RuntimeError(
            textwrap.dedent("""\
            env var DM_SQUARE_DEBUG '{debug_lvl}' is not a string value that
            can be converted to an int.""".format(debug_lvl=debug_lvl))
        ) from None
