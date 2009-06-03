"""

  fs.expose.sftp:  expose an FS object over SFTP (via paramiko).

This module provides the necessary interfaces to expose an FS object over
SFTP, plugging into the infratructure provided by the 'paramiko' module.

For simple usage, the class 'BaseSFTPServer' provides an all-in-one server
class based on the standard SocketServer module.  Use it like so:

    server = BaseSFTPServer((hostname,port),fs)
    server.serve_forever()

Note that the base class allows UNAUTHENTICATED ACCESS by default.  For more
serious work you will probably want to subclass it and override methods such
as check_auth_password() and get_allowed_auths().

To integrate this module into an existing server framework based on paramiko,
the 'SFTPServerInterface' class provides a concrete implementation of the
paramiko.SFTPServerInterface protocol.  If you don't understand what this
is, you probably don't want to use it.

"""

import os
import stat as statinfo
import time
import SocketServer as sockserv
import threading
from StringIO import StringIO

import paramiko

from fs.errors import *
from fs.helpers import *


# Default host key used by BaseSFTPServer
#
DEFAULT_HOST_KEY = paramiko.RSAKey.from_private_key(StringIO("-----BEGIN RSA PRIVATE KEY-----\nMIICXgIBAAKCAIEAl7sAF0x2O/HwLhG68b1uG8KHSOTqe3Cdlj5i/1RhO7E2BJ4B\n3jhKYDYtupRnMFbpu7fb21A24w3Y3W5gXzywBxR6dP2HgiSDVecoDg2uSYPjnlDk\nHrRuviSBG3XpJ/awn1DObxRIvJP4/sCqcMY8Ro/3qfmid5WmMpdCZ3EBeC0CAwEA\nAQKCAIBSGefUs5UOnr190C49/GiGMN6PPP78SFWdJKjgzEHI0P0PxofwPLlSEj7w\nRLkJWR4kazpWE7N/bNC6EK2pGueMN9Ag2GxdIRC5r1y8pdYbAkuFFwq9Tqa6j5B0\nGkkwEhrcFNBGx8UfzHESXe/uE16F+e8l6xBMcXLMJVo9Xjui6QJBAL9MsJEx93iO\nzwjoRpSNzWyZFhiHbcGJ0NahWzc3wASRU6L9M3JZ1VkabRuWwKNuEzEHNK8cLbRl\nTyH0mceWXcsCQQDLDEuWcOeoDteEpNhVJFkXJJfwZ4Rlxu42MDsQQ/paJCjt2ONU\nWBn/P6iYDTvxrt/8+CtLfYc+QQkrTnKn3cLnAkEAk3ixXR0h46Rj4j/9uSOfyyow\nqHQunlZ50hvNz8GAm4TU7v82m96449nFZtFObC69SLx/VsboTPsUh96idgRrBQJA\nQBfGeFt1VGAy+YTLYLzTfnGnoFQcv7+2i9ZXnn/Gs9N8M+/lekdBFYgzoKN0y4pG\n2+Q+Tlr2aNlAmrHtkT13+wJAJVgZATPI5X3UO0Wdf24f/w9+OY+QxKGl86tTQXzE\n4bwvYtUGufMIHiNeWP66i6fYCucXCMYtx6Xgu2hpdZZpFw==\n-----END RSA PRIVATE KEY-----\n"))


try:
    from functools import wraps
except ImportError:
    def wraps(f):
        return f


def report_sftp_errors(func):
    """Decorator to catch and report FS errors as SFTP error codes.

    Any FSError exceptions are caught and translated into an appropriate
    return code, while other exceptions are passed through untouched.
    """
    @wraps(func)
    def wrapper(*args,**kwds):
        try:
            return func(*args,**kwds)
        except ResourceNotFoundError, e:
            return paramiko.SFTP_NO_SUCH_FILE
        except UnsupportedError, e:
            return paramiko.SFTP_OP_UNSUPPORTED
        except FSError, e:
            return paramiko.SFTP_FAILURE
    return wrapper


class SFTPServerInterface(paramiko.SFTPServerInterface):
    """SFTPServerInferface implementation that exposes an FS object.

    This SFTPServerInterface subclass expects a single additional argument,
    the fs object to be exposed.  Use it to set up a transport subsystem
    handler like so:

      t.set_subsystem_handler("sftp",SFTPServer,SFTPServerInterface,fs)

    If this all looks too complicated, you might consider the BaseSFTPServer
    class also provided by this module - it automatically creates the enclosing
    paramiko server infrastructure.
    """

    def __init__(self,server,fs,*args,**kwds):
        self.fs = fs
        super(SFTPServerInterface,self).__init__(server,*args,**kwds)

    @report_sftp_errors
    def open(self,path,flags,attr):
        return SFTPHandle(self,path,flags)

    @report_sftp_errors
    def list_folder(self,path):
        stats = []
        for entry in self.fs.listdir(path,absolute=True):
            stats.append(self.stat(entry))
        return stats
 
    @report_sftp_errors
    def stat(self,path):
        info = self.fs.getinfo(path)
        stat = paramiko.SFTPAttributes()
        stat.filename = resourcename(path)
        stat.st_size = info.get("size")
        stat.st_atime = time.mktime(info.get("accessed_time").timetuple())
        stat.st_mtime = time.mktime(info.get("modified_time").timetuple())
        if self.fs.isdir(path):
            stat.st_mode = 0777 | statinfo.S_IFDIR
        else:
            stat.st_mode = 0777 | statinfo.S_IFREG
        return stat

    def lstat(self,path):
        return self.stat(path)

    @report_sftp_errors
    def remove(self,path):
        self.fs.remove(path)
        return paramiko.SFTP_OK

    @report_sftp_errors
    def rename(self,oldpath,newpath):
        if self.fs.isfile(oldpath):
            self.fs.move(oldpath,newpath)
        else:
            self.fs.movedir(oldpath,newpath)
        return paramiko.SFTP_OK

    @report_sftp_errors
    def mkdir(self,path,attr):
        self.fs.makedir(path)
        return paramiko.SFTP_OK

    @report_sftp_errors
    def rmdir(self,path):
        self.fs.removedir(path)
        return paramiko.SFTP_OK

    def canonicalize(self,path):
        return makeabsolute(path)

    def chattr(self,path,attr):
        return paramiko.SFTP_OP_UNSUPPORTED

    def readlink(self,path):
        return paramiko.SFTP_OP_UNSUPPORTED

    def symlink(self,path):
        return paramiko.SFTP_OP_UNSUPPORTED


