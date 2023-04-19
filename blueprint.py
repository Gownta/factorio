from copy import deepcopy

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


# Create my own entity numbers! No overlap
new_entity_number = 0
def genEntityNumber():
  global new_entity_number
  new_entity_number -= 1
  return new_entity_number


class Blueprint:
  def __init__(self, entities=None, tiles=None):
    self.entities = []
    for e in (entities or []):
      if isinstance(e, Entity):
        self.entities.append(e)
      else:
        self.entities.append(Entity(e))
    self.tiles = tiles or []

    table = {}
    for e in self.entities:
      table[e.number] = genEntityNumber()
    self.reindex(table)

  # each entity number -> table[entity_number]
  def reindex(self, table):
    # Apply new numbers to dependent fields
    for e in self.entities:
      # Fix up the entity's own number
      e.number = table[e.number]

      # Fix up neighbours for electrical power lines
      if "neighbours" in e.repr:
        e.repr["neighbours"] = [table[n] for n in e["neighbours"] if n in table]

      # Fix up connections
      if "connections" in e.repr:
        for access_point, circuits in e["connections"].items():
          for wire_color, wires in circuits.items():
            connections = []
            for entity_table in wires:
              for _, entity_id in entity_table.items():
                if entity_id in table:
                  connections.append(table[entity_id])
            circuits[wire_color] = [
                {"entity_id": n} for n in connections
            ]

  # bump = 2 per 90 degrees clockwise
  def rotate(self, bump):
    for e in self.entities:
      e.sendTo(-e.x, -e.y)

      if e.name in [
        "assembling-machine-3",
        "stack-inserter",
        "stack-filter-inserter",
        "pump",
        "offshore-pump",
        "pipe",
        "pipe-to-ground",
        "electric-mining-drill",
        "oil-refinery",
        "chemical-plant",
        "centrifuge",
        "express-splitter",
        "express-transport-belt",
        "express-underground-belt",
        "rail",
        "train-stop",
        "rail-signal",
        "rail-chain-signal",
      ]:
        curr = e.repr.get("direction", 0)
        curr += bump
        curr %= 8
        e.repr["direction"] = curr
      elif e.name in [
        "locomotive",
        "cargo-wagon",
        "fluid-wagon",
      ]:
        curr = e.repr.get("orientation", 0)
        curr += bump * 0.125
        while curr >= 1:
          curr -= 1
        e.repr["orientation"] = curr

  def merge(self, more):
    new_more = deepcopy(more)
    self.entities.extend(more.entities)
    self.tiles.extend(more.tiles)
    # Todo: add wire connections between self and more?

  # get new numbers
  def dupe(self):
    c = deepcopy(self)
    table = {}
    for e in c.entities:
      table[e.number] = genEntityNumber()
    c.reindex(table)
    return c
    
  # Takes all entities that match the predicate and put them in a new blueprint
  # Tiles stay
  def calve(self, pred):
    new_blueprint = Blueprint()
    new_entities = []
    for e in self.entities:
      if pred(e):
        new_blueprint.entities.append(e)
      else:
        new_entities.append(e)
    self.entities = new_entities
    return new_blueprint

  def shift(self, dx, dy):
    for e in self.entities:
      e.shift(dx, dy)
    for t in self.tiles:
      t["position"]["x"] += dx
      t["position"]["y"] += dy

  def northWestTo(self, x, y):
    bb = BoundingBox(self.entities)
    dx = x - bb.minx
    dy = y - bb.miny
    self.shift(dx, dy)

  def northwestmost(self, name):
    candidates = [e for e in self.entities if e.name == name]
    bb = BoundingBox(candidates)
    northmost = [e for e in candidates if e.y == bb.miny]
    northwest = [e for e in northmost if e.x == bb.minx]
    assert(len(northwest) == 1)
    return northwest[0]

  def toJson(self, label, icons=None):
    table = {}
    curr = 1
    for e in self.entities:
      table[e.number] = curr
      curr += 1
    self.reindex(table)

    base = {
      "label": label,
    }
    if icons:
      base["icons"] = icons
    if self.entities:
      base["entities"] = [e.toJson() for e in self.entities]
    if self.tiles:
      base["tiles"] = self.tiles
    return base


class Entity:
  def __init__(self, d):
    self.repr = d

    self.name = d["name"]

    self.number = d["entity_number"]

    self.x = d["position"]["x"]
    self.y = d["position"]["y"]
    self.xy = (self.x, self.y)

  def __getitem__(self, k):
    return self.repr[k]

  def shift(self, dx, dy):
    self.x += dx
    self.y += dy
    self.xy = (self.x, self.y)

  def sendTo(self, x, y):
    self.x = x
    self.y = y
    self.xy = (x, y)

  def toJson(self):
    self.repr.update({
        "position": {
            "x": self.x,
            "y": self.y,
        },
        "entity_number": self.number,
        "name": self.name,
    })
    return self.repr


class BoundingBox:
  def __init__(self, entities):
    xs = [e.x for e in entities]
    ys = [e.y for e in entities]
    self.minx = min(xs)
    self.maxx = max(xs)
    self.miny = min(ys)
    self.maxy = max(ys)

  def contains(self, e):
    return self.minx <= e.x <= self.maxx and self.miny <= e.y <= self.maxy

  def __call__(self, entities):
    return self.contains(entities)
