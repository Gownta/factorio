from blueprint import Blueprint, BoundingBox
from collections import namedtuple, defaultdict
import icons
import itertools
import math

'''
Blueprint Object:

 - Blueprint(jsonEntities, jsonTiles)
 - merge(other)
 - dupe()
 - calve(pred)
 - shift(dx, dy)
 - toJson(label, icons)
 - .entities
 - .tiles

 NOTE: put schedules on the locomotives

Entity Object:

 - .name
 - .number
 - .x
 - .y
 - .repr for everything else

Bounding Box Object:

 - BoundingBox(entities)
 - can be used as a predicate, such as in calve
 - .{min, max}{x, y}
'''

def go(prints):
  '''
  [0]: locomotive, train stop, chain signal; plus a positional rail signal
  [1]: wagon
  [2]: electric pole for start and end of line
  [3]: furnace array for iron processing
  [4]: nuclear refueling setup
  [5, 6, 7, 8]: Q1 Q2 Q3 Q4 rails
  [9]: green chip double
  [10]: copper cable single
  '''
  locomotiveStop = Blueprint(prints[0]["blueprint"]["entities"])
  wagon = Blueprint(prints[1]["blueprint"]["entities"])
  power = Blueprint(prints[2]["blueprint"]["entities"])
  refueling = Blueprint(prints[4]["blueprint"]["entities"])
  quadrants = [Blueprint(prints[i]["blueprint"]["entities"]) for i in range(5, 9)]

  # How many 2+8 trains to link together
  k = 2

  stop = mkStop(locomotiveStop, wagon, power, k)
  units = mkUnits(prints)

  def mkGreen():
    nonlocal refueling
    nonlocal quadrants
    nonlocal k
    nonlocal stop
    nonlocal units

    w = 3

    # copper-ore/iron-ore
    # copper-plate/iron-plate
    # special double

    p1 = mkProcessor(stop, bundleProcessors(units['copper-plate'], units['iron-plate']), k)
    p2 = mkProcessor(stop, units['electronic-circuit'], k)

    seq = mkSequence(stop, refueling, w, quadrants, [
        ('p1', p1, 7),
        ('p2', p2, 3),
    ])

    # names
    nb = "electronic-circuit"
    nw = mkStopName("X", nb, 1, special="start")
    n1 = mkStopName("X", nb, 1, "copper-ore", "iron-ore", "copper-plate", "iron-plate")
    n2 = mkStopName("X", nb, 1, "copper-plate", "iron-plate", nb, None)
    color = mkC(0.25, 1, 0, 0.75)
    sched = mkSched([
        (nw, 2),
        (n1, 5),
        (n2, 3),
    ])

    for e in seq.entities:
      if e.name == "locomotive":
        e.repr['color'] = color
        e.repr["schedule"] = sched
      elif e.name == "train-stop":
        e.repr['color'] = color
        if e.repr["station"] == 'p1':
          e.repr["station"] = n1
        elif e.repr["station"] == 'p2':
          e.repr["station"] = n2
        elif e.repr["station"].startswith('w'):
          e.repr["station"] = nw

    return seq

  def mkRedScience():
    nonlocal refueling
    nonlocal quadrants
    nonlocal k
    nonlocal stop
    nonlocal units

    w = 3

    # copper-ore/iron-ore
    # copper-plate/iron-plate
    # ./gear
    # ./science1

    p1 = mkProcessor(stop, bundleProcessors(units['copper-plate'], units['iron-plate']), k)
    p2 = mkProcessor(stop, bundleProcessors(units['nop'], units['iron-gear-wheel']), k)

    seq = mkSequence(stop, refueling, w, quadrants, [
        ('p1', p1, 2),
        ('p2', p2, 4),
    ])

    # names
    nb = "science-pack-1"
    nw = mkStopName("X", nb, 1, special="start")
    n1 = mkStopName("X", nb, 1, "copper-ore", "iron-ore", "copper-plate", "iron-plate")
    n2 = mkStopName("X", nb, 1, "copper-plate", "iron-plate", "copper-plate", "iron-gear-wheel")
    color = mkC(0.25, 1, 0, 0.75)
    sched = mkSched([
        (nw, 2),
        (n1, 5),
        (n2, 3),
    ])

    for e in seq.entities:
      if e.name == "locomotive":
        e.repr['color'] = color
        e.repr["schedule"] = sched
      elif e.name == "train-stop":
        e.repr['color'] = color
        if e.repr["station"] == 'p1':
          e.repr["station"] = n1
        elif e.repr["station"] == 'p2':
          e.repr["station"] = n2
        elif e.repr["station"].startswith('w'):
          e.repr["station"] = nw

    return seq

  return [
      stop.toJson('station', icons.mkIcons('train-stop')),
      mkGreen().toJson('green', icons.mkIcons('electronic-circuit')),
  ]
    

