from dataclasses import dataclass

from src.Board import Board
from src.level_data import LevelRepository
from src.rules_engine import (
    LavaContactRule,
    LavaSpreadHitRule,
    PlayerGoalRule,
    RulesEngine,
)
from src.systems import CounterSystem, MovementSystem, SpreadSystem


@dataclass
class GameContext:
    board: Board
    movement: MovementSystem
    spread: SpreadSystem
    counter: CounterSystem
    rules_engine: RulesEngine


class GameFactory:
    def __init__(self, levels_dir="levels", repository: LevelRepository | None = None):
        self.levels_dir = levels_dir
        self.repository = repository or LevelRepository(levels_dir)

    def create(self, level_number):
        layout = self.repository.load(level_number)
        board = Board(layout)
        movement = MovementSystem(board)
        spread = SpreadSystem(board)
        counter = CounterSystem(board)
        rules_engine = RulesEngine(
            handlers=[
                LavaContactRule(),
                PlayerGoalRule(),
                LavaSpreadHitRule(),
            ]
        )
        return GameContext(
            board=board,
            movement=movement,
            spread=spread,
            counter=counter,
            rules_engine=rules_engine,
        )
