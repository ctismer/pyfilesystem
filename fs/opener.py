import sys
from fs.osfs import OSFS
from fs.path import pathsplit, basename, join, iswildcard
import os
import os.path
import re
from urlparse import urlparse

class OpenerError(Exception):
    pass

class NoOpenerError(OpenerError):
    pass

class MissingParameterError(OpenerError):
    pass


def _expand_syspath(path):
    if path is None:
        return path      
    path = os.path.expanduser(os.path.expandvars(path))    
    path = os.path.normpath(os.path.abspath(path))    
    if sys.platform == "win32":
        if not path.startswith("\\\\?\\"):
            path = u"\\\\?\\" + root_path
        #  If it points at the root of a drive, it needs a trailing slash.
        if len(path) == 6:
            path = path + "\\"

    return path

    
def _parse_credentials(url):        
    username = None
    password = None
    if '@' in url:
        credentials, url = url.split('@', 1)
        if ':' in credentials:
            username, password = credentials.split(':', 1)
        else:
            username = credentials
    return username, password, url

def _parse_name(fs_name):
    if '#' in fs_name:
        fs_name, fs_name_params = fs_name.split('#', 1)
        return fs_name, fs_name_params
    else:
        return fs_name, None


class OpenerRegistry(object):
     

    re_fs_url = re.compile(r'''
^
(.*?)
:\/\/

(?:
|(.*?)
|(?:(.*?)!)
)

(?:
!(.*?)$
)*$
''', re.VERBOSE)
        
    
     
    def __init__(self, openers=[]):
        self.registry = {}
        self.openers = {}
        self.default_opener = 'osfs'
        for opener in openers:
            self.add(opener)
    
    @classmethod
    def split_segments(self, fs_url):        
        match = self.re_fs_url.match(fs_url)        
        return match        
    
    def get_opener(self, name):
        if name not in self.registry:
            raise NoOpenerError("No opener for %s" % name)
        index = self.registry[name]
        return self.openers[index]        
    
    def add(self, opener):
        index = len(self.openers)
        self.openers[index] = opener
        for name in opener.names:
            self.registry[name] = index
    
    def parse(self, fs_url, default_fs_name=None, open_dir=True, writeable=False, create_dir=False):
                   
        orig_url = fs_url     
        match = self.split_segments(fs_url)
        
        if match:
            fs_name, fs_url, _, path = match.groups()
            path = path or ''
            fs_url = fs_url or ''
            if ':' in fs_name:
                fs_name, sub_protocol = fs_name.split(':', 1)
                fs_url = '%s://%s' % (sub_protocol, fs_url)
            if '!' in path:
                paths = path.split('!')
                path = paths.pop()
                fs_url = '%s!%s' % (fs_url, '!'.join(paths))
            
            fs_name = fs_name or self.default_opener                                                                    
                
        else:
            fs_name = default_fs_name or self.default_opener
            fs_url = _expand_syspath(fs_url) 
            path = ''           
    
        fs_name,  fs_name_params = _parse_name(fs_name)        
        opener = self.get_opener(fs_name)
        
        if fs_url is None:
            raise OpenerError("Unable to parse '%s'" % orig_url)        
        
        fs, fs_path = opener.get_fs(self, fs_name, fs_name_params, fs_url, writeable, create_dir)
        
        if fs_path and iswildcard(fs_path):
            pathname, resourcename = pathsplit(fs_path or '')
            if pathname:
                fs = fs.opendir(pathname)
            return fs, resourcename
                            
        fs_path = join(fs_path, path)
                
        pathname, resourcename = pathsplit(fs_path or '')        
        if pathname and resourcename:
            fs = fs.opendir(pathname)
            fs_path = resourcename
                               
        return fs, fs_path        

    def open(self, fs_url, mode='rb'):
        """Opens a file from a given FS url
        
        If you intend to do a lot of file manipulation, it would likely be more
        efficient to do it directly through the an FS instance (from `parse` or 
        `opendir`). This method is fine for one-offs though.
        
        :param fs_url: a FS URL, e.g. ftp://ftp.mozilla.org/README
        :param mode: mode to open file file
        :rtype: a file        
        
        """        
        
        writeable = 'w' in mode or 'a' in mode or '+' in mode
        fs, path = self.parse(fs_url, writeable=writeable)                
        file_object = fs.open(path, mode)
        
        # If we just return the file, the fs goes out of scope and closes,
        # which may make the file unusable. To get around this, we store a
        # reference in the file object to the FS, and patch the file's
        # close method to also close the FS.    
        close = file_object.close
        def replace_close():
            fs.close()
            return close()
        file_object.close = replace_close
                    
        return file_object
    
    def getcontents(self, fs_url):
        """Gets the contents from a given FS url (if it references a file)
        
        :param fs_url: a FS URL e.g. ftp://ftp.mozilla.org/README
        
        """
        
        fs, path = self.parse(fs_url)
        return fs.getcontents(path)
    
    def opendir(self, fs_url, writeable=True, create_dir=False):
        """Opens an FS object from an FS URL
        
        :param fs_url: an FS URL e.g. ftp://ftp.mozilla.org
        :param writeable: set to True (the default) if the FS must be writeable
        :param create_dir: create the directory references by the FS URL, if
        it doesn't already exist          
        
        """
        fs, path = self.parse(fs_url, writable=writeable, create_dir=create_dir)
        if path:
            return fs.opendir(path)
        return fs
                    

