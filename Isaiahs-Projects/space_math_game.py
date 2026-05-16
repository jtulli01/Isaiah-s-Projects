"""
╔══════════════════════════════════════════╗
║   Isaiah's Space Math Adventure! 🚀      ║
║   Destroy asteroids by solving math!     ║
╚══════════════════════════════════════════╝

HOW TO PLAY:
  - Asteroids fall from space, each showing a math problem.
  - Type your answer and press ENTER to fire the laser and blast it!
  - If an asteroid reaches the ground, you lose a life (3 lives total).
  - Earn points for each asteroid destroyed!

Controls:
  ENTER  = fire laser with your typed answer
  ESC    = return to the main menu
"""

import tkinter as tk
import random
import math

# ── Window & Layout ────────────────────────────────────────────────────────────
W, H = 860, 620          # canvas size
FPS_MS = 16              # ~60 fps (milliseconds per frame)
NUM_STARS = 200

# ── Difficulty Tuning ──────────────────────────────────────────────────────────
BASE_SPEED   = {1: 0.35, 2: 0.55, 3: 0.80}
SPAWN_FRAMES = {1: 160,  2: 120,  3: 90}    # frames between new asteroids
MAX_ASTEROIDS = {1: 2,   2: 3,    3: 4}     # max on screen at once
SPEED_BOOST  = 0.04      # extra speed per correct answer
MIN_SPAWN    = 55        # floor on spawn interval

# ── Colours ────────────────────────────────────────────────────────────────────
BG      = "#080818"
CYAN    = "#00e5ff"
YELLOW  = "#ffe600"
GREEN   = "#39ff14"
RED     = "#ff4444"
ORANGE  = "#ff8c00"
PINK    = "#ff77ff"
WHITE   = "white"

# ── Messages ───────────────────────────────────────────────────────────────────
HIT_MSGS = [
    "BOOM!  Asteroid destroyed!",
    "Direct hit, Commander!",
    "KABOOM!  Nice shot, Isaiah!",
    "Target eliminated!",
    "Stellar aim! ⭐",
    "PERFECT shot!",
]
MISS_MSGS = [
    "Asteroid escaped!  -1 Life ❤️",
    "Oh no — it got through!  -1 Life ❤️",
    "Shields hit!  -1 Life ❤️",
]

