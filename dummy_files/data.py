import json
import os
import re
import sqlite3
import time

class DataManager( object ):

    """Implements methods to create and manage sqlite tables."""

    #-----------------------------------------------------------------
    def __init__( self, parent ):
        """Constructor"""
        self.con = None
        self.count = 0
        self.cur = None
        self._limit = 100
        self.fetched = 0
        self.paging_offset = 0
        self.parent = parent
        self.type_ids = {}
        self.table_names = []
        self.start_epoch = 0
        self.end_epoch = 0

    #-----------------------------------------------------------------
    def close( self ):
        self.con.close()

    #-----------------------------------------------------------------
    def execute(self, statement, args = ()):
        with self.con:
            self.cur.execute(statement, args)


    #-----------------------------------------------------------------
    def executemany(self, statement, buf):
        with self.con:
            self.cur.executemany(statement, buf)

    #-----------------------------------------------------------------
    def fetchall(self):
        with self.con:
            return self.cur.fetchall()

    #-----------------------------------------------------------------
    def fetchone(self):
        with self.con:
            return self.cur.fetchone()

    #-----------------------------------------------------------------
    def fetch_many(self, size=None):
        with self.con:
            if size is None:
                return self.cur.fetchmany()
            else:
                return self.cur.fetchmany(size)

    #-----------------------------------------------------------------
    def open( self, name ):
        """Open an sqlite database.
        @param name - String of the name of the database.

        This method opens the specified database, and if it
        doesn't exist it is created.
        """
        self.con = sqlite3.connect(name)
        self.cur = self.con.cursor()

    #-----------------------------------------------------------------
    def open_temp(self):
        """Open a temporary sqlite database.

        This method opens a temporary database.
        """
        self.con = sqlite3.connect(':memory:')
        self.cur = self.con.cursor()

    #-----------------------------------------------------------------
    def get_paging_offset(self):
        return self.paging_offset

    #-----------------------------------------------------------------
    def get_type_ids(self):
        identifiers = open('config\identifiers_type.json', 'r')
        decoded_id = json.load(identifiers)
        identifiers.close()
        with self.con:
            self.cur.execute("SELECT type, id FROM type_unique")
            rows = self.cur.fetchall()
            for row in rows:
                type_id = row[0] + '/' + str(row[1])
                if type_id in decoded_id:
                    self.type_ids[type_id] = decoded_id[type_id]
                else:
                    self.type_ids[type_id] = {'data_type':'NONE', 'name':type_id}

    #-----------------------------------------------------------------
    def get_page_size(self):
        return self._limit

    #-----------------------------------------------------------------
    def get_times(self):
        with self.con:

            self.cur.execute("SELECT epoch FROM packet ORDER BY epoch")
            rows = self._get_data(10)
            list = [ value for value in rows if value[0] != 0]
            while list == [] and rows != []:
                rows = self._get_data(10)
                list = [ value for value in rows if value[0] != 0]
            if list == []:
                raise Exception("Error getting capture file timestamps")
            self.start_epoch = list[0][0]
            self.cur.execute("SELECT MAX(epoch) FROM packet")
            rows = self.cur.fetchone()
            self.end_epoch = rows[0]

    #-----------------------------------------------------------------
    def get_checked_data(self, start, end, checked, count = False):
        if len(checked) > 1000:
            return [], [], len(checked)
        state = ''
        json_data = open('config\identifiers_name.json', 'r')
        decoded_names = json.load(json_data)
        json_data.close()
        type_str = ''
        for type in checked:
            if type in decoded_names:
                type_id = decoded_names[type]['type_id']
                type_str = type_str + self._type_convert(type_id) + 'OR'
            else:
                type_str = type_str + self._type_convert(type) + 'OR'
        type_str = type_str[0:-2]
        type_str = "(" + type_str + ")"
        if count == True:
            self.count = 0
            cmd = """SELECT COUNT (*)
                  FROM packet
                  WHERE %s
                  AND (epoch >= %s and epoch <= %s)""" % (type_str, str(start), str(end) )
            state = 'getting_count'
            self.update_progress(state)
            self._run_cmd(cmd)
            with self.con:
                self.count = self.cur.fetchone()[0]
        if self.paging_offset > self.count:
            self.paging_offset = self.count
        if self._limit is None:
            cmd = """SELECT *
                FROM packet
                WHERE %s
                AND (epoch >= %s and epoch <= %s)
                ORDER BY offset""" % (type_str, str(start), str(end) )
        else:
            cmd = """SELECT *
                FROM packet
                WHERE %s
                AND (epoch >= %d and epoch <= %d)
                ORDER BY epoch, prec
                LIMIT %d
                OFFSET %d""" % (type_str, start, end, self._limit, self.paging_offset)
        state = 'requesting_returns'
        self.update_progress(state)
        self._run_cmd(cmd)
        columns = self._get_columns()
        data = []
        state = 'fetching_results'
        data = self._get_data(self._limit)
        self.paging_offset += len(data)
        if self.paging_offset > self.count:
            self.paging_offset = self.count
        state = 'complete'
        self.update_progress(state)
        return columns, data

    #-----------------------------------------------------------------
    def get_count(self):
        return self.count

    #-----------------------------------------------------------------
    def get_data(self, start, end, count = False):
        state = ''
        json_data = open('config\identifiers_name.json', 'r')
        decoded_names = json.load(json_data)
        json_data.close()
        type_str = ''
        if count == True:
            cmd = """SELECT COUNT (*)
                  FROM packet
                  WHERE epoch >= %d
                  AND epoch <= %d""" % (start, end )
            state = 'fetching'
            self._run_cmd(cmd)
            with self.con:
                self.count = self.cur.fetchone()[0]
        cmd = """SELECT *
            FROM packet
            WHERE epoch >= %d
            AND epoch <= %d
            ORDER BY offset
            LIMIT %d
            OFFSET %d""" % (start, end, self._limit, self.paging_offset )
        self._run_cmd(cmd)
        columns = self._get_columns()
        data = []
        state = 'fetching_results'
        data = self._get_data(self._limit)
        self.paging_offset += len(data)
        if self.paging_offset > self.count:
            self.paging_offset = self.count
        state = 'complete'
        self.update_progress(state)
        return columns, data

    #-----------------------------------------------------------------
    def _get_columns(self):
        columns = list(map(lambda x: x[0], self.cur.description))
        columns.remove('row_id')
        columns.append('data')
        columns.insert(2,'iso')
        columns.insert(0, 'name')
        return columns

    #-----------------------------------------------------------------
    def _type_convert(self, type):
        parts = type.split('/')
        str = "(type=='%s' AND id==%s)" % (parts[0], parts[1])
        return str

    #-----------------------------------------------------------------
    def _run_cmd( self, cmd ):
        with self.con:
            return self.cur.execute(cmd)

    #-----------------------------------------------------------------
    def _get_data(self, size = None):
        with self.con:
            if size is not None:
                return self.cur.fetchmany(size)
            else:
                return self.cur.fetchall()

    #-----------------------------------------------------------------
    def set_offset(self, offset):
        self.paging_offset = offset

    #-----------------------------------------------------------------
    def set_page_size(self, limit):
        self._limit = limit

    #-----------------------------------------------------------------
    def sanitize(self, arg):
        """sanatize stub"""
        return arg

    #-----------------------------------------------------------------
    def update_progress(self, state):
        return self.parent.fetching_progress(self.fetched, self.count, state)

def main():
    """Module entry point.

    This method is an entry point to the module, and should only be
    used for testing.
    """

if __name__ == '__main__':
    main()

