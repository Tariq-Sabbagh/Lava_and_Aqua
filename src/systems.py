from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from src.Board import Board
from src.events import CounterEvent, MoveEvent, OrbCollectedEvent, PushEvent, SpreadEvent
from src.tiles import (
    BOX_PUSH_BLOCKED,
    BOX_PUSH_RULES,
    KIND_TO_SYMBOL,
    SPREAD_RULES,
    SYMBOL_TO_KIND,
    TILE_TYPES,
)

Coord = Tuple[int, int]


@dataclass
class MovementResult:
    ok: bool
    reason: str | None = None
    data: dict | None = None
    events: List[MoveEvent] = field(default_factory=list)


@dataclass
class PushResult:
    ok: bool
    reason: str | None = None
    info: dict | None = None
    event: PushEvent | None = None


class MovementSystem:
    KEY_TO_DELTA = {
        "W": (-1, 0),
        "A": (0, -1),
        "S": (1, 0),
        "D": (0, 1),
    }

    def __init__(self, board: Board):
        self.board = board

    def available_moves(self) -> Dict[str, Coord]:
        start = self._player_position()
        if start is None:
            return {}

        moves: Dict[str, Coord] = {}
        for key, delta in self.KEY_TO_DELTA.items():
            if self._can_move(start, delta):
                nr, nc = start[0] + delta[0], start[1] + delta[1]
                moves[key] = (nr, nc)
        return moves

    def move_player(self, key: str) -> MovementResult:
        key = key.upper()
        if key not in self.KEY_TO_DELTA:
            return MovementResult(ok=False, reason="invalid_move_key")

        start = self._player_position()
        for pos in self.board.neighbors4(start[0], start[1]):
            if(self._can_move(pos , (0,0))):
                print(pos)
        if start is None:
            return MovementResult(ok=False, reason="no_player")

        delta = self.KEY_TO_DELTA[key]
        nr, nc = start[0] + delta[0], start[1] + delta[1]

        if not self.board.in_bounds(nr, nc):
            return MovementResult(ok=False, reason="out_of_bounds")
        if self.board.is_wall(nr, nc):
            return MovementResult(ok=False, reason="wall")

        tile_symbol = self.board.get(nr, nc)
        tile_kind = SYMBOL_TO_KIND.get(tile_symbol)

        push_info = None
        push_event = None
        orb_event = None
        if tile_kind == "box":
            push_result = self._push_box((nr, nc), delta)
            if not push_result.ok:
                return MovementResult(ok=False, reason=push_result.reason)
            push_info = push_result.info
            push_event = push_result.event

        collected_orb = False
        if tile_kind == "orb":
            collected_orb = self.board.collect_orb((nr, nc))
            if collected_orb:
                orb_event = OrbCollectedEvent(position=(nr, nc), remaining=self.board.orbs_remaining)

        preserve_symbol = None
        if tile_kind:
            tile_type = TILE_TYPES.get(tile_kind)
            if tile_type and tile_type.preserve_when_occupied:
                preserve_symbol = KIND_TO_SYMBOL[tile_kind]

        self.board.update_entity("player", start, (nr, nc), preserve_symbol=preserve_symbol)
        landed_goal = self.board.is_goal_cell(nr, nc)

        move_event = MoveEvent(
            actor="player",
            origin=start,
            destination=(nr, nc),
            target_kind=tile_kind,
            landed_on_goal=landed_goal,
            push=push_event,
        )

        events = [move_event]
        if orb_event:
            events.append(orb_event)

        return MovementResult(
            ok=True,
            data={
                "from": start,
                "to": (nr, nc),
                "target": tile_symbol,
                "on_goal": landed_goal,
                "push": push_info,
                "collected_orb": collected_orb,
                "orbs_remaining": self.board.orbs_remaining,
                "orbs_total": self.board.orbs_total,
                "orbs_collected": self.board.orbs_total - self.board.orbs_remaining,
            },
            events=events,
        )

    def _player_position(self) -> Coord | None:
        try:
            return next(iter(self.board.player_positions))
        except StopIteration:
            return None

    def _can_move(self, start: Coord, delta: Coord) -> bool:
        nr, nc = start[0] + delta[0], start[1] + delta[1]
        if not self.board.in_bounds(nr, nc):
            return False
        if self.board.is_wall(nr, nc):
            return False

        tile_symbol = self.board.get(nr, nc)
        tile_kind = SYMBOL_TO_KIND.get(tile_symbol)
        if tile_kind == "box":
            return self._can_push_to((nr, nc), delta)
        if tile_symbol.isdigit() or tile_symbol == "W":
            return False
        return True

    def _can_push_to(self, box_pos: Coord, delta: Coord) -> bool:
        dest = (box_pos[0] + delta[0], box_pos[1] + delta[1])
        if not self.board.in_bounds(*dest):
            return False
        tile_symbol = self.board.get(*dest)
        if tile_symbol in ("W", "B") or tile_symbol.isdigit():
            return False
        tile_kind = SYMBOL_TO_KIND.get(tile_symbol)
        interaction = BOX_PUSH_RULES.get(tile_kind)
        return bool(interaction and interaction.allowed)

    def _push_box(self, box_pos: Coord, delta: Coord) -> PushResult:
        dest = (box_pos[0] + delta[0], box_pos[1] + delta[1])

        if not self.board.in_bounds(*dest):
            return PushResult(ok=False, reason="box_out_of_bounds")

        tile_symbol = self.board.get(*dest)
        if tile_symbol in ("W", "B") or tile_symbol.isdigit():
            return PushResult(ok=False, reason="box_blocked")

        tile_kind = SYMBOL_TO_KIND.get(tile_symbol)
        interaction = BOX_PUSH_RULES.get(tile_kind)
        if interaction is None:
            interaction = BOX_PUSH_BLOCKED
        if not interaction.allowed:
            reason = "box_blocked" if tile_symbol in ("W", "B") else f"box_hits_{tile_symbol}"
            return PushResult(ok=False, reason=reason)

        neutralized_kind = interaction.removes_kind
        neutralized_lava = False
        neutralized_aqua = False
        if neutralized_kind:
            self.board.remove_entity(neutralized_kind, dest)
            neutralized_lava = neutralized_kind == "lava"
            neutralized_aqua = neutralized_kind == "aqua"
        elif tile_kind not in ("floor", "goal") and tile_symbol not in (".", "G"):
            return PushResult(ok=False, reason=f"box_hits_{tile_symbol}")

        self.board.update_entity("box", box_pos, dest)

        push_event = PushEvent(from_pos=box_pos, to_pos=dest, neutralized_kind=neutralized_kind)
        return PushResult(
            ok=True,
            info={
                "from": box_pos,
                "to": dest,
                "neutralized_lava": neutralized_lava,
                "neutralized_aqua": neutralized_aqua,
            },
            event=push_event,
        )