# rgba -> color dictionary
def mkC(r, g, b, a=None):
  if a is None:
    a = 0.5
  return {
    "r": r,
    "g": g,
    "b": b,
    "a": a,
  }

# [(stop, time)] -> a schedule
def mkSched(stopTimes):
  stops = []
  def mkTWC(stop, time):
    return {
        "station": stop,
        "wait_conditions": [
            {
                "compare_type": "or",
                "type": "time",
                "ticks": 60 * time,
            },
        ],
    }
  return [mkTWC(stop, time) for stop, time in stopTimes]
    

# stop name
def mkStopName(line, name, number, i1=None, i2=None, o1=None, o2=None, special=None):
  def item(i):
    if i is None:
      return '_'
    return f'[item={i}]'

  if special is None:
    spec = f"({item(i1)}{item(i2)})\u2192({item(o1)}{item(o2)})"
  else:
    spec = special

  return f"{line} {item(name)}.{number:0=2} {spec}"


def mkUnits(prints):
  def mkSmithy(ironPrint):
    ret = Blueprint(ironPrint["blueprint"]["entities"])
    for e in ret.entities:
      if e.name == "stack-filter-inserter":
        e.name = "stack-inserter"
        e.repr.pop("filters")
    return ret

  def mkNop(ironPrint):
    ret = Blueprint(ironPrint["blueprint"]["entities"])
    ret.calve(lambda e: e.name in ["electric-furnace", "stack-inserter", "stack-filter-inserter"])
    return ret

  return {
    'nop': mkNop(prints[3]),

    'iron-plate': Blueprint(prints[3]["blueprint"]["entities"]),
    'copper-plate': mkSmithy(prints[3]),
    'electronic-circuit': Blueprint(prints[9]["blueprint"]["entities"]),
  }


def testSequence(stop, refueling, w, quadrants, units):
  exampleProcessor = mkProcessor(
      stop,
      bundleProcessors(units['iron-plate'], units['iron-plate']),
      k)
  return mkSequence(stop, refueling, w, quadrants, [('boopsies', exampleProcessor, 2)])


def mkSequence(stop, refueling, w, quadrants, namedProcessorsN):
  waiting = mkWaiting(stop, refueling, w)
  waiting.rotate(4)
  augAccess(waiting, quadrants, True)
  ret = waiting

  rotate = False
  for name, _p, n in namedProcessorsN:
    p = _p.dupe()
    renameStops(p, name)
    rot = rotate
    if rotate:
      p.rotate(4)
    rotate = not rotate

    bb = BoundingBox(p.entities)
    width = bb.maxx - bb.minx + 3
    if width % 2 == 1:
      width += 1

    segment = Blueprint([])
    for i in range(n):
      segment.merge(p.dupe())
      p.shift(width, 0)
    augAccess(segment, quadrants, rot)
    augConnection(segment, ret, rot)
    ret.merge(segment)

  augPower(ret)
  augOutline(ret, quadrants)

  return ret

