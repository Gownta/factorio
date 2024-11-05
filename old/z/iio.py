import os

io_data_dir = 'data'

def read(filename):
  with open(os.path.join(io_data_dir, filename), 'r') as f:
    return f.read().strip()

def write(filename, content):
  with open(os.path.join(io_data_dir, filename), 'w') as f:
    f.write(content)
