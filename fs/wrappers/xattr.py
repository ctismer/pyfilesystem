"""

  fs.wrappers.xattr:  FS wrapper for simulating extended-attribute support.

This module defines a standard interface for FS subclasses that want to
support extended attributes, and an FSWrapper subclass that can simulate
extended attributes on top of an ordinery FS.

If extended attributes are required by FS-consuming code, it should use the
function 'ensure_xattr'.  This will interrogate an FS object to determine
if it has native xattr support, and return a wrapped version if it does not.
"""

try:
    import cPickle as pickle
except ImportError:
    import pickle

from fs.path import *
from fs.errors import *
from fs.wrappers import FSWrapper


def ensure_xattr(fs):
    """Ensure that the given FS supports xattrs, simulating them if required.

    Given an FS object, this function returns an equivalent FS that has support
    for extended attributes.  This may be the original object if they are
    supported natively, or a wrapper class is they must be simulated.
    """
    try:
        #  This doesn't have to exist, it should return None by default
        fs.getxattr("/","testingx-xattr")
        return fs
    except Exception:
        return SimulateXAttr(fs)

class SimulateXAttr(FSWrapper):
    """FS wrapper class that simulates xattr support.

    The following methods are supplied for manipulating extended attributes:
        * xattrs:    list all extended attribute names for a path
        * getxattr:  get an xattr of a path by name
        * setxattr:  set an xattr of a path by name
        * delxattr:  delete an xattr of a path by name

    For each file in the underlying FS, this class maintains a corresponding 
    file '.xattrs.FILENAME' containing its extended attributes.  Extended
    attributes of a directory are stored in the file '.xattrs' within the
    directory itself.
    """

    def _get_attr_path(self, path):
        """Get the path of the file containing xattrs for the given path."""
        if self.wrapped_fs.isdir(path):
            attr_path = pathjoin(path, '.xattrs')
        else:
            dir_path, file_name = pathsplit(path)
            attr_path = pathjoin(dir_path, '.xattrs.'+file_name)
        return attr_path

    def _is_attr_path(self, path):
        """Check whether the given path references an xattrs file."""
        _,name = pathsplit(path)
        if name.startswith(".xattrs"):
            return True
        return False

    def _get_attr_dict(self, path):
        """Retrieve the xattr dictionary for the given path."""
        attr_path = self._get_attr_path(path)
        if self.wrapped_fs.exists(attr_path):
            return pickle.loads(self.wrapped_fs.getcontents(attr_path))
        else:
            return {}

    def _set_attr_dict(self, path, attrs):
        """Store the xattr dictionary for the given path."""
        attr_path = self._get_attr_path(path)
        self.wrapped_fs.setcontents(attr_path, pickle.dumps(attrs))

    def setxattr(self, path, key, value):
        """Set an extended attribute on the given path."""
        if not self.exists(path):
            raise ResourceNotFoundError(path)
        attrs = self._get_attr_dict(path)
        attrs[key] = value
        self._set_attr_dict(path, attrs)

    def getxattr(self, path, key, default=None):
        """Retrieve an extended attribute for the given path."""
        if not self.exists(path):
            raise ResourceNotFoundError(path)
        attrs = self._get_attr_dict(path)
        return attrs.get(key, default)

    def delxattr(self, path, key):
        if not self.exists(path):
            raise ResourceNotFoundError(path)
        attrs = self._get_attr_dict(path)
        try:
            del attrs[key]
        except KeyError:
            pass
        self._set_attr_dict(path, attrs)

    def xattrs(self,path):
        """List all the extended attribute keys set on the given path."""
        if not self.exists(path):
            raise ResourceNotFoundError(path)
        return self._get_attr_dict(path).keys()

    def _encode(self,path):
        """Prevent requests for operations on .xattr files."""
        if self._is_attr_path(path):
            raise PathError(path,msg="Paths cannot contain '.xattrs': %(path)s")
        return path

    def _decode(self,path):
        return path

    def listdir(self,path="",**kwds):
        """Prevent .xattr from appearing in listings."""
        entries = self.wrapped_fs.listdir(path,**kwds)
        return [e for e in entries if not self._is_attr_path(e)]

    def copy(self,src,dst,**kwds):
        """Ensure xattrs are copied when copying a file."""
        self.wrapped_fs.copy(self._encode(src),self._encode(dst),**kwds)
        s_attr_file = self._get_attr_path(src)
        d_attr_file = self._get_attr_path(dst)
        try:
            self.wrapped_fs.copy(s_attr_file,d_attr_file,overwrite=True)
        except ResourceNotFoundError,e:
            pass

    def move(self,src,dst,**kwds):
        """Ensure xattrs are preserved when moving a file."""
        self.wrapped_fs.move(self._encode(src),self._encode(dst),**kwds)
        s_attr_file = self._get_attr_path(src)
        d_attr_file = self._get_attr_path(dst)
        try:
            self.wrapped_fs.move(s_attr_file,d_attr_file,overwrite=True)
        except ResourceNotFoundError:
            pass
 
