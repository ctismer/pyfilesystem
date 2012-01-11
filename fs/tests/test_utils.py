import unittest

from fs.tempfs import TempFS
from fs.memoryfs import MemoryFS
from fs import utils

class TestUtils(unittest.TestCase):
    
    def _make_fs(self, fs):
        fs.setcontents("f1", "file 1")
        fs.setcontents("f2", "file 2")
        fs.setcontents("f3", "file 3")
        fs.makedir("foo/bar", recursive=True)
        fs.setcontents("foo/bar/fruit", "apple")
        
    def _check_fs(self, fs):
        self.assert_(fs.isfile("f1"))
        self.assert_(fs.isfile("f2"))
        self.assert_(fs.isfile("f3"))
        self.assert_(fs.isdir("foo/bar"))
        self.assert_(fs.isfile("foo/bar/fruit"))
        self.assertEqual(fs.getcontents("f1", "rb"), "file 1")
        self.assertEqual(fs.getcontents("f2", "rb"), "file 2")
        self.assertEqual(fs.getcontents("f3", "rb"), "file 3")
        self.assertEqual(fs.getcontents("foo/bar/fruit", "rb"), "apple")        
        
    def test_copydir_root(self):
        """Test copydir from root"""
        fs1 = MemoryFS()
        self._make_fs(fs1)        
        fs2 = MemoryFS()
        utils.copydir(fs1, fs2)        
        self._check_fs(fs2)
                
        fs1 = TempFS()
        self._make_fs(fs1)        
        fs2 = TempFS()
        utils.copydir(fs1, fs2)        
        self._check_fs(fs2)
    
    def test_copydir_indir(self):
        """Test copydir in a directory"""        
        fs1 = MemoryFS()
        fs2 = MemoryFS()
        self._make_fs(fs1)        
        utils.copydir(fs1, (fs2, "copy"))        
        self._check_fs(fs2.opendir("copy"))

        fs1 = TempFS()
        fs2 = TempFS()
        self._make_fs(fs1)        
        utils.copydir(fs1, (fs2, "copy"))        
        self._check_fs(fs2.opendir("copy"))
    
    def test_movedir_indir(self):
        """Test movedir in a directory"""        
        fs1 = MemoryFS()
        fs2 = MemoryFS()
        fs1sub = fs1.makeopendir("from")
        self._make_fs(fs1sub)            
        utils.movedir((fs1, "from"), (fs2, "copy"))        
        self.assert_(not fs1.exists("from"))     
        self._check_fs(fs2.opendir("copy"))

        fs1 = TempFS()
        fs2 = TempFS()
        fs1sub = fs1.makeopendir("from")
        self._make_fs(fs1sub)            
        utils.movedir((fs1, "from"), (fs2, "copy"))
        self.assert_(not fs1.exists("from"))      
        self._check_fs(fs2.opendir("copy"))
        
    def test_movedir_root(self):
        """Test movedir to root dir"""        
        fs1 = MemoryFS()
        fs2 = MemoryFS()
        fs1sub = fs1.makeopendir("from")
        self._make_fs(fs1sub)            
        utils.movedir((fs1, "from"), fs2)
        self.assert_(not fs1.exists("from"))     
        self._check_fs(fs2)

        fs1 = TempFS()
        fs2 = TempFS()
        fs1sub = fs1.makeopendir("from")
        self._make_fs(fs1sub)            
        utils.movedir((fs1, "from"), fs2)
        self.assert_(not fs1.exists("from"))        
        self._check_fs(fs2)
    
if __name__ == "__main__":
    
    def _make_fs(fs):
        fs.setcontents("f1", "file 1")
        fs.setcontents("f2", "file 2")
        fs.setcontents("f3", "file 3")
        fs.makedir("foo/bar", recursive=True)
        fs.setcontents("foo/bar/fruit", "apple")
    
    fs1 = TempFS()
    fs2 = TempFS()
    fs1sub = fs1.makeopendir("from")
    _make_fs(fs1sub)            
    utils.movedir((fs1, "from"), fs2)
    #self.assert_(not fs1.exists("from"))        
    #self._check_fs(fs2)