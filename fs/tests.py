#!/usr/bin/env python

import unittest
import fs
from helpers import *
import shutil

class TestHelpers(unittest.TestCase):

    def test_isabsolutepath(self):
        tests = [   ('', False),
                    ('/', True),
                    ('/A/B', True),
                    ('/asdasd', True),
                    ('a/b/c', False),
                    ]
        for path, result in tests:
            self.assertEqual(fs.isabsolutepath(path), result)

    def test_normpath(self):
        tests = [   ("\\a\\b\\c", "/a/b/c"),
                    ("", ""),
                    ("/a/b/c", "/a/b/c"),
                    ]
        for path, result in tests:
            self.assertEqual(fs.normpath(path), result)

    def test_pathjon(self):
        tests = [   ("", "a", "a"),
                    ("a", "a", "a/a"),
                    ("a/b", "../c", "a/c"),
                    ("a/b/../c", "d", "a/c/d"),
                    ("/a/b/c", "d", "/a/b/c/d"),
                    ("/a/b/c", "../../../d", "/d"),
                    ("a", "b", "c", "a/b/c"),
                    ("a/b/c", "../d", "c", "a/b/d/c"),
                    ("a/b/c", "../d", "/a", "/a"),
                    ("aaa", "bbb/ccc", "aaa/bbb/ccc"),
                    ("aaa", "bbb\ccc", "aaa/bbb/ccc"),
                    ("aaa", "bbb", "ccc", "/aaa", "eee", "/aaa/eee"),
                    ("a/b", "./d", "e", "a/b/d/e"),
                    ("/", "/", "/"),
                    ("/", "", "/"),
        ]
        for testpaths in tests:
            paths = testpaths[:-1]
            result = testpaths[-1]
            self.assertEqual(fs.pathjoin(*paths), result)

        self.assertRaises(ValueError, fs.pathjoin, "../")
        self.assertRaises(ValueError, fs.pathjoin, "./../")
        self.assertRaises(ValueError, fs.pathjoin, "a/b", "../../..")
        self.assertRaises(ValueError, fs.pathjoin, "a/b/../../../d")

    def test_makerelative(self):
        tests = [   ("/a/b", "a/b"),
                    ("a/b", "a/b"),
                    ("/", "") ]

        for path, result in tests:
            print path, result
            self.assertEqual(fs.makerelative(path), result)

    def test_makeabsolute(self):
        tests = [   ("/a/b", "/a/b"),
                    ("a/b", "/a/b"),
                    ("/", "/") ]

        for path, result in tests:
            self.assertEqual(fs.makeabsolute(path), result)

    def test_iteratepath(self):
        tests = [   ("a/b", ["a", "b"]),
                    ("", [] ),
                    ("aaa/bbb/ccc", ["aaa", "bbb", "ccc"]),
                    ("a/b/c/../d", ["a", "b", "d"]) ]

        for path, results in tests:
            print repr(path), results
            for path_component, expected in zip(fs._iteratepath(path), results):
                self.assertEqual(path_component, expected)

        self.assertEqual(list(fs._iteratepath("a/b/c/d", 1)), ["a", "b/c/d"])
        self.assertEqual(list(fs._iteratepath("a/b/c/d", 2)), ["a", "b", "c/d"])

    def test_pathsplit(self):
        tests = [   ("a/b", ("a", "b")),
                    ("a/b/c", ("a/b", "c")),
                    ("a", ("", "a")),
                    ("", ("", "")),
                    ("/", ("", "")),
                    ("foo/bar", ("foo", "bar")),
                    ("foo/bar/baz", ("foo/bar", "baz")),
                ]
        for path, result in tests:
            self.assertEqual(fs.pathsplit(path), result)


import objecttree

