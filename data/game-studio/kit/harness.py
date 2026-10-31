"""Run a Comet Arcade game headless : scripted rule tests and a bot, through QuickJS.

A game is one HTML file. Its `logic` block is pure JavaScript, so it runs here exactly as in the browser.

    report = run_tests(html, twist="shield")   # {"passed": bool, "total": n, "failures": [...], "bot": {...}}
    print(render(report))
"""
import json
import re

from quickjs_rs import Runtime
from quickjs_rs.errors import QuickJSError

LOGIC_RE = re.compile(r"/\* LOGIC:START \*/\n(.*?)/\* LOGIC:END \*/", re.S)
THEME_RE = re.compile(r"/\* THEME:START \*/\n(.*?)/\* THEME:END \*/", re.S)
BOT_RE = re.compile(r'<script id="bot">\n(.*?)</script>', re.S)
PURITY = """
Math.random = () => { throw new Error('Math.random is not allowed in the logic : use nextRandom(state)'); };
Date.now = () => { throw new Error('Date.now is not allowed in the logic'); };
"""
BOT_GAMES = 5
BOT_TICKS = 1500
BOT_MIN_MEAN_EATEN = 10


def logic_of(html):
    """The logic block of a game file."""
    return LOGIC_RE.search(html).group(1)


def normalize_theme(theme):
    """Force every sprite to 7 rows of 7 characters. The model miscounts rows now and then, and the drawing survives a trim."""
    fixed = json.loads(json.dumps(theme))
    for name, rows in fixed["sprites"].items():
        rows = [re.sub(r"[^#.]", ".", row)[:7].ljust(7, ".") for row in rows[:7]]
        fixed["sprites"][name] = rows + ["......."] * (7 - len(rows))
    return fixed


def splice(template, logic=None, theme=None):
    """Put a new logic block and theme into the template. Returns a complete game file."""
    html = template
    theme = normalize_theme(theme) if theme else None
    if logic is not None:
        html = LOGIC_RE.sub(lambda _: f"/* LOGIC:START */\n{logic.strip()}\n/* LOGIC:END */", html, count=1)
    if theme is not None:
        html = THEME_RE.sub(lambda _: f"/* THEME:START */\n{json.dumps(theme, indent=2)}\n/* THEME:END */", html, count=1)
    return html


class Game:
    """One loaded game in one QuickJS context. The state crosses the border as JSON."""

    def __init__(self, ctx, html):
        self.ctx = ctx
        self.lines = logic_of(html).splitlines()
        for source in (PURITY, logic_of(html), BOT_RE.search(html).group(1)):
            ctx.eval(source + "\n;0")    # the 0 keeps a last function from crossing into Python

    def crash(self, exc):
        """A crash as text : the error and the lines of the logic it passed through, innermost first."""
        # QuickJS names every frame eval_script, so frames of the harness and the bot are dropped by name.
        frames = re.findall(r"at (\S+) \(eval_script:(\d+)", getattr(exc, "stack", "") or "")
        frames = [(name, int(line)) for name, line in frames
                  if name not in ("<eval>", "botMove") and 1 < int(line) <= len(self.lines)]
        where = [f"{name}, line {line} : {self.lines[line - 1].strip()}" for name, line in frames[:3]]
        return f"crash, {type(exc).__name__}: {exc}" + (f", at {' <- '.join(where)}" if where else "")

    def init(self, seed=7):
        return json.loads(self.ctx.eval(f"JSON.stringify(init({seed}))"))

    def step(self, state, move=None):
        return json.loads(self.ctx.eval(f"JSON.stringify(step({json.dumps(state)}, {json.dumps(move)}))"))

    def steps(self, state, moves):
        for move in moves:
            state = self.step(state, move)
        return state

    def play(self, seed, ticks=BOT_TICKS):
        """The bot plays one game inside QuickJS, which is much faster than crossing the border per tick."""
        code = f"""(() => {{
          let s = init({seed}); let n = 0;
          while (!s.over && n < {ticks}) {{ s = step(s, botMove(s)); n++; }}
          return JSON.stringify({{ eaten: s.eaten, score: s.score, ticks: n, reason: s.reason, tickMs: s.tickMs,
                                  length: s.snake.length, comets: s.comets.length }});
        }})()"""
        return json.loads(self.ctx.eval(code))