def augOutline(b, quadrants):
  # build the outlines
  rails = sorted(
      [e for e in b.entities if e.name == 'straight-rail'],
      key=lambda e: (e.x, e.y))
  west = rails[0]
  east = rails[-1]

  # the west inline will be aligned with ElderAxe's RHD chunk-snapped power pole
  # the east outline needs to go to the same x line, but be 32c+6 lesser y
  # need to add a rail-signal
  rs = Blueprint([{
    "entity_number": 1,
    "name": "rail-signal",
    "position": {
        "x": east.x - 0.5,
        "y": east.y + 1.5,
    },
  }])
  b.merge(rs)

  q4 = quadrants[3].dupe()
  q4in = sorted(q4.entities, key=lambda e: e.x)[0]
  q4.shift(east.x - q4in.x, east.y - q4in.y)
  b.merge(q4.dupe())

  bb = BoundingBox(b.entities)
  top = bb.miny - 3
  outy = west.y - 6
  while outy > top:
    outy -= 32

  q1 = quadrants[0].dupe()
  q1in = sorted(q1.entities, key=lambda e: e.y)[-1]
  q1out = sorted(q1.entities, key=lambda e: e.x)[0]
  q4out = sorted(q4.entities, key=lambda e: e.y)[0]
  dx = q4out.x - q1in.x
  dy = outy - q1out.y
  q1.shift(dx, dy)
  b.merge(q1.dupe())

  # stretch the rails out
  ew = q1.dupe().calve(lambda e: e.y == outy)
  while ew.entities[0].x >= west.x:
    b.merge(ew.dupe())
    ew.shift(-2, 0)
  ns = q1.dupe().calve(lambda e: e.x == q4out.x)
  while ns.entities[0].y < q4out.y:
    b.merge(ns.dupe())
    ns.shift(0, 2)


