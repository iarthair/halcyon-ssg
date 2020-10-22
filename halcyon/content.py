import yaml
import re
import os
from datetime import datetime
from hycmark import CMark
from .utils import canonicpath, normalize_space

class Content(object):
    """
# Content(filename)

The Content() constructor takes a single filename argument which should be a
regular file containing Markdown text.  The markdown content is transformed on
demand.  The output format depends on what is provided by the underlying
Markdown implementation. Currently only HTML is provided.

The following methods are supported:
* `__str__()` --- The processed content of the Markdown file,

The following properties are supported:
* `filename` --- Source file.
* `date` --- Source file modification time.
* `source` --- Unprocessed (raw) text less any frontmatter.
* `excerpt` --- Raw text from the first paragraph in the document.
* `heading` --- Raw text from the first level 1 heading in the document.
* `frontmatter` --- Dictionary containing the YaML front matter, if provided.
* `metadata` --- Dictionary containing the Markdown metadata, if supported.
* `toc` --- List of 3-tuples for first and second level headings, if supported.
"""

    _element = re.compile(r'</?\w+/?>')

    def __init__(self, filename):
        super().__init__()
        self._filename = filename
        self._raw_content = None
        self._content = None
        self._frontmatter = None
        self._metadata = None
        self._toc = None
        self._date = None
        self._cm = None


    def __str__(self):
        """content is processed markdown (or whatever) text"""
        if self._content is None:
            self._render()
        return self._content


    def __repr__(self):
        return "<class Content('{filename}')>".format(filename=self._filename)


    @property
    def filename(self):
        return self._filename


    @property
    def source(self):
        if self._raw_content is None:
            self._include()
        return self._raw_content


    @property
    def heading(self):
        if self._cm is None:
            self._include()
        return self._cm.title()


    @property
    def excerpt(self):
        if self._cm is None:
            self._include()
        return self._cm.excerpt()


    @property
    def frontmatter(self):
        """frontmatter is a dictionary of name-value pairs for markdown frontmatter"""
        if self._frontmatter is None and self._raw_content is None:
            self._include()
        return self._frontmatter


    @property
    def metadata(self):
        """metadata is a dictionary of name-value pairs for markdown metadata"""
        if self._metadata is None:
            if self._raw_content is None:
                self._include()
            # FIXME load metadata
            self._metadata = dict()
        return self._metadata


    @property
    def date(self):
        if self._date is None:
            mtime = os.path.getmtime(self._filename)
            self._date = datetime.fromtimestamp(mtime).isoformat()
        return self._date


    def links(self):
        if self._cm is None:
            self._include()
        return self._cm.links()


    def update_links(self, linkmap):
        if self._cm is None:
            self._include()
        return self._cm.update_links(linkmap)


    def _include(self):
        """ Include pathname at current node.

        Read frontmatter from filename.  Read the rest of the content from the
        file as _raw_content.  If 'date' is missing from frontmatter, use the
        file's modification time.
        """

        def frontmatter(stream):
            """Read frontmatter from the stream"""
            if stream.readline() != '---\n':
                stream.seek(0)
                return ''
            return ''.join(iter(stream.readline, '---\n'))

        with open(self._filename) as stream:
            self._frontmatter = yaml.load(frontmatter(stream),
                                          Loader=yaml.CSafeLoader)
            self._raw_content = stream.read()
        self._cm = CMark(self._raw_content)


    def _render(self):
        if self._cm is None:
            self._include()
        self._content = self._cm.render_html()