class SpreadSystem:
    def __init__(self, board: Board):
        self.board = board

    def spread(self, kind: str) -> SpreadEvent:
        initial_sources = self.board.positions(kind, include_overlays=True)
        new_cells = set()
        floor_spawns = set()
        overlay_spawns = set()
        hits_player = False
        new_walls = set()

        for r, c in initial_sources:
            for nr, nc in self.board.neighbors4(r, c):
                tile_symbol = self.board.get(nr, nc)
                if tile_symbol.isdigit() or tile_symbol == "W":
                    continue

                overlay_kind = self.board.overlay_kind(nr, nc)
                tile_kind = overlay_kind or SYMBOL_TO_KIND.get(tile_symbol)
                effect = SPREAD_RULES.get((kind, tile_kind))
                if effect is None:
                    if tile_symbol == "P" and kind == "lava":
                        hits_player = True
                    continue

                if effect.hits_player:
                    hits_player = True

                if effect.convert_to_kind:
                    convert_symbol = KIND_TO_SYMBOL[effect.convert_to_kind]
                    if effect.convert_location == "source":
                        target_coord = (r, c)
                    else:
                        target_coord = (nr, nc)
                    self.board.set(*target_coord, convert_symbol)
                    if effect.convert_to_kind == "wall":
                        new_walls.add(target_coord)
                    continue

                if effect.spawn and (nr, nc) not in new_cells:
                    if tile_symbol in ("."):
                        floor_spawns.add((nr, nc))
                        new_cells.add((nr, nc))
                    elif tile_symbol in ("P","O") and kind == "aqua":
                        overlay_spawns.add((nr, nc))
                        new_cells.add((nr, nc))

        for pos in floor_spawns:
            self.board.add_entity(kind, pos)
        for pos in overlay_spawns:
            self.board.add_overlay(kind, pos)

        return SpreadEvent(
            kind=kind,
            sources=frozenset(initial_sources),
            new_cells=frozenset(new_cells),
            hits_player=hits_player,
            new_walls=frozenset(new_walls),
        )


class CounterSystem:
    def __init__(self, board: Board):
        self.board = board

    def tick(self) -> CounterEvent:
        result = self.board.tick_counters()
        return CounterEvent(
            removed=frozenset(result["removed"]),
            updated={coord: value for coord, value in result["updated"].items()},
        )
