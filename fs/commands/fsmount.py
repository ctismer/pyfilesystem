#!/usr/bin/env python

from fs.opener import opener
from fs.commands.runner import Command
import sys
import platform
import os
import os.path
import time

platform = platform.system()

class FSMount(Command):
    
    if platform == "Windows":
        usage = """fsmount [OPTIONS]... [FS] [DRIVE LETTER]
or fsmount -u [DRIVER LETTER]
Mounts a filesystem on a drive letter"""
    else:
        usage = """fsmount [OPTIONS]... [FS] [SYSTEM PATH]
or fsmount -u [SYSTEM PATH]
Mounts a file system on a system path"""

    version = "1.0"
    
    def get_optparse(self):
        optparse = super(FSMount, self).get_optparse()        
        optparse.add_option('-f', '--foreground', dest='foreground', action="store_true", default=False,
                            help="run the mount process in the foreground", metavar="FOREGROUND")
        optparse.add_option('-u', '--unmount', dest='unmount', action="store_true", default=False,
                            help="unmount path", metavar="UNMOUNT")
        optparse.add_option('-n', '--nocache', dest='nocache', action="store_true", default=False,
                            help="do not cache network filesystems", metavar="NOCACHE")
        
        return optparse
    
    
    def do_run(self, options, args):
        
        windows = platform == "Windows"
                
        if options.unmount:
            try:                
                mount_path = args[0][:1]
            except IndexError:
                self.error('Mount path required\n')
                return 1
            if windows:
                from fs.expose import dokan
                mount_path = mount_path[:1].upper()
                dokan.unmount(mount_path)
                self.output('unmounting %s:' % mount_path, True)
                return
            else:
                from fs.expose import fuse
                fuse.unmount(mount_path)
                self.output('unmounting %s' % mount_path, True)
                return
        
        try:
            fs_url = args[0]
        except IndexError:
            self.error('FS path required\n')
            return 1
        
        try:                
            mount_path = args[1]
        except IndexError:
            if windows:
                mount_path = mount_path[:1].upper()
                self.error('Drive letter required')
            else:
                self.error('Mount path required\n')
            return 1                    
            
        fs, path = self.open_fs(fs_url, create_dir=True)
        if path:
            if not fs.isdir(path):
                self.error('%s is not a directory on %s' % (fs_url. fs))
                return 1
            fs = fs.opendir(path)
            path = '/'
        if not options.nocache:
            fs.cache_hint(True)
        if windows and not os.path.exists(mount_path):
           os.makedirs(mount_path)
           
        if windows:
            from fs.expose import dokan
            
            if len(mount_path) > 1:
                self.error('Driver letter should be one character')
                return 1
            
            self.output("Mounting %s on %s:" % (fs, mount_path), True)
            flags = dokan.DOKAN_OPTION_REMOVABLE
            if options.debug:
                flags |= dokan.DOKAN_OPTION_DEBUG | dokan.DOKAN_OPTION_STDERR
                
            mp = dokan.mount(fs,
                             mount_path,
                             numthreads=5,
                             foreground=options.foreground,
                             flags=flags,
                             volname=str(fs))
            
        else:
            from fs.expose import fuse
            self.output("Mounting %s on %s" % (fs, mount_path), True)
            
            if options.foreground:                                            
                fuse_process = fuse.mount(fs,
                                          mount_path,                                          
                                          foreground=True)                                                    
            else:
                if not os.fork():                
                    mp = fuse.mount(fs,
                                    mount_path,
                                    foreground=True)
                

    
def run():
    return FSMount().run()
    
if __name__ == "__main__":
    sys.exit(run())
        