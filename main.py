import argparse
import json
import sys
from pathlib import Path

import serde


def main(args):
    p = Path("ex_bp.txt")
    j = serde.deserialize(p.read_text())
    print(json.dumps(j, indent=4))

if __name__ == "__main__":
    main(sys.argv[1:])
