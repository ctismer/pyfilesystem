#!/usr/bin/env python
"""

  fs.tests.test_expose:  testcases for fs.expose and associated FS classes

"""

import unittest
import socket
import threading

from fs.tests import FSTestCases
from fs.tempfs import TempFS

from fs import rpcfs
from fs.expose.xmlrpc import RPCFSServer
class TestRPCFS(unittest.TestCase,FSTestCases):

    def makeServer(self,fs,addr):
        return RPCFSServer(fs,addr,logRequests=False)

    def startServer(self):
        port = 8000
        self.temp_fs = TempFS()
        self.server = None
        while not self.server:
            try:
                self.server = self.makeServer(self.temp_fs,("localhost",port))
            except socket.error, e:
                if e.args[1] == "Address already in use":
                    port += 1
                else:
                    raise
        self.server_addr = ("localhost",port)
        self.serve_more_requests = True
        self.server_thread = threading.Thread(target=self.runServer)
        self.server_thread.start()

    def runServer(self):
        """Run the server, swallowing shutdown-related execptions."""
        self.server.socket.settimeout(0.1)
        try:
            while self.serve_more_requests:
                self.server.handle_request()
        except Exception, e:
            pass

    def setUp(self):
        self.startServer()
        self.fs = rpcfs.RPCFS("http://%s:%d" % self.server_addr)

    def tearDown(self):
        self.serve_more_requests = False
        try:
            self.bump()
            self.server.server_close()
        except Exception:
            pass
        self.server_thread.join()
        self.temp_fs.close()

    def bump(self):
        host, port = self.server_addr
        for res in socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM):
            af, socktype, proto, cn, sa = res
            sock = None
            try:
                sock = socket.socket(af, socktype, proto)
                sock.settimeout(1)
                sock.connect(sa)
                sock.send("\n")
            except socket.error, e:
                pass
            finally:
                if sock is not None:
                    sock.close()


from fs import sftpfs
from fs.expose.sftp import BaseSFTPServer
class TestSFTPFS(TestRPCFS):

    def makeServer(self,fs,addr):
        return BaseSFTPServer(addr,fs)

    def setUp(self):
        self.startServer()
        self.fs = sftpfs.SFTPFS(self.server_addr)

    def bump(self):
        # paramiko doesn't like being bumped, just wait for it to timeout.
        # TODO: do this using a paramiko.Transport() connection
        pass


