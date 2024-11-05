from collections import namedtuple


#
# Get the type of an icon name
#
# Either "item", "fluid", or "virtual"
#
def getIconType(name):
  return "item"  # TODO


# Make a Factorio Blueprint
#
# @label  The name of of the blueprint. String
# @icons  Up to four icons to be displayed on the blueprint. [String]
# @entities  Everything else. [json]
#
# This function will separate the tiles from the entities.
# This function will extract schedules from locomotives.
#
def mkBlueprint(label, entities, icons=None):
  b = {
    "item": "blueprint",
    "version": 281479275151360,
    "label": label,
  }
  #b["item"] = "blueprint"
  #b["version"] = 281479275151360
  #b["label"] = label

  if icons:
    assert(len(icons) <= 4)
    il = []
    for i, name in enumerate(icons):
      sig = {}
      sig["type"] = getIconType(name)
      sig["name"] = name
      icon = {}
      icon["index"] = i
      icon["signal"] = sig
      il.append(icon)
    b["icons"] = il

  es = [] # entities
  ts = [] # tiles
  ss = [] # schedules
  for entity in entities:
    assert(entity["name"])
    if isTile(entity["name"]):
      ts.append(entity)
    else:
      entity_number = len(es) + 1

      if entity["name"] == "locomotive":
        if "schedule" in entity:
          sched = entity["schedule"]
          if sched in ss:
            sched_idx = ss.index(sched)
          else:
            ss.append(sched)
            
        

    entity["entity_number"] = i
    
    






{
  "blueprint": {
    "entities": [
      {
        "entity_number": 1,
        "name": "express-underground-belt",
        "position": {
          "x": -1548.5,
          "y": 2991.5
        },
        "type": "output"
      },
      {
        "entity_number": 2,
        "name": "express-underground-belt",
        "position": {
          "x": -1548.5,
          "y": 2995.5
        },
        "type": "input"
      },
      {
        "entity_number": 3,
        "name": "express-transport-belt",
        "position": {
          "x": -1548.5,
          "y": 2997.5
        }
      },
      {
        "entity_number": 4,
        "name": "express-transport-belt",
        "position": {
          "x": -1546.5,
          "y": 2997.5
        },
        "direction": 2
      },
      {
        "entity_number": 5,
        "name": "express-transport-belt",
        "position": {
          "x": -1544.5,
          "y": 2997.5
        },
        "direction": 4
      },
      {
        "entity_number": 6,
        "name": "express-transport-belt",
        "position": {
          "x": -1542.5,
          "y": 2997.5
        },
        "direction": 6
      },
      {
        "entity_number": 7,
        "name": "substation",
        "position": {
          "x": -1540,
          "y": 2997
        },
        "connections": {
          "1": {
            "green": [
              {
                "entity_id": 9
              }
            ]
          }
        }
      },
      {
        "entity_number": 8,
        "name": "train-stop",
        "position": {
          "x": -1547,
          "y": 2999
        },
        "direction": 6,
        "station": "FooBar [item=electric-mining-drill] Station",
        "manual_trains_limit": 1
      },
      {
        "entity_number": 9,
        "name": "stack-filter-inserter",
        "position": {
          "x": -1538.5,
          "y": 2999.5
        },
        "direction": 4,
        "connections": {
          "1": {
            "green": [
              {
                "entity_id": 7
              }
            ]
          }
        },
        "filters": [
          {
            "index": 1,
            "name": "assembling-machine-2"
          }
        ]
      },
      {
        "entity_number": 10,
        "name": "rail-signal",
        "position": {
          "x": -1532.5,
          "y": 2999.5
        },
        "direction": 2
      },
      {
        "entity_number": 11,
        "name": "straight-rail",
        "position": {
          "x": -1549,
          "y": 3001
        },
        "direction": 2
      },
      {
        "entity_number": 12,
        "name": "locomotive",
        "position": {
          "x": -1544,
          "y": 3001
        },
        "orientation": 0.75,
        "items": {
          "nuclear-fuel": 1
        }
      },
      {
        "entity_number": 13,
        "name": "straight-rail",
        "position": {
          "x": -1547,
          "y": 3001
        },
        "direction": 2
      },
      {
        "entity_number": 14,
        "name": "straight-rail",
        "position": {
          "x": -1545,
          "y": 3001
        },
        "direction": 2
      },
      {
        "entity_number": 15,
        "name": "straight-rail",
        "position": {
          "x": -1543,
          "y": 3001
        },
        "direction": 2
      },
      {
        "entity_number": 16,
        "name": "straight-rail",
        "position": {
          "x": -1541,
          "y": 3001
        },
        "direction": 2
      },
      {
        "entity_number": 17,
        "name": "cargo-wagon",
        "position": {
          "x": -1537,
          "y": 3001
        },
        "orientation": 0.25,
        "inventory": {
          "filters": [
            {
              "index": 1,
              "name": "rail"
            }
          ],
          "bar": 35
        }
      },
      {
        "entity_number": 18,
        "name": "straight-rail",
        "position": {
          "x": -1539,
          "y": 3001
        },
        "direction": 2
      },
      {
        "entity_number": 19,
        "name": "straight-rail",
        "position": {
          "x": -1537,
          "y": 3001
        },
        "direction": 2
      },
      {
        "entity_number": 20,
        "name": "straight-rail",
        "position": {
          "x": -1535,
          "y": 3001
        },
        "direction": 2
      },
      {
        "entity_number": 21,
        "name": "straight-rail",
        "position": {
          "x": -1533,
          "y": 3001
        },
        "direction": 2
      },
      {
        "entity_number": 22,
        "name": "straight-rail",
        "position": {
          "x": -1531,
          "y": 3001
        },
        "direction": 2
      }
    ],
  }
}
