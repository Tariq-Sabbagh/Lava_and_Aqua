from src.result import Result


class Rules:
    def __init__(self, board, actions):
        self.board = board
        self.actions = actions

    def apply_move(self, cmd):
        res = self.actions.player_move(cmd)
        if not res.ok:
            return res

        payload = res.data or {}
        target = payload.get("target")
        if target == "L":
            return Result(ok=False, status="lose", reason="lava_hit", data=res.data)
        if payload.get("on_goal"):
            return Result(ok=True, status="win", data=res.data)
        return Result(ok=True, status="ok", data=res.data)
    
    def apply_spread(self, kind):
        res = self.actions.spread(kind)
        if not res.ok:
            return res

        hits_player = bool((res.data or {}).get("hits_player"))
        if kind == "lava" and hits_player:
            return Result(ok=False, status="lose", reason=f"{kind}_spread_hit", data=res.data)
        return Result(ok=True, status="ok", data=res.data)

    def tick_counters(self):
        return self.actions.tick_counters()
