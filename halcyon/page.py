import jinja2
import re
import os
from .content import Content
from .utils import canonicpath, changeext, pathjoin


class Page(dict):
    """Create a Page object.

Page() is a mapping type initialised as per the dict() constructor's
arguments.  eg:

```markdown
pages:
  - !page
    theme: xyzzy.html
    path: content/out.html
    content: filename.md # or content: !include filename.mkdown
  - !page
    theme: xyzzy.html
    path: content/out.html
    content: some literal text to use
```

Page() objects are not directly accessed via templates, however they might
be accessed via the tree parsed from YAML, e.g. `pages[0].theme` above.

'content' should be either literal text or a Content() instance, if the latter
it merges values from the content frontmatter or metadata if available. In
addition it ensures the following keys are available:

* `page` --- self reference for better Jekyll compatibility
* `path` --- output file/URL name either explicitly specified or derived
  from `content.filename`.
* `url` --- derived from `path` and supplied site root (usually '/').

The following methods are available to templates:

* `previous(list)` --- Find the page preceding this one in list or None.
* `next(list)` --- Find the page following this one in list or None.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._output_dir = os.curdir
        content = self.get('content', None)
        if isinstance(content, Content):
            if 'path' not in self:
                self['path'] = changeext(content.filename, 'html')
        self._content = content


    def __repr__(self):
        return '<class Page({})>'.format(self.get('path',''))


    def configure(self, root):
        """configure the page in a pass prior to rendering so that templates
        can access metadata for all pages rather than just the current page"""

        # Jekyll compatibility, sort of. Merge frontmatter or metadata.
        # XXX merge or should templates use 'content.frontmatter.key'?
        if self._content:
            var = getattr(self._content, 'frontmatter', None)
            if isinstance(var, dict):
                self.update(var)
            else:
                var = getattr(self._content, 'metadata', None)
                if isinstance(var, dict):
                    self.update(var)

        if 'title' not in self:
            self['title'] = getattr(self._content, 'heading', None)
        if 'date' not in self:
            self['date'] = getattr(self._content, 'date', None)

        # Make sure URL is set. NB 'path' is required
        if 'url' not in self:
            path = self['path']
            self['url'] = pathjoin(root, path)

        # Hack to ensure methods visible to Jinja, here so cannot be overwritten
        page = {'previous': self._previous,
                'next': self._next,
                'active': False}
        self.update(page)


    def render(self, output_dir, jinja_env):
        """render the page to output_dir, using jinja_env"""

        path = self['path']
        print("Processing page:       {path}".format(path=path))

        filename = os.path.join(output_dir, path)

        # ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        # get the page theme and render output
        # Note that properties and methods on this and other classes
        # are called via the templates.
        theme = self.get('theme', jinja_env.globals.get('theme', 'default.html'))
        template = jinja_env.get_template(theme)
        with open(filename, 'w') as stream:
            self['active'] = True
            for chunk in template.generate(self):
                stream.write(chunk)
            self['active'] = False


    def _previous(self, sequence):
        """If this page is a member of sequence, return the previous page, else None."""
        try:
            index = sequence.index(self)
        except:
            return None
        return sequence[index - 1] if index > 0 else None


    def _next(self, sequence):
        """If this page is a member of sequence, return the next page, else None."""
        try:
            index = sequence.index(self)
        except:
            return None
        return sequence[index + 1] if index < len(sequence) - 1 else None
