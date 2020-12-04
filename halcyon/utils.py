import re, os

def rootname():
    cre = re.compile(r'\W+')
    def func(pathname):
        basename = os.path.basename(pathname).split('.', 1)[0]
        return cre.sub('_', basename).lstrip('_')
    return func
rootname = rootname()


# https://www.xormedia.com/string-truncate-middle-with-ellipsis/
def truncate_middle(s, length=255, separator=' … '):
    if len(s) <= length:
        return s
    slen = len(separator)
    n_2 = length // 2 - slen
    n_1 = length - n_2 - slen
    return separator.join((s[:n_1].strip(), s[-n_2:].strip()))


def changeext(path, ext):
    return os.extsep.join((os.path.splitext(path)[0], ext))

def pathjoin(path, *tail):
    return os.path.normpath(os.path.join(path, *tail))

def canonicpath(path):
    return os.path.normpath(os.path.expanduser(path))


def newer(path1, path2):
    """Test of path1 is newer than path2"""
    return os.path.getmtime(path1) > os.path.getmtime(path2)


def normalize_space(text):
    return ' '.join(text.split())


def getpath(node, key, dflt):
    """Return a list of normalised pathnames from the specified key.

    The value at key should be a colon separated list of pathnames or a list
    specifying one pathname per item.
    """
    return expand_path(node.get(key, dflt))


def expand_path(value):
    """Return a list of normalised pathnames from the specified key.

    Value should be a colon separated list of pathnames or a list
    specifying one pathname per item.
    """
    if not isinstance(value, (list,tuple)):
        value = value.split(os.pathsep) if isinstance(value, str) else []
    return [canonicpath(item or os.curdir) for item in value]

def system_data_path():
    # XDG spec
    # https://specifications.freedesktop.org/basedir-spec/latest/ar01s03.html

    # System directories
    path = os.getenv('XDG_DATA_DIRS', default='/usr/local/share/:/usr/share/')
    paths = [item or os.curdir for item in path.split(os.pathsep)]

    # User directory
    localdata = os.getenv('XDG_DATA_HOME', default='~/.local/share/')
    paths.insert(0, os.path.expanduser(localdata))

    # remove non-existent directories and duplicates
    return [path for index, path in enumerate(paths)
                    if path not in paths[:index] and os.path.isdir(path)]

def user_data_path():
    # XDG spec
    # https://specifications.freedesktop.org/basedir-spec/latest/ar01s03.html

    # User directory
    localdata = os.getenv('XDG_DATA_HOME', default='~/.local/share/')
    path = os.path.expanduser(localdata)

    return [path] if os.path.isdir(path) else []

def data_path(dirs, localdir, which):
    # user theme directory
    temp = [os.path.expanduser(os.path.join('~/.' + localdir, which))]
    temp.extend(os.path.join(item, 'halcyon', which) for item in dirs)

    # remove non-existent directories
    return [path for path in temp if os.path.isdir(path)]
