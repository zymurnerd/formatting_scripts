import os

class Stream( file ):

    """Implements methods to open and move through a data stream.
    @param name - String path of file name
    @param mode - String mode of stream
    @returns a handle to the stream
    """

    #-----------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """Constructor."""
        super( Stream, self).__init__( *args, **kwargs )
        self.seek(0,2)
        self.file_size = self.tell()
        self.seek(0,0)

    #-----------------------------------------------------------------
    def is_eof( self ):
        """Check of EOF.
        @returns True if the read index is at the end of the stream.

        This method checks the read position and compares it to the
        file size to determine if it is at the end of the file.
        """
        return( self.tell() == self.file_size )

    #-----------------------------------------------------------------
    def seek_to( self, record ):
        """Go to the end of the record.
        @param record - Record object
        
        This method takes in the current record object, and then moves
        the read index to the end of the record.
        """
        self.seek( record.offset+record.length, 0 )

def main():
    """Entry point of the module.

    This method is an entry point to the module, and should only be used
    for testing.
    """
    pass
if __name__ == '__main__':
    main()