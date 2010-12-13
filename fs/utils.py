"""

The `utils` module provides a number of utility functions that don't belong in the Filesystem interface. Generally the functions in this module work with multiple Filesystems, for instance moving and copying between non-similar Filesystems.

"""

__all__ = ['copyfile',
           'movefile',
           'movedir',
           'copydir',
           'countbytes',
           'isfile',
           'isdir',
           'find_duplicates',
           'print_fs']

import shutil
import os
import sys
import stat
from fs.mountfs import MountFS
from fs.path import pathjoin, pathsplit
from fs.errors import DestinationExistsError
from fs.base import FS



def copyfile(src_fs, src_path, dst_fs, dst_path, overwrite=True, chunk_size=64*1024):
    """Copy a file from one filesystem to another. Will use system copyfile, if both files have a syspath.
    Otherwise file will be copied a chunk at a time.

    :param src_fs: Source filesystem object
    :param src_path: -- Source path
    :param dst_fs: Destination filesystem object
    :param dst_path: Destination filesystem object
    :param chunk_size: Size of chunks to move if system copyfile is not available (default 16K)

    """
    
    # If the src and dst fs objects are the same, then use a direct copy
    if src_fs is dst_fs:
        src_fs.copy(src_path, dst_path, overwrite=overwrite)
        return
    
    src_syspath = src_fs.getsyspath(src_path, allow_none=True)
    dst_syspath = dst_fs.getsyspath(dst_path, allow_none=True)
    
    if not overwrite and dst_fs.exists(dst_path):
        raise DestinationExistsError(dst_path)

    # System copy if there are two sys paths
    if src_syspath is not None and dst_syspath is not None:
        FS._shutil_copyfile(src_syspath, dst_syspath)
        return

    src = None
    dst = None        
    try:
        # Chunk copy
        src = src_fs.open(src_path, 'rb')        
        dst = src_fs.open(dst_path, 'wb')
        write = dst.write
        read = src.read
        chunk = read(chunk_size)
        while chunk:            
            write(chunk)
            chunk = read(chunk_size)                    
    finally:
        if src is not None:
            src.close()
        if dst is not None:
            dst.close()


def movefile(src_fs, src_path, dst_fs, dst_path, overwrite=True, chunk_size=64*1024):
    """Move a file from one filesystem to another. Will use system copyfile, if both files have a syspath.
    Otherwise file will be copied a chunk at a time.

    :param src_fs: Source filesystem object
    :param src_path: Source path
    :param dst_fs: Destination filesystem object
    :param dst_path: Destination filesystem object
    :param chunk_size: Size of chunks to move if system copyfile is not available (default 16K)

    """
    src_syspath = src_fs.getsyspath(src_path, allow_none=True)
    dst_syspath = dst_fs.getsyspath(dst_path, allow_none=True)

    if not overwrite and dst_fs.exists(dst_path):
        raise DestinationExistsError(dst_path)
        
    if src_fs is dst_fs:
        src_fs.move(src_path, dst_path, overwrite=overwrite)
        return

    # System copy if there are two sys paths
    if src_syspath is not None and dst_syspath is not None:        
        FS._shutil_movefile(src_syspath, dst_syspath)        
        return

    src = None
    dst = None        
    try:
        # Chunk copy
        src = src_fs.open(src_path, 'rb')        
        dst = src_fs.open(dst_path, 'wb')
        write = dst.write
        read = src.read
        chunk = read(chunk_size)
        while chunk:            
            write(chunk)
            chunk = read(chunk_size)                    
    finally:
        if src is not None:
            src.close()
        if dst is not None:
            dst.close()
    src_fs.remove(src_path)


def movedir(fs1, fs2, overwrite=False, ignore_errors=False, chunk_size=64*1024):
    """Moves contents of a directory from one filesystem to another.

    :param fs1: Source filesystem, or a tuple of (<filesystem>, <directory path>)
    :param fs2: Destination filesystem, or a tuple of (<filesystem>, <directory path>)
    :param ignore_errors: If True, exceptions from file moves are ignored
    :param chunk_size: Size of chunks to move if a simple copy is used

    """
    if isinstance(fs1, tuple):
        fs1, dir1 = fs1
        fs1 = fs1.opendir(dir1)
    if isinstance(fs2, tuple):
        fs2, dir2 = fs2
        fs2.makedir(dir2, allow_recreate=True)
        fs2 = fs2.opendir(dir2)

    mount_fs = MountFS()
    mount_fs.mount('src', fs1)
    mount_fs.mount('dst', fs2)

    mount_fs.movedir('src', 'dst',
                     overwrite=overwrite,
                     ignore_errors=ignore_errors,
                     chunk_size=chunk_size)