class TestObjectTree(unittest.TestCase):

    def test_getset(self):
        ot = objecttree.ObjectTree()
        ot['foo'] = "bar"
        self.assertEqual(ot['foo'], 'bar')

        ot = objecttree.ObjectTree()
        ot['foo/bar'] = "baz"
        self.assertEqual(ot['foo'], {'bar':'baz'})
        self.assertEqual(ot['foo/bar'], 'baz')

        del ot['foo/bar']
        self.assertEqual(ot['foo'], {})

        ot = objecttree.ObjectTree()
        ot['a/b/c'] = "A"
        ot['a/b/d'] = "B"
        ot['a/b/e'] = "C"
        ot['a/b/f'] = "D"
        self.assertEqual(sorted(ot['a/b'].values()), ['A', 'B', 'C', 'D'])
        self.assert_(ot.get('a/b/x', -1) == -1)

        self.assert_('a/b/c' in ot)
        self.assert_('a/b/x' not in ot)
        self.assert_(ot.isobject('a/b/c'))
        self.assert_(ot.isobject('a/b/d'))
        self.assert_(not ot.isobject('a/b'))

        left, object, right = ot.partialget('a/b/e/f/g')
        self.assertEqual(left, "a/b/e")
        self.assertEqual(object, "C")
        self.assertEqual(right, "f/g")


import tempfile
import osfs
import os

