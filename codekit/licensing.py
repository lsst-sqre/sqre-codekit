"""Utilities for maintaining and asserting LICENSE and COPYRIGHT in
LSST DM repos.
"""

import re


comment_pattern = re.compile(
    '(?P<comment_flag>^[#* ])(?P<content>[\d\w\s<]*)')


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
    # Text for the new copyright/license boilerplate
    template_lines = [
        '{comment} See the COPYRIGHT and LICENSE files in the top-level '
        'directory of this\n',
        '{comment} package for notices and licensing terms.\n'
    ]
    lines = code_stream.readlines()
    new_lines = []
    omitting_mode = False
    for line in lines:
        m = comment_pattern.match(line)
        if m is None:
            # Pass through of non-comment characters
            new_lines.append(line)
            continue

        content = m.group('content').lstrip()
        if m is not None and content.startswith('Copyright'):
            # Trigger replacement at start of Copyright block
            for template_line in template_lines:
                new_lines.append(
                    template_line.format(comment=m.group('comment_flag')))
            omitting_mode = True
        elif content.startswith('see <http'):  # NOQA
            # End replacement mode
            omitting_mode = False
        elif omitting_mode is False:
            # Pass through mode
            if line.rstrip() == '#':
                # remove whitespace from comment header/footer for Python
                new_lines.append('#\n')
            else:
                new_lines.append(line)
    return ''.join(new_lines)
