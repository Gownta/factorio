import base64
import json
import zlib


def deserialize(s):
    return json.loads(zlib.decompress(base64.b64decode(s[1:].rstrip())))


def serialize(b):
    j = json.dumps(b)
    b = bytes(j, 'ascii')
    c = zlib.compress(b, level=9)
    e = base64.b64encode(c)
    z = b'0' + e
    return z