def board(game, **changes):
    """A quiet board : a snake of three moving right, one far star, no comets. Tests change what they need."""
    state = game.init(7)
    state.update(snake=[{"x": 5, "y": 5}, {"x": 4, "y": 5}, {"x": 3, "y": 5}], dir="right",
                 stars=[{"x": 20, "y": 15}], comets=[], extras=[], eaten=0, score=0, tickMs=200, ticks=0)
    state.update(changes)
    return state


def comet(x, y, dx, dy):
    return {"x": x, "y": y, "dx": dx, "dy": dy}


def extra(x, y, kind):
    return {"x": x, "y": y, "kind": kind}


def expect(condition, message):
    if not condition:
        raise AssertionError(message)


def cells(items):
    return [(item["x"], item["y"]) for item in items]


# ---- the rules -------------------------------------------------------------
def t_init_contract(g):
    s = g.init(7)
    for field in ("snake", "dir", "stars", "comets", "extras", "score", "eaten", "tickMs", "ticks", "over", "reason", "seed"):
        expect(field in s, f"init(7) has no field {field}")
    expect(s["tickMs"] == 200, f"tickMs should start at 200, got {s['tickMs']}")
    expect(len(s["stars"]) == 1, f"init should place 1 star, got {len(s['stars'])}")


def t_two_comets(g):
    s = g.init(7)
    expect(len(s["comets"]) == 2, f"init should place 2 comets, got {len(s['comets'])}")
    expect(all(k in s["comets"][0] for k in ("x", "y", "dx", "dy")), f"a comet needs x, y, dx, dy, got {s['comets'][0]}")


def t_movement(g):
    s = g.step(board(g))
    expect(cells(s["snake"]) == [(6, 5), (5, 5), (4, 5)], f"snake should be at (6,5),(5,5),(4,5), got {cells(s['snake'])}")
    expect(s["ticks"] == 1, f"ticks should be 1 after one step, got {s['ticks']}")


def t_steering(g):
    s = g.step(board(g), "down")
    expect(s["dir"] == "down" and cells(s["snake"])[0] == (5, 6), f"input down should move the head to (5,6), got {cells(s['snake'])[0]}")


def t_no_reverse(g):
    s = g.step(board(g), "left")
    expect(s["dir"] == "right" and cells(s["snake"])[0] == (6, 5), f"input left while moving right must be ignored, head at {cells(s['snake'])[0]}, dir {s['dir']}")
    expect(not s["over"], "an ignored reverse input must not end the game")


def t_wrap(g):
    s = g.step(board(g, snake=[{"x": 23, "y": 5}, {"x": 22, "y": 5}, {"x": 21, "y": 5}]))
    expect(cells(s["snake"])[0] == (0, 5), f"head should wrap to (0,5), got {cells(s['snake'])[0]}")


def t_star_grows(g):
    s = g.step(board(g, stars=[{"x": 6, "y": 5}]))
    expect(not s["over"], f"eating a star must not end the game, got over={s['over']} reason={s['reason']}")
    expect(len(s["snake"]) == 4, f"eating a star should give length 4, got {len(s['snake'])}")
    expect(s["score"] == 1 and s["eaten"] == 1, f"score and eaten should be 1, got {s['score']} and {s['eaten']}")
    expect(len(s["stars"]) == 1 and cells(s["stars"]) != [(6, 5)], f"one new star should appear elsewhere, got {s['stars']}")


def t_comets_move(g):
    s = g.step(board(g, comets=[comet(10, 10, 1, 0), comet(23, 0, 1, 0), comet(0, 0, 0, -1)]))
    expect(cells(s["comets"]) == [(11, 10), (0, 0), (0, 17)], f"comets should move and wrap to (11,10),(0,0),(0,17), got {cells(s['comets'])}")


def t_comet_hit(g):
    s = g.step(board(g, comets=[comet(6, 3, 0, 1), comet(6, 4, 0, 1)]))   # the second comet reaches (6,5) with the head
    expect(s["over"] and s["reason"] == "comet", f"head and comet both on (6,5) should end the game with reason comet, got over={s['over']} reason={s['reason']}")


def t_comet_swap(g):
    s = g.step(board(g, comets=[comet(6, 5, -1, 0)]))
    expect(s["over"] and s["reason"] == "comet", f"head (5,5) to (6,5) and comet (6,5) to (5,5) swap cells, which should end the game, got over={s['over']}")


