"""

  fs.tests.test_fs:  testcases for basic FS implementations

"""

from fs.tests import FSTestCases, ThreadingTestCases

import unittest

import os
import sys
import shutil
import tempfile

from fs.path import *


from fs import osfs
class TestOSFS(unittest.TestCase,FSTestCases,ThreadingTestCases):

    def setUp(self):
        sys.setcheckinterval(1)
        self.temp_dir = tempfile.mkdtemp(u"fstest")
        self.fs = osfs.OSFS(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def check(self, p):
        return os.path.exists(os.path.join(self.temp_dir, relpath(p)))


class TestSubFS(unittest.TestCase,FSTestCases,ThreadingTestCases):

    def setUp(self):
        sys.setcheckinterval(1)
        self.temp_dir = tempfile.mkdtemp(u"fstest")
        self.parent_fs = osfs.OSFS(self.temp_dir)
        self.parent_fs.makedir("foo/bar", recursive=True)
        self.fs = self.parent_fs.opendir("foo/bar")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def check(self, p):
        p = os.path.join("foo/bar", relpath(p))
        full_p = os.path.join(self.temp_dir, p)
        return os.path.exists(full_p)


from fs import memoryfs
class TestMemoryFS(unittest.TestCase,FSTestCases,ThreadingTestCases):

    def setUp(self):
        sys.setcheckinterval(1)
        self.fs = memoryfs.MemoryFS()


from fs import mountfs
class TestMountFS(unittest.TestCase,FSTestCases,ThreadingTestCases):

    def setUp(self):
        sys.setcheckinterval(1)
        self.mount_fs = mountfs.MountFS()
        self.mem_fs = memoryfs.MemoryFS()
        self.mount_fs.mountdir("mounted/memfs", self.mem_fs)
        self.fs = self.mount_fs.opendir("mounted/memfs")

    def tearDown(self):
        pass

    def check(self, p):
        return self.mount_fs.exists(os.path.join("mounted/memfs", relpath(p)))


from fs import tempfs
class TestTempFS(unittest.TestCase,FSTestCases,ThreadingTestCases):

    def setUp(self):
        self.fs = tempfs.TempFS()

    def tearDown(self):
        td = self.fs._temp_dir
        self.fs.close()
        self.assert_(not os.path.exists(td))

    def check(self, p):
        td = self.fs._temp_dir
        return os.path.exists(os.path.join(td, relpath(p)))
     
        
from fs import wrapfs
class TestWrapFS(unittest.TestCase, FSTestCases, ThreadingTestCases):
    
    def setUp(self):
        sys.setcheckinterval(1)
        self.temp_dir = tempfile.mkdtemp(u"fstest")
        self.fs = wrapfs.WrapFS(osfs.OSFS(self.temp_dir))

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def check(self, p):
        return os.path.exists(os.path.join(self.temp_dir, relpath(p)))