class SFTPHandle(paramiko.SFTPHandle):
    """SFTP file handler pointing to a file in an FS object.

    This is a simple file wrapper for SFTPServerInterface, passing read
    and write requests directly through the to underlying file from the FS.
    """

    def __init__(self,owner,path,flags):
        super(SFTPHandle,self).__init__(flags)
        mode = self._flags_to_mode(flags)
        self.owner = owner
        self.path = path
        self._file = owner.fs.open(path,mode)

    def _flags_to_mode(self,flags):
        """Convert an os.O_* bitmask into an FS mode string."""
        if flags & os.O_EXCL:
            raise UnsupportedError("open",msg="O_EXCL is not supported")
        if flags & os.O_WRONLY:
            if flags & os.O_TRUNC:
                mode = "w"
            elif flags & os.O_APPEND:
                mode = "a"
            else:
                mode = "r+"
        elif flags & os.O_RDWR:
            if flags & os.O_TRUNC:
                mode = "w+"
            elif flags & os.O_APPEND:
                mode = "a+"
            else:
                mode = "r+"
        else:
            mode = "r"
        return mode

    @report_sftp_errors
    def close(self):
        self._file.close()
        return paramiko.SFTP_OK

    @report_sftp_errors
    def read(self,offset,length):
        self._file.seek(offset)
        return self._file.read(length)

    @report_sftp_errors
    def write(self,offset,data):
        self._file.seek(offset)
        self._file.write(data)
        return paramiko.SFTP_OK

    def stat(self):
        return self.owner.stat(self.path)

    def chattr(self,attr):
        return self.owner.chattr(self.path,attr)


class SFTPRequestHandler(sockserv.StreamRequestHandler):
    """SockerServer RequestHandler subclass for BaseSFTPServer.

    This RequestHandler subclass creates a paramiko Transport, sets up the
    sftp subsystem, and hands off the the transport's own request handling
    thread.  Note that paramiko.Transport uses a separate thread by default,
    so there is no need to use TreadingMixIn.
    """

    def handle(self):
        t = paramiko.Transport(self.request)
        t.add_server_key(self.server.host_key)
        t.set_subsystem_handler("sftp",paramiko.SFTPServer,SFTPServerInterface,self.server.fs)
        # Note that this actually spawns a new thread to handle the requests.
        # (Actually, paramiko.Transport is a subclass of Thread)
        t.start_server(server=self.server)


class BaseSFTPServer(sockserv.TCPServer,paramiko.ServerInterface):
    """SocketServer.TCPServer subclass exposing an FS via SFTP.

    BaseSFTPServer combines a simple SocketServer.TCPServer subclass with an
    implementation of paramiko.ServerInterface, providing everything that's
    needed to expose an FS via SFTP.

    Operation is in the standard SocketServer style.  The target FS object
    can be passed into the constructor, or set as an attribute on the server:

        server = BaseSFTPServer((hostname,port),fs)
        server.serve_forever()

    It is also possible to specify the host key used by the sever by setting
    the 'host_key' attribute.  If this is not specified, it will default to
    the key found in the DEFAULT_HOST_KEY variable.

    Note that this base class allows UNAUTHENTICATED ACCESS to the exposed
    FS.  This is intentional, since we can't guess what your authentication
    needs are.  To protect the exposed FS, override the following methods:

        get_allowed_auths:      determine the allowed auth modes
        check_auth_none:        check auth with no credentials
        check_auth_password:    check auth with a password
        check_auth_publickey:   check auth with a public key

    """

    def __init__(self,address,fs=None,host_key=None,RequestHandlerClass=None):
        self.fs = fs
        if host_key is None:
            host_key = DEFAULT_HOST_KEY
        self.host_key = host_key
        if RequestHandlerClass is None:
            RequestHandlerClass = SFTPRequestHandler
        sockserv.TCPServer.__init__(self,address,RequestHandlerClass)

    def close_request(self,request):
        #  paramiko.Transport closes itself when finished.
        #  If we close it here, we'll break the Transport thread.
        pass

    def check_channel_request(self,kind,chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_none(self,username):
        """Check whether the user can proceed without authentication."""
        return paramiko.AUTH_SUCCESSFUL

    def check_auth_publickey(self,username,key):
        """Check whether the given public key is valid for authentication."""
        return paramiko.AUTH_FAILED

    def check_auth_password(self,username,password):
        """Check whether the given password is valid for authentication."""
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self,username):
        """Return list of allowed auth modes.

        The available modes are  "node", "password" and "publickey".
        """
        return ("none",)


#  When called from the command-line, expose a TempFS for testing purposes
if __name__ == "__main__":
    from fs.tempfs import TempFS
    server = BaseSFTPServer(("localhost",8022),TempFS())
    try:
        server.serve_forever()
    except (SystemExit,KeyboardInterrupt):
        server.shutdown()