def t_comet_body(g):
    s = g.step(board(g, comets=[comet(4, 4, 0, 1)]))
    expect(not s["over"], f"a comet crossing the body at (4,5) must do nothing, got over={s['over']} reason={s['reason']}")


def t_self_hit(g):
    snake = [{"x": 5, "y": 5}, {"x": 6, "y": 5}, {"x": 6, "y": 6}, {"x": 5, "y": 6}, {"x": 4, "y": 6}]
    s = g.step(board(g, snake=snake, dir="down"))
    expect(s["over"] and s["reason"] == "self", f"head landing on body cell (5,6) should end the game with reason self, got over={s['over']} reason={s['reason']}")


def t_follow_tail(g):
    snake = [{"x": 5, "y": 5}, {"x": 6, "y": 5}, {"x": 6, "y": 6}, {"x": 5, "y": 6}]
    s = g.step(board(g, snake=snake, dir="down"))
    expect(not s["over"], f"the tail leaves (5,6) in this step, so the head may enter it, got over={s['over']} reason={s['reason']}")
    expect(cells(s["snake"])[0] == (5, 6), f"head should be at (5,6), got {cells(s['snake'])[0]}")


def t_speed_fifth(g):
    s = g.step(board(g, stars=[{"x": 6, "y": 5}], eaten=4, score=4))
    expect(s["tickMs"] == 180, f"the fifth star should lower tickMs from 200 to 180, got {s['tickMs']}")
    s = g.step(board(g, stars=[{"x": 6, "y": 5}], eaten=5, score=5, tickMs=180))
    expect(s["tickMs"] == 180, f"the sixth star must not change tickMs, got {s['tickMs']}")
    s = g.step(board(g, stars=[{"x": 6, "y": 5}], eaten=9, score=9, tickMs=180))
    expect(s["tickMs"] == 160, f"the tenth star should lower tickMs from 180 to 160, got {s['tickMs']}")


def t_speed_floor(g):
    s = g.step(board(g, stars=[{"x": 6, "y": 5}], eaten=69, score=69, tickMs=60))
    expect(s["tickMs"] == 60, f"tickMs never goes below 60, got {s['tickMs']}")


def t_more_comets(g):
    s = g.step(board(g, stars=[{"x": 6, "y": 5}], eaten=4, score=4, comets=[comet(12, 14, 1, 0)]))
    expect(len(s["comets"]) == 2, f"the fifth star should add a comet, 1 becomes 2, got {len(s['comets'])}")
    full = [comet(10 + i, 14, 1, 0) for i in range(6)]
    s = g.step(board(g, stars=[{"x": 6, "y": 5}], eaten=9, score=9, comets=full))
    expect(len(s["comets"]) == 6, f"never more than 6 comets, got {len(s['comets'])}")


def t_over_final(g):
    start = board(g, over=True, reason="comet", ticks=9)
    s = g.steps(start, ["up", None])
    expect(s == start, f"step on a finished game must return the same state, ticks {start['ticks']} became {s['ticks']}, snake {cells(s['snake'])[:2]}")


def t_pure(g):
    start = board(g, stars=[{"x": 6, "y": 5}], comets=[comet(10, 10, 1, 0)])
    code = f"""(() => {{ const s = {json.dumps(start)}; const before = JSON.stringify(s); step(s, 'down');
                         return JSON.stringify(s) === before; }})()"""
    expect(g.ctx.eval(code), "step changed the state it received ; it must work on a copy")


def t_replay(g):
    moves = ["down", None, "left", None, "up", None, "right", None, None, "down"] * 4
    a, b = g.steps(g.init(11), moves), g.steps(g.init(11), moves)
    expect(a == b, "two games with the same seed and inputs ended differently")


# ---- the twists ------------------------------------------------------------
def t_golden(g):
    s = g.step(board(g, stars=[{"x": 6, "y": 5}], eaten=2, score=2))
    golden = [e for e in s["extras"] if e["kind"] == "golden"]
    expect(len(golden) == 1, f"the third star should place one golden extra, got {s['extras']}")
    s = g.step(board(g, extras=[extra(6, 5, "golden")], score=4, eaten=4))
    expect(s["score"] == 7, f"a golden extra is worth 3, score 4 should become 7, got {s['score']}")
    expect(len(s["snake"]) == 3, f"a golden extra must not grow the snake, length {len(s['snake'])}")
    expect(s["eaten"] == 4, f"a golden extra must not change eaten, got {s['eaten']}")
    expect(s["extras"] == [], f"the golden extra should be removed, got {s['extras']}")


