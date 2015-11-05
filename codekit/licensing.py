"""Utilities for maintaining and asserting LICENSE and COPYRIGHT in
LSST DM repos.
"""


def convert_boilerplate(code_stream):
    """Convert old-style licensing boilerplate (with full GPLv3) to RFC-45
    style.

    Parameters
    ----------
    code_stream : file-like object
        File handle to code.

    Returns
    -------
    converted_text : str
        Converted code text, as a string.
    """
    lines = code_stream.readlines()
    new_lines = []
    omitting_mode = False
    for line in lines:
        if line.startswith('# Copyright'):
            # Trigger replacement at start of Copyright block
            new_lines.append('# See the COPYRIGHT and LICENSE files in the top-level directory of this\n')  # NOQA
            new_lines.append('# package for notices and licensing terms.\n')  # NOQA
            omitting_mode = True
        elif line.startswith('# see <http://www.lsstcorp.org/LegalNotices/>.'):
            # End replacement mode
            omitting_mode = False
        elif omitting_mode is False:
            # Pass through mode
            if line.rstrip() == '#':
                # remove whitespace from comment header/footer
                new_lines.append('#\n')
            else:
                new_lines.append(line)
    return ''.join(new_lines)
