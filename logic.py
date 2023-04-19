from blueprint import Blueprint, BoundingBox
from collections import namedtuple
from copy import deepcopy
import icons
import json

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

# return a list of blueprints
def process(
    recipes, l_print, factory_print, fluid_factory_print,
    in4_print, in8_print, out4_print, out8_print, jump4_print, jump8_print):
  l_blueprint = Blueprint(l_print["entities"])
  factory_blueprint = Blueprint(factory_print["entities"])
  fluid_factory_blueprint = Blueprint(fluid_factory_print["entities"])
  in4_blueprint = Blueprint(in4_print["entities"])
  in8_blueprint = Blueprint(in8_print["entities"])
  out4_blueprint = Blueprint(out4_print["entities"])
  out8_blueprint = Blueprint(out8_print["entities"])
  jump4_blueprint = Blueprint(jump4_print["entities"])
  jump8_blueprint = Blueprint(jump8_print["entities"])

  core, pickup, dropoffs, power = divideLPrint(l_blueprint)
  f1 = divideFactoryPrint(factory_blueprint)
  factory_1, east_belt_inline, west_belt_inline, east_belt_supply, west_belt_supply, outline = f1
  factory, east_pipe_inline, west_pipe_inline, east_pipe_supply, west_pipe_supply, _ = (
      divideFactoryPrint(fluid_factory_blueprint))
  def getCenter(b):
    return [e.xy for e in b.entities if e.name.startswith("assembling")][0]
  center1 = getCenter(factory_1)
  center0 = getCenter(factory)
  dx = center0[0] - center1[0]
  dy = center0[1] - center1[1]
  for b in f1:
    b.shift(dx, dy)

  full_prints = {}
  for item, recipe in recipes.items():
    if item in [
          "rocket-control-unit",
          "advanced-circuit",
          "low-density-structure",
          "battery",
          "solar-panel",
          "processing-unit",
          "accumulator",
          "engine-unit",
          "electric-engine-unit",
          "flying-robot-frame",
          "high-tech-science-pack",
          "production-science-pack",
    ]:
      ff = mkFullFactory(
          item, recipe, recipes,
          core, pickup, dropoffs, power,
          factory,
          east_belt_inline, west_belt_inline, east_pipe_inline, west_pipe_inline,
          east_belt_supply, west_belt_supply, east_pipe_supply, west_pipe_supply,
          in4_blueprint, in8_blueprint, out4_blueprint, out8_blueprint,
            jump4_blueprint, jump8_blueprint,
          outline.dupe())
      ff.merge(core.dupe())
      ff.merge(power.dupe())
      full_prints[item] = ff

  def fiddle(bp, label, icns, idx=None):
    j = bp.toJson(label, icons.mkIcons(*icns))
    if idx:
      j.update({"index": idx})
    return j

  return [fiddle(f, item, [item]) for item, f in full_prints.items()]
  return [
      #fiddle(factory, "factory", ["assembling-machine-3"], 0),

      #fiddle(core, "Core", ["rail"], 0),
      #fiddle(pickup, "Pickup", ["logistic-chest-requester"], 5),
      #fiddle(dropoffs[0], "Dropoff 1", ["logistic-chest-passive-provider", "signal-1"], 10),
      #fiddle(dropoffs[1], "Dropoff 2", ["logistic-chest-passive-provider", "signal-2"], 11),
      #fiddle(dropoffs[2], "Dropoff 3", ["logistic-chest-passive-provider", "signal-3"], 12),
      #fiddle(dropoffs[3], "Dropoff 4", ["logistic-chest-passive-provider", "signal-4"], 13),
      #fiddle(power, "Power", ["solar-panel"], 4),
  ]

