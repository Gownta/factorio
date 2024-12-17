
from dataclasses import dataclass, asdict
import serde


@dataclass
class Blueprint:
    snap_to_grid

    @classmethod
    def from_file(cls, path):
        j = serde.deserialize(path.read_text())
        for k, m in {
            "snap-to-grid": "snap_to_grid",
        }.items():
            if v := j.pop(k, None):
                j[m] = v
        return cls(**j)




