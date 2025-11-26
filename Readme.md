# Lava & Aqua – Python Grid Game

Lava & Aqua is a small grid-based puzzle game written in Python.

You move a player on a board, push boxes, avoid lava, and sometimes use water (aqua) to block lava.  
Lava and aqua spread every turn, so you must think before you move.

The game can run in:

- **Text mode (CLI)** – in the terminal
- **Pygame mode** – simple graphics if you have Pygame installed

---

## 1. How to run

### Requirements

- Python 3.10+
- (Optional) `pygame` for the graphical version

Install pygame (optional):

```bash
pip install pygame
```

## Run the game

If your entry file is main.py (similar to the one in the question):
```bash
python main.py
```

The game will ask:

Level number
```bash
please write the level you need to play:
```

Renderer type
```bash
Run with Pygame renderer? (y/N):
```

Type y → run with Pygame window

Type n or press Enter → run in the terminal

Controls

Same controls for both modes:

W – up

S – down

A – left

D – right

R – restart level

U – undo last move (you can undo multiple turns)

Q – quit

## 2. Basic game rules

Board symbols:

P – player

G – goal

B – box

L – lava

A – aqua (water)

H – grate tile; blocks player/boxes but lava/aqua can spread across it

W – wall

. – floor (empty space)

0–9 – counter tiles (numbers that go down each turn)

Main rules:

You win if the player reaches the goal tile G.

You lose if:

The player moves onto lava.

Or lava spreads into the player’s cell.

Boxes B can be pushed if the tile behind them is allowed.

Lava and aqua spread one step per turn, following simple rules.

Number tiles (counters) go down every turn. When they reach zero, they disappear.

Undo:

- Press U to step back one full turn (your move plus spread/counters). You can undo multiple turns.

## 3. Project structure

Typical layout (your paths may be slightly different):
```bash

.
├── levels
│   ├── level_10.json
│   ├── level_11.json
│   ├── level_12.json
│   ├── level_13.json
│   ├── level_14.json
│   ├── level_15.json
│   ├── level_1.json
│   ├── level_2.json
│   ├── level_3.json
│   ├── level_4.json
│   ├── level_5.json
│   ├── level_6.json
│   ├── level_7.json
│   ├── level_8.json
│   └── level_9.json
├── main.py                 # Game entry point (CLI / renderer switch)
├── Readme.md
└── src
    ├── Board.py            # Board and board state logic
    ├── events.py           # Domain events (Move, Spread, Counter...)
    ├── factory.py          # GameFactory and GameContext
    ├── level_data.py       # Level loading and layout
    ├── renderer.py         # Pygame renderer (optional)
    ├── result.py           # Result type for outcomes (ok / blocked / win / lose)
    ├── rules_engine.py     # Rules engine (win/lose logic)
    ├── session.py          # GameSession: runs a full turn
    ├── solver.py           # auot solver game
    ├── systems.py          # Movement, spread, and counter systems
    └── tiles.py            # Tile types and interaction rules
```

## 4. Main entry – CLI loop

Example main file (similar to your code):
```python
from src.factory import GameFactory
from src.renderer import play_with_renderer
from src.session import GameSession

def print_board(grid):
    for row in grid:
        print(" ".join(row))
    print()

def game_loop(session: GameSession):
    board = session.board

    print_board(board.grid)
    print("Controls: W/A/S/D to move, Q to quit.\n")

    while True:
        cmd = input("Move (W/A/S/D/R or Q): ").strip().upper()

        if cmd == "Q":
            print("bye!")
            break
        elif cmd == "R":
            print("initial board.")
            session.reset()
            board = session.board
            print_board(board.grid)
            continue
        elif cmd not in ("W","A","S","D"):
            print("invalid key.")
            continue

        outcome = session.step(cmd).result
        board = session.board

        if outcome.status == "blocked":
            print(f"blocked: {outcome.reason or 'unknown'}")
            print_board(board.grid)
            continue
        
        if outcome.status == "win":
            print_board(board.grid)
            print("YOU WIN!")
            break

        if outcome.status == "lose":
            print_board(board.grid)
            print(f"YOU LOSE! ({outcome.reason or 'move failed'})")
            break

        print_board(board.grid)

def main():
    try:
        level = int(input("please write the level you need to play: ").strip())
    except ValueError:
        print("invalid level number.")
        return

    use_renderer = input("Run with Pygame renderer? (y/N): ").strip().lower() == "y"
    factory = GameFactory()
    if use_renderer:
        play_with_renderer(level, factory)
    else:
        session = GameSession(factory, level)
        game_loop(session)

if __name__ == '__main__':
    main()
```

