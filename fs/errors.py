"""
Defines the Exception classes thrown by PyFilesystem objects. Exceptions relating to the underling filesystem are translated in to one of the following Exceptions. Exceptions that relate to a path store that path in `self.path`.

All Exception classes are derived from `FSError` which can be used as a catch-all exception.

"""

__all__ = ['FSError',
           'CreateFailedError',
           'PathError',
           'OperationFailedError',
           'UnsupportedError',
           'RemoteConnectionError',
           'StorageSpaceError',
           'PermissionDeniedError',
           'FSClosedError',
           'OperationTimeoutError',
           'ResourceError',
           'NoSysPathError',
           'ResourceNotFoundError',
           'ResourceInvalidError',           
           'DestinationExistsError',
           'DirectoryNotEmptyError',
           'ParentDirectoryMissingError',
           'ResourceLockedError',
           'convert_fs_errors',
           'convert_os_errors'
           ]

import sys
import errno

from fs.path import *
from fs.functools import wraps


class FSError(Exception):
    """Base exception class for the FS module."""
    default_message = "Unspecified error"

    def __init__(self,msg=None,details=None):
        if msg is None:
            msg = self.default_message
        self.msg = msg
        self.details = details

    def __str__(self):
        keys = {}
        for k,v in self.__dict__.iteritems():
            if isinstance(v,unicode):
                v = v.encode(sys.getfilesystemencoding())
            keys[k] = v
        return str(self.msg % keys)

    def __unicode__(self):
        return unicode(self.msg) % self.__dict__

    def __getstate__(self):
       return self.__dict__.copy()


class CreateFailedError(FSError):
    """An exception thrown when a FS could not be created"""
    default_message = "Unable to create filesystem"


class PathError(FSError):
    """Exception for errors to do with a path string.
    """
    default_message = "Path is invalid: %(path)s"

    def __init__(self,path="",**kwds):
        self.path = path
        super(PathError,self).__init__(**kwds)
 

class OperationFailedError(FSError):
    """Base exception class for errors associated with a specific operation."""
    default_message = "Unable to %(opname)s: unspecified error [%(errno)s - %(details)s]"

    def __init__(self,opname="",path=None,**kwds):
        self.opname = opname
        self.path = path
        self.errno = getattr(kwds.get("details",None),"errno",None)
        super(OperationFailedError,self).__init__(**kwds)


class UnsupportedError(OperationFailedError):
    """Exception raised for operations that are not supported by the FS."""
    default_message = "Unable to %(opname)s: not supported by this filesystem"


class RemoteConnectionError(OperationFailedError):
    """Exception raised when operations encounter remote connection trouble."""
    default_message = "%(opname)s: remote connection errror"


class StorageSpaceError(OperationFailedError):
    """Exception raised when operations encounter storage space trouble."""
    default_message = "Unable to %(opname)s: insufficient storage space"


class PermissionDeniedError(OperationFailedError):
    default_message = "Unable to %(opname)s: permission denied"


class FSClosedError(OperationFailedError):
    default_message = "Unable to %(opname)s: the FS has been closed"


class OperationTimeoutError(OperationFailedError):
    default_message = "Unable to %(opname)s: operation timed out"


class ResourceError(FSError):
    """Base exception class for error associated with a specific resource."""
    default_message = "Unspecified resource error: %(path)s"

    def __init__(self,path="",**kwds):
        self.path = path
        self.opname = kwds.pop("opname",None)
        super(ResourceError,self).__init__(**kwds)


class NoSysPathError(ResourceError):
    """Exception raised when there is no syspath for a given path."""
    default_message = "No mapping to OS filesystem: %(path)s"


class ResourceNotFoundError(ResourceError):
    """Exception raised when a required resource is not found."""
    default_message = "Resource not found: %(path)s"


class ResourceInvalidError(ResourceError):
    """Exception raised when a resource is the wrong type."""
    default_message = "Resource is invalid: %(path)s"


class DestinationExistsError(ResourceError):
    """Exception raised when a target destination already exists."""
    default_message = "Destination exists: %(path)s"


