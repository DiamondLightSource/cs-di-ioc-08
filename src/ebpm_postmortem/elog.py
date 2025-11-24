# Code for posting to elog

import http.client
import mimetypes

host = "rdb.pri.diamond.ac.uk"


def post_multipart(host, selector, fields, files):
    """
    Post fields and files to an http host as multipart/form-data.
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be
    uploaded as files.
    Return the server's response page.
    """
    content_type, body = encode_multipart_formdata(fields, files)
    h = http.client.HTTPConnection(host)
    h.putrequest("POST", selector)
    h.putheader("content-type", content_type)
    h.putheader("content-length", str(len(body)))
    h.endheaders()
    h.send(body)
    resp = h.getresponse()
    return resp.read()


def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be
    uploaded as files
    Return (content_type, body) ready for http.client.HTTP instance
    """
    boundary = "----------ThIs_Is_tHe_bouNdaRY_$"
    crlf = b"\r\n"
    parts = []
    for key, value in fields:
        parts.append("--" + boundary)
        parts.append(f'Content-Disposition: form-data; name="{key}"')
        parts.append("")
        parts.append(value)
    for key, filename, value in files:
        parts.append("--" + boundary)
        parts.append(
            f'Content-Disposition: form-data; name="{key}"; filename="{filename}"'
        )
        parts.append(f"Content-Type: {get_content_type(filename)}")
        parts.append("")
        parts.append(value)
    parts.append("--" + boundary + "--")
    parts.append("")

    # Convert all parts to bytes
    parts = [
        p if isinstance(p, (bytes, bytearray)) else str(p).encode("utf-8")
        for p in parts
    ]
    body = crlf.join(parts)
    content_type = f"multipart/form-data; boundary={boundary}"
    return content_type, body


def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or "application/octet-stream"


def entry(title, content, png, debug):
    if debug:
        selector = "/devl/php/elog/cs_logaddfromioc.php"
    else:
        selector = "/php/elog/cs_logaddfromioc.php"
    fields = [("txtLOGBOOKID", "OPR"), ("txtCONTENT", content), ("txtTITLE", title)]
    files = (("userfile1", "postmortem.png", png),)
    try:
        post_multipart(host, selector, fields, files)
    except Exception:
        import traceback

        traceback.print_exc()