class Opener(object):
    
    @classmethod
    def get_param(cls, params, name, default=None):        
        try:
            param = params.pop(0)
        except IndexError:
            if default is not None:
                return default
            raise MissingParameterError(error_msg)
        return param


class OSFSOpener(Opener):
    names = ['osfs', 'file']    
    desc = "OS filesystem opener, works with any valid system path. This is the default opener and will be used if you don't indicate which opener to use."
    
    @classmethod
    def get_fs(cls, registry, fs_name, fs_name_params, fs_path, writeable, create_dir):
        from fs.osfs import OSFS 
                                            
        path = _expand_syspath(fs_path)
        if create_dir and not os.path.exists(path):
            from fs.osfs import _os_makedirs                    
            _os_makedirs(path)            
        dirname, resourcename = pathsplit(fs_path)
        osfs = OSFS(dirname)
        return osfs, resourcename                
        
class ZipOpener(Opener):
    names = ['zip', 'zip64']    
    desc = "Opens zip files. Use zip64 for > 2 megabyte zip files, if you have a 64 bit processor.\ne.g. zip://myzip"
    
    @classmethod
    def get_fs(cls, registry, fs_name, fs_name_params, fs_path, writeable, create_dir):
                                
        append_zip = fs_name_params == 'add'     
                
        zip_fs, zip_path = registry.parse(fs_path)
        if zip_path is None:
            raise OpenerError('File required for zip opener')
        if zip_fs.exists(zip_path):
            if writeable:
                open_mode = 'r+b'
            else:
                open_mode = 'rb'
        else:
            open_mode = 'w+'
        zip_file = zip_fs.open(zip_path, mode=open_mode)                                            
                        
        username, password, fs_path = _parse_credentials(fs_path)
        
        from fs.zipfs import ZipFS
        if zip_file is None:            
            zip_file = fs_path
        
        mode = 'r'
        if writeable:
            mode = 'a'            
         
        allow_zip_64 = fs_name.endswith('64')                
              
        zipfs = ZipFS(zip_file, mode=mode, allow_zip_64=allow_zip_64)
        return zipfs, None
    

class RPCOpener(Opener):
    names = ['rpc']
    desc = "An opener for filesystems server over RPC (see the fsserve command). e.g. rpc://127.0.0.1"

    @classmethod
    def get_fs(cls, registry, fs_name, fs_name_params, fs_path, writeable, create_dir):
        from fs.rpcfs import RPCFS             
        username, password, fs_path = _parse_credentials(fs_path)
        if not fs_path.startswith('http://'):
            fs_path = 'http://' + fs_path
            
        scheme, netloc, path, params, query, fragment = urlparse(fs_path)

        rpcfs = RPCFS('%s://%s' % (scheme, netloc))
        
        if create_dir and path:
            rpcfs.makedir(path, recursive=True, allow_recreate=True)
                
        return rpcfs, path or None