def mkFullFactory(
    item, recipe, recipes,
    core, pickup, dropoffs, power,
    factory,
    east_belt_inline, west_belt_inline, east_pipe_inline, west_pipe_inline,
    east_belt_supply, west_belt_supply, east_pipe_supply, west_pipe_supply,
    in4_print, in8_print, out4_print, out8_print, jump4_print, jump8_print,
    outline):
  print(f"Making {item}")
  
  # ingredient -> [amount, channel, in/second]
  # liquid -> amount (must be channel 4)
  ingredients, liquids = getInputChannels(recipe, recipes)

  # Is it an intermediate product? Productivity or Speed modules
  is_intermediate = recipe["category"] == "Intermediate product"

  # Make a single cell for the factory
  cell = mkCell(
    item, recipe, recipes,
    is_intermediate, ingredients, liquids,
    core, pickup, dropoffs, power,
    factory,
    east_belt_inline, west_belt_inline, east_pipe_inline, west_pipe_inline,
    east_belt_supply, west_belt_supply, east_pipe_supply, west_pipe_supply,
    outline)

  # double: should there be 8 rows of factories or 4
  # depth: how many factories should each row have
  double, depth = getLayout(recipe, is_intermediate, ingredients, liquids)

  # how much space do we have to play with?
  space_depth = (getFreeSpace(dropoffs[0], pickup, len(recipe["recipe"]["ingredients"])) - 3) // 9

  # Make a grid of the cells
  grid = mkGrid(
      cell, 8 if double else 4, max(1, int(min(depth, space_depth))),
      ingredients, liquids,
      east_belt_inline, west_belt_inline, east_pipe_inline, west_pipe_inline,
      outline)
  alignGrid(grid, dropoffs[0], len(ingredients) + len(liquids))

  bb = BoundingBox(grid.entities)
  w = bb.maxx - bb.minx
  print(f"width for {item} is {w}")

  # create input and output lines
  inoutputs = mkInOutLines(
      ingredients, liquids, double,
      in4_print, in8_print, out4_print, out8_print, jump4_print, jump8_print,
      grid, dropoffs, pickup)

  inoutputs.merge(grid)

  bb = BoundingBox(inoutputs.entities)
  w = bb.maxx - bb.minx
  print(f"width for {item} is {w}")

  return inoutputs


