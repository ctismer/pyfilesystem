#!/usr/bin/env python

import os

from fs.base import *
from fs.path import *

try:
    import xattr
except ImportError:
    xattr = None

class OSFS(FS):
    """Expose the underlying operating-system filesystem as an FS object.

    This is the most basic of filesystems, which simply shadows the underlaying
    filesytem of the OS.  Most of its methods simply defer to the corresponding
    methods in the os and os.path modules.

    """

    def __init__(self, root_path, dir_mode=0700, thread_synchronize=True):
        FS.__init__(self, thread_synchronize=thread_synchronize)
        expanded_path = normpath(os.path.abspath(os.path.expanduser(os.path.expandvars(root_path))))
        if not os.path.exists(expanded_path):
            raise ResourceNotFoundError(expanded_path,msg="Root directory does not exist: %(path)s")
        if not os.path.isdir(expanded_path):
            raise ResourceInvalidError(expanded_path,msg="Root path is not a directory: %(path)s")
        self.root_path = normpath(os.path.abspath(expanded_path))
        self.dir_mode = dir_mode

    def __str__(self):
        return "<OSFS: %s>" % self.root_path

    def getsyspath(self, path, allow_none=False):
        sys_path = os.path.join(self.root_path, relpath(path)).replace('/', os.sep)
        return sys_path

    @convert_os_errors
    def open(self, path, mode="r", **kwargs):
        mode = filter(lambda c: c in "rwabt+",mode)
        return open(self.getsyspath(path), mode, kwargs.get("buffering", -1))

    @convert_os_errors
    def exists(self, path):
        path = self.getsyspath(path)
        return os.path.exists(path)

    @convert_os_errors
    def isdir(self, path):
        path = self.getsyspath(path)
        return os.path.isdir(path)

    @convert_os_errors
    def isfile(self, path):
        path = self.getsyspath(path)
        return os.path.isfile(path)

    @convert_os_errors
    def listdir(self, path="./", wildcard=None, full=False, absolute=False, dirs_only=False, files_only=False):
        paths = os.listdir(self.getsyspath(path))
        return self._listdir_helper(path, paths, wildcard, full, absolute, dirs_only, files_only)

    @convert_os_errors
    def makedir(self, path, recursive=False, allow_recreate=False):
        sys_path = self.getsyspath(path)
        try:
            if recursive:
                os.makedirs(sys_path, self.dir_mode)
            else:
                os.mkdir(sys_path, self.dir_mode)
        except OSError, e:
            if e.errno == 17 or e.errno == 183:
                if self.isfile(path):
                    raise ResourceInvalidError(path,msg="Cannot create directory, there's already a file of that name: %(path)s")
                if not allow_recreate:
                    raise DestinationExistsError(path,msg="Can not create a directory that already exists (try allow_recreate=True): %(path)s")
            elif e.errno == 2:
                raise ParentDirectoryMissingError(path)
            else:
                raise
                
    @convert_os_errors
    def remove(self, path):
        sys_path = self.getsyspath(path)
        os.remove(sys_path)

    @convert_os_errors
    def removedir(self, path, recursive=False,force=False):
        sys_path = self.getsyspath(path)
        #  Don't remove the root directory of this FS
        if path in ("","/"):
            return
        if force:
            for path2 in self.listdir(path,absolute=True,files_only=True):
                self.remove(path2)
            for path2 in self.listdir(path,absolute=True,dirs_only=True):
                self.removedir(path2,force=True)
        os.rmdir(sys_path)
        #  Using os.removedirs() for this can result in dirs being
        #  removed outside the root of this FS, so we recurse manually.
        if recursive:
            try:
                self.removedir(dirname(path),recursive=True)
            except DirectoryNotEmptyError:
                pass

    @convert_os_errors
    def rename(self, src, dst):
        if not issamedir(src, dst):
            raise ValueError("Destination path must the same directory (use the move method for moving to a different directory)")
        path_src = self.getsyspath(src)
        path_dst = self.getsyspath(dst)
        os.rename(path_src, path_dst)

    @convert_os_errors
    def getinfo(self, path):
        sys_path = self.getsyspath(path)
        stats = os.stat(sys_path)
        info = dict((k, getattr(stats, k)) for k in dir(stats) if not k.startswith('__') )
        info['size'] = info['st_size']
        #  TODO: this doesn't actually mean 'creation time' on unix
        ct = info.get('st_ctime', None)
        if ct is not None:
            info['created_time'] = datetime.datetime.fromtimestamp(ct)
        at = info.get('st_atime', None)
        if at is not None:
            info['accessed_time'] = datetime.datetime.fromtimestamp(at)
        mt = info.get('st_mtime', None)
        if mt is not None:
            info['modified_time'] = datetime.datetime.fromtimestamp(at)
        return info

    @convert_os_errors
    def getsize(self, path):
        sys_path = self.getsyspath(path)
        stats = os.stat(sys_path)
        return stats.st_size


    #  Provide native xattr support if available
    if xattr:
        @convert_os_errors
        def setxattr(self, path, key, value):
            xattr.xattr(self.getsyspath(path))[key]=value

        @convert_os_errors
        def getxattr(self, path, key, default=None):
            try:
                return xattr.xattr(self.getsyspath(path)).get(key)
            except KeyError:
                return default

        @convert_os_errors
        def delxattr(self, path, key):
            try:
                del xattr.xattr(self.getsyspath(path))[key]
            except KeyError:
                pass

        @convert_os_errors
        def listxattrs(self, path):
            return xattr.xattr(self.getsyspath(path)).keys()


