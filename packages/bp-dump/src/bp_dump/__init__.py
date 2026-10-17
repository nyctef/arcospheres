import sys
from draftsman.blueprintable import Blueprint


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: bp-dump <blueprint string>")
        return

    blueprint_string = sys.argv[1]
    blueprint = Blueprint.from_string(blueprint_string)
    print(repr(blueprint))