def mkInOutLines(
      ingredients, liquids, double,
      in4_print, in8_print, out4_print, out8_print, jump4_print, jump8_print,
      grid, dropoffs, pickup):
  res = Blueprint([])

  num_inlines = len(ingredients) + len(liquids)

  north_west_beacon = min(
      [e for e in grid.entities if e.name == "beacon"],
      key=lambda e: e.x + e.y)

  channel_x_offsets = {
      1: 2,
      2: 3,
      3: 4,
      4: 8,
      5: 9,
      6: 10,
  }

  # [(channel, item)]
  solid_channels = sorted([(v[1], item) for item, v in ingredients.items()])

  east_belt = Blueprint([{
      "entity_number": 1,
      "name": "express-transport-belt",
      "position": {
          "x": 0.5,
          "y": 0.5,
      },
      "direction": 2,
  }])
  east_4_belt = east_belt.dupe()
  for _ in range(3):
    east_belt.shift(0, 1)
    east_4_belt.merge(east_belt.dupe())

  #south_belt = east_belt.dupe()
  #south_belt.entities[0]["direction"] = 4

  for i, [channel, item] in enumerate(solid_channels):
    off = dropoffs[i].dupe()
    
    # we need to set the trainstop and the train schedule
    station = [e for e in off.entities if e.name == "train-stop"][0]
    station.repr["station"] = f"SW [item={item}] Dropoff"
    station.repr["manual_trains_limit"] = 2

    locomotives = [e for e in off.entities if e.name == "locomotive"]
    for locomotive in locomotives:
      locomotive.repr["schedule"] = [
          {
              "station": f"SW [item={item}] Pickup",
              "wait_conditions": [{
                  "compare_type": "or",
                  "type": "full",
              }],
          },
          {
              "station": f"SW [item={item}] Dropoff",
              "wait_conditions": [{
                  "compare_type": "or",
                  "type": "empty",
              }],
          },
      ]

    res.merge(off.dupe())

    # get the north-east belt, align everything from there
    north_east_dropoff_belt = min(
        [e for e in dropoffs[i].entities if e.name.startswith("express")],
        key=lambda e: e.y - e.x)

    overall_offset_x = north_west_beacon.x - 1 - north_east_dropoff_belt.x
    channel_offset_x = overall_offset_x + channel_x_offsets[channel]
    rungap = int(channel_offset_x - (2 if double else 1))

    inbelts = in8_print.dupe() if double else in4_print.dupe()
    bb = BoundingBox(inbelts.entities)
    bb.maxx = bb.minx
    extenders = inbelts.calve(bb)
    for _ in range(rungap):
      inbelts.merge(extenders.dupe())
      extenders.shift(-1, 0)

    bb = BoundingBox(inbelts.entities)
    dx = north_east_dropoff_belt.x + 1 - bb.minx
    dy = north_east_dropoff_belt.y - bb.miny
    inbelts.shift(dx, dy)

    res.merge(inbelts.dupe())

    # the southmost row of inlines has south-facing express belts. get them
    southlines = inbelts.dupe()
    bb = BoundingBox(southlines.entities)
    southlines = southlines.calve(lambda e: e.name == "express-transport-belt" and e.y == bb.maxy)

    # we need to jump over some other inlines
    numjumps = num_inlines - i - 1
    for q in range(numjumps):
      jumper = jump8_print.dupe() if double else jump4_print.dupe()

      # align the jumper with the southlines
      bb = BoundingBox(southlines.entities)
      jumper.northWestTo(bb.minx, bb.maxy + 1)

      jumper.shift(0, 6 * q)
      res.merge(jumper)

  # todo: liquid in channels

  res.merge(pickup.dupe())

  # north_east_out is the NE belt of the pickup leading to the train
  north_east_out = min(pickup.entities, key=lambda e: e.y - e.x)
  #print(f"neout.y = {north_east_out.y}")

  # outsies collect the south-lines from the grid and make them go west
  outsies = out8_print.dupe() if double else out4_print.dupe()

  # align outsies with output
  bb = BoundingBox(outsies.entities)
  dy = north_east_out.y + 3 - bb.maxy
  outsies.shift(0, dy)
  #print(f"outsie.y = {bb.maxy}, dy = {dy}")

  # gridsouths are the south lines coming out of the grid
  bb = BoundingBox(grid.entities)
  gridsouths = grid.dupe().calve(lambda e: e.y == bb.maxy)
  #print(f"gridsouth at {bb.maxy}")

  # align outsies with gridsouths
  dx = BoundingBox(gridsouths.entities).minx - BoundingBox(outsies.entities).minx
  #print(f"dx = {dx}")
  outsies.shift(dx, 0)
  res.merge(outsies)

  # the four southmost westmost outsie lines are west-facing
  # fill in the gap to outlines
  bb = BoundingBox(outsies.entities)
  westlines = outsies.dupe().calve(lambda e: e.x == bb.minx and e.y >= bb.maxy - 3)
  gap = int(bb.minx - BoundingBox(pickup.entities).maxx - 1)
  #print(f"ew gap is {gap}")
  for q in range(gap):
    toadd = westlines.dupe()
    toadd.shift(-(q + 1), 0)
    res.merge(toadd)

  # fill in the gap from the gridsouths
  gap = int(BoundingBox(outsies.entities).miny - gridsouths.entities[0].y - 1)
  #print(f"ns gap is {gap}")
  for q in range(gap):
    toadd = gridsouths.dupe()
    toadd.shift(0, q + 1)
    res.merge(toadd)

  return res


def alignGrid(grid, dropoff0, numInputs):
  north_west_beacon = min(
      [e for e in grid.entities if e.name == "beacon"],
      key=lambda e: e.x + e.y)

  north_east_dropoff_belt = min(
      [e for e in dropoff0.entities if e.name.startswith("express")],
      key=lambda e: e.y - e.x)

  desired_x = north_east_dropoff_belt.x + 2
  desired_y = north_east_dropoff_belt.y + 6 * numInputs + 1

  # -1 because beacons are big
  actual_x = north_west_beacon.x - 1
  actual_y = north_west_beacon.y - 1

  dx = desired_x - actual_x
  dy = desired_y - actual_y
  grid.shift(dx, dy)


