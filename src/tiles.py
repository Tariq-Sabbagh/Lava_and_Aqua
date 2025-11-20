from dataclasses import dataclass
from typing import Dict, Iterable, Tuple


@dataclass(frozen=True)
class TileType:
    name: str
    symbol: str
    category: str
    dynamic: bool = False
    preserve_when_occupied: bool = False
    collectible: bool = False


@dataclass(frozen=True)
class SpreadEffect:
    spawn: bool = False
    hits_player: bool = False
    convert_to_kind: str | None = None
    convert_location: str = "target"  # "source" or "target"


@dataclass(frozen=True)
class PushEffect:
    allowed: bool
    removes_kind: str | None = None


_TILE_TYPES: Tuple[TileType, ...] = (
    TileType("floor", ".", "terrain"),
    TileType("wall", "W", "terrain"),
    TileType("goal", "G", "terrain"),
    TileType("orb", "O", "collectible"),
    TileType("player", "P", "entity", dynamic=True),
    TileType("lava", "L", "entity", dynamic=True),
    TileType("aqua", "A", "entity", dynamic=True, preserve_when_occupied=True),
    TileType("box", "B", "entity", dynamic=True),
)

TILE_TYPES: Dict[str, TileType] = {tile.name: tile for tile in _TILE_TYPES}
KIND_TO_SYMBOL: Dict[str, str] = {name: tile.symbol for name, tile in TILE_TYPES.items()}
SYMBOL_TO_KIND: Dict[str, str] = {tile.symbol: name for name, tile in TILE_TYPES.items()}
DYNAMIC_KINDS = {name for name, tile in TILE_TYPES.items() if tile.dynamic}


SPREAD_RULES: Dict[Tuple[str, str], SpreadEffect] = {
    ("lava", "floor"): SpreadEffect(spawn=True),
    ("aqua", "floor"): SpreadEffect(spawn=True),
    ("lava", "orb"): SpreadEffect(spawn=True),
    ("aqua", "orb"): SpreadEffect(spawn=True),
    ("lava", "player"): SpreadEffect(hits_player=True),
    ("lava", "aqua"): SpreadEffect(convert_to_kind="wall", convert_location="source"),
    ("aqua", "lava"): SpreadEffect(convert_to_kind="wall"),
}


BOX_PUSH_RULES: Dict[str, PushEffect] = {
    "floor": PushEffect(allowed=True),
    "goal": PushEffect(allowed=False),
    "lava": PushEffect(allowed=True, removes_kind="lava"),
    "aqua": PushEffect(allowed=True, removes_kind="aqua"),
}

BOX_PUSH_BLOCKED = PushEffect(allowed=False)
