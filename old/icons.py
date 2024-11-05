def getTypeOfIcon(name):
  if name.startswith("signal"):
    return "virtual"
  if name in []:
    return "fluid"
  return "item"

def mkIcons(*names):
  ret = []
  index = 1
  for name in names:
    ret.append({
      "signal": {
        "type": getTypeOfIcon(name),
        "name": name,
      },
      "index": index,
    })
    index += 1
  return ret
