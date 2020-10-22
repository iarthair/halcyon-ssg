import os
from .page import Page
from .content import Content
from .utils import rootname, expand_path, canonicpath, changeext, pathjoin
import yaml

# read extra config - add to item named with basename of file
# FIXME different directories with the same filename will clobber

def include_config(sitemap, include):

    config = {}

    def loaddir(pathname):
        for basename in os.listdir(pathname):
            if not basename.endswith(('.yml', '.yaml')):
                continue
            loadfile(os.path.join(pathname, basename))

    def loadfile(pathname):
        if pathname.endswith(sitemap):
            return
        root = rootname(pathname)
        print("Reading configuration: {conf}".format(conf=pathname))
        with open(pathname) as cfp:
            conf = yaml.load(cfp, Loader=yaml.CSafeLoader)
        config[root] = conf

    for pathname in expand_path(include):
        if os.path.isdir(pathname):
            loaddir(pathname)
        else:
            loadfile(pathname)
    return config

# This scans each directory looking for source files (markdown) and constructs
# a list of Page()s.

def search_page(include):

    prefixes = ('.', '_')
    extensions = ('.md', '.mkd', '.mdown', '.markdown')
    self_render_pages = []

    def whitelist(name):
        return not name.startswith(prefixes) and name.endswith(extensions)

    def removeprefix(s,p):
        return s[len(p):] if s.startswith(p) else s

    for name in expand_path(include):
        canon = canonicpath(name)
        prefix = os.path.basename(canon) if canon.startswith(('.','/')) else ''

        for root, dirs, files in os.walk(canon):
            # don't process directories starting with . or _
            dirs[:] = [item for item in dirs if not item.startswith(prefixes)]

            url_prefix = os.path.relpath(root, start=prefix)

            print(name, canon, root, prefix, url_prefix)

            for basename in (item for item in files if whitelist(item)):
                if not basename.endswith(extensions):
                    continue
                url = pathjoin(url_prefix, changeext(basename, 'html'))
                filename = pathjoin(root, basename)

                # construct the page
                entry = Page(path=url, content=Content(filename))
                self_render_pages.append(entry)

    return self_render_pages
