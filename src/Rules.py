
class Rules:
    def __init__(self, board):
        self.board = board  

    @property
    def grid(self):
        return self.board.grid

    @property
    def rows(self):
        return self.board.row

    @property
    def cols(self):
        return self.board.col


    def is_goal(self , r , c): return self.grid[r][c] == "G"

    def apply_move(self, actions, cmd):
        res = actions.player_move(cmd)
        if not res["ok"]:
            return {"ok": False, "status": "blocked", "reason": res["reason"]}

        t = res.get("target")
        if t == "L":
            return {"ok": False, "status": "lose", "reason": "lava_hit"}
        if t == "G":
            return {"ok": True,  "status": "win"}
        return {"ok": True, "status": "ok"}
    
    def apply_spread(self, actions, kind):
        spr = actions.spread(kind)
        new_cells = spr.get("effects", {}).get("new_cells", set())
        hits_player = spr.get("status")
        if hits_player == "lose":
            return {"ok": False, "status": "lose", "reason": f"{kind}_spread_hit"}
        return {"ok": True, "status": "ok", "effects": spr.get("effects", {})}
