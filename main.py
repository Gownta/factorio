import argparse
import json
import sys
from pathlib import Path

import Blueprint as B
import serde


def get_args(argv):
    parser = argparse.ArgumentParser(description="factorio utilities")
    return parser.parse_args(argv)


def main(argv):
    pb = Path("public_blueprints")
    b = pb / "wolfers1337_recycling.txt"
    #for b in pb.iterdir():
    j = serde.deserialize(b.read_text())
    #print(json.dumps(j, indent=4))
    print(B.parse(j))
    #B.Blueprint.from_json(j)


if __name__ == "__main__":
    main(sys.argv[1:])