# ─────────────────────────────────────────────────────────────────────────────
#  Helper: draw a rounded rectangle on a canvas
# ─────────────────────────────────────────────────────────────────────────────
def rounded_rect(canvas, x1, y1, x2, y2, r=12, **kwargs):
    pts = [
        x1+r, y1,   x2-r, y1,
        x2,   y1,   x2,   y1+r,
        x2,   y2-r, x2,   y2,
        x2-r, y2,   x1+r, y2,
        x1,   y2,   x1,   y2-r,
        x1,   y1+r, x1,   y1,
        x1+r, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
#  Star — twinkling background dot
# ─────────────────────────────────────────────────────────────────────────────
class Star:
    _COLOURS = [WHITE, "#ccccff", "#ffcccc", "#ccffcc", "#ffffcc"]

    def __init__(self, canvas):
        self.canvas = canvas
        x = random.randint(0, W)
        y = random.randint(0, H)
        s = random.choice([1, 1, 1, 2, 2, 3])
        col = random.choice(self._COLOURS)
        self.id = canvas.create_oval(x, y, x+s, y+s, fill=col, outline="", tags="star")
        self._timer = random.randint(0, 80)
        self._on = True

    def tick(self):
        self._timer -= 1
        if self._timer <= 0:
            self._timer = random.randint(40, 130)
            col = random.choice(self._COLOURS) if self._on else BG
            self.canvas.itemconfig(self.id, fill=col)
            self._on = not self._on


# ─────────────────────────────────────────────────────────────────────────────
#  Asteroid — falling rock with a math question
# ─────────────────────────────────────────────────────────────────────────────
_ASTEROID_TEMPLATES = [
    [(0.0, -1.0), (0.6, -0.5), (0.9,  0.2), ( 0.4, 0.9), (-0.4, 1.0), (-0.9, 0.3), (-0.7, -0.6)],
    [(0.2, -1.0), (0.8, -0.3), (1.0,  0.4), ( 0.3, 1.0), (-0.5, 0.8), (-1.0, 0.1), (-0.6, -0.7)],
    [(0.0, -0.9), (0.7, -0.6), (1.0,  0.1), ( 0.5, 1.0), (-0.3, 0.9), (-0.9, 0.4), (-0.8, -0.5)],
    [(0.3, -1.0), (0.9, -0.2), (0.8,  0.6), ( 0.1, 1.0), (-0.6, 0.8), (-1.0, 0.0), (-0.5, -0.8)],
]
_ASTEROID_COLOURS = [
    ("#7B5E3A", "#C4A26A"),
    ("#5A5A6A", "#9999BB"),
    ("#6B6B3A", "#B0B070"),
    ("#6A3A3A", "#BB7070"),
]

class Asteroid:
    def __init__(self, canvas, question, answer, speed):
        self.canvas  = canvas
        self.answer  = answer
        self.x       = random.randint(80, W - 80)
        self.y       = -70
        self.size    = random.randint(48, 66)
        self.speed   = speed
        self._angle  = random.uniform(0, 360)
        self._spin   = random.uniform(-1.2, 1.2)
        self._shape  = random.choice(_ASTEROID_TEMPLATES)
        fill, out    = random.choice(_ASTEROID_COLOURS)
        pts          = self._poly()
        self.body    = canvas.create_polygon(pts, fill=fill, outline=out,
                                             width=2, tags="asteroid")
        self.label   = canvas.create_text(self.x, self.y, text=question,
                                          font=("Arial", 14, "bold"),
                                          fill=WHITE, tags="asteroid")

    def _poly(self):
        a = math.radians(self._angle)
        pts = []
        for fx, fy in self._shape:
            rx = fx * math.cos(a) - fy * math.sin(a)
            ry = fx * math.sin(a) + fy * math.cos(a)
            pts += [self.x + rx * self.size, self.y + ry * self.size]
        return pts

    def update(self):
        self.y      += self.speed
        self._angle += self._spin
        self.canvas.coords(self.body, self._poly())
        self.canvas.coords(self.label, self.x, self.y)

    def destroy(self):
        self.canvas.delete(self.body)
        self.canvas.delete(self.label)

    @property
    def past_bottom(self):
        return self.y > H + 70


# ─────────────────────────────────────────────────────────────────────────────
#  Explosion — particle burst
# ─────────────────────────────────────────────────────────────────────────────
_SPARK_COLOURS = ["#ff8800", "#ffff00", "#ff4400", "#ffcc00", WHITE, "#ff6666"]

class Explosion:
    def __init__(self, canvas, x, y):
        self.canvas    = canvas
        self._particles = []
        for _ in range(26):
            ang   = random.uniform(0, 2 * math.pi)
            spd   = random.uniform(2.5, 9)
            col   = random.choice(_SPARK_COLOURS)
            sz    = random.randint(3, 9)
            oid   = canvas.create_oval(x, y, x+sz, y+sz,
                                       fill=col, outline="", tags="explosion")
            self._particles.append({
                "id": oid, "x": float(x), "y": float(y),
                "dx": math.cos(ang)*spd, "dy": math.sin(ang)*spd,
                "life": random.randint(14, 26),
            })

    def update(self):
        alive = []
        for p in self._particles:
            p["x"]   += p["dx"]
            p["y"]   += p["dy"]
            p["dy"]  += 0.35      # gravity
            p["life"] -= 1
            if p["life"] > 0:
                self.canvas.coords(p["id"], p["x"], p["y"],
                                   p["x"]+5, p["y"]+5)
                alive.append(p)
            else:
                self.canvas.delete(p["id"])
        self._particles = alive

    @property
    def done(self):
        return not self._particles


# ─────────────────────────────────────────────────────────────────────────────
#  Rocket — player's ship at the bottom
# ─────────────────────────────────────────────────────────────────────────────
class Rocket:
    def __init__(self, canvas, x, y):
        self.canvas = canvas
        self.x, self.y = x, y
        self._frame = 0
        self._build()

    def _build(self):
        x, y = self.x, self.y
        # Body
        self._body = self.canvas.create_polygon(
            [x, y-46, x+20, y+22, x-20, y+22],
            fill="#dddddd", outline="#aaaaaa", width=2, tags="rocket")
        # Cockpit window
        self._window = self.canvas.create_oval(
            x-10, y-22, x+10, y-2,
            fill="#00ccff", outline=WHITE, width=2, tags="rocket")
        # Left fin
        self._fin_l = self.canvas.create_polygon(
            [x-20, y+22, x-38, y+40, x-20, y+8],
            fill="#cc2222", outline="#991111", width=1, tags="rocket")
        # Right fin
        self._fin_r = self.canvas.create_polygon(
            [x+20, y+22, x+38, y+40, x+20, y+8],
            fill="#cc2222", outline="#991111", width=1, tags="rocket")
        # Flame
        self._flame = self.canvas.create_polygon(
            [x-9, y+22, x+9, y+22, x, y+50],
            fill=ORANGE, outline="", tags="rocket")
        # Laser barrel (tiny)
        self._barrel = self.canvas.create_rectangle(
            x-3, y-50, x+3, y-46,
            fill="#aaaaaa", outline="", tags="rocket")

    def tick(self):
        """Flicker the engine flame."""
        self._frame += 1
        x, y = self.x, self.y
        tip_y = y + 22 + random.randint(12, 26)
        tip_x = x + random.randint(-4, 4)
        self.canvas.coords(self._flame, x-9, y+22, x+9, y+22, tip_x, tip_y)
        cols = [ORANGE, "#ffcc00", "#ff4400"]
        self.canvas.itemconfig(self._flame, fill=random.choice(cols))

    def fire_beam(self, target_x, target_y, frames=8):
        """Draw a quick laser beam from rocket to target."""
        x, y = self.x, self.y - 50
        beam = self.canvas.create_line(
            x, y, target_x, target_y,
            fill=CYAN, width=3, tags="beam")
        self.canvas.after(frames * FPS_MS,
                          lambda: self.canvas.delete(beam))


# ─────────────────────────────────────────────────────────────────────────────
#  Main Game
# ─────────────────────────────────────────────────────────────────────────────
class SpaceMathGame:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Isaiah's Space Math Adventure! 🚀")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self.canvas = tk.Canvas(root, width=W, height=H,
                                bg=BG, highlightthickness=0)
        self.canvas.pack()

        # Persistent background stars
        self._stars: list[Star] = []
        for _ in range(NUM_STARS):
            self._stars.append(Star(self.canvas))

        # Game objects
        self._asteroids:  list[Asteroid]  = []
        self._explosions: list[Explosion] = []
        self._rocket: Rocket | None       = None

        # State
        self._state        = "title"   # "title" | "playing" | "gameover"
        self._level        = 1
        self._score        = 0
        self._lives        = 3
        self._speed        = 0.0
        self._spawn_timer  = 0
        self._spawn_ivl    = 120
        self._frame        = 0

        # HUD canvas items
        self._hud_score = None
        self._hud_lives = None

        # Answer entry widget
        self._ans_var   = tk.StringVar()
        self._entry: tk.Entry | None     = None
        self._entry_win                  = None

        # Bindings
        self.root.bind("<Return>", self._on_enter)
        self.root.bind("<Escape>", lambda _e: self._go_menu())

        self._show_title()
        self._loop()

    # ── Title Screen ──────────────────────────────────────────────────────────
    def _show_title(self):
        self._state = "title"
        self.canvas.delete("ui", "hud", "asteroid", "rocket",
                           "explosion", "beam", "flash", "ground")
        self._asteroids.clear()
        self._explosions.clear()
        if self._entry:
            self._entry.destroy();  self._entry = None

        # Decorative planet (right)
        self.canvas.create_oval(630, 60, 840, 270,
                                fill="#334488", outline="#6699ff",
                                width=3, tags="ui")
        self.canvas.create_oval(618, 158, 852, 182,
                                fill="", outline="#aabbff",
                                width=4, tags="ui")
        # Moon (left)
        self.canvas.create_oval(30, 100, 120, 190,
                                fill="#888888", outline="#bbbbbb",
                                width=2, tags="ui")
        for cx, cy, r in [(55, 130, 8), (90, 155, 5), (48, 165, 6)]:
            self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                                    fill="#777777", outline="", tags="ui")

        # Title text
        self.canvas.create_text(W//2, 110,
            text="SPACE  MATH", font=("Arial Black", 56, "bold"),
            fill=CYAN, tags="ui")
        self.canvas.create_text(W//2, 180,
            text="A D V E N T U R E", font=("Arial", 26, "bold"),
            fill=YELLOW, tags="ui")
        self.canvas.create_text(W//2, 220,
            text="starring  Isaiah  🚀", font=("Arial", 18, "italic"),
            fill=PINK, tags="ui")

        # Big decorative rocket in centre
        self._draw_deco_rocket(W//2, 330)

        # Instruction
        self.canvas.create_text(W//2, 435,
            text="Asteroids are attacking!  Type the answer and press ENTER to blast them!",
            font=("Arial", 13), fill="#9999aa", tags="ui")

        # Level buttons
        self._btn(W//2 - 240, 500, "🟢  EASY",   "#1a6632", lambda: self._start(1))
        self._btn(W//2,        500, "🟡  MEDIUM", "#666600", lambda: self._start(2))
        self._btn(W//2 + 240,  500, "🔴  HARD",   "#882222", lambda: self._start(3))

    def _draw_deco_rocket(self, x, y):
        pts_body = [x, y-60, x+28, y+30, x-28, y+30]
        self.canvas.create_polygon(pts_body, fill="#cccccc",
                                   outline="#999999", width=2, tags="ui")
        self.canvas.create_oval(x-13, y-28, x+13, y-4,
                                fill="#00ccff", outline=WHITE, width=2, tags="ui")
        self.canvas.create_polygon([x-28, y+30, x-48, y+52, x-28, y+14],
                                   fill=RED, outline="#990000", tags="ui")
        self.canvas.create_polygon([x+28, y+30, x+48, y+52, x+28, y+14],
                                   fill=RED, outline="#990000", tags="ui")
        self.canvas.create_polygon([x-12, y+30, x+12, y+30, x, y+66],
                                   fill=ORANGE, outline="", tags="ui")

    def _btn(self, cx, cy, text, colour, cmd):
        bw, bh = 180, 50
        x1, y1, x2, y2 = cx-bw//2, cy-bh//2, cx+bw//2, cy+bh//2
        r = rounded_rect(self.canvas, x1, y1, x2, y2, r=10,
                         fill=colour, outline=WHITE, width=2, tags="ui")
        t = self.canvas.create_text(cx, cy, text=text,
                                    font=("Arial", 15, "bold"),
                                    fill=WHITE, tags="ui")
        for item in (r, t):
            self.canvas.tag_bind(item, "<Button-1>", lambda _e, c=cmd: c())
            self.canvas.tag_bind(item, "<Enter>",
                lambda _e, rr=r: self.canvas.itemconfig(rr, outline=YELLOW, width=3))
            self.canvas.tag_bind(item, "<Leave>",
                lambda _e, rr=r: self.canvas.itemconfig(rr, outline=WHITE, width=2))

    # ── Start Game ────────────────────────────────────────────────────────────
    def _start(self, level: int):
        self._level      = level
        self._score      = 0
        self._lives      = 3
        self._speed      = BASE_SPEED[level]
        self._spawn_ivl  = SPAWN_FRAMES[level]
        self._spawn_timer = 0    # spawn first asteroid immediately
        self._asteroids.clear()
        self._explosions.clear()

        self.canvas.delete("ui", "hud", "asteroid", "rocket",
                           "beam", "flash", "explosion", "ground")

        # Ground line
        self.canvas.create_line(0, H-50, W, H-50,
                                fill="#224422", width=2, tags="ground")

        # Rocket
        self._rocket = Rocket(self.canvas, W//2, H-80)

        # HUD
        lvl_name = {1: "EASY", 2: "MEDIUM", 3: "HARD"}[level]
        self.canvas.create_text(W//2, 14, anchor="n",
                                text=f"— {lvl_name} —",
                                font=("Arial", 13, "bold"),
                                fill=YELLOW, tags="hud")
        self._hud_score = self.canvas.create_text(
            10, 10, anchor="nw",
            text="Score: 0",
            font=("Arial", 16, "bold"), fill=GREEN, tags="hud")
        self._hud_lives = self.canvas.create_text(
            W-10, 10, anchor="ne",
            text=self._hearts(),
            font=("Arial", 16, "bold"), fill=RED, tags="hud")

        # Answer entry
        if self._entry:
            self._entry.destroy()
        self._ans_var.set("")
        self._entry = tk.Entry(
            self.root, textvariable=self._ans_var,
            font=("Arial", 24, "bold"), width=7,
            bg="#0a0a2a", fg=YELLOW, insertbackground=YELLOW,
            bd=3, relief="solid", justify="center")
        self._entry_win = self.canvas.create_window(
            W//2 + 55, H-22, window=self._entry, tags="entry_win")
        self.canvas.create_text(W//2 - 105, H-22,
            text="Answer ➤", font=("Arial", 15, "bold"),
            fill=CYAN, tags="hud")

        self._state = "playing"
        self._entry.focus_set()

    # ── Question Generator ────────────────────────────────────────────────────
    def _make_question(self):
        lv = self._level
        if lv == 1:
            n1 = random.randint(1, 10)
            n2 = random.randint(1, 10)
            op = random.choice(["+", "−"])
        elif lv == 2:
            n1 = random.randint(2, 20)
            n2 = random.randint(1, 10)
            op = random.choice(["+", "−", "×"])
        else:
            n1 = random.randint(1, 12)
            n2 = random.randint(1, 12)
            op = random.choice(["×", "+", "−"])

        if op == "+":
            ans = n1 + n2
        elif op == "−":
            if n1 < n2:
                n1, n2 = n2, n1
            ans = n1 - n2
        else:
            ans = n1 * n2

        return f"{n1} {op} {n2} = ?", ans

    # ── Player Input ──────────────────────────────────────────────────────────
    def _on_enter(self, _event=None):
        if self._state != "playing":
            return
        raw = self._ans_var.get().strip()
        self._ans_var.set("")
        if not raw.lstrip("-").isdigit():
            return
        player_ans = int(raw)

        # Hit the lowest matching asteroid
        target = None
        for ast in sorted(self._asteroids, key=lambda a: -a.y):
            if ast.answer == player_ans:
                target = ast
                break

        if target:
            if self._rocket:
                self._rocket.fire_beam(target.x, target.y)
            self._blast(target)
        else:
            # Wrong answer flash
            self._flash("Wrong answer — try again!", RED)

    def _blast(self, ast: Asteroid):
        self._asteroids.remove(ast)
        self._explosions.append(Explosion(self.canvas, ast.x, ast.y))
        ast.destroy()

        pts = {1: 15, 2: 20, 3: 30}[self._level]
        self._score += pts
        self._speed   = min(self._speed + SPEED_BOOST, 4.0)
        self._spawn_ivl = max(self._spawn_ivl - 1, MIN_SPAWN)
        self._refresh_hud()
        self._flash(random.choice(HIT_MSGS), GREEN)

    # ── Escape / Lost life ────────────────────────────────────────────────────
    def _asteroid_escaped(self, ast: Asteroid):
        self._asteroids.remove(ast)
        ast.destroy()
        self._lives -= 1
        self._refresh_hud()
        self._flash(random.choice(MISS_MSGS), RED)
        if self._lives <= 0:
            self.root.after(600, self._game_over)

    # ── HUD helpers ───────────────────────────────────────────────────────────
    def _hearts(self):
        return "Lives: " + "❤ " * self._lives + "  " + "🖤 " * (3 - self._lives)

    def _refresh_hud(self):
        if self._hud_score:
            self.canvas.itemconfig(self._hud_score, text=f"Score: {self._score}")
        if self._hud_lives:
            self.canvas.itemconfig(self._hud_lives, text=self._hearts())

    def _flash(self, msg: str, colour: str):
        item = self.canvas.create_text(
            W//2, H//2 - 80, text=msg,
            font=("Arial", 19, "bold"), fill=colour, tags="flash")
        self.root.after(1400, lambda: self.canvas.delete(item))

    # ── Game Over Screen ──────────────────────────────────────────────────────
    def _game_over(self):
        self._state = "gameover"
        if self._entry:
            self._entry.destroy();  self._entry = None
        self.canvas.delete("entry_win", "flash")
        for a in self._asteroids:
            a.destroy()
        self._asteroids.clear()

        # Panel
        rounded_rect(self.canvas, 160, 130, W-160, H-120,
                     r=20, fill="#000033", outline=CYAN, width=3, tags="ui")

        # Score rating
        if self._score >= 300:
            grade, grade_col = "S  RANK — LEGENDARY!", YELLOW
        elif self._score >= 200:
            grade, grade_col = "A  RANK — Outstanding!", GREEN
        elif self._score >= 120:
            grade, grade_col = "B  RANK — Great job!", CYAN
        elif self._score >= 60:
            grade, grade_col = "C  RANK — Good effort!", ORANGE
        else:
            grade, grade_col = "Keep practising, Cadet!", WHITE

        self.canvas.create_text(W//2, 210,
            text="MISSION COMPLETE" if self._lives > 0 else "MISSION FAILED",
            font=("Arial Black", 30, "bold"),
            fill=GREEN if self._lives > 0 else RED, tags="ui")
        self.canvas.create_text(W//2, 275,
            text=f"Score:  {self._score}",
            font=("Arial", 32, "bold"), fill=YELLOW, tags="ui")
        self.canvas.create_text(W//2, 335,
            text=grade, font=("Arial", 20, "bold"), fill=grade_col, tags="ui")
        self.canvas.create_text(W//2, 385,
            text="Isaiah, you're an awesome Math Commander! 🚀",
            font=("Arial", 14, "italic"), fill=PINK, tags="ui")

        self._btn(W//2 - 140, 460, "🔄  Play Again", "#1a4422",
                  lambda: self._start(self._level))
        self._btn(W//2 + 140, 460, "🏠  Main Menu", "#1a1a44",
                  self._go_menu)

    def _go_menu(self):
        self._state = "title"
        if self._entry:
            self._entry.destroy();  self._entry = None
        self.canvas.delete("ui", "hud", "asteroid", "rocket",
                           "explosion", "beam", "flash", "ground", "entry_win")
        for a in self._asteroids:
            a.destroy()
        self._asteroids.clear()
        self._explosions.clear()
        self._show_title()

    # ── Main Loop ─────────────────────────────────────────────────────────────
    def _loop(self):
        self._frame += 1

        # Twinkle a few stars every 4 frames
        if self._frame % 4 == 0:
            for s in random.sample(self._stars, 6):
                s.tick()

        if self._state == "playing":
            self._tick_game()

        self.root.after(FPS_MS, self._loop)

    def _tick_game(self):
        # Rocket flame flicker
        if self._rocket:
            self._rocket.tick()

        # Spawn asteroids
        self._spawn_timer -= 1
        if (self._spawn_timer <= 0
                and len(self._asteroids) < MAX_ASTEROIDS[self._level]):
            self._spawn_timer = self._spawn_ivl
            q, ans = self._make_question()
            self._asteroids.append(
                Asteroid(self.canvas, q, ans, self._speed))

        # Move / check asteroids
        escaped = [a for a in self._asteroids if a.past_bottom]
        for a in escaped:
            if self._state == "playing":   # guard against double-trigger
                self._asteroid_escaped(a)

        for a in self._asteroids:
            a.update()

        # Update explosions
        for ex in list(self._explosions):
            ex.update()
            if ex.done:
                self._explosions.remove(ex)


# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    SpaceMathGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