class TestOSFS(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp("fstest")
        self.fs = osfs.OSFS(self.temp_dir)
        print "Temp dir is", self.temp_dir

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def check(self, p):
        return os.path.exists(os.path.join(self.temp_dir, makerelative(p)))

    def test_makedir(self):
        check = self.check

        self.fs.makedir("a")
        self.assert_(check("a"))
        self.assertRaises(fs.FSError, self.fs.makedir, "a/b/c")

        self.fs.makedir("a/b/c", recursive=True)
        self.assert_(check("a/b/c"))

        self.fs.makedir("foo/bar/baz", recursive=True)
        self.assert_(check("foo/bar/baz"))

        self.fs.makedir("a/b/child")
        self.assert_(check("a/b/child"))


    def test_removedir(self):
        check = self.check
        self.fs.makedir("a")
        self.assert_(check("a"))
        self.fs.removedir("a")
        self.assert_(not check("a"))
        self.fs.makedir("a/b/c/d", recursive=True)
        self.assertRaises(fs.FSError, self.fs.removedir, "a/b")
        self.fs.removedir("a/b/c/d")
        self.assert_(not check("a/b/c/d"))
        self.fs.removedir("a/b/c")
        self.assert_(not check("a/b/c"))
        self.fs.removedir("a/b")
        self.assert_(not check("a/b"))

        self.fs.makedir("foo/bar/baz", recursive=True)
        self.fs.removedir("foo/bar/baz", recursive=True)
        self.assert_(not check("foo/bar/baz"))
        self.assert_(not check("foo/bar"))
        self.assert_(not check("foo"))

    def test_listdir(self):

        def makefile(fname):
            f = self.fs.open(fname, "wb")
            f.write("*")
            f.close()

        makefile("a")
        makefile("b")
        makefile("foo")
        makefile("bar")

        d1 = self.fs.listdir()
        self.assertEqual(len(d1), 4)
        self.assertEqual(sorted(d1), ["a", "b", "bar", "foo"])

        d2 = self.fs.listdir(absolute=True)
        self.assertEqual(len(d2), 4)
        self.assertEqual(sorted(d2), ["/a", "/b", "/bar", "/foo"])

        self.fs.makedir("p/1/2/3", recursive=True)
        makefile("p/1/2/3/a")
        makefile("p/1/2/3/b")
        makefile("p/1/2/3/foo")
        makefile("p/1/2/3/bar")

        self.fs.makedir("q")
        dirs_only = self.fs.listdir(dirs_only=True)
        files_only = self.fs.listdir(files_only=True)
        self.assertEqual(sorted(dirs_only), ["p", "q"])
        self.assertEqual(sorted(files_only), ["a", "b", "bar", "foo"])

        d3 = self.fs.listdir("p/1/2/3")
        self.assertEqual(len(d3), 4)
        self.assertEqual(sorted(d3), ["a", "b", "bar", "foo"])

        d4 = self.fs.listdir("p/1/2/3", absolute=True)
        self.assertEqual(len(d4), 4)
        self.assertEqual(sorted(d4), ["/p/1/2/3/a", "/p/1/2/3/b", "/p/1/2/3/bar", "/p/1/2/3/foo"])

        d4 = self.fs.listdir("p/1/2/3", full=True)
        self.assertEqual(len(d4), 4)
        self.assertEqual(sorted(d4), ["p/1/2/3/a", "p/1/2/3/b", "p/1/2/3/bar", "p/1/2/3/foo"])


    def test_rename(self):
        check = self.check
        self.fs.open("foo.txt", 'wt').write("Hello, World!")
        self.assert_(check("foo.txt"))
        self.fs.rename("foo.txt", "bar.txt")
        self.assert_(check("bar.txt"))

    def test_info(self):
        test_str = "Hello, World!"
        f = self.fs.open("info.txt", 'wb')
        f.write(test_str)
        f.close()
        info = self.fs.getinfo("info.txt")
        self.assertEqual(info['size'], len(test_str))

    def test_getsize(self):
        test_str = "*"*23
        f = self.fs.open("info.txt", 'wb')
        f.write(test_str)
        f.close()
        size = self.fs.getsize("info.txt")
        self.assertEqual(size, len(test_str))

    def test_movefile(self):

        check = self.check
        contents = "If the implementation is hard to explain, it's a bad idea."
        def makefile(path):
            f = self.fs.open(path, "wb")
            f.write(contents)
            f.close()
        def checkcontents(path):
            f = self.fs.open(path, "rb")
            check_contents = f.read()
            f.close()
            return contents == check_contents

        self.fs.makedir("foo/bar", recursive=True)
        makefile("foo/bar/a.txt")
        self.assert_(check("foo/bar/a.txt"))
        self.assert_(checkcontents("foo/bar/a.txt"))
        self.fs.move("foo/bar/a.txt", "foo/b.txt")
        self.assert_(not check("foo/bar/a.txt"))
        self.assert_(check("foo/b.txt"))
        self.assert_(checkcontents("foo/b.txt"))

        self.fs.move("foo/b.txt", "c.txt")
        fs.print_fs(self.fs)
        self.assert_(not check("foo/b.txt"))
        self.assert_(check("/c.txt"))
        self.assert_(checkcontents("/c.txt"))

class TestSubFS(TestOSFS):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp("fstest")
        self.parent_fs = osfs.OSFS(self.temp_dir)
        self.parent_fs.makedir("foo/bar", recursive=True)
        self.fs = self.parent_fs.opendir("foo/bar")
        print "Temp dir is", self.temp_dir

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def check(self, p):
        p = os.path.join("foo/bar", makerelative(p))
        full_p = os.path.join(self.temp_dir, p)
        return os.path.exists(full_p)


import memoryfs
class TestMemoryFS(TestOSFS):

    def setUp(self):
        self.fs = memoryfs.MemoryFS()

    def tearDown(self):
        pass

    def check(self, p):
        return self.fs.exists(p)


import mountfs
class TestMountFS(TestOSFS):

    def setUp(self):
        self.mount_fs = mountfs.MountFS()
        self.mem_fs = memoryfs.MemoryFS()
        self.mount_fs.mountdir("mounted/memfs", self.mem_fs)
        self.fs = self.mount_fs.opendir("mounted/memfs")

    def tearDown(self):
        pass

    def check(self, p):
        return self.mount_fs.exists(os.path.join("mounted/memfs", makerelative(p)))


if __name__ == "__main__":
    #t = TestFS()
    #t.setUp()
    #t.tearDown()
    import nose
    nose.main()