def t_wormhole(g):
    s = g.init(7)
    holes = [e for e in s["extras"] if e["kind"] == "wormhole"]
    expect(len(holes) == 2, f"init should place 2 wormhole extras, got {s['extras']}")
    pair = [extra(6, 5, "wormhole"), extra(15, 12, "wormhole")]
    s = g.step(board(g, extras=pair))
    expect(cells(s["snake"])[0] == (15, 12), f"head entering (6,5) should come out at (15,12), got {cells(s['snake'])[0]}")
    expect(len(s["snake"]) == 3, f"a wormhole must not change the length, got {len(s['snake'])}")
    expect(len(s["extras"]) == 2, f"wormholes stay on the board, got {s['extras']}")


def t_wormhole_arrival(g):
    pair = [extra(6, 5, "wormhole"), extra(15, 12, "wormhole")]
    s = g.step(board(g, extras=pair, stars=[{"x": 15, "y": 12}]))
    expect(s["eaten"] == 1, f"a star on the exit wormhole cell should be eaten on arrival, eaten {s['eaten']}")
    s = g.step(board(g, extras=pair, comets=[comet(15, 11, 0, 1)]))
    expect(s["over"] and s["reason"] == "comet", f"a comet reaching the exit cell should hit the head there, got over={s['over']}")


def t_shield(g):
    expect(g.init(7).get("shield") is False, "init should set shield to false")
    s = g.step(board(g, stars=[{"x": 6, "y": 5}], eaten=3, score=3, shield=False))
    expect(len([e for e in s["extras"] if e["kind"] == "shield"]) == 1, f"the fourth star should place one shield extra, got {s['extras']}")
    s = g.step(board(g, extras=[extra(6, 5, "shield")], shield=False))
    expect(s["shield"] is True and s["extras"] == [], f"picking up a shield sets shield true and removes the extra, got shield={s['shield']} extras={s['extras']}")


def t_shield_hit(g):
    s = g.step(board(g, shield=True, comets=[comet(6, 4, 0, 1), comet(10, 14, 1, 0)]))
    expect(not s["over"], f"a shielded hit must not end the game, got reason {s['reason']}")
    expect(s["shield"] is False, f"the hit should use up the shield, got shield={s['shield']}")
    expect(len(s["comets"]) == 1, f"the comet that hit should be removed, got {s['comets']}")
    s = g.step(board(g, shield=False, comets=[comet(6, 4, 0, 1)]))
    expect(s["over"] and s["reason"] == "comet", f"without a shield a hit ends the game, got over={s['over']}")


def t_clock(g):
    expect(g.init(7).get("frozen") == 0, "init should set frozen to 0")
    s = g.step(board(g, stars=[{"x": 6, "y": 5}], eaten=3, score=3, frozen=0))
    expect(len([e for e in s["extras"] if e["kind"] == "clock"]) == 1, f"the fourth star should place one clock extra, got {s['extras']}")
    s = g.step(board(g, extras=[extra(6, 5, "clock")], frozen=0))
    expect(s["frozen"] == 20 and s["extras"] == [], f"picking up a clock sets frozen to 20 and removes it, got frozen={s['frozen']} extras={s['extras']}")


def t_clock_freeze(g):
    s = g.step(board(g, frozen=2, comets=[comet(10, 10, 1, 0)]))
    expect(cells(s["comets"]) == [(10, 10)] and s["frozen"] == 1, f"frozen comets stay and frozen counts down, comets {cells(s['comets'])} frozen {s['frozen']}")
    s = g.step(board(g, frozen=0, comets=[comet(10, 10, 1, 0)]))
    expect(cells(s["comets"]) == [(11, 10)], f"at frozen 0 comets move again, got {cells(s['comets'])}")


