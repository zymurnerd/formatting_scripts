import record


class Parser( object ):

    """Implements extensible methods for parser subclasses."""

    #-----------------------------------------------------------------
    def __iter__(self):
        """Iterator"""
        return self

    #-----------------------------------------------------------------
    def __init__(self, stream, type_registry):
        """Constructor
        @param stream - Stream object from data manager
        @param type_registry - Type registry database object
        """
        self.hdr_type = None
        self.stream = stream
        self.type_registry = type_registry
        self.id = None
        self.r = None
        self.type = None
        self.initialize()

    #-----------------------------------------------------------------
    def next( self ):
        """Next iteration"""
        raise NotImplementedError

    #-----------------------------------------------------------------
    def initialize( self ):
        """Initialize variables

        This method is called once at the initialization
        of the object. It can be used to initialize
        instance variables.
        """
        pass

class BlockParser( Parser ):

    """Extends Parser class to implement fixed header parser.

    This class extends the Parser class and overrides Parser
    methods to implement a fixed header parser. The parser
    can read any header that is in the type registry.
    """

    #-----------------------------------------------------------------
    def next( self ):
        """Next iteration of object.
        @returns record object of the next record in the stream

        This method is passively called with each loop over the object.
        """
        # stop iterating if we're at the end of the file
        if self.stream.is_eof():
            raise StopIteration()

        # get record object for the next record
        self.identify_record()
        del self.type

        # if not a nested packet, move to next header
        if ( self.r.frag == True ) or ( self.r.flags & 2 ) == 0:
            self.stream.seek_to( self.r )

        return self.r

    #-----------------------------------------------------------------
    def identify_record( self ):
        """Identify the type of record.

        This method reads the the next header in the data stream
        and identifies the record type.
        """
        # get type object for the header
        self.type = self.type_registry.get_type( self.hdr_type )

        # get packed header string
        data = self.stream.read( self.type.size )

        # unpack the header into a tuple
        parts = self.type.unpack( data )

        # get header id value
        id = self.type_registry.get_id( self.hdr_type, parts )

        # get size of the packet data
        size = self.type_registry.get_size(  self.hdr_type, parts )

        # TODO: DON'T LEAVE THIS HARD CODED!
        if self.hdr_type == 'hsdb':
            id = int(id) & 0x9F
            id = str(id)
        elif self.hdr_type == 'ethr':
            temp = (parts[0].encode('hex'), parts[1].encode('hex'), parts[2])
            parts = temp

        # create type id string
        type_id = self.hdr_type + '/' + str( id )

        # report the record
        self.found( type_id, size, self.type.fields, parts )

    #-----------------------------------------------------------------
    def found( self, type_id, length, fields, data ):
        """Report identified record.
        @param type_id - String of the record type id
        @param length - Integer of the record's data length
        @param fields - Dictionary of the record's fields
        @param data - Tuple of the record's header information

        This method is an interface for creating a record
        object from the header information.
        """
        # get the offset of start of packet data
        offset = self.stream.tell()

        # get the flags that correspond to the payload type
        payload_flags = self.type_registry.get_payload_flags( type_id )

        # check if length includes the header length
        hdr_flags = self.type_registry.get_hdr_flags( type_id )

        if hdr_flags & (1<<5):
            length = length - self.type.size

        # check fragmentation
        frag = self.type_registry.is_fragmented( self.hdr_type, data )

        # TODO: DON'T LEAVE THIS HARD CODED!
        if self.hdr_type == 'hsdb':
            parts = type_id.split('/')
            id = int(parts[1]) & 0x0F
            type_id = parts[0] + '/' + str( id )

        # create record object for this packet
        self.r = record.Record( type_id, offset, self.type.size, length, payload_flags, frag, fields, data )

    #-----------------------------------------------------------------
    def set_header_type( self, hdr_type ):
        """Set the header type of the parser.
        @param hdr_type - String of the header type's name.

        This method allow the header type of the parser to be
        modified.
        """
        self.hdr_type = hdr_type
