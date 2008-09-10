#!/usr/bin/env python

from fs import *

from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from tempfile import NamedTemporaryFile
import tempfs

class _TempWriteFile(object):

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

class ZipFS(FS):

    def __init__(self, zip_file, mode="r", compression="deflated", allowZip64=False):
        FS.__init__(self)
        if compression == "deflated":
            compression_type = ZIP_DEFLATED
        elif compression == "stored":
            compression_type = ZIP_STORED
        else:
            raise ValueError("Compression should be 'deflated' (default) or 'stored'")

        if len(mode) > 1 or mode not in "rwa":
            raise ValueError("mode must be 'r', 'w' or 'a'")

        self.zip_mode = mode
        self.zf = ZipFile(zip_file, mode, compression_type, allowZip64)

        self.temp_fs = None
        if mode in 'wa':
            self.temp_fs = tempfs.TempFS()

        self.resource_list = None
        if mode == 'r':
            self.resource_list = self.zf.namelist()

    def _get_resource_list(self):
        return self.resource_list or self.zf.namelist()

    def close(self):
        """Finalizes the zip file so that it can be read.
        No further operations will work after this method is called."""

        if self.zf is not None:
            self.zf.close()
            self.zf = None

    def __del__(self):
        self.close()

    def open(self, path, mode="r", **kwargs):

        path = normpath(path)

        if 'r' in mode:
            if self.zip_mode not in 'ra':
                raise OperationFailedError("OPEN_FAILED", path=path, msg="Zip file must be opened for reading ('r') or appending ('a')")
            try:
                contents = self.zf.read(path)
            except KeyError:
                raise ResourceNotFoundError("NO_FILE", path)
            return StringIO(contents)

        if 'w' in mode:
            dirname, filename = pathsplit(path)
            if dirname:
                self.temp_fs.makedir(dirname, recursive=True, allow_recreate=True)

            f = _TempWriteFile(self.temp_fs, path, self._on_write_close)

            return f

        raise ValueError("Mode must contain be 'r' or 'w'")

    def _on_write_close(self, filename):
        sys_path = self.temp_fs.getsyspath(filename)
        self.zf.write(sys_path, filename)


    def listdir(self, path="/", wildcard=None, full=False, absolute=False, hidden=False, dirs_only=False, files_only=False):

        path = normpath(path)

        def indir(p):
            p = makeabsolute(p)
            list_dir = makeabsolute(path)
            sub_path = normpath(p[len(list_dir)+1:])
            return sub_path and '/' not in sub_path

        paths = [getresourcename(p.rstrip('/')) for p in self._get_resource_list() if indir(p.rstrip('/'))]

        return self._listdir_helper(path, paths, wildcard, full, absolute, hidden, dirs_only, files_only)

if __name__ == "__main__":
    def test():
        zfs = ZipFS("t.zip", "w")
        zfs.createfile("t.txt", "Hello, World!")
        zfs.close()
        rfs = ZipFS("t.zip", 'r')
        print rfs.getcontents("t.txt")
        print rfs.getcontents("w.txt")

    def test2():
        zfs = ZipFS("t2.zip", "r")
        print zfs.listdir("/tagging-trunk")
        print zfs.listdir("/")

    test2()
    #zfs.close()
