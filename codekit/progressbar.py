""" progressbar2 related utils"""

from codekit.codetools import warn
from public import public
from time import sleep
import progressbar
import functools


@public
def setup_logging(verbosity=0):
    """Configure progressbar sys.stderr wrapper which is required to play nice
    with logging and not have strange formatting artifacts.
    """
    progressbar.streams.wrap_stderr()


@public
def countdown_timer(seconds=10):
    """Show a simple countdown progress bar

    Parameters
    ----------
    seconds
        Period of time the progress bar takes to reach zero.
    """

    tick = 0.1  # seconds
    n_ticks = int(seconds / tick)

    widgets = ['Pause for panic: ', progressbar.ETA(), ' ', progressbar.Bar()]
    pbar = progressbar.ProgressBar(
        widgets=widgets, max_value=n_ticks
    ).start()

    for i in range(n_ticks):
        pbar.update(i)
        sleep(tick)

    pbar.finish()


@public
def wait_for_user_panic(**kwargs):
    """Display a scary message and count down progresss bar so an interative
    user a chance to panic and kill the program.

    Parameters
    ----------
    kwargs
        Passed verbatim to countdown_timer()
    """
    warn('Now is the time to panic and Ctrl-C')
    countdown_timer(**kwargs)


@public
@functools.lru_cache()
def wait_for_user_panic_once(**kwargs):
    """Same functionality as wait_for_user_panic() but will only display a
    countdown once, reguardless of how many times it is called.

    Parameters
    ----------
    kwargs
        Passed verbatim to wait_for_user_panic()
    """

    wait_for_user_panic(**kwargs)


@public
def eta_bar(msg, max_value):
    """Display an adaptive ETA / countdown bar with a message.

    Parameters
    ----------
    msg: str
        Message to prefix countdown bar line with

    max_value: max_value
        The max number of progress bar steps/updates
    """

    widgets = [
        "{msg}:".format(msg=msg),
        progressbar.Bar(), ' ', progressbar.AdaptiveETA(),
    ]

    return progressbar.ProgressBar(widgets=widgets, max_value=max_value)
