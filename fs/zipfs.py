"""
fs.zipfs
========

A FS object that represents the contents of a Zip file

"""

from fs.base import *
from fs.path import *
from fs.errors import *

from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED, BadZipfile, LargeZipFile
from memoryfs import MemoryFS

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import tempfs


class ZipOpenError(CreateFailedError):
    """Thrown when the zip file could not be opened"""
    pass


class ZipNotFoundError(CreateFailedError):
    """Thrown when the requested zip file does not exist"""
    pass


class _TempWriteFile(object):

    """Proxies a file object and calls a callback when the file is closed."""

    def __init__(self, fs, filename, close_callback):
        self.fs = fs
        self.filename = filename
        self._file = self.fs.open(filename, 'w+')
        self.close_callback = close_callback

    def write(self, data):
        return self._file.write(data)

    def tell(self):
        return self._file.tell()

    def close(self):
        self._file.close()
        self.close_callback(self.filename)


class _ExceptionProxy(object):

    """A placeholder for an object that may no longer be used."""

    def __getattr__(self, name):
        raise ValueError("Zip file has been closed")

    def __setattr__(self, name, value):
        raise ValueError("Zip file has been closed")

    def __nonzero__(self):
        return False


class ZipFS(FS):

    """A FileSystem that represents a zip file."""

    def __init__(self, zip_file, mode="r", compression="deflated", allow_zip_64=False, encoding="CP437", thread_synchronize=True):
        """Create a FS that maps on to a zip file.

        :param zip_file: A (system) path, or a file-like object
        :param mode: Mode to open zip file: 'r' for reading, 'w' for writing or 'a' for appending
        :param compression: Can be 'deflated' (default) to compress data or 'stored' to just store date
        :param allow_zip_64: -- Set to True to use zip files greater than 2 GB, default is False
        :param encoding: --  The encoding to use for unicode filenames
        :param thread_synchronize: -- Set to True (default) to enable thread-safety
        :raises ZipOpenError: Thrown when the zip file could not be opened
        :raises ZipNotFoundError: Thrown when the zip file does not exist (derived from ZipOpenError)

        """
        super(ZipFS, self).__init__(thread_synchronize=thread_synchronize)
        if compression == "deflated":
            compression_type = ZIP_DEFLATED
        elif compression == "stored":
            compression_type = ZIP_STORED
        else:
            raise ValueError("Compression should be 'deflated' (default) or 'stored'")

        if len(mode) > 1 or mode not in "rwa":
            raise ValueError("mode must be 'r', 'w' or 'a'")

        self.zip_mode = mode
        self.encoding = encoding
        try:
            self.zf = ZipFile(zip_file, mode, compression_type, allow_zip_64)
        except BadZipfile, bzf:            
            raise ZipOpenError("Not a zip file or corrupt (%s)" % str(zip_file),
                               details=bzf)
        except IOError, ioe:
            if str(ioe).startswith('[Errno 22] Invalid argument'):
                raise ZipOpenError("Not a zip file or corrupt (%s)" % str(zip_file),
                                   details=bzf)
            raise ZipNotFoundError("Zip file not found (%s)" % str(zip_file),
                                  details=ioe)
                
        self.zip_path = str(zip_file)

        self.temp_fs = None
        if mode in 'wa':
            self.temp_fs = tempfs.TempFS()

        self._path_fs = MemoryFS()
        if mode in 'ra':
            self._parse_resource_list()

    def __str__(self):
        return "<ZipFS: %s>" % self.zip_path

    def __unicode__(self):
        return unicode(self.__str__())

    def _parse_resource_list(self):
        for path in self.zf.namelist():
            self._add_resource(path.decode(self.encoding))

    def _add_resource(self, path):
        if path.endswith('/'):
            path = path[:-1]
            if path:
                self._path_fs.makedir(path, recursive=True, allow_recreate=True)
        else:
            dirpath, filename = pathsplit(path)
            if dirpath:
                self._path_fs.makedir(dirpath, recursive=True, allow_recreate=True)
            f = self._path_fs.open(path, 'w')
            f.close()


    def close(self):
        """Finalizes the zip file so that it can be read.
        No further operations will work after this method is called."""

        if hasattr(self, 'zf') and self.zf:
            self.zf.close()
            self.zf = _ExceptionProxy()

    @synchronize
    def open(self, path, mode="r", **kwargs):
        path = normpath(relpath(path))        

        if 'r' in mode:
            if self.zip_mode not in 'ra':
                raise OperationFailedError("open file", path=path, msg="Zip file must be opened for reading ('r') or appending ('a')")
            try:
                contents = self.zf.read(path.encode(self.encoding))
            except KeyError:
                raise ResourceNotFoundError(path)
            return StringIO(contents)

        if 'w' in mode:
            dirname, filename = pathsplit(path)
            if dirname:
                self.temp_fs.makedir(dirname, recursive=True, allow_recreate=True)

            self._add_resource(path)
            f = _TempWriteFile(self.temp_fs, path, self._on_write_close)

            return f

        raise ValueError("Mode must contain be 'r' or 'w'")

    @synchronize
    def getcontents(self, path):
        if not self.exists(path):
            raise ResourceNotFoundError(path)
        path = normpath(relpath(path))
        try:
            contents = self.zf.read(path.encode(self.encoding))
        except KeyError:
            raise ResourceNotFoundError(path)
        except RuntimeError:
            raise OperationFailedError("read file", path=path, msg="Zip file must be oppened with 'r' or 'a' to read")
        return contents

    @synchronize
    def _on_write_close(self, filename):
        sys_path = self.temp_fs.getsyspath(filename)
        self.zf.write(sys_path, filename.encode(self.encoding))

    def desc(self, path):
        if self.isdir(path):
            return "Dir in zip file: %s" % self.zip_path
        else:
            return "File in zip file: %s" % self.zip_path

    def isdir(self, path):
        return self._path_fs.isdir(path)

    def isfile(self, path):
        return self._path_fs.isfile(path)

    def exists(self, path):
        return self._path_fs.exists(path)

    @synchronize
    def makedir(self, dirname, recursive=False, allow_recreate=False):
        dirname = normpath(dirname)
        if self.zip_mode not in "wa":
            raise OperationFailedError("create directory", path=dirname, msg="Zip file must be opened for writing ('w') or appending ('a')")
        if not dirname.endswith('/'):
            dirname += '/'
        self._add_resource(dirname)

    def listdir(self, path="/", wildcard=None, full=False, absolute=False, dirs_only=False, files_only=False):
        return self._path_fs.listdir(path, wildcard, full, absolute, dirs_only, files_only)

    @synchronize
    def getinfo(self, path):
        if not self.exists(path):
            raise ResourceNotFoundError(path)
        path = normpath(path).lstrip('/')
        try:
            zi = self.zf.getinfo(path.encode(self.encoding))
            zinfo = dict((attrib, getattr(zi, attrib)) for attrib in dir(zi) if not attrib.startswith('_'))
            for k, v in zinfo.iteritems():
                if callable(v):
                    zinfo[k] = v()
        except KeyError:
            zinfo = {'file_size':0}
        info = {'size' : zinfo['file_size'] }
        if 'date_time' in zinfo:
            info['created_time'] = datetime.datetime(*zinfo['date_time'])
        info.update(zinfo)
        return info
