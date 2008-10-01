#!/bin/env python2.4

import datetime
import httplib
import mimetypes

host = 'rdb.pri.diamond.ac.uk'

def encode_multipart_formdata(fields):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

def post_multipart(host, selector, fields):
    """
    Post fields to an http host as multipart/form-data.
    fields is a sequence of (name, value) elements for regular form fields.
    Return the server's response page.
    """
    content_type, body = encode_multipart_formdata(fields)
    h = httplib.HTTP(host)
    h.putrequest('POST', selector)
    h.putheader('content-type', content_type)
    h.putheader('content-length', str(len(body)))
    h.endheaders()
    h.send(body)
    errcode, errmsg, headers = h.getreply()
    return h.file.read()

def entry(title, content, debug = False):
    if debug:
        selector = '/devl/php/elog/cs_logaddfromioc.php'
    else:
        selector = '/php/elog/cs_logaddfromioc.php'
    args = dict(txtLOGBOOKID = 'OPR', txtCONTENT = content, txtTITLE = title)
    fields = args.items()
    try:
        post_multipart(host, selector, args.items())
    except:
        import traceback
        traceback.print_exc()
    
    
if __name__ == '__main__':
    message = '''This is a test with some new lines
        and some more text
        and some stuff.

        THE END'''
        
    entry('Testing', 'One line message', True)