# default: in from top left, out on bottom right
# if isRot: in from the bottom left, out the top right
def augAccess(lines, quadrants, isRot):
  rails = [e for e in lines.entities if e.name == 'straight-rail']
  bb = BoundingBox(rails)
  tops = [e for e in rails if e.y == bb.miny]
  bottoms = [e for e in rails if e.y == bb.maxy]

  if isRot:
    qs = [quadrants[1], quadrants[3]]
  else:
    qs = [quadrants[0], quadrants[2]]
  for t in tops:
    q = qs[0].dupe()
    bb = BoundingBox(q.entities)
    bottomRail = [e for e in q.entities if e.y == bb.maxy][0]
    q.shift(t.x - bottomRail.x, t.y - bottomRail.y)
    lines.merge(q)
  for b in bottoms:
    q = qs[1].dupe()
    bb = BoundingBox(q.entities)
    topRail = [e for e in q.entities if e.y == bb.miny][0]
    q.shift(b.x - topRail.x, b.y - topRail.y)
    lines.merge(q)

  # connect all the tops and bottoms
  bb = BoundingBox(lines.entities)
  tops = sorted(
      [e for e in lines.entities if e.y == bb.miny],
      key=lambda e: e.x)
  extra = Blueprint([tops[0]]).dupe()
  for i in range(int(tops[-1].x - tops[0].x) // 2 - 1):
    extra.shift(2, 0)
    lines.merge(extra.dupe())

  bottoms = sorted(
      [e for e in lines.entities if e.y == bb.maxy],
      key=lambda e: e.x)
  extra = Blueprint([bottoms[0]]).dupe()
  for i in range(int(bottoms[-1].x - bottoms[0].x) // 2 - 1):
    extra.shift(2, 0)
    lines.merge(extra.dupe())
  

# move additional to be near main and have connections
def augConnection(additional, main, isRot):
  mainRails = [e for e in main.entities if e.name == 'straight-rail']
  bb1 = BoundingBox(mainRails)
  addRails = [e for e in additional.entities if e.name == 'straight-rail']
  bb2 = BoundingBox(addRails)

  if not isRot:
    # connect top rails
    connectorMain = [e for e in mainRails if e.x == bb1.maxx and e.y == bb1.miny][0]
    connectorAdd = [e for e in addRails if e.x == bb2.minx and e.y == bb2.miny][0]
  else:
    connectorMain = [e for e in mainRails if e.x == bb1.maxx and e.y == bb1.maxy][0]
    connectorAdd = [e for e in addRails if e.x == bb2.minx and e.y == bb2.maxy][0]

  extraSep = (
      min(BoundingBox(main.entities).maxx - bb1.maxx, 0) +
      min(bb2.minx - BoundingBox(additional.entities).minx, 0))
  if extraSep % 2 == 1:
    extraSep += 1

  tx = connectorMain.x + extraSep + 2
  ty = connectorMain.y
  dx = tx - connectorAdd.x
  dy = ty - connectorAdd.y

  additional.shift(dx, dy)

  extraRail = Blueprint([connectorMain]).dupe()
  for i in range(int(extraSep / 2)):
    extraRail.shift(2, 0)
    additional.merge(extraRail.dupe())


def augPower(sequence):
  powers = [e for e in sequence.entities if e.name in ["big-electric-pole", "substation"]]

  columns = defaultdict(list)
  rows = defaultdict(list)
  for p in powers:
    columns[p.x].append(p)
    if p.name == 'big-electric-pole':
      rows[p.y].append(p)

  def connectLines(p1, p2):
    p1.repr.setdefault("neighbours", []).append(p2.number)
    p2.repr.setdefault("neighbours", []).append(p1.number)

    conns1 = p1.repr.setdefault("connections", {"1": {"red": [], "green": []}})
    conns2 = p2.repr.setdefault("connections", {"1": {"red": [], "green": []}})
    conns1["1"].setdefault("red", []).append({"entity_id": p2.number})
    conns1["1"].setdefault("green", []).append({"entity_id": p2.number})
    conns2["1"].setdefault("red", []).append({"entity_id": p1.number})
    conns2["1"].setdefault("green", []).append({"entity_id": p1.number})
    
  def pairwise(iterable):
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)

  for col in columns.values():
    col.sort(key=lambda e: e.y)
    for p1, p2 in pairwise(col):
      connectLines(p1, p2)
  for row in rows.values():
    row.sort(key=lambda e: e.x)
    for p1, p2 in pairwise(row):
      connectLines(p1, p2)

  # Connect to the elderaxe power pole in bottom left
  inRail = sorted(
      [e for e in sequence.entities if e.name == 'straight-rail'],
      key=lambda e: e.x)[0]
  pp = Blueprint([{
      "entity_number": 1,
      "name": "big-electric-pole",
      "position": {
          "x": inRail.x - 1,
          "y": inRail.y - 3,
      },
  }])
  bb = BoundingBox(powers)
  pp2 = sorted([e for e in powers if e.y == bb.maxy], key=lambda e: e.x)[0]
  connectLines(pp.entities[0], pp2)
  sequence.merge(pp)


'''
1. Extend the rail line to the correct length
2. Add rail signals
3. Add locomotives and wagons
4. Add big electric poles
'''
def mkStop(locomotiveStop, wagon, power, k):
  ret = locomotiveStop.dupe()

  # Remove the regular rail signal; keep it
  signal = ret.calve(lambda e: e.name == 'rail-signal')

  # A 2+8 train is 70 long (including 1 trailing gap)
  # A rail is 2 long
  # The stop needs 3 extra rails; 1.5 in front, 2 behind (1.5 + gap)
  numRail = len([e for e in locomotiveStop.entities if e.name == 'straight-rail'])
  numNeeded = 35 * k + 3 - numRail
  northmostRail = locomotiveStop.northwestmost('straight-rail')
  adder = Blueprint([northmostRail])
  for i in range(numNeeded):
    adder.shift(0, -2)
    ret.merge(adder.dupe())

  # We need a rail signal at the back, and beside each intermediate locomotive
  for i in range(k):
    signal.shift(0, -70)
    ret.merge(signal.dupe())

  # Add the locomotives and wagons
  loco = ret.calve(lambda e: e.name == 'locomotive')
  for i in range(k):
    ret.merge(loco.dupe())
    loco.shift(0, -7)
    ret.merge(loco.dupe())

    w = wagon.dupe()
    w.northWestTo(loco.entities[0].x, loco.entities[0].y)
    for j in range(8):
      w.shift(0, -7)
      ret.merge(w.dupe())

    loco.shift(0, -63)

  # Add power at the bottom and top of the line
  if power:
    power = power.dupe()
    powerRail = power.northwestmost('straight-rail')
    power.shift(northmostRail.x - powerRail.x, northmostRail.y - powerRail.y)
    power.calve(lambda e: e.name == 'straight-rail')
    power.shift(0, -1)
    ret.merge(power.dupe())
    power.shift(0, 70 * k + 6)
    ret.merge(power.dupe())

  return ret


def renameStops(b, nm, prev=None):
  for e in b.entities:
    if e.name == 'train-stop':
      if prev is None or e.repr["station"] == prev:
        e.repr["station"] = nm

def mkWaiting(stop, refueling, w):
  core = stop.dupe()
  poles = core.calve(lambda e: e.name == "big-electric-pole")
  assert(len(poles.entities) == 4)
  bb = BoundingBox(poles.entities)
  bb.maxx -= 1
  wpoles = poles.calve(bb)
  epoles = poles

  refueling = refueling.dupe()
  # TODO add refueling to waiting stops


  ret = wpoles
  ret.shift(2, 0) # make the poles closer
  for i in range(w):
    renameStops(core, f"w{i}")
    ret.merge(core.dupe())
    core.shift(4, 0)
    epoles.shift(4, 0)
  epoles.shift(-6, 0) # make the poles closer
  ret.merge(epoles)

  return ret

'''
Turn two single-car processing stations into one two-car
'''
def bundleProcessors(a, b):
  a = a.dupe()
  b = b.dupe()

  # align a and b
  a.northWestTo(0.5, 0.5)
  b.northWestTo(0.5, 0.5)

  b.shift(0, -7)
  a.merge(b)
  return a


'''
1. Make processing segments
2. Keep power and light pattern for loco segments
'''
def mkProcessor(stop, _double, k):
  double = _double.dupe()
  bb = BoundingBox(double.entities)
  power = double.dupe().calve(
      lambda e: e.name in ['big-electric-pole', 'substation', 'medium-electric-pole', 'small-lamp'])

  # initial shifts
  double.shift(0, -14)

  ret = Blueprint([])

  # Add all the processors
  for i in range(k):
    ret.merge(power.dupe())
    power.shift(0, -70)

    for j in range(4):
      ret.merge(double.dupe())
      double.shift(0, -14)
    double.shift(0, -14)

  # Add the train stop
  # find the middle of all beacons
  # find the beacons just east of middle
  # use them to decide the center
  beacons = sorted(
      [e for e in _double.entities if e.name == "beacon"],
      key=lambda e: e.x)
  assert(len(beacons) % 2 == 0)
  eastline = beacons[len(beacons) // 2].x
  eastBeacons = [e for e in beacons if e.x == eastline]
  bb = BoundingBox(eastBeacons)
  cx = eastline - 2.5
  cy = (bb.miny + bb.maxy) / 2
  station = [e for e in stop.entities if e.name == "train-stop"][0]
  ret.shift(station.x + 2 - cx, int(station.y - 6.5 - cy))
  ret.merge(stop.dupe())

  # fixup: if any rail-signal shares xy with any small-lamp, prioritize the former
  xys = set([e.xy for e in ret.entities if e.name == 'rail-signal'])
  ret.calve(lambda e: e.name == 'small-lamp' and e.xy in xys)

  return ret

"""
  waiting = mkWaiting(stop, refueling, w)

    

  #exampleProcessor = mkProcessor(
  #    stop,
  #    bundleProcessors(units['iron-plate'], units['iron-plate']),
  #    k)
  #
  #sequence = mkSequence(stop, refueling, w, quadrants, [('oh hai', exampleProcessor, 2)])
  
  return [
      stop.toJson('station', icons.mkIcons('train-stop')),
      waiting.toJson('waiting', icons.mkIcons('train-stop')),
      exampleProcessor.toJson('test processor', icons.mkIcons('electric-furnace')),
      sequence.toJson('test sequence', icons.mkIcons('iron-plate')),
  ]
"""
