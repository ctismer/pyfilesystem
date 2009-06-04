"""

  fs.wrappers.hidedotfiles:  FS wrapper to hide dot-files in dir listings

"""

from fs.path import *
from fs.errors import *
from fs.wrappers import FSWrapper


class HideDotFiles(FSWrapper):
    """FS wrapper class that hides dot-files in directory listings.

    The listdir() function takes an extra keyword argument 'hidden'
    indicating whether hidden dotfiles shoud be included in the output.
    It is False by default.
    """

    def is_hidden(self,path):
        """Check whether the given path should be hidden."""
        return path and basename(path)[0] == "."

    def _encode(self,path):
        return path

    def _decode(self,path):
        return path

    def listdir(self,path="",**kwds):
        hidden = kwds.pop("hidden",True)
        entries = self.wrapped_fs.listdir(path,**kwds)
        if not hidden:
            entries = [e for e in entries if not self.is_hidden(e)]
        return entries

    def walk(self, path="/", wildcard=None, dir_wildcard=None, search="breadth",hidden=False):
        if search == "breadth":
            dirs = [path]
            while dirs:
                current_path = dirs.pop()
                paths = []
                for filename in self.listdir(current_path,hidden=hidden):
                    path = pathjoin(current_path, filename)
                    if self.isdir(path):
                        if dir_wildcard is not None:
                            if fnmatch.fnmatch(path, dir_wilcard):
                                dirs.append(path)
                        else:
                            dirs.append(path)
                    else:
                        if wildcard is not None:
                            if fnmatch.fnmatch(path, wildcard):
                                paths.append(filename)
                        else:
                            paths.append(filename)
                yield (current_path, paths)
        elif search == "depth":
            def recurse(recurse_path):
                for path in self.listdir(recurse_path, wildcard=dir_wildcard, full=True, dirs_only=True,hidden=hidden):
                    for p in recurse(path):
                        yield p
                yield (recurse_path, self.listdir(recurse_path, wildcard=wildcard, files_only=True,hidden=hidden))
            for p in recurse(path):
                yield p
        else:
            raise ValueError("Search should be 'breadth' or 'depth'")


    def isdirempty(self, path):
        path = normpath(path)
        iter_dir = iter(self.listdir(path,hidden=True))
        try:
            iter_dir.next()
        except StopIteration:
            return True
        return False

