from dataclasses import dataclass

from src.Board import Board
from src.Move import Actions
from src.Rules import Rules


@dataclass
class GameContext:
    board: Board
    actions: Actions
    rules: Rules


class GameFactory:
    """Creates fully-wired game components for a given level."""

    def __init__(self, levels_dir="levels"):
        self.levels_dir = levels_dir

    def create(self, level_number):
        board = Board(level_number, base_dir=self.levels_dir)
        actions = Actions(board)
        rules = Rules(board, actions)
        return GameContext(board=board, actions=actions, rules=rules)