class FTPOpener(Opener):
    names = ['ftp']
    desc = "An opener for FTP (File Transfer Protocl) servers. e.g. ftp://ftp.mozilla.org"
    
    @classmethod
    def get_fs(cls, registry, fs_name, fs_name_params, fs_path, writeable, create_dir):
        from fs.ftpfs import FTPFS
        username, password, fs_path = _parse_credentials(fs_path)
                                        
        scheme, netloc, path, params, query, fragment = urlparse(fs_path)
        if not scheme:
            fs_path = 'ftp://' + fs_path
        scheme, netloc, path, params, query, fragment = urlparse(fs_path)
                 
        dirpath, resourcepath = pathsplit(path)        
        url = netloc
                                
        ftpfs = FTPFS(url, user=username or '', passwd=password or '')
        ftpfs.cache_hint(True)
        
        if create_dir and path:
            ftpfs.makedir(path, recursive=True, allow_recreate=True)
        
        if dirpath:
            ftpfs = ftpfs.opendir(dirpath)
                            
        if not resourcepath:
            return ftpfs, None        
        else:
            return ftpfs, resourcepath


class SFTPOpener(Opener):
    names = ['sftp']
    desc = "An opener for SFTP (Secure File Transfer Protocol) servers"

    @classmethod
    def get_fs(cls, registry, fs_name, fs_name_params, fs_path,  writeable, create_dir):
        username, password, fs_path = _parse_credentials(fs_path)        
        
        from fs.sftpfs import SFTPFS
        
        credentials = {}
        if username is not None:
            credentials['username'] = username
        if password is not None:
            credentials['password'] = password
            
        if '/' in fs_path:
            addr, fs_path = fs_path.split('/', 1)
        else:
            addr = fs_path
            fs_path = '/'
            
        fs_path, resourcename = pathsplit(fs_path)
            
        host = addr
        port = None
        if ':' in host:
            addr, port = host.rsplit(':', 1)
            try:
                port = int(port)
            except ValueError:
                pass
            else:
                host = (addr, port)
            
        if create_dir:
            sftpfs = SFTPFS(host, root_path='/', **credentials)
            if not sftpfs._transport.is_authenticated():
                sftpfs.close()
                raise OpenerError('SFTP requires authentication')
            sftpfs = sfspfs.makeopendir(fs_path)
            return sftpfs, None
                
        sftpfs = SFTPFS(host, root_path=fs_path, **credentials)
        if not sftpfs._transport.is_authenticated():
            sftpfs.close()
            raise OpenerError('SFTP requires authentication')            
            
        return sftpfs, resourcename
    
    
class MemOpener(Opener):
    names = ['mem', 'ram']
    desc = """Creates an in-memory filesystem (very fast but contents will disappear on exit)."""
    
    @classmethod
    def get_fs(cls, registry, fs_name, fs_name_params, fs_path,  writeable, create_dir):
        from fs.memoryfs import MemoryFS
        memfs = MemoryFS()
        if create_dir:
            memfs = memfs.makeopendir(fs_path)
        return memfs, None
    
    
class DebugOpener(Opener):
    names = ['debug']
    desc = "For developer -- adds debugging information to output. To use prepend an exisiting opener with debug: e.g debug:ftp://ftp.mozilla.org"
    
    @classmethod
    def get_fs(cls, registry, fs_name, fs_name_params, fs_path,  writeable, create_dir):
        from fs.wrapfs.debugfs import DebugFS
        if fs_path:
            fs, path = registry.parse(fs_path, writeable=writeable, create=create_dir)
            return DebugFS(fs, verbose=False), None     
        if fs_name_params == 'ram':
            from fs.memoryfs import MemoryFS
            return DebugFS(MemoryFS(), identifier=fs_name_params, verbose=False), None
        else:
            from fs.tempfs import TempFS
            return DebugFS(TempFS(), identifier=fs_name_params, verbose=False), None
    
    
class TempOpener(Opener):
    names = ['temp']
    desc = "Creates a temporary filesystem, that is erased on exit."
    
    @classmethod
    def get_fs(cls, registry, fs_name, fs_name_params, fs_path,  writeable, create_dir):
        from fs.tempfs import TempFS        
        fs = TempFS(identifier=fs_name_params)
        if create_dir and fs_path:
            fs = fs.makeopendir(fs_path)
            fs_path = pathsplit(fs_path)
        return fs, fs_path
    

opener = OpenerRegistry([OSFSOpener,
                         ZipOpener,
                         RPCOpener,
                         FTPOpener,
                         SFTPOpener,
                         MemOpener,
                         DebugOpener,
                         TempOpener,
                         ])
   

def main():
    
    #fs, path = opener.parse('zip:zip://~/zips.zip!t.zip!')
    fs, path = opener.parse('ftp://releases.mozilla.org/welcome.msg')
    
    print fs, path
    
if __name__ == "__main__":
       
    main()             
    