def mkGrid(
    cell, cols, rows,
    ingredients, liquids,
    east_belt_inline, west_belt_inline, east_pipe_inline, west_pipe_inline,
    outline):
  print(f"cols = {cols}, rows = {rows}")
  # copy outline and shift it while we construct a column
  outline = outline.dupe()

  # make a cell without the top three tiles (beacons) - these overlap
  north_beacons = min([e.y for e in cell.entities if e.name == "beacon"])
  partial = cell.dupe()
  partial.calve(lambda e: e.name == "beacon" and e.y == north_beacons)

  # make an entire column of cells
  col = cell.dupe()
  tip_power = [e for e in col.entities if e.name == "substation"][0]
  for _ in range(rows - 1):
    partial.shift(0, 9)
    outline.shift(0, 9)
    col.merge(partial.dupe())

    new_tip_power = max(
        [e for e in col.entities if e.name == "substation"],
        key=lambda e: e.y)
    new_tip_power.repr.setdefault("neighbours", []).append(tip_power.number)
    tip_power.repr.setdefault("neighbours", []).append(new_tip_power.number)
    tip_power = new_tip_power

  # add inlines and outlines
  col.merge(outline.dupe())

  channels = [v[1] for _, v in ingredients.items()]
  if 1 in channels or 3 in channels:
    col.merge(west_belt_inline.dupe())
  if 2 in channels:
    wbi = west_belt_inline.dupe()
    wings = BoundingBox(wbi.entities)
    wings.minx += 1
    wings.maxx -= 1
    wbi = wbi.calve(wings)
    col.merge(wbi.dupe())
  if 4 in channels or 6 in channels:
    col.merge(east_belt_inline.dupe())
  if 5 in channels:
    ebi = east_belt_inline.dupe()
    wings = BoundingBox(ebi.entities)
    wings.minx += 1
    wings.maxx -= 1
    ebi = ebi.calve(wings)
    col.merge(ebi.dupe())
  if liquids:
    col.merge(east_pipe_inline.dupe())

  # duplicate this rows-many times
  # first, make a partial without the west 3 tiles - these overlap
  west_beacons = min([e.x for e in cell.entities if e.name == "beacon"])
  partial = col.dupe()
  partial.calve(lambda e: e.name == "beacon" and e.x == west_beacons)

  powers = [e for e in col.entities if e.name == "substation"]
  powerx = powers[0].x

  grid = col
  for _ in range(cols - 1):
    partial.shift(10, 0)
    powerx += 10
    grid.merge(partial.dupe())
    new_powers = [e for e in grid.entities if e.name == "substation" and e.x == powerx]
    for p1, p2 in zip(powers, new_powers):
      p1.repr.setdefault("neighbours", []).append(p2.number)
      p2.repr.setdefault("neighbours", []).append(p1.number)
    powers = new_powers
  
  return grid


def getFreeSpace(dropoff0, pickup, n):
  # get the bounds from inline and outline
  bbin = BoundingBox(dropoff0.entities)
  bbo = BoundingBox(pickup.entities)
  space_for_inlines = 6*n
  space_for_outlines = 2
  # low y is north
  return bbo.miny - bbin.miny - space_for_inlines - space_for_outlines


def mkCell(
    item, recipe, recipes,
    is_intermediate, ingredients, liquids,
    core, pickup, dropoffs, power,
    factory,
    east_belt_inline, west_belt_inline, east_pipe_inline, west_pipe_inline,
    east_belt_supply, west_belt_supply, east_pipe_supply, west_pipe_supply,
    outline):
  # make a single element of the grid
  cell = factory.dupe()
  assembler = [e for e in cell.entities if e.name.startswith("assembling")][0]
  assembler.repr["recipe"] = item
  if is_intermediate:
    assembler.repr["items"] = {
        "productivity-module-3": 4,
    }
  else:
    assembler.repr["items"] = {
        "speed-module-3": 4,
    }
  if liquids:
    cell.merge(east_pipe_supply.dupe())
  solid_channels = set([v[1] for k, v in ingredients.items()])
  west_channels = set([1, 2, 3])
  east_channels = set([4, 5, 6])
  if solid_channels & west_channels:
    cell.merge(west_belt_supply.dupe())
  if solid_channels & east_channels:
    assert(not liquids)
    cell.merge(east_belt_supply.dupe())

  return cell


