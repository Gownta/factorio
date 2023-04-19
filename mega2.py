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

# dict-like class
class E:
  pass

def go(prints):
  # Make Blueprints out of the json input
  z = mkInputBlueprints(prints)

  # Train configuration
  z.nwagons = 6  # wagons per 2xloco
  z.ntrains = 2  # number of chained loco-wagons
  z.line = 'W'  # name of the train line

  color = mkC(0.6, 0.3, 0, 0.5)
  g = mkGreen(z)

  ret = []
  for item in ['iron-ore', 'copper-ore', 'coal', 'stone']:
    for isOdd in [True, False]:
      q = mkDrill(z, item, isOdd).toJson(
              f'mining.{mkOddOrEvenName(isOdd)}',
              icons.mkIcons('electric-mining-drill', item))
      ret.append(q)

  ret.append(mkPumpsAsJson(z, 14))
  ret.append(mkOilRefinery(z).toJson(
    "oil refinery",
    icons.mkIcons('oil-refinery')
  ))

  return ret + [
    mkWait('wait', color, [], z).toJson('wait', icons.mkIcons('train-stop')),
    mkFuel(z).toJson('fuel', icons.mkIcons('nuclear-fuel')),
    g.toJson('electronic-circuit', icons.mkIcons('electronic-circuit')),
    z.stop.head.toJson('oops', icons.mkIcons('rail')),
  ]


# return a named-dict class
# everything except Q rails are aligned
#
# ret.{stop, fuel, wait}.{head, station, loco1, loco2, wagon, tail}
# ret.fuel.roboport
# ret.locos  two locomotives and a wagon
# ret.q{1-4}  quadrant rails
# ret.mine.{head, drill, tail}
# ret.pump.d14
# ret.oil.refinery
# ret.unit.[product]  how to make a thing
def mkInputBlueprints(prints):
  ret = E()

  for p in prints:
    b = p["blueprint"]

    # The name is the label or the first icon
    if "label" in b:
      name = b["label"]
    else:
      item = b["icons"][0]["signal"]["name"]
      name = 'unit.' + item.replace('-', '_')

    # Find where the thing belongs in ret
    path = name.split('.')
    obj = ret
    for i in range(len(path) - 1):
      if not hasattr(obj, path[i]):
        setattr(obj, path[i], E())
      obj = getattr(obj, path[i])

    # Make the blueprint
    b = Blueprint(b["entities"], b.get("tiles", []))

    # Align the blueprint
    # All blueprints, except specials, align by buffer chests
    if len(path) > 1 and name not in ['pump.d14']:
      es = list(filter(lambda e: e.name == "logistic-chest-buffer", b.entities))
      bb = BoundingBox(es)
      b.shift(int(0.5 - bb.minx), int(0.5 - bb.miny))
    elif name == "locos":
      bb1 = BoundingBox(list(filter(lambda e: e.name == "train-stop", b.entities)))
      bb2 = BoundingBox(list(filter(lambda e: e.name == "train-stop", ret.stop.station.entities)))
      b.shift(int(bb2.minx - bb1.minx), int(bb2.miny - bb1.miny))

    # remove the buffer chests
    b.calve(lambda e: e.name == "logistic-chest-buffer")

    setattr(obj, path[-1], b)

  return ret


def mkDouble(wagon1, wagon2):
  ret = wagon2.dupe()
  ret.shift(0, 7)
  ret.merge(wagon1.dupe())
  return ret


