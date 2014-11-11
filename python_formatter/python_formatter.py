#!/usr/bin/env python 
import os
import re
import sys


class Formatter(object):
    def __iter__(self):
        return self
        
    def __init__(self, contents):
        self.contents = contents
        self.modified = ''
        
class MethodDivider(Formatter):
    
    def next(self):
        #TODO: change to True
        ret_val = False
        self.find_method()
        
        if ret_val == False:
            raise StopIteration()
            
    def find_method(self):
       #match = re.sub( r'(?<!#-+$)(^)(?=\s+\bdef\b)', "\s{4}#-----------------------------------------------------------------\r\n", self.contents, re.M)
        match = re.search(r'(\s{4}\bdef\b)', self.contents, re.M)
        
        if match:
            self.modified = self.contents[0:match.start(1)] + "    #-----------------------------------------------------------------\n" + self.contents[match.start(1):]
            print match.start(1)
        else:
            print 'oops!'

#---------------------------------------------------------------------
def main(args):
    #----------------------------------------------------------------
    # If there isn't a directory provided from the command line,
    # then use the dummy file directory.
    # TODO: WCD
    # This is here for testing in IDE. Remove this later.
    #----------------------------------------------------------------
    if len(args) == 1:
        print "No path provided."
        print "Usage: PATH"
        working_dir = "..\\dummy_files"
    else: 
        working_dir = args[1]

    for root, dirs, files, in os.walk(working_dir):
        #-------------------------------------------------------------
        # make a backup directory
        #-------------------------------------------------------------
        if not os.path.exists(root+'\\backups'):
            os.makedirs(root+'\\backups')
            
        for file in files:
            if file.endswith('.py') or file.endswith('.pyw'):
                path = os.path.join(root, file)
                print path
                f = open(path, 'r+')
                file_contents = f.read()
                f.close()

                #create back up file
                name = path.split('.')
                backup = open(root+'\\backups\\'+os.path.basename(path)+'.bak', 'w')
                backup.write(file_contents)
                backup.close()
                
                method_formatter = MethodDivider(file_contents)
                print method_formatter.contents
                for each in method_formatter:
                    pass
                print method_formatter.modified
                f = open(path, 'w+')
                f.write(method_formatter.modified)
                f.close()
                del method_formatter

    return 0
    
if __name__ == '__main__':
    sys.exit( main(sys.argv) )