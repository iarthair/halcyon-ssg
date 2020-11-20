import os
from datetime import datetime

class Plaintext(object):
    """
# Plaintext(filename)

The Plaintext() constructor takes a single filename argument which should be a
regular file containing plain text.  This is sometimes useful to include a file
verbatim.

The following methods are supported:
* `__str__()` --- The processed content of the Markdown file,

The following properties are supported:
* `filename` --- Source file.
* `date` --- Source file modification time.
"""

    def __init__(self, filename):
        super().__init__()
        self._filename = filename
        self._content = None
        self._date = None


    def __repr__(self):
        return "<class Content('{filename}')>".format(filename=self._filename)


    def __str__(self):
        if self._content is None:
            self._include()
        return self._content


    @property
    def filename(self):
        return self._filename


    @property
    def date(self):
        if self._date is None:
            mtime = os.path.getmtime(self._filename)
            self._date = datetime.fromtimestamp(mtime).isoformat()
        return self._date


    def _include(self):
        """ Include pathname at current node."""

        if self._content is not None:
            return

        with open(self._filename) as stream:
            self._content = stream.read()
