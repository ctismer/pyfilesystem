"""
fs.expose.xmlrpc
================

Server to expose an FS via XML-RPC

This module provides the necessary infrastructure to expose an FS object
over XML-RPC.  The main class is 'RPCFSServer', a SimpleXMLRPCServer subclass
designed to expose an underlying FS.

If you need to use a more powerful server than SimpleXMLRPCServer, you can
use the RPCFSInterface class to provide an XML-RPC-compatible wrapper around
an FS object, which can then be exposed using whatever server you choose
(e.g. Twisted's XML-RPC server).

"""

import xmlrpclib
from SimpleXMLRPCServer import SimpleXMLRPCServer


class RPCFSInterface(object):
    """Wrapper to expose an FS via a XML-RPC compatible interface.

    The only real trick is using xmlrpclib.Binary objects to transport
    the contents of files.
    """

    def __init__(self, fs):
        self.fs = fs

    def encode_path(self, path):
        """Encode a filesystem path for sending over the wire.

        Unfortunately XMLRPC only supports ASCII strings, so this method
        must return something that can be represented in ASCII.  The default
        is base64-encoded UTF-8.
        """
        return path.encode("utf8").encode("base64")

    def decode_path(self, path):
        """Decode paths arriving over the wire."""
        return path.decode("base64").decode("utf8")

    def getmeta(self, meta_name):
        meta = self.fs.getmeta(meta_name)
        return meta
    
    def getmeta_default(self, meta_name, default):
        meta = self.fs.getmeta(meta_name, default)
        return xmlrpclib.Binary(meta)
    
    def hasmeta(self, meta_name):
        return self.fs.hasmeta(meta_name)

    def get_contents(self, path):
        path = self.decode_path(path)
        data = self.fs.getcontents(path)
        return xmlrpclib.Binary(data)

    def set_contents(self, path, data):
        path = self.decode_path(path)
        self.fs.createfile(path,data.data)

    def exists(self, path):
        path = self.decode_path(path)
        return self.fs.exists(path)

    def isdir(self, path):
        path = self.decode_path(path)
        return self.fs.isdir(path)

    def isfile(self, path):
        path = self.decode_path(path)
        return self.fs.isfile(path)

    def listdir(self, path="./", wildcard=None, full=False, absolute=False, dirs_only=False, files_only=False):
        path = self.decode_path(path)
        entries = self.fs.listdir(path,wildcard,full,absolute,dirs_only,files_only)
        return [self.encode_path(e) for e in entries]

    def makedir(self, path, recursive=False, allow_recreate=False):
        path = self.decode_path(path)
        return self.fs.makedir(path, recursive, allow_recreate)

    def remove(self, path):
        path = self.decode_path(path)
        return self.fs.remove(path)

    def removedir(self, path, recursive=False, force=False):
        path = self.decode_path(path)
        return self.fs.removedir(path, recursive, force)
        
    def rename(self, src, dst):
        src = self.decode_path(src)
        dst = self.decode_path(dst)
        return self.fs.rename(src, dst)

    def settimes(self, path, accessed_time, modified_time):
        path = self.decode_path(path)
        return self.fs.settimes(path, accessed_time, modified_time)

    def getinfo(self, path):
        path = self.decode_path(path)
        return self.fs.getinfo(path)

    def desc(self, path):
        path = self.decode_path(path)
        return self.fs.desc(path)

    def getxattr(self, path, attr, default=None):
        path = self.decode_path(path)
        attr = self.decode_path(attr)
        return self.fs.getxattr(path, attr, default)

    def setxattr(self, path, attr, value):
        path = self.decode_path(path)
        attr = self.decode_path(attr)
        return self.fs.setxattr(path, attr, value)

    def delxattr(self, path, attr):
        path = self.decode_path(path)
        attr = self.decode_path(attr)
        return self.fs.delxattr(path, attr)

    def listxattrs(self, path):
        path = self.decode_path(path)
        return [self.encode_path(a) for a in self.fs.listxattrs(path)]

    def copy(self, src, dst, overwrite=False, chunk_size=16384):
        src = self.decode_path(src)
        dst = self.decode_path(dst)
        return self.fs.copy(src, dst, overwrite, chunk_size)

    def move(self,src,dst,overwrite=False,chunk_size=16384):
        src = self.decode_path(src)
        dst = self.decode_path(dst)
        return self.fs.move(src, dst, overwrite, chunk_size)

    def movedir(self, src, dst, overwrite=False, ignore_errors=False, chunk_size=16384):
        src = self.decode_path(src)
        dst = self.decode_path(dst)
        return self.fs.movedir(src, dst, overwrite, ignore_errors, chunk_size)

    def copydir(self, src, dst, overwrite=False, ignore_errors=False, chunk_size=16384):
        src = self.decode_path(src)
        dst = self.decode_path(dst)
        return self.fs.copydir(src, dst, overwrite, ignore_errors, chunk_size)


class RPCFSServer(SimpleXMLRPCServer):
    """Server to expose an FS object via XML-RPC.

    This class takes as its first argument an FS instance, and as its second
    argument a (hostname,port) tuple on which to listen for XML-RPC requests.
    Example::

        fs = OSFS('/var/srv/myfiles')
        s = RPCFSServer(fs,("",8080))
        s.serve_forever()

    To cleanly shut down the server after calling serve_forever, set the
    attribute "serve_more_requests" to False.
    """

    def __init__(self, fs, addr, requestHandler=None, logRequests=None):
        kwds = dict(allow_none=True)
        if requestHandler is not None:
            kwds['requestHandler'] = requestHandler
        if logRequests is not None:
            kwds['logRequests'] = logRequests
        self.serve_more_requests = True
        SimpleXMLRPCServer.__init__(self,addr,**kwds)
        self.register_instance(RPCFSInterface(fs))

    def serve_forever(self):
        """Override serve_forever to allow graceful shutdown."""
        while self.serve_more_requests:
            self.handle_request()

