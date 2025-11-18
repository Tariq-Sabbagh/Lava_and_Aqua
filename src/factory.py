from dataclasses import dataclass

from src.Board import Board
from src.Move import Actions
from src.Rules import Rules
from src.level_data import LevelRepository


@dataclass
class GameContext:
    board: Board
    actions: Actions
    rules: Rules


class GameFactory:
    """Creates fully-wired game components for a given level."""

    def __init__(self, levels_dir="levels", repository: LevelRepository | None = None):
        self.levels_dir = levels_dir
        self.repository = repository or LevelRepository(levels_dir)

    def create(self, level_number):
        layout = self.repository.load(level_number)
        board = Board(layout)
        actions = Actions(board)
        rules = Rules(board, actions)
        return GameContext(board=board, actions=actions, rules=rules)