CORE = {
    "init-contract": (t_init_contract, "the state has every field"),
    "two-comets": (t_two_comets, "rule 5, init places 2 comets"),
    "movement": (t_movement, "rule 1, one cell per step"),
    "steering": (t_steering, "rule 2, an input turns the snake"),
    "no-reverse": (t_no_reverse, "rule 2, the opposite input is ignored"),
    "wrap": (t_wrap, "rule 3, space wraps"),
    "star-grows": (t_star_grows, "rule 4, eating a star grows the snake"),
    "comets-move": (t_comets_move, "rule 6, comets move and wrap"),
    "comet-hit": (t_comet_hit, "rule 7, a comet ends the game"),
    "comet-swap": (t_comet_swap, "rule 7, head and comet swapping cells ends the game"),
    "comet-body": (t_comet_body, "rule 7, a comet crossing the body does nothing"),
    "self-hit": (t_self_hit, "rule 8, the head on the body ends the game"),
    "follow-tail": (t_follow_tail, "rule 8, the tail cell is free in the step it leaves"),
    "speed-fifth": (t_speed_fifth, "rule 9, every fifth star speeds up"),
    "speed-floor": (t_speed_floor, "rule 9, never below 60 ms"),
    "more-comets": (t_more_comets, "rule 10, every fifth star adds a comet, up to 6"),
    "over-final": (t_over_final, "rule 11, game over is final"),
    "pure": (t_pure, "step leaves its input untouched"),
    "replay": (t_replay, "same seed and inputs, same game"),
}
TWISTS = {
    "golden": {"golden": (t_golden, "twist, golden stars")},
    "wormhole": {"wormhole": (t_wormhole, "twist, wormholes"), "wormhole-arrival": (t_wormhole_arrival, "twist, the exit cell counts")},
    "shield": {"shield": (t_shield, "twist, shield pickup"), "shield-hit": (t_shield_hit, "twist, a shield absorbs one hit")},
    "clock": {"clock": (t_clock, "twist, clock pickup"), "clock-freeze": (t_clock_freeze, "twist, frozen comets")},
}


def run_tests(html, twist=None, bot=True):
    """Run every rule test on one game file, then let the bot play. Returns a report dict."""
    report = {"twist": twist, "total": 0, "failures": [], "bot": None, "passed": False}
    tests = {**CORE, **TWISTS.get(twist, {})}
    report["total"] = len(tests)
    try:
        with Runtime(memory_limit=64 * 1024 * 1024) as runtime, runtime.new_context(timeout=20.0) as ctx:
            try:
                game = Game(ctx, html)
            except (QuickJSError, AttributeError) as exc:
                report["failures"].append({"test": "loads", "rule": "the logic block runs", "message": f"{type(exc).__name__}: {exc}"})
                return report
            for name, (test, rule) in tests.items():
                try:
                    test(game)
                except AssertionError as exc:
                    report["failures"].append({"test": name, "rule": rule, "message": str(exc)})
                except (QuickJSError, ValueError, KeyError, TypeError) as exc:
                    report["failures"].append({"test": name, "rule": rule, "message": game.crash(exc)})
            if bot:
                try:
                    games = [game.play(seed) for seed in range(1, BOT_GAMES + 1)]
                    mean = sum(item["eaten"] for item in games) / len(games)
                    report["bot"] = {"games": games, "mean_eaten": mean, "best_score": max(item["score"] for item in games)}
                    if mean < BOT_MIN_MEAN_EATEN:
                        report["failures"].append({"test": "bot-score", "rule": "the bot can play the game",
                                                   "message": f"the bot ate {mean:.1f} stars on average over {BOT_GAMES} games, at least {BOT_MIN_MEAN_EATEN} expected. Games : {games}"})
                except QuickJSError as exc:
                    report["failures"].append({"test": "bot-plays", "rule": "the bot can play the game", "message": game.crash(exc)})
    except QuickJSError as exc:
        report["failures"].append({"test": "runtime", "rule": "the game runs", "message": f"{type(exc).__name__}: {exc}"})
    report["passed"] = not report["failures"]
    return report


def render(report):
    """The report as plain text, one line per failed test."""
    failed = [item for item in report["failures"] if item["test"] not in ("bot-score", "bot-plays")]
    ran = not any(item["test"] in ("loads", "runtime") for item in report["failures"])
    lines = [f"{report['total'] - len(failed) if ran else 0} of {report['total']} rule tests pass"]
    if report["bot"]:
        lines.append(f"bot : {report['bot']['mean_eaten']:.1f} stars on average, best score {report['bot']['best_score']}")
    lines += [f"FAIL {item['test']} ({item['rule']}) : {item['message']}" for item in report["failures"]]
    return "\n".join(lines)
