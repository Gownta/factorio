import book
import calculator
import icons
import json
import logic
import mega
import mega2
import sys
import serde
from collections import defaultdict

def main():
  serde.load('rail_and_signal')
  f3()


def f3():
  prints = serde.load('s12')["blueprint_book"]["blueprints"]
  new_prints = mega2.go(prints)
  new_book = book.make(
      "Mega Base",
      icons.mkIcons('satellite'),
      new_prints)
  serde.dump("megabase", new_book)


def f2():
  t_print = serde.load("colortrain")["blueprint"]
  t_out = logic.mkColorTrains(t_print)
  new_book = book.make(
      "Train colors",
      icons.mkIcons('locomotive'),
      t_out)
  serde.dump("colortrain", new_book)


def f1():
  # Load the prints
  l_book = serde.load("l")
  l_print = l_book["blueprint_book"]["blueprints"][0]["blueprint"]
  factory_book = serde.load("factory")
  factory_print = factory_book["blueprint_book"]["blueprints"][0]["blueprint"]
  fluid_factory_print = factory_book["blueprint_book"]["blueprints"][1]["blueprint"]
  inoutline_book = serde.load("inoutlines")
  in4 = inoutline_book["blueprint_book"]["blueprints"][0]["blueprint"]
  in8 = inoutline_book["blueprint_book"]["blueprints"][1]["blueprint"]
  out4 = inoutline_book["blueprint_book"]["blueprints"][2]["blueprint"]
  out8 = inoutline_book["blueprint_book"]["blueprints"][3]["blueprint"]
  jump4 = inoutline_book["blueprint_book"]["blueprints"][4]["blueprint"]
  jump8 = inoutline_book["blueprint_book"]["blueprints"][5]["blueprint"]

  elderaxe_book = serde.load("elderaxe")
  logic.augmentElderaxe(elderaxe_book)
  serde.dump("elderaxe_augmented", elderaxe_book)

  # Load crafting info.
  # 0=assemble, 2=chem, 4=centrifuge, 6=oil, 8=rocket
  recipes = {e["id"]: e for e in json.loads(serde.read("recipes.json"))}
  crafting_types = json.loads(serde.read("craft_info.txt"))

  '''
  need = calculator.calculate(recipes, crafting_types, {
      "rocket-part": 100,
      "satellite": 1,
      "science-pack-1": 1000,
      "science-pack-2": 1000,
      "science-pack-3": 1000,
      "high-tech-science-pack": 1000,
      "production-science-pack": 1000,
  })
  revd = defaultdict(list)
  for item, amt in need.items():
    revd[amt].append(item)
  for amt in sorted(revd.keys()):
    for item in revd[amt]:
      print(f"{amt}\t{item}")

  return 
  '''

  # Process the blueprint. So begins super-custom code.
  new_prints = logic.process(
      recipes,
      l_print,
      factory_print, fluid_factory_print,
      in4, in8, out4, out8, jump4, jump8)

  # Put all the blueprints into a new book
  new_book = book.make(
      "Factory prints",
      icons.mkIcons('assembling-machine-1', 'rail'),
      new_prints)

  # Output
  serde.dump("all", new_book)


main()

# Notes
#
# Direction: N=0, E=2, S=4, W=6
# Orientation (for trains): N=0, E=0.25, S=0.5, W=0.75
#