def copydir(fs1, fs2, overwrite=False, ignore_errors=False, chunk_size=64*1024):
    """Copies contents of a directory from one filesystem to another.

    :param fs1: Source filesystem, or a tuple of (<filesystem>, <directory path>)
    :param fs2: Destination filesystem, or a tuple of (<filesystem>, <directory path>)
    :param ignore_errors: If True, exceptions from file moves are ignored
    :param chunk_size: Size of chunks to move if a simple copy is used

    """
    if isinstance(fs1, tuple):
        fs1, dir1 = fs1
        fs1 = fs1.opendir(dir1)
    if isinstance(fs2, tuple):
        fs2, dir2 = fs2
        fs2.makedir(dir2, allow_recreate=True)
        fs2 = fs2.opendir(dir2)

    mount_fs = MountFS()
    mount_fs.mount('src', fs1)
    mount_fs.mount('dst', fs2)
    mount_fs.copydir('src', 'dst',
                     overwrite=overwrite,
                     ignore_errors=ignore_errors,
                     chunk_size=chunk_size)


def copystructure(src_fs, dst_fs):
    """Copies the directory structure from one filesystem to another, so that
    all directories in `src_fs` will have a corresponding directory in `dst_fs`
    
    :param src_fs: Filesystem to copy structure from
    :param dst_fs: Filesystem to copy structure to
    
    """
    
    for path in src_fs.walkdirs():
        dst_fs.makedir(path, allow_recreate=True)


def countbytes(fs):
    """Returns the total number of bytes contained within files in a filesystem.

    :param fs: A filesystem object

    """
    total = sum(fs.getsize(f) for f in fs.walkfiles())
    return total


def isdir(fs,path,info=None):
    """Check whether a path within a filesystem is a directory.

    If you're able to provide the info dict for the path, this may be possible
    without querying the filesystem (e.g. by checking st_mode).
    """
    if info is not None:
        st_mode = info.get("st_mode")
        if st_mode:
            if stat.S_ISDIR(st_mode):
                return True
            if stat.S_ISREG(st_mode):
                return False
    return fs.isdir(path)


def isfile(fs,path,info=None):
    """Check whether a path within a filesystem is a file.

    If you're able to provide the info dict for the path, this may be possible
    without querying the filesystem (e.g. by checking st_mode).
    """
    if info is not None:
        st_mode = info.get("st_mode")
        if st_mode:
            if stat.S_ISREG(st_mode):
                return True
            if stat.S_ISDIR(st_mode):
                return False
    return fs.isfile(path)

def contains_files(fs, path='/'):
    """Check if there are any files in the filesystem"""
    try:
        iter(fs.walkfiles(path)).next()
    except StopIteration:
        return False
    return True

def find_duplicates(fs,
                    compare_paths=None,
                    quick=False,
                    signature_chunk_size=16*1024,
                    signature_size=10*16*1024):
    """A generator that yields the paths of duplicate files in an FS object.
    Files are considered identical if the contents are the same (dates or
    other attributes not take in to account).

    :param fs: A filesystem object
    :param compare_paths: An iterable of paths within the FS object, or all files if omitted
    :param quick: If set to True, the quick method of finding duplicates will be used, which can potentially return false positives if the files have the same size and start with the same data. Do not use when deleting files!
    :param signature_chunk_size: The number of bytes to read before generating a signature checksum value
    :param signature_size: The total number of bytes read to generate a signature

    For example, the following will list all the duplicate .jpg files in "~/Pictures"::
    
        >>> from fs.utils import find_duplicates
        >>> from fs.osfs import OSFS
        >>> fs = OSFS('~/Pictures')
        >>> for dups in find_duplicates(fs, fs.walkfiles('*.jpg')):
        ...     print list(dups)

    """

    from collections import defaultdict
    from zlib import crc32

    if compare_paths is None:
        compare_paths = fs.walkfiles()

    # Create a dictionary that maps file sizes on to the paths of files with
    # that filesize. So we can find files of the same size with a quick lookup
    file_sizes = defaultdict(list)
    for path in compare_paths:
        file_sizes[fs.getsize(path)].append(path)

    size_duplicates = [paths for paths in file_sizes.itervalues() if len(paths) > 1]

    signatures = defaultdict(list)

    # A signature is a tuple of CRC32s for each 4x16K of the file
    # This allows us to find potential duplicates with a dictionary lookup
    for paths in size_duplicates:
        for path in paths:
            signature = []
            fread = None
            bytes_read = 0
            try:
                fread = fs.open(path, 'rb')
                while signature_size is None or bytes_read < signature_size:
                    data = fread.read(signature_chunk_size)
                    if not data:
                        break
                    bytes_read += len(data)
                    signature.append(crc32(data))
            finally:
                if fread is not None:
                    fread.close()
            signatures[tuple(signature)].append(path)

    # If 'quick' is True then the signature comparison is adequate (although
    # it may result in false positives)
    if quick:
        for paths in signatures.itervalues():
            if len(paths) > 1:
                yield paths
        return

    def identical(p1, p2):
        """ Returns True if the contents of two files are identical. """
        f1, f2 = None, None
        try:
            f1 = fs.open(p1, 'rb')
            f2 = fs.open(p2, 'rb')
            while True:
                chunk1 = f1.read(16384)
                if not chunk1:
                    break
                chunk2 = f2.read(16384)
                if chunk1 != chunk2:
                    return False
            return True
        finally:
            if f1 is not None:
                f1.close()
            if f2 is not None:
                f2.close()

    # If we want to be accurate then we need to compare suspected duplicates
    # byte by byte.
    # All path groups in this loop have the same size and same signature, so are
    # highly likely to be identical.
    for paths in signatures.itervalues():

        while len(paths) > 1:

            test_p = paths.pop()
            dups = [test_p]

            for path in paths:
                if identical(test_p, path):
                    dups.append(path)

            if len(dups) > 1:
                yield dups

            paths = list(set(paths).difference(dups))