# returns double (ie 8 v 4 columns), and depth (ie rows)
def getLayout(recipe, is_intermediate, solids, liquids):
  # 12 speed beacons = 24 +50%, but beacons have 50% effectiveness
  speed_boost = 600
  productivity_boost = 0

  if is_intermediate:
    # 4 productivity modules.
    # 10% productivity boost, -15% speed boost
    productivity_boost += 40
    speed_boost -= 60
  else:
    # 4 speed: +50% each
    speed_boost += 200

  speed = 1.25 * (100 + speed_boost) / 100.0 / recipe["recipe"]["time"]
  productivity = (100.0 + productivity_boost) / 100.0 * recipe["recipe"]["yield"]

  # an output belt supports 22.5 items/s single lane, which we use
  factory_depth_max_output = 22.5 / productivity / speed
  input_depth_max = min([v[2] / v[0] / speed for k, v in solids.items()])

  depth = min(factory_depth_max_output, input_depth_max)

  # should we double up? If all inputs are halves, yes. Otherwise, if halving the full one
  # won't change the depth, then yes
  doubled_input_max = min(
      [v[2] / v[0] / 2 / speed for k, v in solids.items() if v[2] == 45],
      default=depth)
  should_double = (doubled_input_max >= depth)

  return should_double, depth
  

# ingredient -> [amount, channel, in/second]
# liquid -> amount (must be channel 4)
# return [ingredients, liquids]
def getInputChannels(recipe, recipes):
  # A factory has 6 input channels
  # 1 and 3 are the two sides of the west inline; 2 is them both. similarly 4 6 5
  # 4 is the only liquid channel
  ins = {}
  liquids = {}
  for ingredient in recipe["recipe"]["ingredients"]:
    if recipes[ingredient["id"]]["type"] == "Liquid":
      liquids[ingredient["id"]] = ingredient["amount"]
    else:
      ins[ingredient["id"]] = [ingredient["amount"], 2, 45.0]

  channels = []
  if liquids:
    channels.append(5)
    if len(ins) == 2:
      first = True
      for name, vals in ins.items():
        vals[2] = 22.5
        if first:
          first = False
          vals[1] = 1
          channels.append(1)
        else:
          vals[1] = 3
          channels.append(3)
    else:
      assert(len(ins) == 1)
      channels.append(2)
  else:
    # no liquid
    if len(ins) == 1:
      channels.append(2)
    elif len(ins) == 2:
      for name, vals in ins.items():
        vals[1] = 5
        break
      channels.append(2)
      channels.append(5)
    elif len(ins) == 3:
      maxamtitem = max(ins, key=lambda k: ins[k][0])
      chan = 4
      for name, vals in ins.items():
        if name != maxamtitem:
          channels.append(chan)
          vals[1] = chan
          vals[2] = 22.5
          chan += 2
    else:
      assert(len(ins) == 4)
      chans = [1, 3, 4, 6]
      chanidx = 0
      for name, vals in ins.items():
        chan = chans[chanidx]
        chanidx += 1
        vals[1] = chan
        vals[2] = 22.5

  assert(len(channels) == len(set(channels)))
  if 1 in channels:
    assert(3 in channels)
  if 3 in channels:
    assert(1 in channels)
  if 2 in channels:
    assert(1 not in channels)
    assert(3 not in channels)
  if 4 in channels:
    assert(6 in channels)
  if 6 in channels:
    assert(4 in channels)
  if 5 in channels:
    assert(4 not in channels)
    assert(6 not in channels)

  return ins, liquids


