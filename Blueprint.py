
import json
import re
import serde
from dataclasses import dataclass, asdict, field, fields
from typing import Any, ClassVar, Optional, Union, List, get_origin, get_args


def maybe_optional(tp):
    if get_origin(tp) is Union:
        args = get_args(tp)
        if len(args) == 2 and args[1] is type(None):
            return args[0]
    elif get_origin(tp) is Optional:
        return get_args(tp)[0]
    return None


@dataclass
class Spec:

    @classmethod
    def parse(cls, j, depth=1):
        print(f"{' ' * (2 * (depth - 1))}Parsing {cls.__name__}")

        # Ensure there are no unfamiliar keys
        for k in j:
            assert k in cls._jmap.values(), f"{cls.__name__} has no {k}, only {list(cls._jmap.values())}. Entity is {json.dumps(j[k], indent=4)}"

        args = {}
        for field in fields(cls):
            jkey = cls._jmap[field.name]
            v = j.get(jkey, None)

            if v is None:
                assert maybe_optional(field.type), f"Class {cls.__name__} expected field {k}. Given:\n{json.dumps(j, indent=4)}"
                args[field.name] = None
                continue

            ftype = field.type
            if inner := maybe_optional(ftype):
                ftype = inner

            if get_origin(ftype) is list:
                assert isinstance(v, list), f"{cls.__name__}.{jkey} should be a list; given {json.dumps(v, indent=4)}"
                inner_type = get_args(ftype)[0]
                args[field.name] = [parse(e, inner_type, depth=depth + 1) for e in v]
            else:
                args[field.name] = parse(v, ftype, depth=depth + 1)
        return cls(**args)


##########
# Specs

@dataclass
class XY(Spec):
    x: int = 0
    y: int = 0


@dataclass
class Signal(Spec):
    name: str = ""


@dataclass
class Icon(Spec):
    signal: Signal = Signal()
    index: int = 0


@dataclass
class Entity(Spec):
    entity_number: int = 0
    name: str = ""
    position: XY = XY()
    request_filters: Optional[Any] = None


@dataclass
class Section(Spec):
    pass


@dataclass
class Parameter(Spec):
    pass


@dataclass
class X(Spec):
    pass


@dataclass
class Blueprint(Spec):
    description: Optional[str] = None
    snap_to_grid: Optional[XY] = None
    icons: List[Icon] = field(default_factory=list)
    entities: List[Entity] = field(default_factory=list)
    parameters: Optional[List[Parameter]] = None
    item: str = ""
    label: str = ""
    version: int = 0

    _inner: ClassVar[str] = "blueprint"
    _mapping: ClassVar[Any] = {"snap-to-grid": "snap_to_grid"}

    def __post_init__(self):
        assert self.item == "blueprint"
        assert self.version == 562949954928640


##########
# Post processing


Inners = {c._inner: c for c in Spec.__subclasses__() if hasattr(c, "_inner")}


def fixup_spec(spec_cls):
    j_keys = [f.name for f in fields(spec_cls)]
    j_map = {x: x for x in j_keys}
    for jk, jid in getattr(spec_cls, "_mapping", {}).items():
        j_map[jid] = jk
    spec_cls._jmap = j_map


for c in Spec.__subclasses__():
    fixup_spec(c)


##########
# parser


def parse(j, cls=None, depth=1):
    if cls is None or cls is Any or maybe_optional(cls) is Any:
        assert len(j) == 1
        inner, j = list(j.items())[0]
        cls = Inners[inner]
    if cls in [int, str]:
        ret = cls(j)
    else:
        ret = cls.parse(j, depth=depth)
    return ret





SPECSTR = """
Blueprint blueprint
    description? str
    snap-to-grid? XY
    icons?+ Icon

Icon
    signal Signal
    index int

Signal
    name str
"""

EntryPat = re.compile(r"([a-zA-Z0-9_-]+)([*+?]*) (.*)")

@dataclass
class SpecEntry:
    name: str
    cardinal: str
    type: str

    id: str = None

    def __post_init__(self):
        assert self.name
        if not self.id:
            self.id = self.name.replace("-", "_")


@dataclass
class Spec:
    name: str
    inner: str  # None if no inner
    fields: [SpecEntry]


def parse_spec(specstr):
    lines = specstr.splitlines(keepends=False)
    idx = 0

    def parse_entry(line):
        m = EntryPat.fullmatch(line)
        assert m, line
        return SpecEntry(m.group(1), m.group(2), m.group(3))

    def parse_one():
        nonlocal idx
        header = lines[idx]
        assert header, idx
        name, inner, *rest = header.split() + [None]

        idx += 1
        subs = []
        while idx < len(lines) and (line := lines[idx]) != "":
            idx += 1
            s = line.strip()
            assert line != s
            subs.append(s)

        return Spec(name, inner, [parse_entry(s) for s in subs])

    specs = {}
    while idx < len(lines):
        spec = parse_one()
        specs[spec.name] = spec
        idx += 1

    return specs

SPEC = parse_spec(SPECSTR.strip())

#print(SPEC)
