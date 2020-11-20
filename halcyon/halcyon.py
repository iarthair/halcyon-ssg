import os, shutil
import yaml
import sass
import re
from .utils import canonicpath, getpath, expand_path, newer, halcyon_data_path
from .utils import changeext
from .page import Page
from .content import Content
from .plaintext import Plaintext
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
        self._template_path = './templates' # Jinja templates directory
        self._sass_path = './sass:./scss'   # libsass search path
        self._asset_path = './assets'       # assets to copy to site
        self._site_root = '/'               # site URL path root
        self._ignore_dir = {self._output_dir}
        self._dump_sitemap = False
        self._render_pages = []
        self._content = []
        self._markdown_ext = re.compile(r'.*\.(md|mkd|mdown|markdown)$')
        self._plaintext_ext = re.compile(r'.*\.txt$')

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


        def _plaintext_tag(loader, node):
            filename = loader.construct_scalar(node)
            content = Plaintext(canonicpath(filename))
            self._content.append(content)
            return content
        yaml.add_constructor('!plaintext', _plaintext_tag, Loader=yaml.CSafeLoader)
        yaml.add_implicit_resolver('!plaintext', self._markdown_ext, Loader=yaml.CSafeLoader)


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
        """The sitemap is a structure ultimately passed through to Jinja.

        Halcyon configuration variables in the sitemap are at the top level
        but being migrated to the 'halcyon' key.  Configuration variables are:
        - date_format   Format for printing dates       '%A %-d %B %Y %H:%M'
        - output_dir    Site output directory           './html'
        - root          Site root                       '/'
        - template_path Search path for templates       './templates'
        - sass_path     Search path for SASS/SCSS       './sass:./scss'
        - asset_path    Search path for copied assets   './assets'
        - theme_path    Search path for Halcyon themes
                        in addition to system defaults.
        The site theme is specified at top level using 'theme'.
        """
        with open(sitemap) as stream:
            self._data = yaml.load(stream, Loader=yaml.CSafeLoader)

        # Migrate config variables to 'halcyon' key.
        config = self._data.get('halcyon', self._data)
        if 'halcyon' not in self._data:
            self._data['halcyon'] = dict()
        print("config", type(config))

        # pop these configuration items
        self._date_format = canonicpath(config.pop('date_format', self._date_format))
        self._output_dir = canonicpath(config.pop('output_dir', self._output_dir))
        self._site_root = config.pop('root', self._site_root)

        # build up the templates path and assets path
        # add variables from sitemap first so they can override the theme, if necessary
        template_path = expand_path(config.pop('template_path', self._template_path))
        sass_path = expand_path(config.pop('sass_path', self._sass_path))
        asset_path = expand_path(config.pop('asset_path', self._asset_path))

        # compute theme path for the selected theme and append to respective paths
        theme = self._data.get('theme', 'halcyon')
        if 'theme_path' not in config:
            theme_path = self._theme_path
        else:
            theme_path = expand_path(config.pop('theme_path'))
            theme_path.extend(self._theme_path)
        for item in theme_path:
            for templates in ('templates', '_layouts'):
                directory = os.path.join(item, theme, templates)
                template_path.append(directory)
            for scss in ('sass', 'scss', '_sass', '_scss'):
                directory = os.path.join(item, theme, scss)
                sass_path.append(directory)
            for assets in ('assets', 'css', 'js', 'images'):
                directory = os.path.join(item, theme, assets)
                asset_path.append(directory)

        # filter down paths for the directories that actually exist and de-duplicate
        self._template_path = [path for index, path in enumerate(template_path)
                                if path not in template_path[:index] and os.path.isdir(path)]
        self._sass_path = [os.path.abspath(path) for index, path in enumerate(sass_path)
                                if path not in sass_path[:index] and os.path.isdir(path)]
        self._asset_path = [path for index, path in enumerate(asset_path)
                             if path not in asset_path[:index] and os.path.isdir(path)]

        print("""Processing files:
        Output:    {output}
        Templates: {templates}
        Assets:    {assets}
        Sass/Scss: {sass}
        Site Root: {root}\n""".format(output=self._output_dir,
                                      templates=os.pathsep.join(self._template_path),
                                      assets=os.pathsep.join(self._asset_path),
                                      sass=os.pathsep.join(self._sass_path),
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
        def filterdir(root, name):
            """
            Return True if the name starts with . or _ or the dirname is the
            same file as any of the directories in the ignore_dir collection.
            Dirname must exist and only existing directories are tested.
            """
            if name.startswith(('.', '_')):
                return True
            dirname = os.path.join(root, name)
            return any(os.path.samefile(dirname, item)
                       for item in self._ignore_dir if os.path.exists(item))

        def filterfile(name):
            if name == self._sitemap or name.startswith(('.', '_')):
                return True
            return False

        # Copy assets to the destination dir.  Ignore files and directories
        # starting with '_'. Scan source directory then theme directory.
        # During theme scan ignore files if destination already present.
        print("Copying assets:        {assets}".format(
                                    assets=os.pathsep.join(self._asset_path)))
        for path in self._asset_path:
            cpath = os.path.abspath(path)
            parent = os.path.dirname(cpath)
            for root, dirs, files in os.walk(cpath):
                # filter the list of subdirectories to search
                dirs[:] = [item for item in dirs if not filterdir(root, item)]

                # relroot is the path to the files' output directory
                relroot = os.path.join(self._output_dir, os.path.relpath(root, start=parent))

                # create tuples of source and destination filenames
                # ignore names stating with . or _ and the sitemap itself
                copy = [(os.path.join(root, item), os.path.join(relroot, item))
                            for item in files if not filterfile(item)]

                # copy the files, ignore files already present unless source is newer
                # Hack: if source file is SASS or SCSS, process with libsass
                for src, dst in copy:
                    try:
                        if src.endswith(('.sass', '.scss')):
                            dstcss = changeext(dst, 'css')
                            css = sass.compile(filename=src,
                                               include_paths=self._sass_path)
                            os.makedirs(relroot, exist_ok=True)
                            with open(dstcss, 'w') as stream:
                                stream.write(css)
                        elif not os.path.isfile(dst) or newer(src, dst):
                            os.makedirs(relroot, exist_ok=True)
                            shutil.copy(src, dst)
                    except Exception as err:
                        print('Error: {}'.format(err))
                        #traceback.print_exc()


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
            print("reminder implement url() filter")
            return value
        env.filters['url'] = url

        def obfuscate(string, **kwargs):
            print("reminder implement obfuscate() filter")
            return string
        env.filters['obfuscate'] = obfuscate


    def render_pages(self):
        loader = jinja2.FileSystemLoader(self._template_path, encoding='utf-8',
                                         followlinks=True)
        jinja_env = jinja2.Environment(loader=loader, trim_blocks=True,
                                       lstrip_blocks=True)
        self.add_filters(jinja_env)
        self._data['halcyon'].update(sitemap=self._sitemap,
                                     output_dir=self._output_dir,
                                     template_path=self._template_path,
                                     sass_path=self._sass_path,
                                     asset_path=self._asset_path,
                                     root=self._site_root,
                                     pages=self._render_pages)
        jinja_env.globals.update(self._data)

        for page in self._render_pages:
            try:
                page.render(self._output_dir, jinja_env)
            except Exception as err:
                #print('Error: {}'.format(err))
                traceback.print_exc()
