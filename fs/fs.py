#!/usr/bin/env python

import os
import os.path
import fnmatch
from itertools import chain
import datetime


error_msgs = {

    "UNKNOWN_ERROR" :   "No information on error: %(path)s",
    "UNSUPPORTED" :     "Action is unsupported by this filesystem.",
    "INVALID_PATH" :    "Path is invalid: %(path)s",
    "NO_DIR" :          "Directory does not exist: %(path)s",
    "NO_FILE" :         "No such file: %(path)s",
    "NO_RESOURCE" :     "No path to: %(path)s",
    "LISTDIR_FAILED" :  "Unable to get directory listing: %(path)s",
    "DELETE_FAILED" :   "Unable to delete file: %(path)s",
    "NO_SYS_PATH" :     "No mapping to OS filesytem: %(path)s,",
    "DIR_EXISTS" :      "Directory exists (try allow_recreate=True): %(path)s",
    "OPEN_FAILED" :     "Unable to open file: %(path)s",
    "FILE_LOCKED" :     "File is locked: %(path)s",
}

error_codes = error_msgs.keys()

class FSError(Exception):

    """A catch all exception for FS objects."""

    def __init__(self, code, path=None, msg=None, details=None):

        """

        code -- A short identifier for the error
        path -- A path associated with the error
        msg -- An textual description of the error
        details -- Any additional details associated with the error

        """

        self.code = code
        self.msg = msg or error_msgs.get(code, error_msgs['UNKNOWN_ERROR'])
        self.path = path
        self.details = details

    def __str__(self):

        msg = self.msg % dict((k, str(v)) for k, v in self.__dict__.iteritems())

        return '%s. %s' % (self.code, msg)