def mkStop(
    name, color, sched,
    locos, nwagons, ntrains,
    head, station, loco2, loco1, double, tail,
    hasTrain=True):
  ret = Blueprint([])
  totalShift = 0

  # Make the non-train/track factory parts
  def aug(part, size=1):
    nonlocal ret
    nonlocal totalShift
    ret.merge(part.dupe())
    ret.shift(0, -7 * size)
    totalShift += -7 * size

  aug(head)
  totalShift = 0
  aug(station)
  aug(loco2)
  for i in range(ntrains - 1):
    for j in range(nwagons // 2):
      aug(double, 2)
    aug(loco1)
    aug(loco2)
  for i in range(nwagons // 2):
    aug(double, 2)
  powerLights = double.dupe().calve(lambda e: e.name in [
      "substation", "medium-electric-pole", "small-lamp"])
  aug(powerLights, 2)
  aug(tail)
  ret.shift(0, -totalShift)

  # add in the train/tracks
  if hasTrain:
    loco = locos.dupe()
    wagon = loco.calve(lambda e: e.name == "cargo-wagon")
    for i in range(nwagons):
      loco.merge(wagon.dupe())
      wagon.shift(0, 7)
    caravan = Blueprint([])
    for i in range(ntrains):
      caravan.merge(loco.dupe())
      loco.shift(0, 7 * (2 + nwagons))
    caravan.calve(lambda e: e.name == "train-stop")
    ret.merge(caravan)

  # train/stop name, color, schedule
  for e in ret.entities:
    if e.name == "locomotive":
      e.repr["color"] = color
      e.repr["schedule"] = sched
    elif e.name == "train-stop":
      e.repr["color"] = color
      e.repr["station"] = name


  # join rails
  augJoinRails(ret)

  # power happens later

  return ret
  

def mkWait(name, color, sched, z, hasTrain=True):
  double = mkDouble(z.wait.wagon, z.wait.wagon)
  stop = mkStop(
      name, color, sched,
      z.locos, z.nwagons, z.ntrains,
      z.wait.head, z.wait.station, z.wait.loco2, z.wait.loco1, double, z.wait.tail,
      hasTrain)
  augPower(stop)
  return stop


def mkFuel(z, fuelActivationLimit=111):
  name = mkFuelDropoffName(z)
  color = colorFor("nuclear-fuel")
  sched = None
  double = mkDouble(z.fuel.wagon, z.fuel.wagon)
  stop = mkStop(
      name, color, sched,
      z.locos, z.nwagons, z.ntrains,
      z.fuel.head, z.fuel.station, z.fuel.loco2, z.fuel.loco1, double, z.fuel.tail,
      hasTrain=False)
  for e in stop.entities:
    if e.name == 'train-stop':
      e.repr["control_behavior"]["circuit_condition"]["constant"] = fuelActivationLimit
  for i in range(2, (2 + z.nwagons) * z.ntrains, 5):
    robo = z.fuel.roboport.dupe()
    robo.shift(0, 7 * i)
    stop.merge(robo)
  augPower(stop)
  return stop


def mkSignalBP(x, y, dir_0IsNorth):
  return Blueprint([{
    "entity_number": 1,
    "name": "rail-signal",
    "position": {
      "x": x,
      "y": y,
    },
    "direction": ((4 + dir_0IsNorth) % 8),
  }])

def mkNWRailBp(x, y):
  return Blueprint([{
    "entity_number": 1,
    "name": "straight-rail",
    "position": {
      "x": x,
      "y": y,
    },
  }])

def augExit(z, b, xmin):
  # find the lowest and highest ew rails
  rails = [e for e in b.entities if (
      e.name == 'straight-rail' and (e.repr.get('direction', 0) % 4 == 2))]
  miny = min(rails, key=lambda e: e.y)
  maxy = max(rails, key=lambda e: e.y)
  targetx = max(e.x for e in rails if e.y == miny.y)

  q4 = z.q4.dupe()
  inrail = max(q4.entities, key=lambda e: e.y)

  def addSigRail(y_offset=0):
    nonlocal b
    nonlocal q4

    sigrail = min(q4.entities, key=lambda e: e.y)
    sig = mkSignalBP(sigrail.x + 1.5, sigrail.y + 0.5 + y_offset, 0)
    b.merge(sig.dupe())

  q4.shift(int(targetx - inrail.x), int(miny.y - inrail.y))
  b.merge(q4.dupe())
  addSigRail(-2)
  addSigRail(10)
  q4.shift(int(targetx - inrail.x), int(maxy.y - inrail.y))
  b.merge(q4.dupe())
  addSigRail()

  q1 = z.q1.dupe()
  # the height difference between the inline and the outline is 32m+6
  # the height of q4+q1 is H
  H = 24
  required = maxy.y - miny.y + H
  extra = (32 + 6 - (required % 32)) % 32
  toprail = min(q1.entities, key=lambda e: e.y)
  q1.shift(int(targetx - toprail.x), int(miny.y - H - extra - toprail.y))
  b.merge(q1.dupe())

  # extend the top line all the way to xmin
  toprailb = q1.calve(lambda e: e.y == toprail.y)
  toprailb.shift(int(xmin - toprail.x), 0)
  b.merge(toprailb.dupe())


def augJoinRails(b):
  # find all straight rails, by direction
  h = defaultdict(list)
  for e in b.entities:
    if e.name == 'straight-rail':
      d = e.repr.get('direction', 0) % 4
      h[d].append(e)
  # find equal x on direction 0, equal y on direction 2
  ns = defaultdict(list)
  for r in h[0]:
    ns[r.x].append(r)
  for rails in ns.values():
    if rails:
      ys = set([e.y for e in rails])
      miny = min(rails, key=lambda e: e.y)
      maxy = max(rails, key=lambda e: e.y)
      d = Blueprint([miny])
      d = d.dupe()
      d.shift(0, 2)
      while d.entities[0].y < maxy.y:
        if d.entities[0].y not in ys:
          b.merge(d.dupe())
        d.shift(0, 2)
  ew = defaultdict(list)
  for r in h[2]:
    ew[r.y].append(r)
  for rails in ew.values():
    if rails:
      xs = set([e.x for e in rails])
      minx = min(rails, key=lambda e: e.x)
      maxx = max(rails, key=lambda e: e.x)
      d = Blueprint([minx])
      d = d.dupe()
      d.shift(2, 0)
      while d.entities[0].x < maxx.x:
        if d.entities[0].x not in xs:
          b.merge(d.dupe())
        d.shift(2, 0)


def augPower(b, allCols=False):
  powers = [e for e in b.entities if e.name in [
      "big-electric-pole", "substation", "medium-electric-pole"]]

  columns = defaultdict(list)
  rows = defaultdict(list)
  for p in powers:
    columns[p.x].append(p)
    if p.name == 'big-electric-pole' or allCols:
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

# created aligned in and out curves
# return [inCurve, outCurve]
def mkInOut(b, z, inFromTop=True):
  rails = sorted(
      [e for e in b.entities if e.name == 'straight-rail'],
      key=lambda e: e.y)
  top = rails[0]
  bottom = rails[-1]

  if inFromTop:
    inCurve = z.q1
    outCurve = z.q3
    inRail = top
    outRail = bottom
  else:
    inCurve = z.q4
    outCurve = z.q2
    inRail = bottom
    outRail = top

  def linkage(c):
    for e in c.entities:
      if e.name == 'straight-rail':
        if e.repr.get('direction', 0) % 4 == 0:
          return e

  def align(c, r):
    l = linkage(c)
    c.shift(int(r.x - l.x), int(r.y - l.y))

  inB = inCurve.dupe()
  align(inB, inRail)
  outB = outCurve.dupe()
  align(outB, outRail)
  return [inB, outB]


# rotate a line, align by the power poles
def rotLine(b):
  bb1 = BoundingBox([e for e in b.entities if e.name == "big-electric-pole"])
  b.rotate(4)
  bb2 = BoundingBox([e for e in b.entities if e.name == "big-electric-pole"])
  b.shift(int(bb1.minx - bb2.minx), int(bb1.miny - bb2.miny))

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


def colorFor(item):
  if item == "electronic-circuit":
    #return mkC(0.25, 1, 0, 0.75)
    return mkC(0, .75, 0, .75)
  if item == "advanced-circuit":
    return mkC(1, 0, 0.1, .75)
  if item == "processing-unit":
    return mkC(0, 0, 1, 0)
  if item == "steel-plate":
    return mkC(.75, .75, 1, .1)
  if item == "plastic-bar":
    return mkC(.75, .25, .75, .1)
  if item == "nuclear-fuel":
    return mkC(.75, 1, 0, .5)
  if item in ["iron-ore", "copper-ore", "coal", "stone"]:
    return mkC(.5, .5, .5, .5)
  if item == 'crude-oil':
    return mkC(0, 0, 0, .6)
  if item == 'heavy-oil':
    return mkC(.75, .25, 0, .7)
  if item == 'light-oil':
    return mkC(1, .75, 0, .5)
  if item == 'petroleum-gas':
    return mkC(.25, .25, .25, .7)
  return mkC(1, 0, 0, 1)

# even cars or odd cars
def mkOddOrEvenName(odd):
  if odd:
    return "a"
  return "b"

def mkFuelDropoffName(z):
  return mkStopName(z.line, "nuclear-fuel", special="refueling")

def mkStationDropoffWaitName(z, item, odd=True):
  return mkStopName(z.line, item, special=f"{mkOddOrEvenName(odd)}.dropoff.wait")

def mkStationDropoffName(z, item, odd=True):
  return mkStopName(z.line, item, special=f"{mkOddOrEvenName(odd)}.dropoff")

def mkDropoffStops(z, item, odd=True):
  return [
    (mkStationDropoffWaitName(z, item, odd), mkSchedCondTime(2)),
    (mkStationDropoffName(z, item, odd), mkSchedCondItemZero(item)),
  ]

def mkStopName(line, name, number=None, i1=None, i2=None, o1=None, o2=None, special=None):
  def item(i):
    if i is None:
      return '_'
    return f'[item={i}]'

  if special is None:
    spec = f"({item(i1)}{item(i2)})\u2192({item(o1)}{item(o2)})"
  else:
    spec = special

  if number is None:
    num = ''
  else:
    num = f" p{number:0=2}"

  return f"{line} {item(name)}{num} {spec}"


def mkSchedCondTime(time_s):
  return [
      {
          "compare_type": "or",
          "type": "time",
          "ticks": 60 * time_s,
      },
  ]

def mkSchedCondInactivity():
  return [
      {
          "compare_type": "or",
          "type": "inactivity",
          "ticks": 60,
      },
  ]

def mkSchedCondItemZero(item):
  return [
      {
          "compare_type": "or",
          "type": "item_count",
          "condition": {
            "first_signal": {
              "type": "item",
              "name": item,
            },
            "constant": 0,
            "comparator": "=",
          },
      },
  ]


# [(stop, cond)] -> a schedule
def mkSched(stopAndConds):
  stops = []
  def mkTWC(stop, cond):
    return {
        "station": stop,
        "wait_conditions": cond,
    }
  return [mkTWC(stop, cond) for stop, cond in stopAndConds]


# [(waiting blueprint, how many)] -> (blueprint of input, q2 curve towards rest, width)
def mkIngress(z, waitings):
  nwaitings = sum(n for w, n in waitings)

  fueling = mkFuel(z, nwaitings * 2 * z.ntrains * 6)
  [i, o] = mkInOut(fueling, z, inFromTop=False)

  shift = 0
  def augh(_b, space):
    nonlocal i
    nonlocal o
    nonlocal shift
    nonlocal ret

    b = _b.dupe()
    b.merge(i.dupe())
    b.merge(o.dupe())
    b.shift(shift, 0)
    ret.merge(b)
    shift += space

  ret = Blueprint([])
  augh(fueling, 8)
  for w, n in waitings:
    for j in range(n):
      augh(w, 4)
  augJoinRails(ret)

  egress = o.dupe()
  egress.shift(shift - 4, 0)
  return (ret, egress, shift)


# -> (blueprint, width)
# note: return width includes initial shift
def mkGroup(z, b, n, shift, gap, inFromTop):
  ret = Blueprint([])

  def augh(_b):
    nonlocal shift
    nonlocal gap
    nonlocal ret
    nonlocal z

    b = _b.dupe()
    b.shift(shift, 0)
    if inFromTop:
      rotLine(b)
    ret.merge(b)
    [i, o] = mkInOut(b, z, inFromTop)
    ret.merge(i.dupe())
    ret.merge(o.dupe())
    shift += gap

  for j in range(n):
    augh(b)
  return (ret, shift)



def mkGreen(z, n=1):
  item = "electronic-circuit"
  color = colorFor(item)

  stationWait = mkStopName(z.line, item, n, special="ingress")
  stationSmelt = mkStopName(z.line, item, n, "copper-ore", "iron-ore", "copper-plate", "iron-plate")
  stationGreen = mkStopName(z.line, item, n, "copper-plate", "iron-plate", item, None)

  stopsAndConds = mkMiningStopsFor(z, 'copper-ore', 'iron-ore', 3) + [
    (stationWait, mkSchedCondTime(2)),
    (stationSmelt, mkSchedCondTime(350)),
    (stationGreen, mkSchedCondTime(170)),
  ] + mkDropoffStops(z, item, odd=True)
  sched = mkSched(stopsAndConds)

  waiting1 = mkWait(stationWait, color, sched, z)
  waiting2 = mkWait(stationWait, color, sched, z, hasTrain=False)
  smelting = mkStop(
      stationSmelt, color, sched,
      z.locos, z.nwagons, z.ntrains,
      z.stop.head, z.stop.station, z.stop.loco2, z.stop.loco1,
      mkDouble(z.unit.copper_plate, z.unit.iron_plate),
      z.stop.tail)
  green = mkStop(
      stationGreen, color, sched,
      z.locos, z.nwagons, z.ntrains,
      z.stop.head, z.stop.station, z.stop.loco2, z.stop.loco1,
      z.unit.electronic_circuit,
      z.stop.tail)

  # TODO reduce to 5 total
  [b1, egress, shift] = mkIngress(z, [(waiting1, 3), (waiting2, 3)])
  shift += 22
  [b2, shift] = mkGroup(z, smelting, 7, shift, 20, inFromTop=True)
  shift += 6
  [b3, shift] = mkGroup(z, green, 3, shift, 20, inFromTop=False)
  ret = b2
  ret.merge(b3)
  ret.merge(egress)
  augExit(z, ret, min(e.x for e in b1.entities))
  augJoinRails(ret)
  ret.merge(b1)
  augPower(ret)

  return ret


def mkMiningStopsFor(z, itemA, itemB, nPairs=3):
  indices = z.ntrains * z.nwagons // (2 * nPairs)
  cond = mkSchedCondInactivity()
  ret = []
  for i in range(indices):
    ret.append((mkDrillStationName(z, itemA, True, i + 1), mkSchedCondInactivity()))
  for i in range(indices):
    ret.append((mkDrillStationName(z, itemB, False, i + 1), mkSchedCondInactivity()))
  return ret


def mkDrillStationName(z, item, isOdd, idx):
  return mkStopName(z.line, item, special=f"mining.{mkOddOrEvenName(isOdd)}.{idx:0=2}")

def renameStops(b, name, item):
  for e in b.entities:
    if e.name == "train-stop":
      e.repr["station"] = name
      e.repr["color"] = colorFor(item)
      e.repr["manual_trains_limit"] = 1

# isOdd: A or B cars
# nPairs: how many pairs of cars to fill at once (keep in mind, only one of the pair is filled)
def mkDrill(z, item, isOdd=True, nPairs=3):
  # ensure that 2*nPairs divides z.nwagons
  assert(z.nwagons % (2 * nPairs) == 0)
  sets = z.nwagons // (2 * nPairs)

  head = z.mine.head.dupe()
  drill = z.mine.drill.dupe()
  tail = z.mine.tail.dupe()

  # add the drill bits
  ret = Blueprint([])
  if not isOdd:
    drill.shift(0, 7)
  for i in range(nPairs):
    drill.shift(0, 14)
    ret.merge(drill.dupe())

  # add the tail, far away
  # basically, two train lengths: a train at stop #2 has to be able to have a full train
  # coming to stop #1; but stop #2 is near the head of the train
  tail.shift(0, 2 * 7 * z.ntrains * (2 + z.nwagons))
  ret.merge(tail.dupe())

  # add the stations
  idx = 1
  for i in range(z.ntrains):
    for j in range(sets):
      if i == z.ntrains - 1 and j == sets:
        # add rail signal just above the station
        station = [e for e in head if e.name == 'train-stop'][0]
        sig = mkSignalBP(station.x - 0.5, station.y - 2.5, 0)
        ret.merge(sig)
      renameStops(head, mkDrillStationName(z, item, isOdd, idx), item)
      idx += 1
      ret.merge(head.dupe())
      head.shift(0, -14 * nPairs)
    head.shift(0, -14)

  # flesh out the system
  augJoinRails(ret)
  augPower(ret)

  return ret

# have 3 drills side by side all set up with in and out lines
def mkDrillSet(z, item, isOdd=True, nRows=3, nPairs=3):
  pass


def mkLiquidStationName(z, item, isPickup, idx):
  def mkPickupName(isPickup):
    if isPickup:
      return "pickup"
    return "dropoff"
  return mkStopName(z.line, item, special=f"liquid.{mkPickupName(isPickup)}.{idx:0=2}")

def mkOilRefinery(z, maxRefineries=13):
  ret = Blueprint([])

  # remove all but the rails and station and signals
  head = z.stop.station.dupe()
  head.calve(lambda e: e.name not in ['straight-rail', 'train-stop'])
  tail = z.stop.loco1.dupe() # it's just a rail and signal
  tail.calve(lambda e: e.name not in ['straight-rail', 'rail-signal'])

  lines = [
    # item, isPickup, xoffset, yoffset
    ('crude-oil', False, 0, 0),
    ('light-oil', True, 18, 0),
    ('petroleum-gas', True, 24, 2),
    ('heavy-oil', True, 30, 0),
  ]

  assert(2 * maxRefineries >= z.nwagons)

  # add train stops
  for item, isPickup, xoffset, yoffset in lines:
    for j in range(z.ntrains):
      stop = head.dupe()
      renameStops(stop, mkLiquidStationName(z, item, isPickup, j + 1), item)
      stop.shift(xoffset, yoffset - 7 * j * (2 + z.nwagons))
      for e in stop.entities:
        if e.name == 'train-stop' and False:
          print(f'Train stop at {e.x} {e.y}')
      ret.merge(stop.dupe())
    for offset in [
        -7 * ((z.ntrains - 1) * (2 + z.nwagons) + 1),
        7 * (z.ntrains * (2 + z.nwagons) + 1),
        14 * (z.ntrains * (2 + z.nwagons) + 1),
    ]:
      sig = tail.dupe()
      sig.shift(xoffset, yoffset + offset)
      ret.merge(sig.dupe())

  # add refineries
  for j in range(z.nwagons // 2):
    oil = z.oil.refinery.dupe()
    oil.shift(0, 14 * (j + 1))
    ret.merge(oil.dupe())

  # add rails
  for e in ret.entities:
    if e.name == 'rail-signal':
      if int(e.y + 0.5) % 2 == 0:
        qy = e.y - 0.5
      else:
        qy = e.y + 0.5
      ret.merge(mkNWRailBp(e.x - 1.5, qy))

  augPower(ret, True)
  augJoinRails(ret)

  # add landfill
  def halfRoundUp(v):
    return int(v + 1)
  def halfRoundDown(v):
    return int(v - 1)

  bb = BoundingBox(ret.entities)
  minx = halfRoundDown(bb.minx)
  maxx = halfRoundUp(bb.maxx)
  miny = halfRoundDown(bb.miny)
  maxy = halfRoundUp(bb.maxy)
  for i in range(minx, maxx):
    for j in range(miny, maxy):
      ret.tiles.append({
        "position": {
          "x": i + 0.5,
          "y": j + 0.5,
        },
        "name": "landfill",
      })

  return ret


def mkPumpsAsJson(z, gap):
  pump = z.pump.d14.dupe()
  pump.tiles = pump.tiles[0:2]
  pump.entities = [pump.entities[0]]

  ret = Blueprint([])
  for i in range(z.nwagons):
    ret.merge(pump.dupe())
    pump.shift(gap, 0)

  j = ret.toJson(
    f'pump{gap}',
    icons.mkIcons('offshore-pump')
  )
  j["snap-to-grid"] = {
    "x": 2,
    "y": 2,
  }
  j["absolute-snapping"] = True
  j["position-relative-to-grid"] = {
    "x": 1,
    "y": 0,
  }
  return j

    


        