This file:

Asks for level number.

Asks if you want Pygame.

Creates a GameSession or calls play_with_renderer.

In text mode, runs game_loop, which:

reads user input,

calls session.step(...),

checks if you win, lose, or are blocked,

prints the board.

## 5. Auto solver

You can let the game solve itself:

1) At startup, choose `a` for auto mode.
2) Choose solver: `b` for BFS (breadth-first) or `d` for DFS (depth-first).
3) Optionally show solver playback in Pygame.

Details:

- Solver uses the same rules as the player: move resolution, counters, lava/aqua spread, win/lose checks.
- Stats reported after solving: path length (moves), attempts (nodes expanded), visited states, and elapsed time.
- With Pygame playback, each solver step is animated with an overlay showing live stats (moves, attempts, visited, elapsed). After a win, the final stats remain on-screen for 3 minutes with a countdown.

## 5. Turn flow (what happens each move)

Every time you press W/A/S/D, one turn happens:

Movement

MovementSystem tries to move the player.

It may also push a box.

If move is impossible (wall, bad push…), the result is "blocked".

Counters

CounterSystem reduces all number tiles by 1.

Tiles that hit 0 are removed.

Spread

SpreadSystem spreads lava one step.

Then it spreads aqua one step.

The spread uses rules from tiles.py.

Rules check

RulesEngine looks at all events (move, spread, counters).

It decides if:

The player died on lava → "lose"

The player reached the goal → "win"

Lava spread into the player → "lose"

Nothing special → "ok"

Draw / print

CLI: the board is printed.

Pygame: the board is drawn on screen.

## 6. Core components
### 6.1 GameFactory & GameContext (factory.py)

```python
@dataclass
class GameContext:
    board: Board
    movement: MovementSystem
    spread: SpreadSystem
    counter: CounterSystem
    rules_engine: RulesEngine
```

GameFactory:

Loads level data via LevelRepository.

Creates a Board from the LevelLayout.

Creates systems:

MovementSystem

SpreadSystem

CounterSystem

Creates RulesEngine with these handlers:

LavaContactRule

PlayerGoalRule

LavaSpreadHitRule

Returns a GameContext with all of this.

### 6.2 GameSession (session.py)

GameSession owns the current GameContext and hides the details of each turn.

Key methods:
```python
__init__(factory, level_number)
```

Calls factory.create(level_number) to build context.

board property

Returns the current Board.

reset()

Creates a fresh context for the same level.

available_moves()

Asks MovementSystem which directions are allowed.

step(command: str) -> StepOutcome

Move the player with movement.move_player(command).

Tick counters with counter.tick().

Call spread.spread("lava") and spread.spread("aqua").

Let rules_engine.evaluate(...) decide status.

Attach available_moves to the result.

StepOutcome.result is a Result:
```python
Result(
  ok=True/False,
  status="ok" | "blocked" | "win" | "lose",
  reason="lava_hit" | "lava_spread_hit" | "wall" | ...,
  data={...}
)
```
### 6.3 Board & BoardState (Board.py)

BoardState holds the mutable state of the board:

grid – current symbols (P, L, A, boxes, numbers…)

base_grid – static layer (walls, goals, floor)

static_goals – list/set of goal positions

counters – positions and values of number tiles

entities – positions of dynamic things (player, lava, aqua, box)

overlays – hidden tiles under an entity
(for example: aqua under the player)

Important methods:

iter_cells() – iterate over all cells.

positions(kind, include_overlays=False) – positions for a given type ("lava", "aqua", "player", "box"…).

lava_positions, aqua_positions, box_positions – shortcuts.

is_goal_cell(r, c) – true if this cell is a goal.

get(r, c) – symbol on the grid.

set(r, c, symbol, preserve_symbol=None) – sets a cell, updates entities/overlays.

update_entity(kind, old_pos, new_pos, preserve_symbol=None) – moves an entity.