class PathError(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class NullFile(object):

    """A NullFile is a file object that has no functionality. Null files are
    returned by the 'safeopen' method in FS objects when the file does not exist.
    This can simplify code by negating the need to check if a file exists,
    or handling exceptions.

    """

    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True

    def flush(self):
        pass

    def __iter__(self):
        return self

    def next(self):
        raise StopIteration

    def readline(self, *args, **kwargs):
        return ""

    def close(self):
        self.closed = True

    def read(self, size=None):
        return ""

    def seek(self, *args, **kwargs):
        pass

    def tell(self):
        return 0

    def truncate(self, *args, **kwargs):
        return 0

    def write(self, data):
        pass

    def writelines(self, *args, **kwargs):
        pass


def isabsolutepath(path):
    """Returns True if a given path is absolute."""
    if path:
        return path[0] in '\\/'
    return False

def normpath(path):
    """Normalizes a path to be in the formated expected by FS objects.
    Returns a new path string."""
    return path.replace('\\', '/')


def pathjoin(*paths):
    """Joins any number of paths together. Returns a new path string.

    paths -- An iterable of path strings

    """
    absolute = False

    relpaths = []
    for p in paths:
        if p:
         if p[0] in '\\/':
             del relpaths[:]
             absolute = True
         relpaths.append(p)

    pathstack = []

    for component in chain(*(normpath(path).split('/') for path in relpaths)):
        if component == "..":
            if not pathstack:
                raise PathError("relative path is invalid")
            sub = pathstack.pop()
        elif component == ".":
            pass
        elif component:
            pathstack.append(component)

    if absolute:
        return "/" + "/".join(pathstack)
    else:
        return "/".join(pathstack)


def pathsplit(path):
    """Splits a path on a path separator. Returns a tuple containing the path up
    to that last separator and the remaining path component.

    >>> pathsplit("foo/bar")
    ('foo', 'bar')

    >>> pathsplit("foo/bar/baz")
    ('foo/bar', 'bar')

    """

    split = normpath(path).rsplit('/', 1)
    if len(split) == 1:
        return ('', split[0])
    return tuple(split)

def resolvepath(path):
    return pathjoin(path)

def makerelative(path):
    if path.startswith('/'):
        return path[1:]
    return path

def makeabsolute(path):
    if not path.startswith('/'):
        return '/'+path
    return path

def _iteratepath(path, numsplits=None):

    path = resolvepath(path)

    if not path:
        return []

    if numsplits == None:
        return filter(lambda p:bool(p), path.split('/'))
    else:
        return filter(lambda p:bool(p), path.split('/', numsplits))


def print_fs(fs, path="/", max_levels=None, indent=' '*2):

    def print_dir(fs, path, level):

        try:
            dir_listing = [(fs.isdir(pathjoin(path,p)), p) for p in fs.listdir(path)]
        except FSError, e:
            print indent*level + "... unabled to retrieve directory list (%s) ..." % str(e)
            return

        dir_listing.sort(key = lambda (isdir, p):(not isdir, p.lower()))

        for is_dir, item in dir_listing:

            if is_dir:
                print indent*level + '[%s]' % item
                if max_levels is None or level < max_levels:
                    print_dir(fs, pathjoin(path, item), level+1)
            else:
                print indent*level + '%s' % item

    print_dir(fs, path, 0)


class FS(object):


    def _resolve(self, pathname):

        resolved_path = resolvepath(pathname)
        return resolved_path


    def abspath(self, pathname):

        pathname = normpath(pathname)

        if not pathname.startswith('/'):
            return pathjoin('/', pathname)
        return pathname

    def getsyspath(self, path):

        raise FSError("NO_SYS_PATH", path)

    def safeopen(self, *args, **kwargs):

        try:
            f = self.open(*args, **kwargs)
        except FSError, e:
            if e.code == "NO_FILE":
                return NullFile()
            raise

    def desc(self, path):

        if not self.exists(path):
            return "No description available"

        try:
            sys_path = self.getsyspath(path)
        except FSError:
            return "No description available"

        if self.isdir(path):
            return "OS dir, maps to %s" % sys_path
        else:
            return "OS file, maps to %s" % sys_path

    def open(self, path, mode="r", buffering=-1, **kwargs):

        pass

    def opendir(self, path):

        if not self.exists(path):
            raise FSError("NO_DIR", path)

        sub_fs = SubFS(self, path)
        return sub_fs


    def remove(self, path):

        raise FSError("UNSUPPORTED", path)


    def _listdir_helper(self, path, paths, wildcard, full, absolute, hidden, dirs_only, files_only):

        if dirs_only and files_only:
            raise ValueError("dirs_only and files_only can not both be True")


        if wildcard is not None:
            match = fnmatch.fnmatch
            paths = [p for p in path if match(p, wildcard)]

        if not hidden:
            paths = [p for p in paths if not self.ishidden(p)]

        if dirs_only:
            paths = [p for p in paths if self.isdir(pathjoin(path, p))]
        elif files_only:
            paths = [p for p in paths if self.isfile(pathjoin(path, p))]

        if full:
            paths = [pathjoin(path, p) for p in paths]
        elif absolute:
            paths = [self.abspath(pathjoin(path, p)) for p in paths]

        return paths


    def walk_files(self, path="/", wildcard=None, dir_wildcard=None):

        dirs = [path]
        files = []

        while dirs:

            current_path = dirs.pop()

            for path in self.listdir(current_path, full=True):
                if self.isdir(path):
                    if dir_wildcard is not None:
                        if fnmatch.fnmatch(path, dir_wilcard):
                            dirs.append(path)
                    else:
                        dirs.append(path)
                else:
                    if wildcard is not None:
                        if fnmatch.fnmatch(path, wildcard):
                            yield path
                    else:
                        yield path

    def walk(self, path="/", wildcard=None, dir_wildcard=None):

        dirs = [path]


        while dirs:

            current_path = dirs.pop()

            paths = []
            for path in self.listdir(current_path, full=True):

                if self.isdir(path):
                    if dir_wildcard is not None:
                        if fnmatch.fnmatch(path, dir_wilcard):
                            dirs.append(path)
                    else:
                        dirs.append(path)
                else:
                    if wildcard is not None:
                        if fnmatch.fnmatch(path, wildcard):
                            paths.append(path)
                    else:
                        paths.append(path)

            yield (current_path, paths)



    def getsize(self, path):

        return self.getinfo(path)['size']


class SubFS(FS):

    def __init__(self, parent, sub_dir):

        self.parent = parent
        self.sub_dir = parent.abspath(sub_dir)

    def __str__(self):
        return "<SubFS \"%s\" of %s>" % (self.sub_dir, self.parent)

    def _delegate(self, dirname):

        delegate_path = pathjoin(self.sub_dir, resolvepath(makerelative(dirname)))
        return delegate_path

    def getsyspath(self, pathname):

        return self.parent.getsyspath(self._delegate(pathname))

    def open(self, pathname, mode="r", buffering=-1, **kwargs):

        return self.parent.open(self._delegate(pathname), mode, buffering)

    def open_dir(self, path):

        if not self.exists(dirname):
            raise FSError("NO_DIR", dirname)

        path = self._delegate(path)
        sub_fs = self.parent.open_dir(path)
        return sub_fs

    def isdir(self, pathname):

        return self.parent.isdir(self._delegate(pathname))

    def listdir(self, path="./", wildcard=None, full=False, absolute=False, hidden=False, dirs_only=False, files_only=False):

        return self.parent.listdir(self._delegate(path), wildcard, full, absolute, hidden, dirs_only, files_only)


def validatefs(fs):

    expected_methods = [ "abspath",
                         "getsyspath",
                         "open",
                         "exists",
                         "isdir",
                         "isfile",
                         "ishidden",
                         "listdir",
                         "mkdir",
                         "remove",
                         "removedir",
                         "getinfo",
                         "getsize",
    ]

    pad_size = len(max(expected_methods, key=str.__len__))
    count = 0
    for method_name in sorted(expected_methods):
        method = getattr(fs, method_name, None)
        if method is None:
            print method_name.ljust(pad_size), '?'
        else:
            print method_name.ljust(pad_size), 'X'
            count += 1
    print
    print "%i out of %i methods" % (count, len(expected_methods))
