from __future__ import annotations

import copy
from collections import deque
from dataclasses import dataclass
from typing import Iterable, List, Optional

from src.factory import GameFactory
from src.result import Result

Move = str
MOVES: List[Move] = ["W", "A", "S", "D"]


@dataclass
class Node:
    state: object
    parent: Optional["Node"]
    action: Optional[Move]


@dataclass
class SolveResult:
    moves: List[Move]
    attempts: int
    visited: int


class StackFrontier:
    def __init__(self):
        self._stack: List[Node] = []

    def add(self, node: Node):
        self._stack.append(node)

    def empty(self) -> bool:
        return not self._stack

    def remove(self) -> Node:
        if self.empty():
            raise Exception("empty frontier")
        return self._stack.pop()


class QueueFrontier(StackFrontier):
    def remove(self) -> Node:
        if self.empty():
            raise Exception("empty frontier")
        return self._stack.pop(0)


class BFSSolver:
    def __init__(self, factory: GameFactory, level_number: int):
        self.factory = factory
        self.level_number = level_number

    def solve(self) -> SolveResult | None:
        context = self.factory.create(self.level_number)
        start_state = copy.deepcopy(context.board.state)

        start = Node(state=start_state, parent=None, action=None)
        frontier = QueueFrontier()
        frontier.add(start)
        visited = {start_state.signature()}
        attempts = 0

        while not frontier.empty():
            node = frontier.remove()
            attempts += 1
            status, _ = self._is_goal(node.state)
            if status == "win":
                path = self._backtrack(node)
                return SolveResult(moves=path, attempts=attempts, visited=len(visited))

            for action in MOVES:
                result_state, result_status = self._simulate(node.state, action)
                if result_state is None:
                    continue
                sig = result_state.signature()
                if sig in visited:
                    continue
                visited.add(sig)
                child = Node(state=result_state, parent=node, action=action)
                if result_status == "win":
                    path = self._backtrack(child)
                    return SolveResult(moves=path, attempts=attempts + 1, visited=len(visited))
                if result_status != "lose":
                    frontier.add(child)

        return None

    # ---------------------------------------------------- Helpers

    def _simulate(self, state, action: Move):
        ctx = self.factory.create(self.level_number)
        ctx.board.state = copy.deepcopy(state)

        movement = ctx.movement.move_player(action)
        if not movement.ok:
            return None, movement.reason

        events: list[object] = list(movement.events)
        counter_event = ctx.counter.tick()
        events.append(counter_event)
        for kind in ("aqua", "lava"):
            spread_event = ctx.spread.spread(kind)
            events.append(spread_event)

        result = ctx.rules_engine.evaluate(events, movement.data)
        return ctx.board.state, result.status

    def _is_goal(self, state) -> tuple[str, Optional[str]]:
        ctx = self.factory.create(self.level_number)
        ctx.board.state = copy.deepcopy(state)
        events: Iterable[object] = []
        result = ctx.rules_engine.evaluate(list(events), {})
        return result.status, result.reason

    def _backtrack(self, node: Node) -> List[Move]:
        actions: List[Move] = []
        while node.parent is not None and node.action is not None:
            actions.append(node.action)
            node = node.parent
        actions.reverse()
        return actions


class DFSSolver(BFSSolver):
    def solve(self) -> SolveResult | None:
        context = self.factory.create(self.level_number)
        start_state = copy.deepcopy(context.board.state)

        start = Node(state=start_state, parent=None, action=None)
        frontier = StackFrontier()
        frontier.add(start)
        visited = {start_state.signature()}
        attempts = 0

        while not frontier.empty():
            node = frontier.remove()
            attempts += 1
            status, _ = self._is_goal(node.state)
            if status == "win":
                path = self._backtrack(node)
                return SolveResult(moves=path, attempts=attempts, visited=len(visited))

            for action in MOVES:
                result_state, result_status = self._simulate(node.state, action)
                if result_state is None:
                    continue
                sig = result_state.signature()
                if sig in visited:
                    continue
                visited.add(sig)
                child = Node(state=result_state, parent=node, action=action)
                if result_status == "win":
                    path = self._backtrack(child)
                    return SolveResult(moves=path, attempts=attempts + 1, visited=len(visited))
                if result_status != "lose":
                    frontier.add(child)

        return None
