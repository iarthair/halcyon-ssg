import os, shutil
import yaml
import re
from .utils import canonicpath, getpath, expand_path, newer, halcyon_data_path
from .page import Page
from .content import Content
from .markdown import Markdown
import jinja2
from datetime import datetime
from .include import include_config, search_page
import traceback

class Halcyon(object):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._sitemap = 'sitemap.yml'
        self._date_format = '%A %-d %B %Y %H:%M'
        self._output_dir = './html'         # output directory for site files
        self._theme_path = halcyon_data_path('themes')
        self._template_path = './templates'    # Jinja templates directory
        self._asset_path = './assets'      # assets to copy to site
        self._site_root = '/'               # site URL path root
        self._ignore_dir = {self._output_dir}
        self._dump_sitemap = False
        self._render_pages = []
        self._content = []
        self._markdown_ext = re.compile(r'.*\.(md|mkd|mdown|markdown)$')

        # !config scalar-or-list --- scan directories for YaML files and parse content
        def _config_tag(loader, node):
            path = loader.construct_scalar(node)
            return include_config(self._sitemap, path)
        yaml.add_constructor('!config', _config_tag, Loader=yaml.CSafeLoader)


        # !search scalar-or-list --- scan directories and files for content and create pages
        def _search_tag(loader, node):
            path = loader.construct_scalar(node)
            pages = search_page(path)
            self._render_pages.extend(pages)
            return pages
        yaml.add_constructor('!search', _search_tag, Loader=yaml.CSafeLoader)


        # !content pathname --- load markdown content and frontmatter from file
        def _content_tag(loader, node):
            filename = loader.construct_scalar(node)
            content = Content(canonicpath(filename))
            self._content.append(content)
            return content
        yaml.add_constructor('!content', _content_tag, Loader=yaml.CSafeLoader)
        yaml.add_implicit_resolver('!content', self._markdown_ext, Loader=yaml.CSafeLoader)


        # !markdown text --- mark text for markdown processing
        def _markdown_tag(loader, node):
            return Markdown(loader.construct_scalar(node))
        yaml.add_constructor('!markdown', _markdown_tag, Loader=yaml.CSafeLoader)


        # !page mapping --- create a page and merge frontmatter with supplied mapping
        def _page_tag(loader, node):
            page = Page(loader.construct_mapping(node))
            self._render_pages.append(page)
            return page
        yaml.add_constructor('!page', _page_tag, Loader=yaml.CSafeLoader)


    def __call__(self, sitemap=None):
        try:
            self.read_sitemap(sitemap or self._sitemap)
            self.fixup_config()
            self.copy_assets()
            self.render_pages()
        except Exception as err:
            print('Error: {}'.format(err))
            #traceback.print_exc()


    def read_sitemap(self, sitemap):
        with open(sitemap) as stream:
            self._data = yaml.load(stream, Loader=yaml.CSafeLoader)

        # pop these configuration items
        self._date_format = canonicpath(self._data.pop('date_format', self._date_format))
        self._output_dir = canonicpath(self._data.pop('output_dir', self._output_dir))
        self._site_root = self._data.pop('root', self._site_root)

        # build up the templates path and assets path
        # add variables from sitemap first so they can override the theme, if necessary
        template_path = expand_path(self._data.pop('template_path', self._template_path))
        asset_path = expand_path(self._data.pop('asset_path', self._asset_path))
        # compute theme path for the selected theme and append to respective paths
        theme = self._data.get('theme', 'halcyon')
        if 'theme_path' not in self._data:
            theme_path = self._theme_path
        else:
            theme_path = expand_path(self._data.pop('theme_path'))
            theme_path.extend(self._theme_path)
        for item in theme_path:
            for templates in ('templates', '_layouts'):
                directory = os.path.join(item, theme, templates)
                template_path.append(directory)
            for assets in ('assets', 'css', 'images'):
                directory = os.path.join(item, theme, assets)
                asset_path.append(directory)

        # filter down paths for the directories that actually exist and de-duplicate
        self._template_path = [path for index, path in enumerate(template_path)
                                if path not in template_path[:index] and os.path.isdir(path)]
        self._asset_path = [path for index, path in enumerate(asset_path)
                             if path not in asset_path[:index] and os.path.isdir(path)]

        print("""Processing files:
        Output:    {output}
        Templates: {templates}
        Assets:    {assets}
        Site Root: {root}\n""".format(output=self._output_dir,
                                      templates=os.pathsep.join(self._template_path),
                                      assets=os.pathsep.join(self._asset_path),
                                      root=self._site_root))


    def fixup_config(self):
        # make sure all pages are fixed up before rendering starts so
        # that menu URLs etc work properly.
        for page in self._render_pages:
            page.configure(self._site_root)

        # ignore output directories and template directories
        self._ignore_dir.update(self._template_path)
        self._ignore_dir.update(page['output_dir'] for page in self._render_pages
                                        if 'output_dir' in page)

        # maybe dump the config as json
        if self._dump_sitemap:
            with open(self._dump_sitemap, 'w') as jfp:
                json.dump(self._data, jfp, indent = 3)


    def copy_assets(self):
        def filterdir(dirname, dirs):
            """Test if dirname is in dirs

            Return True if dirname is the same file as any of the directories
            in the dirs collection.  Dirname must exist and only existing
            directories are tested.
            """
            return any(os.path.samefile(dirname, item)
                         for item in dirs if os.path.exists(item))

        # Copy assets to the destination dir.  Ignore files and directories
        # starting with '_'. Scan source directory then theme directory.
        # During theme scan ignore files if destination already present.
        print("Copying assets:        {assets}".format(
                                    assets=os.pathsep.join(self._asset_path)))
        for path in self._asset_path:
            cpath = os.path.abspath(path)
            parent = os.path.dirname(cpath)
            for root, dirs, files in os.walk(cpath):
                dirs[:] = [item for item in dirs
                             if not (item.startswith(('.', '_'))
                                     or filterdir(os.path.join(root, item), self._ignore_dir))]
                relroot = os.path.join(self._output_dir, os.path.relpath(root, start=parent))
                copy = [(os.path.join(root, item), os.path.join(relroot, item))
                            for item in files
                                if not (item == self._sitemap or item.startswith((os.curdir, '_')))]
                # copy the files, ignore files already present unless source is newer
                for src, dst in copy:
                    if not os.path.isfile(dst) or newer(src, dst):
                        os.makedirs(relroot, exist_ok=True)
                        shutil.copy(src, dst)


    def add_filters(self, env):

        def datetimeformat(value, format=self._date_format):
            if not (value and isinstance(value, str)):
                return value
            dt = datetime.fromisoformat(value)
            return dt.strftime(format)
        env.filters['date'] = datetimeformat

        def chop(value, start=0, limit=10):
            return value[start:limit]
        env.filters['chop'] = chop

        def url(value, **kwargs):
            return value
        env.filters['url'] = url


    def render_pages(self):
        loader = jinja2.FileSystemLoader(self._template_path, encoding='utf-8',
                                         followlinks=True)
        jinja_env = jinja2.Environment(loader=loader, trim_blocks=True,
                                       lstrip_blocks=True)
        self.add_filters(jinja_env)
        halcyon = dict(sitemap=self._sitemap,
                       output_dir=self._output_dir,
                       template_path=self._template_path,
                       asset_path=self._asset_path,
                       root=self._site_root,
                       pages=self._render_pages)
        jinja_env.globals.update(self._data, halcyon=halcyon)

        for page in self._render_pages:
            try:
                page.render(self._output_dir, jinja_env)
            except Exception as err:
                print('Error: {}'.format(err))
                #traceback.print_exc()
