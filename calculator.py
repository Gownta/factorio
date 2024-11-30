import argparse
import os
import re
import sys
from collections import dataclass, field


@dataclass
class Where:
    name: str
    speed: float
    prod: float
    slots: int  # modules


A3 = Where("Assembling Machine 3", 1.25, 1, 4)
EMP = Where("Electromagnetic Plant", 2, 1.5, 5)


@dataclass
class Q:
    amount: int
    what: str


@dataclass
class Recipe:
    name: str
    ins: [Q]
    outs: [Q]
    dur: float  # crafting time
    where: Where


Recipes = {r[0]: Recipe(*r) for r in [
]}
