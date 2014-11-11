import cookielib
import gc
import json
import logging
import mimetypes
import os
import requests
import stream
import sys
import urllib
import urllib2

log = logging.getLogger(__name__)

class Server(object):
    def __init__(self, parent):
        self.observer = parent.observer
        self.cookie_jar = None
        self.complete = 0
        self.total = 0
        self.name = ''
        self.dbi_url = 'http://xdcs.aviation.garmin.com/app/dbi.php'
        self.fsi_url = 'http://xdcs.aviation.garmin.com/app/fsi.php'

    def download_file(self, id, file_name):
        #-------------------------------------------------------------
        # initialize variables
        #-------------------------------------------------------------
        chunk_size = 8388608
        offset = 0

        #-------------------------------------------------------------
        # get file size
        #-------------------------------------------------------------
        node = self.GET_node(id)
        file_size_idx = node['payload']['fields'].index('file_size')
        file_size = node['payload']['values'][file_size_idx]

        #-------------------------------------------------------------
        # open new local file
        #-------------------------------------------------------------
        f = open(file_name, 'wb')

        #-------------------------------------------------------------
        # is the file smaller than 8 MB?
        #-------------------------------------------------------------
        if file_size < chunk_size:
            chunk_size = file_size
        
        #-------------------------------------------------------------
        # set the key value pairs for the request
        #-------------------------------------------------------------
        while offset < file_size:
            urn = 'id=' + str(id) + '&offset=' + str(offset) + '&length=' + str(chunk_size)
            req = self.fsi_url + '?' + urn
            response = self.cookie_jar.opener.open(req)
            f.write(response.read(chunk_size))
            if offset + chunk_size > file_size:
                chunk_size = file_size - offset
            offset += chunk_size
            self.update_progress(offset, file_size)
            self.observer.signal_event('download_progress')
        f.close()

    def GET_http(self, values):
        urn = urllib.urlencode(values)
        req = self.dbi_url + '?' + urn
        response = self.cookie_jar.opener.open(req)
        return response

    def GET_bind(self, key, value):
        values = {'action' : 'bind',
                  'key' : key,
                  'value' : value}
        urn = urllib.urlencode(values)
        req = self.dbi_url + '?' + urn
        response = self.cookie_jar.opener.open(req)
        json_data = response.read()
        decoded = json.loads(json_data)
        return decoded

    def GET_unbind(self, key):
        values = {'action' : 'unbind',
                  'key' : key}
        urn = urllib.urlencode(values)
        req = self.dbi_url + '?' + urn
        response = self.cookie_jar.opener.open(req)
        json_data = response.read()
        decoded = json.loads(json_data)
        return decoded

    def GET_bound(self):
        values = {'action' : 'bound'}
        urn = urllib.urlencode(values)
        req = self.dbi_url + '?' + urn
        response = self.cookie_jar.opener.open(req)
        json_data = response.read()
        decoded = json.loads(json_data)
        return decoded

    def GET_index(self, id=None):
        values = {'action' : 'index'}
        if id is not None:
            values['id'] = id
        urn = urllib.urlencode(values)
        req = self.dbi_url + '?' + urn
        response = self.cookie_jar.opener.open(req)
        json_data = response.read()
        decoded = json.loads(json_data)
        return decoded

    def GET_node(self, id):
        values = {'action' : 'node',
                  'id' : id}
        urn = urllib.urlencode(values)
        req = self.dbi_url + '?' + urn
        response = self.cookie_jar.opener.open(req)
        json_data = response.read()
        decoded = json.loads(json_data)
        return decoded

    def GET_type(self, id):
        values = {'action' : 'type',
                  'id' : id}
        urn = urllib.urlencode(values)
        req = self.dbi_url + '?' + urn
        response = self.cookie_jar.opener.open(req)
        json_data = response.read()
        decoded = json.loads(json_data)
        return decoded

    def POST_insert(self, data):
        data_encoded = json.dumps(data)
        values = {'action' : 'insert'}
        headers = {'Content-Type':'application/json',
                   'Content-Length':len(data_encoded)}
        urn = urllib.urlencode(values)
        req = urllib2.Request(self.dbi_url + '?' + urn, data_encoded, headers)
        response = self.cookie_jar.opener.open(req)
        json_data = response.read()
        decoded = json.loads(json_data)
        return decoded

    def POST_update(self, data):
        data_encoded = json.dumps(data)
        values = {'action' : 'update'}
        headers = {'Content-Type':'application/json',
                   'Content-Length':len(data_encoded)}
        urn = urllib.urlencode(values)
        req = urllib2.Request(self.dbi_url + '?' + urn, data_encoded, headers)
        response = self.cookie_jar.opener.open(req)
        json_data = response.read()
        decoded = json.loads(json_data)
        return decoded

    def POST_delete(self, data):
        data_endoded = json.dumps(data)
        values = {'action' : 'delete'}
        headers = {'Content-Type':'application/json',
                   'Content-Length':len(data_encoded)}
        urn = urllib.urlencode(values)
        req = urllib2.Request(self.dbi_url + '?' + urn, data_encoded, headers)
        response = self.cookie_jar.opener.open(req)
        json_data = response.read()
        decoded = json.loads(json_data)
        return decoded

    def get_group(self, id=None):
        return self.GET_index(id)

    def login(self, name):
        self.name = name
        #-------------------------------------------------------------
        # create cookie jar
        #-------------------------------------------------------------
        self.cookie_jar = XDCSCookieJar()

        ret_val = self.GET_bind('user', self.name)
        if ret_val['status'] != 0:
            log.error("Error registering user. Status: %d" % decoded['status'])
            raise Exception

        ret_val = self.GET_bound()
        if 'user' not in ret_val['payload']:
            log.error("Payload error. User not bound.")
            raise Exception
        if self.name not in ret_val['payload']['user']:
            log.error("Binding error. User not bound.")
            raise Exception

        log.debug("Return value from login GET request is: %d" % ret_val['status'])

    def upload_file(self, parent_id, file, name='', description=''):
        #-------------------------------------------------------------
        # initialize variables
        #-------------------------------------------------------------
        values = {}
        offset = 0
        json_data = {}

        #-------------------------------------------------------------
        # open file stream
        #-------------------------------------------------------------
        strm = stream.Stream(file, 'rb')

        #-------------------------------------------------------------
        # build json_data for creating source
        #-------------------------------------------------------------
        json_data['context'] = {'action':'insert'}
        json_data['payload'] = {'name': name,
                                'description' : description,
                                'parent_id' : parent_id
                                }
        json_data['layout'] = 'hash'
        
        #-------------------------------------------------------------
        # send insert POST
        #-------------------------------------------------------------
        response = self.POST_insert(json_data)

        #-------------------------------------------------------------
        # check insert POST response
        #-------------------------------------------------------------
        if response['status'] != 0:
            raise Exception("Error creating insert source. Status: %d", (response['status']))

        #-------------------------------------------------------------
        # get MIME file type and encoding
        #-------------------------------------------------------------
        mime = mimetypes.MimeTypes()
        url = urllib.pathname2url(strm.name)
        mime_type = mime.guess_type(url)
        type = mime_type[0]
        encoding = mime_type[1]

        #-------------------------------------------------------------
        # if not type is returned, then treat as generic binary
        #-------------------------------------------------------------
        if type is None:
            type = 'application/octet-stream'

        #-------------------------------------------------------------
        # build json data for file upload
        #-------------------------------------------------------------
        time = int( os.path.getmtime(strm.name) )
        values['id'] = response['payload']['id']
        values['name'] = os.path.basename(strm.name)
        values['type'] = type
        values['time_ms'] = time
        values['size'] = strm.file_size
        values['offset'] = offset
        values['length'] = 8388608

        #-------------------------------------------------------------
        # check if file is smaller than 8 MB upload maximum
        #-------------------------------------------------------------
        if strm.file_size < 8388608:
            values['length'] = strm.file_size

        #-------------------------------------------------------------
        # upload file
        #-------------------------------------------------------------
        while offset < values['size']:
            #---------------------------------------------------------
            # build POST for uploading file chunk
            #---------------------------------------------------------
            urn = urllib.urlencode(values)
            req = urllib2.Request(self.fsi_url + '?' + urn, str(strm.read(values['length'])))

            #---------------------------------------------------------
            # send request
            #---------------------------------------------------------
            response = self.cookie_jar.opener.open(req)
            json_data = response.read()
            decoded = json.loads(json_data)

            #---------------------------------------------------------
            # check response status
            #---------------------------------------------------------
            if decoded['status'] != 0:
                raise Exception("Error uploading. Status: %d" % (decoded['status']))

            #---------------------------------------------------------
            # update offset for next chunk
            #---------------------------------------------------------
            offset += values['length']
            values['offset'] = offset
            bytes_left = values['size'] - offset
            if bytes_left < 8388608:
                values['length'] = bytes_left
            self.update_progress(offset, values['size'])
            self.observer.signal_event('upload_progress')

        #-------------------------------------------------------------
        # check for compelete download
        #-------------------------------------------------------------
        if offset != strm.file_size:
            strm.close()
            raise Exception("Error uploading. %d bytes uploaded." % (offset))
        #-------------------------------------------------------------
        # close file stream
        #-------------------------------------------------------------
        strm.close()

    #-----------------------------------------------------------------
    def update_progress(self, complete, total):
        self.complete = complete
        self.total = total

    def get_progress(self):
        return {'complete':self.complete,
                'total': self.total}


class XDCSCookieJar(object):
    def __init__(self):
        self.cj = cookielib.CookieJar()
        cp = urllib2.HTTPCookieProcessor(self.cj)
        self.opener = urllib2.build_opener(cp)


def main():
    import logging .handlers
    log_name = 'server_log.txt'
    # Set up a specific logger with our desired output level
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)

    # Add the log message handler to the logger
    handler = logging.handlers.RotatingFileHandler(log_name,
                                                    maxBytes=10737418240,
                                                    backupCount=5,
                                                    )
    handler.setLevel(logging.DEBUG)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    console.setFormatter(formatter)

    log.addHandler(handler)
    log.addHandler(console)

    log.debug("Logging debug level enabled!")

    s = Server(None)
    s.login('wesley')

    return 0

if __name__ == "__main__":
    sys.exit( main() )