add_overlay(kind, pos) – store an overlay (e.g. aqua under player).

neighbors4(r, c) – up / down / left / right neighbors.

in_bounds(r, c) – checks board bounds.

tick_counters() – reduce counters and remove finished ones.

Board is a thin wrapper on BoardState:

Has a state inside.

For most methods, it forwards to the BoardState.

### 6.4 Tiles and rules (tiles.py)

TileType describes each tile:
```python
@dataclass(frozen=True)
class TileType:
    name: str          # e.g. "lava", "aqua", "player"
    symbol: str        # e.g. "L", "A", "P"
    category: str      # "floor", "hazard", "entity", ...
    dynamic: bool = False
    preserve_when_occupied: bool = False
```

There are registries:

TILE_TYPES

SYMBOL_TO_KIND

KIND_TO_SYMBOL

DYNAMIC_KINDS

Spread rules:

SpreadEffect describes what happens when one kind spreads onto another.

SPREAD_RULES[(source_kind, target_kind)] = SpreadEffect(...)

Examples:

Lava onto floor → spawn lava.

Lava onto player → mark hits_player=True.

Lava + aqua → turn into walls.

Box push rules:

PushEffect describes what happens when a box is pushed into a tile.

BOX_PUSH_RULES[target_kind] = PushEffect(...)

BOX_PUSH_BLOCKED for disallowed pushes.

### 6.5 Systems (systems.py)
MovementSystem

Handles:

Player movement

Box pushing

Checking if a move is allowed

Key points:

Uses KEY_TO_DELTA = {"W": (-1, 0), "A": (0, -1), "S": (1, 0), "D": (0, 1)}.

Checks:

Out of bounds → blocked

Wall → blocked

Counter (number tile) → blocked

Box → uses box push rules

Handles tiles with preserve_when_occupied (e.g. aqua):

When the player stands on aqua, aqua is stored as overlay.

When the player leaves, aqua comes back.

Returns a MovementResult:

ok: True/False

reason: e.g. "wall" or "blocked"

events: includes MoveEvent (and PushEvent if needed)

data: move info (from, to, etc.)

SpreadSystem

Spreads lava and aqua one step each turn.

Gets the current positions for the kind (lava or aqua).

For aqua, can include overlays (aqua under player still spreads).

For each source cell, checks 4 neighbors.

Uses SPREAD_RULES from tiles.py to decide:

Spawn new lava/aqua?

Hit the player?

Convert something to a wall?

Updates the board and returns a SpreadEvent.

CounterSystem

Simple system:

Calls board.tick_counters().

Returns a CounterEvent with:

removed counters

updated counters

### 6.6 Events (events.py)

Domain events:

PushEvent

MoveEvent

SpreadEvent

CounterEvent

Systems emit these.
RulesEngine reads them and decides the outcome.

### 6.7 RulesEngine (rules_engine.py)

Checks events for win/lose conditions.

Handlers:

LavaContactRule

If the player moved onto lava → lose with reason "lava_hit".

PlayerGoalRule

If the player landed on a goal → win.

LavaSpreadHitRule

If lava spread onto the player → lose with reason "lava_spread_hit".

RulesEngine.evaluate(events, base_data):

Runs each handler in order.

If a handler returns a Result, it stops and returns it.

If no handler returns anything, it returns:

Result(ok=True, status="ok", data=base_data)

## 7. Levels (level_data.py)

Levels are stored as JSON files (e.g. levels/level_1.json).

LevelLayout:

number – level number

rows, cols

raw_grid – original grid of symbols

base_grid – static layer (walls, goals, floor)

static_goals – positions of goals

LevelRepository:

Loads level_{n}.json.

Parses it into LevelLayout.

Builds the base_grid by:

Keeping walls and goals.

Turning other cells into . floor.

The Board uses LevelLayout as a base to create a mutable state.

## 8. Changing or extending the game

Some ideas:

Change how lava/aqua spread → edit SPREAD_RULES or SpreadSystem.

Change how boxes work → edit BOX_PUSH_RULES or the box logic in MovementSystem.

Add a new tile type:

Add a new TileType in tiles.py.

Update levels to use its symbol.

Update systems and rules to handle it.

Add new win/lose rules:

Create a new handler in rules_engine.py.

Add it to RulesEngine in GameFactory.