def divideFactoryPrint(b):
  # Segment the entities into a few groups

  # A. Get the beacon box
  beacon_zone = BoundingBox([e for e in b.entities if e.name == "beacon"])

  # B. Get the factory. It is the center
  center_x = [e for e in b.entities if e.name.startswith("assembling")][0].x

  # 1. Everything north of the beacons is input
  north_bound = beacon_zone.miny - 1.5
  inlines = b.calve(lambda e: e.y < north_bound)

  # 1W, 1E. Divide the inlines into east and west
  east_inlines = inlines.calve(lambda e: e.x > center_x)
  west_inlines = inlines

  # 2. Everything south of the beacons is output
  south_bound = beacon_zone.maxy + 1.5
  outlines = b.calve(lambda e: e.y > south_bound)

  # 3E, 3W. The factory has east and west input lines, which may not be in use
  def isSupply(e):
    if e.name in ["stack-inserter"]:
      return True
    if e.name.startswith("pipe"):
      return True
    if e.name.startswith("express"):
      return True
    return False
  east_supply = b.calve(lambda e: isSupply(e) and e.x > center_x)
  west_supply = b.calve(lambda e: isSupply(e) and e.x < center_x)

  return [b, east_inlines, west_inlines, east_supply, west_supply, outlines]


def divideLPrint(b):
  # Segment the entities into a few groups
  
  # 1. Power zone
  solar_zone = BoundingBox([e for e in b.entities if e.name == "solar-panel"])
  solar = b.calve(solar_zone)

  # A. Find the west cutoff and southern limit of the blueprint
  #    Note: south has high y
  #    Note: there is a buffer chest at this location
  west_cutoff, south_bound = max(
      [e for e in b.entities if e.name == "logistic-chest-buffer"],
      key=lambda e: e.y).xy

  # 2. Now that power is gone, strip the west_cutoff
  #    Also stip buffer chests.
  b.calve(lambda e: e.x < west_cutoff or e.name == "logistic-chest-buffer")

  # 3. The low steel chests, adjacent arms, and all belts are output
  low_chest_xs = [e.x for e in b.entities if e.name == "steel-chest" and e.y >= south_bound - 50]
  def isOutputInfra(e):
    nonlocal south_bound
    if e.y < south_bound - 50:
      return False
    if e.name.startswith("express"):
      return True
    if e.name == "steel-chest":
      return True
    nonlocal low_chest_xs
    if e.name == "stack-inserter" and e.x in low_chest_xs:
      return True
    return False
  output_infra = b.calve(isOutputInfra)

  # B. Find all unused dropoff stations' positions. Sort, northmost first
  dropoff_xys = sorted(
      [e.xy for e in b.entities if (
          e.name == "train-stop"
          and e["station"] in ["Unused Dropoff", "SW [item=coal] Dropoff"])],
      key=lambda xy: xy[1])

  # C. Find the northmost and eastmost belt positions (now that output has been removed)
  belts = [e for e in b.entities if e.name == "express-transport-belt"]
  northmost_belt_y = min(e.y for e in belts)
  eastmost_belt_x = max(e.x for e in belts)

  # 4a. Find dropoff train stop infra, including the train stop and refueling
  dropoff_belt_entities = [[], [], [], []]
  new_entities = []
  def isInputInfra(e):
    nonlocal northmost_belt_y
    if e.y > northmost_belt_y + 125:
      return False
    if e.name.startswith("express"):
      return True
    if e.name in ["stack-inserter", "train-stop"]:
      return True
    if "chest" in e.name:
      return True
    return False
  for e in b.entities:
    if isInputInfra(e):
      index = None
      if (e.name == "express-underground-belt"
          and "direction" in e.repr
          and e["direction"] % 4 == 2):
        index = int((e.y - northmost_belt_y) // 6)
      else:
        for i in range(4):
          if e.x > dropoff_xys[i][0] - 2.25:
            index = i
            break
      if index is not None:
        dropoff_belt_entities[index].append(e)
      else:
        new_entities.append(e)
    else:
      new_entities.append(e)
  b.entities = new_entities
  dropoff_infras = [Blueprint(es) for es in dropoff_belt_entities]

  # 4b. Remove the dummy train (on dropoff 4), and add trains to each dropoff
  # Todo: remove 3 nuclear fuel from first
  # Todo: remove rightmost substations
  trains = b.calve(lambda e: e.name in ["locomotive", "cargo-wagon"])
  def addTrains(i):
    nonlocal dropoff_xys
    nonlocal trains
    nonlocal dropoff_infras
    new_trains = trains.dupe()
    dx = dropoff_xys[i][0] - dropoff_xys[3][0]
    dy = dropoff_xys[i][1] - dropoff_xys[3][1]
    new_trains.shift(dx, dy)
    dropoff_infras[i].merge(new_trains)
  addTrains(0)
  addTrains(1)
  addTrains(2)
  addTrains(3)

  # return all these parts
  return [b, output_infra, dropoff_infras, solar]


def augmentElderaxe(elderaxe_book):
  for p in elderaxe_book["blueprint_book"]["blueprints"]:
    if "4 Lane 4-Way" in p.get("blueprint", {}).get("description", ""):
      newp = deepcopy(p)

      qp = deepcopy(newp)
      b = Blueprint(qp["blueprint"]["entities"])
      bb = BoundingBox(b.entities)
      midx = (bb.minx + bb.maxx) / 2
      midy = (bb.miny + bb.maxy) / 2

      for e in newp["blueprint"]["entities"]:
        if abs(e["position"]["x"] - midx) < 2 and abs(e["position"]["y"] - midy) < 2:
          if e["name"] == "big-electric-pole":
            e["name"] = "substation"
            break
      else:
        assert(False)

      newp["blueprint"]["icons"].append({
        "signal": {
            "type": "item",
            "name": "substation",
        },
        "index": 4,
      })

      newp["index"] = 16

      elderaxe_book["blueprint_book"]["blueprints"].append(newp)
      return


def mkColorTrains(_t_print):
  single = Blueprint(_t_print["entities"])
  ret = [single.toJson("same")]

  # make a color object
  def mkC(r, g, b, a=None):
    if a is None:
      a = 0.49803921580314636
    return {
      "r": r,
      "g": g,
      "b": b,
      "a": a,
    }

  # update a train's color
  def upT(es, *args):
    es[0].repr["color"] = mkC(*args)

  # add a colored train to b
  def aug(b, dx, dy, *args):
    new_train = single.dupe()
    upT(new_train.entities, *args)
    new_train.shift(dx * 8, dy * 4)
    b.merge(new_train)

  # see what 'a' does
  ats = Blueprint([])
  aug(ats, 0, 0, 0, 0, 0)
  aug(ats, 0, 1, 1, 0, 0)
  aug(ats, 0, 2, 0, 1, 0)
  aug(ats, 0, 3, 0, 0, 1)
  aug(ats, 0, 4, 1, 1, 1)
  ats2 = Blueprint([])
  for x in range(5):
    ats3 = ats.dupe()
    ats3.shift(x * 8, 0)
    for e in ats3.entities:
      if e.name == "locomotive":
        e.repr["color"]["a"] = 0.25 * x
    ats2.merge(ats3)

  # oh man, saturation is a juicy field, will totally use it
  ret.append(ats2.toJson("transparency"))

  # all combos. a 5x5 square can alternate r,g.
  # square of squares for b,a
  bigs = Blueprint([])
  for i in range(5):
    aug(bigs, i, 0, 0.25 * i, 0, 0, 0)
  c = bigs.dupe()
  for i in range(1, 5):
    d = c.dupe()
    d.shift(0, 4 * i)
    for e in d.entities:
      if e.name == "locomotive":
        e.repr["color"]["g"] = 0.25 * i
    bigs.merge(d)
  c = bigs.dupe()
  for i in range(1, 5):
    d = c.dupe()
    d.shift(i * 48, 0)
    for e in d.entities:
      if e.name == "locomotive":
        e.repr["color"]["b"] = 0.25 * i
    bigs.merge(d)
  c = bigs.dupe()
  for i in range(1, 5):
    d = c.dupe()
    d.shift(0, 24 * i)
    for e in d.entities:
      if e.name == "locomotive":
        e.repr["color"]["a"] = 0.25 * i
    bigs.merge(d)
  ret.append(bigs.toJson("full"))

  return ret
