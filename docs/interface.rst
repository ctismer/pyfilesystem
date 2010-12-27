Filesystem Interface
====================

It requires a relatively small number of methods to implement a working FS object.

If you are looking to implement a working FS object, derive a class from fs.base.FS and implement the essential methods (below). Be sure to convert all exceptions to instances of :class:`fs.errors.FSError`.

It may also be worthwhile implementing some of the non-essential methods, as the default implementations may not be optimal. For example, the method :meth:`fs.base.FS.move` is implemeneted as a file copy followed by a delete, but many filesystems can move a file without copying data.

If the filesystem you are implementing maps paths to the native filesystem, be sure to implement `getsyspath`. Doing so will improve performance, especialy when copying / moving files between FS objects.

Essential Methods
-----------------

The following methods are required for a minimal Filesystem interface:

    * :meth:`~fs.base.FS.open` Opens a file for read/writing
    * :meth:`~fs.base.FS.isfile` Check wether the path exists and is a file
    * :meth:`~fs.base.FS.isdir` Check wether a path exists and is a directory
    * :meth:`~fs.base.FS.listdir` List the contents of a directory
    * :meth:`~fs.base.FS.makedir` Create a new directory
    * :meth:`~fs.base.FS.remove` Remove an existing file
    * :meth:`~fs.base.FS.removedir` Remove an existing directory
    * :meth:`~fs.base.FS.rename` Atomically rename a file or directory
    * :meth:`~fs.base.FS.getinfo` Return information about the path e.g. size, mtime
    

Non - Essential Methods
-----------------------

The following methods have default implementations in fs.base.FS and aren't required for a functional FS interface. They may be overriden if an alternative implementation can be supplied:

    * :meth:`~fs.base.FS.copy` Copy a file to a new location
    * :meth:`~fs.base.FS.copydir` Recursively copy a directory to a new location
    * :meth:`~fs.base.FS.desc` Return a short destriptive text regarding a path
    * :meth:`~fs.base.FS.exists` Check whether a path exists as file or directory    
    * :meth:`~fs.base.FS.listdirinfo` Get a directory listing along with the info dict for each entry
    * :meth:`~fs.base.FS.ilistdir` Generator version of the listdir method
    * :meth:`~fs.base.FS.ilistdirinfo` Generator version of the listdirinfo method
    * :meth:`~fs.base.FS.getsyspath` Get a file's name in the local filesystem, if possible
    * :meth:`~fs.base.FS.hassyspath` Check if a path maps to a system path (recognised by the OS)
    * :meth:`~fs.base.FS.getpathurl` Get an external URL at which the given file can be accessed, if possible
    * :meth:`~fs.base.FS.haspathurl` Check if a path maps to an external URL
    * :meth:`~fs.base.FS.getmeta` Get the value of a filesystem meta value, if it exists
    * :meth:`~fs.base.FS.hasmeta` Check if a filesystem meta value exists
    * :meth:`~fs.base.FS.move` Move a file to a new location        
    * :meth:`~fs.base.FS.movedir` Recursively move a directory to a new location
    * :meth:`~fs.base.FS.opendir` Opens a directory and returns an FS object that represents it
    * :meth:`~fs.base.FS.safeopen` Like :meth:`~fs.base.open` but returns a NullFile if the file could not be opened
    * :meth:`~fs.base.FS.settimes` Sets the accessed and modified times of a path


Utility Methods
---------------

The following members have implementations in fs.base.FS and will probably never require a non-default implementation, although there is nothing to prevent a derived class from implementing these:

    * :meth:`~fs.base.FS.createfile` Create a file with data
    * :meth:`~fs.base.FS.getcontents` Returns the contents of a file as a string
    * :meth:`~fs.base.FS.setcontents` Sets the contents of a file as a string or file-like object
    * :meth:`~fs.base.FS.getsize` Returns the number of bytes used for a given file or directory
    * :meth:`~fs.base.FS.isdirempty` Checks if a directory contains no files
    * :meth:`~fs.base.FS.makeopendir` Creates a directroy (if it exists) and returns an FS object for that directory
    * :meth:`~fs.base.FS.walk` Like `listdir` but descends in to sub-directories
    * :meth:`~fs.base.FS.walkfiles` Returns an iterable of file paths in a directory, and its sub-directories
    * :meth:`~fs.base.FS.walkdirs` Returns an iterable of paths to sub-directories
    
