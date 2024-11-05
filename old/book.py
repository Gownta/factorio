'''
Modifications to Factorio's blueprints that this function fixes up:

 - Blueprints can have an "index" field.
 - Blueprints do not need an "item" or "version" field.
 - Locomotives have schedules.
'''

# mutates p
def fixupPrint(p):
  # Collect all schedules
  schedules = []
  locomotives = []
  if "entities" not in p:
    print(p)
    assert(False)
  for e in p["entities"]:
    if e["name"] == "locomotive":
      if "schedule" in e:
        sched = e.pop("schedule")
        if sched in schedules:
          index = schedules.index(sched)
        else:
          index = len(schedules)
          schedules.append(sched)
          locomotives.append([])
        locomotives[index].append(e["entity_number"])
  print_schedules = []
  for sched, locos in zip(schedules, locomotives):
    print_schedules.append({
        "schedule": sched,
        "locomotives": locos,
    })
  if print_schedules:
    p["schedules"] = print_schedules


# mutates prints
def make(label, icons, prints):
  new_prints = []
  taken_indexes = []

  for p in prints:
    # See if this blueprint has its own index
    if "index" in p:
      taken_indexes.append(p["index"])

  if taken_indexes:
    max_index = max(taken_indexes)
    next_index = (max_index + 4) % 5
  else:
    next_index = 0

  for p in prints:
    # Add constant data to the prints
    p.update({
        "item": "blueprint",
        "version": 281479275151360,
    })

    # Determine the index
    if "index" in p:
      index = p["index"]
      p.pop("index")
    else:
      index = next_index
      next_index += 1

    # Apply fixups to the blueprint
    fixupPrint(p)

    # Make a blueprint entry
    new_prints.append({
        "blueprint": p,
        "index": index,
    })

  # Create the actual book
  book = {
      "item": "blueprint-book",
      "version": 281479275151360,
      "active_index": 0,

      "label": label,
      "icons": icons,
      "blueprints": new_prints,
  }

  # Wrap and return
  return {"blueprint_book": book}
