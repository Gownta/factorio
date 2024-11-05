from collections import Counter, namedtuple

# 0=assemble, 2=chem, 4=centrifuge, 6=oil, 8=rocket
def getProductivityFactor(recipes, crafting_types, item):
  if item not in crafting_types:
    if item in ["used-up-uranium-fuel-cell", "wood"]:
      return 1
    print(item)
    assert(False)
  if item in ["satellite", "space-science-pack"]:
    return 1
  is_intermediate = (recipes[item]["category"] == "Intermediate product")
  if not is_intermediate:
    return 1
  t = int(crafting_types[item] / 2) * 2
  if t == 0:
    return 1.4
  elif t == 2:
    return 1.3
  elif t == 4:
    return 1.2
  elif t == 6:
    assert(False)
  elif t == 8:
    return 1.4
  print(item)
  assert(False)


# wanted: Counter{item: amount}
def calculate(recipes, crafting_types, wanted):
  # create an easy recipe map. ins :: {item: amt}
  Recipe = namedtuple('Recipe', ['y', 'ins'])
  rs = {}
  for item, recipe in recipes.items():
    if recipe["recipe"]["yield"]:
      y = 1.0 * recipe["recipe"]["yield"]
      p = getProductivityFactor(recipes, crafting_types, item)
      more = {i["id"]: i["amount"] for i in recipe["recipe"]["ingredients"]}
      rs[item] = Recipe(y * p, more)

  rest = set(rs.keys())
  toposort = []
  while rest:
    ingrs = set()
    for item in rest:
      for i in rs.get(item, Recipe(1, {})).ins.keys():
        ingrs.add(i)
    unigrd = rest - ingrs
    toposort.extend(unigrd)
    rest -= unigrd
    
  # {item: amt}
  res = {}
  while wanted:
    for item in toposort:
      if item in wanted:
        break
    else:
      return res

    # we have the item
    if item not in rs:
      print(item)
      assert(False)

    r = rs[item]
    more = {i: (1.0 * wanted[item] * amt / r.y) for i, amt in r.ins.items()}
    #print(f"we need {wanted[item]} {item}. Normally, we would need {r.ins} per, but because of yield {r.y} we only need {more} total")
    
    res[item] = int(wanted.pop(item))
    for x, y in more.items():
      if x in wanted:
        wanted[x] += y
      else:
        wanted[x] = y

  return {}