class DirectoryNotEmptyError(ResourceError):
    """Exception raised when a directory to be removed is not empty."""
    default_message = "Directory is not empty: %(path)s"


class ParentDirectoryMissingError(ResourceError):
    """Exception raised when a parent directory is missing."""
    default_message = "Parent directory is missing: %(path)s"


class ResourceLockedError(ResourceError):
    """Exception raised when a resource can't be used because it is locked."""
    default_message = "Resource is locked: %(path)s"



def convert_fs_errors(func):
    """Function wrapper to convert FSError instances into OSErrors."""
    @wraps(func)
    def wrapper(*args,**kwds):
        try:
            return func(*args,**kwds)
        except ResourceNotFoundError, e:
            raise OSError(errno.ENOENT,str(e))
        except ResourceInvalidError, e:
            raise OSError(errno.EINVAL,str(e))
        except PermissionDeniedError, e:
            raise OSError(errno.EACCES,str(e))
        except ResourceLockedError, e:
            if sys.platform == "win32":
                raise WindowsError(32,str(e))
            else:
                raise OSError(errno.EACCES,str(e))
        except DirectoryNotEmptyError, e:
            raise OSError(errno.ENOTEMPTY,str(e))
        except DestinationExistsError, e:
            raise OSError(errno.EEXIST,str(e))
        except StorageSpaceError, e:
            raise OSError(errno.ENOSPC,str(e))
        except RemoteConnectionError, e:
            raise OSError(errno.ENONET,str(e))
        except UnsupportedError, e:
            raise OSError(errno.ENOSYS,str(e))
        except FSError, e:
            raise OSError(errno.EFAULT,str(e))
    return wrapper


def convert_os_errors(func):
    """Function wrapper to convert OSError/IOError instances into FSErrors."""
    opname = func.__name__
    @wraps(func)
    def wrapper(self,*args,**kwds):
        try:
            return func(self,*args,**kwds)
        except (OSError,IOError), e:
            (exc_type,exc_inst,tb) = sys.exc_info()
            path = getattr(e,"filename",None)
            if path and path[0] == "/" and hasattr(self,"root_path"):
                path = normpath(path)
                if isprefix(self.root_path,path):
                    path = path[len(self.root_path):]
            if not hasattr(e,"errno") or not e.errno:
                raise OperationFailedError(opname,details=e),None,tb
            if e.errno == errno.ENOENT:
                raise ResourceNotFoundError(path,opname=opname,details=e),None,tb
            if e.errno == errno.ESRCH:
                raise ResourceNotFoundError(path,opname=opname,details=e),None,tb
            if e.errno == errno.ENOTEMPTY:
                raise DirectoryNotEmptyError(path,opname=opname,details=e),None,tb
            if e.errno == errno.EEXIST:
                raise DestinationExistsError(path,opname=opname,details=e),None,tb
            if e.errno == 183: # some sort of win32 equivalent to EEXIST
                raise DestinationExistsError(path,opname=opname,details=e),None,tb
            if e.errno == errno.ENOTDIR:
                raise ResourceInvalidError(path,opname=opname,details=e),None,tb
            if e.errno == errno.EISDIR:
                raise ResourceInvalidError(path,opname=opname,details=e),None,tb
            if e.errno == errno.EINVAL:
                raise ResourceInvalidError(path,opname=opname,details=e),None,tb
            if e.errno == errno.EOPNOTSUPP:
                raise UnsupportedError(opname,details=e),None,tb
            if e.errno == errno.ENOSPC:
                raise StorageSpaceError(opname,details=e),None,tb
            if e.errno == errno.EPERM:
                raise PermissionDeniedError(opname,details=e),None,tb
            if e.errno == errno.EACCES:
                if sys.platform == "win32":
                    if e.args[0] and e.args[0] == 32:
                        raise ResourceLockedError(path,opname=opname,details=e),None,tb
                raise PermissionDeniedError(opname,details=e),None,tb
            # Sometimes windows gives some random errors...
            if sys.platform == "win32":
                if e.errno in (13,):
                    raise ResourceInvalidError(path,opname=opname,details=e),None,tb
            raise OperationFailedError(opname,details=e),None,tb
    return wrapper


