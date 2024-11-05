import base64
import json
import os
import zlib

def deserialize(s):
  return json.loads(zlib.decompress(base64.b64decode(s[1:])))

def serialize(b):
  j = json.dumps(b)
  b = bytes(j, 'ascii')
  c = zlib.compress(b, level=9)
  e = base64.b64encode(c)
  z = b'0' + e
  return z

io_data_dir = 'data'

def read(filename):
  with open(os.path.join(io_data_dir, filename), 'r') as f:
    return f.read().strip()

def write(filename, content):
  with open(os.path.join(io_data_dir, filename), 'w') as f:
    f.write(content)

def load(name):
  infile = f"hashed_{name}_in.txt"
  human_infile = f"{name}_in.txt"
  result = deserialize(read(infile))
  pretty = json.dumps(result, indent=2)
  write(human_infile, pretty)
  return result

def dump(name, j):
  outfile = f"hashed_{name}_out.txt"
  human_outfile = f"{name}_out.txt"
  pretty = json.dumps(j, indent=2)
  write(human_outfile, pretty)
  write(outfile, str(serialize(j))[2:-1] + '\n')
