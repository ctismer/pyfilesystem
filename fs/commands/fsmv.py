from fs.utils import movefile, contains_files
from fs.commands import fscp
import sys

class FSMove(fscp.FScp):
    
    usage = """fsmv [OPTION]... [SOURCE] [DESTINATION]
Move files from SOURCE to DESTINATION"""
    
    def get_verb(self):
        return 'moving...'
    
    def get_action(self):        
        return movefile
    
    def post_actions(self):
        for fs, dirpath in self.root_dirs:
            if not contains_files(fs, dirpath):                
                fs.removedir(dirpath, force=True)
    
def run():
    return FSMove().run()
    
if __name__ == "__main__":
    sys.exit(run())