def print_fs(fs, path='/', max_levels=5, file_out=None, terminal_colors=None, hide_dotfiles=False, dirs_first=False):
    """Prints a filesystem listing to stdout (including sub dirs). Useful as a debugging aid.
    Be careful about printing a OSFS, or any other large filesystem.
    Without max_levels set, this function will traverse the entire directory tree.
    
    For example, the following will print a tree of the files under the current working directory::
    
        >>> from fs.osfs import *
        >>> from fs.utils import *
        >>> fs = OSFS('.')
        >>> print_fs(fs)


    :param fs: A filesystem object
    :param path: Path of a directory to list (default "/")
    :param max_levels: Maximum levels of dirs to list (default 5), set to None for no maximum
    :param file_out: File object to write output to (defaults to sys.stdout)
    :param terminal_colors: If True, terminal color codes will be written, set to False for non-console output.
        The default (None) will select an appropriate setting for the platform.
    :param hide_dotfiles: if True, files or directories begining with '.' will be removed

    """

    if file_out is None:
        file_out = sys.stdout

    file_encoding = getattr(file_out, 'encoding', 'utf-8') or 'utf-8'

    if terminal_colors is None:
        if sys.platform.startswith('win'):
            terminal_colors = False
        else:
            terminal_colors = True
    
    def write(line):
        file_out.write(line.encode(file_encoding)+'\n')
        
    def wrap_prefix(prefix):
       if not terminal_colors:
           return prefix           
       return '\x1b[34m%s\x1b[0m' % prefix           
   
    def wrap_dirname(dirname):
        if not terminal_colors:
            return dirname
        return '\x1b[1;32m%s\x1b[0m' % dirname
    
    def wrap_error(msg):
        if not terminal_colors:
            return msg
        return '\x1b[31m%s\x1b[0m' % msg
    
    def wrap_filename(fname):
        if not terminal_colors:
            return fname        
        if '.' in fname:
            name, ext = os.path.splitext(fname)
            fname = '%s\x1b[36m%s\x1b[0m' % (name, ext)
        if fname.startswith('.'):
            fname = '\x1b[2m%s\x1b[0m' % fname
        return fname
    
    def print_dir(fs, path, levels=[]):
        
        try:
            dir_listing = ( [(True, p) for p in fs.listdir(path, dirs_only=True)] +
                            [(False, p) for p in fs.listdir(path, files_only=True)] )
        except Exception, e:
            prefix = ''.join([('|   ', '    ')[last] for last in levels]) + '   '
            write(wrap_prefix(prefix[:-1] + '    ') + wrap_error("unabled to retrieve directory list (%s) ..." % str(e)))
            return 0        
        
        if hide_dotfiles:
            dir_listing = [(isdir, p) for isdir, p in dir_listing if not p.startswith('.')]
        
        if dirs_first:
            dir_listing.sort(key = lambda (isdir, p):(not isdir, p.lower()))
        else:
            dir_listing.sort(key = lambda (isdir, p):p.lower())
                            
        for i, (is_dir, item) in enumerate(dir_listing):
            
            is_last_item = (i == len(dir_listing) - 1)            
            prefix = ''.join([('|   ', '    ')[last] for last in levels])
            if is_last_item:
                prefix += '`'
            else:
                prefix += '|'
                                            
            if is_dir:                
                write('%s %s' % (wrap_prefix(prefix + '--'), wrap_dirname(item)))
                if max_levels is not None and len(levels) + 1 >= max_levels:
                    pass
                    #write(wrap_prefix(prefix[:-1] + '       ') + wrap_error('max recursion levels reached'))
                else:
                    print_dir(fs, pathjoin(path, item), levels[:] + [is_last_item])                                            
            else:
                write('%s %s' % (wrap_prefix(prefix + '--'), wrap_filename(item)))
                
        return len(dir_listing)
                
    print_dir(fs, path)
            
            


if __name__ == "__main__":
    #from osfs import *
    #fs = OSFS('~/copytest')

    #from memoryfs import *
    #m = MemoryFS()
    #m.makedir('maps')

    #copydir((fs, 'maps'), (m, 'maps'))

    #from browsewin import browse
    #browse(m)

    from osfs import *
    #f = OSFS('/home/will/projects')
    f=OSFS('/home/will/tests')
    from fs.memoryfs import MemoryFS
    mem = MemoryFS()
    from fs.utils import copydir
    copydir(f, mem)
    print_fs(mem)
    
