from hycmark import CMark
from .utils import truncate_middle

class Markdown(object):
    """
# Markdown(text)

The Markdown() constructor takes a single string argument which should be
Markdown text.  The markdown content is transformed on demand.  The output
format depends on what is provided by the underlying Markdown implementation.
Currently only HTML is provided.

This provides more limited capability than Content() and is intended for
marking up short fragments of text provided from YaML or other content.

The following properties are supported:
* `source` --- Unprocessed (raw) text.

The following methods are supported:
* `__str__()` --- The processed content of the Markdown file,
"""

    def __init__(self, markdown):
        super().__init__()
        self._raw_content = str(markdown)
        self._cm = CMark(self._raw_content)
        self._content = None


    def __str__(self):
        """content is processed markdown text"""
        if self._content is None:
            self._render()
        return self._content


    def __repr__(self):
        return "<class Markdown('{md}')>".format(md=truncate_middle(self._raw_content, 60))


    @property
    def source(self):
        return self._raw_content

    def links(self):
        return self._cm.links()


    def update_links(self, linkmap):
        return self._cm.update_links(linkmap)


    def _render(self):
        self._content = self._cm.render_html()
