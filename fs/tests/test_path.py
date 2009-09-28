"""

  fs.tests.test_path:  testcases for the fs path functions

"""


import unittest
import fs.tests

from fs.path import *

class TestPathFunctions(unittest.TestCase):
    """Testcases for FS path functions."""

    def test_normpath(self):
        tests = [   ("\\a\\b\\c", "/a/b/c"),
                    ("", ""),
                    ("/a/b/c", "/a/b/c"),
                    ("a/b/c", "a/b/c"),
                    ("a/b/../c/", "a/c"),
                    ("/","/"),
                    (u"a/\N{GREEK SMALL LETTER BETA}\\c",u"a/\N{GREEK SMALL LETTER BETA}/c"),
                    ]
        for path, result in tests:
            self.assertEqual(normpath(path), result)

    def test_pathjoin(self):
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
                    (u"a/\N{GREEK SMALL LETTER BETA}","c",u"a/\N{GREEK SMALL LETTER BETA}/c"),
        ]
        for testpaths in tests:
            paths = testpaths[:-1]
            result = testpaths[-1]
            self.assertEqual(fs.pathjoin(*paths), result)

        self.assertRaises(ValueError, fs.pathjoin, "../")
        self.assertRaises(ValueError, fs.pathjoin, "./../")
        self.assertRaises(ValueError, fs.pathjoin, "a/b", "../../..")
        self.assertRaises(ValueError, fs.pathjoin, "a/b/../../../d")

    def test_relpath(self):
        tests = [   ("/a/b", "a/b"),
                    ("a/b", "a/b"),
                    ("/", "") ]

        for path, result in tests:
            self.assertEqual(fs.relpath(path), result)

    def test_abspath(self):
        tests = [   ("/a/b", "/a/b"),
                    ("a/b", "/a/b"),
                    ("/", "/") ]

        for path, result in tests:
            self.assertEqual(fs.abspath(path), result)

    def test_iteratepath(self):
        tests = [   ("a/b", ["a", "b"]),
                    ("", [] ),
                    ("aaa/bbb/ccc", ["aaa", "bbb", "ccc"]),
                    ("a/b/c/../d", ["a", "b", "d"]) ]

        for path, results in tests:
            for path_component, expected in zip(iteratepath(path), results):
                self.assertEqual(path_component, expected)

        self.assertEqual(list(iteratepath("a/b/c/d", 1)), ["a", "b/c/d"])
        self.assertEqual(list(iteratepath("a/b/c/d", 2)), ["a", "b", "c/d"])

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



