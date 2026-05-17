# -*- coding: utf-8 -*-
"""
Isaiah's Space Math Adventure! -- Web/iPad Edition
Built with Pygame + Pygbag

HOW TO RUN ON PC (for testing):
  pip install pygame-ce pygbag
  python -m pygbag space_math_web/
  Open http://localhost:8000 in any browser

On iPad: open the hosted URL in Safari.

HOW TO PLAY:
  Asteroids fall -- each shows a math problem.
  Tap number buttons (or type on keyboard) then
  press FIRE to blast the asteroid with your answer!
  Lose a life if an asteroid hits the ground.
"""

# ─────────────────────────────────────────────────────────────────────────────
#  Imports
# ─────────────────────────────────────────────────────────────────────────────
import asyncio
import array
import pygame
import random
import math

print("=== SCRIPT LOADED ===")

# ─────────────────────────────────────────────────────────────────────────────
#  Window / timing
# ─────────────────────────────────────────────────────────────────────────────
W, H   = 800, 700
FPS    = 60
SR     = 22050          # audio sample rate

# ─────────────────────────────────────────────────────────────────────────────
#  Difficulty tables
# ─────────────────────────────────────────────────────────────────────────────
BASE_SPEED    = {1: 0.40, 2: 0.65, 3: 0.95}
SPAWN_FRAMES  = {1: 180,  2: 130,  3: 95}
MAX_ASTEROIDS = {1: 2,    2: 3,    3: 4}
SPEED_BOOST   = 0.04
MIN_SPAWN     = 55

# ─────────────────────────────────────────────────────────────────────────────
#  Colours  (R, G, B tuples)
# ─────────────────────────────────────────────────────────────────────────────
BG         = (8,   8,  24)
CYAN       = (0,  229, 255)
YELLOW     = (255, 230,  0)
GREEN      = (57,  255, 20)
RED        = (255,  68, 68)
ORANGE     = (255, 140,  0)
PINK       = (255, 119, 255)
WHITE      = (255, 255, 255)
DARK_BLUE  = (0,   0,  51)
GRAY       = (150, 150, 150)
DIM_GRAY   = (50,  50,  80)

# Ground line Y — asteroids that pass this cost a life
GROUND_Y   = 490
# Rocket sits just above the ground
ROCKET_Y   = 448
# Numpad top — everything below this is the input strip
PAD_TOP    = 502


# ─────────────────────────────────────────────────────────────────────────────
#  8-BIT SOUND GENERATION
#  Synthesised from scratch using array.array + pygame buffer interface.
#  No external files, no `wave` or `io` modules needed.
# ─────────────────────────────────────────────────────────────────────────────

def _samples_to_sound(samples: array.array) -> pygame.mixer.Sound:
    """Wrap a mono 16-bit PCM array into a pygame Sound via buffer interface."""
    return pygame.mixer.Sound(buffer=samples)


def _square(freq: float, t: float) -> float:
    return 1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0


def _sine(freq: float, t: float) -> float:
    return math.sin(2 * math.pi * freq * t)


def _noise() -> float:
    return random.random() * 2.0 - 1.0


def make_laser_sound() -> pygame.mixer.Sound:
    n = int(SR * 0.15)
    buf = array.array("h")
    for i in range(n):
        t    = i / SR
        freq = 900 * (1.0 - i / n * 0.8) + 200
        env  = 1.0 - i / n * 0.4
        buf.append(int(_square(freq, t) * env * 0.55 * 32767))
    return _samples_to_sound(buf)


def make_explosion_sound() -> pygame.mixer.Sound:
    n = int(SR * 0.45)
    buf = array.array("h")
    for i in range(n):
        env = (1.0 - i / n) ** 1.5
        buf.append(int(_noise() * env * 0.65 * 32767))
    return _samples_to_sound(buf)


def make_correct_sound() -> pygame.mixer.Sound:
    notes = [523, 659, 784, 1047]
    buf = array.array("h")
    note_len = int(SR * 0.10)
    for freq in notes:
        for i in range(note_len):
            t   = i / SR
            env = 1.0 if i < note_len * 0.7 else (note_len - i) / (note_len * 0.3)
            buf.append(int(_square(freq, t) * env * 0.45 * 32767))
    return _samples_to_sound(buf)


def make_wrong_sound() -> pygame.mixer.Sound:
    n = int(SR * 0.22)
    buf = array.array("h")
    for i in range(n):
        t   = i / SR
        env = 1.0 - i / n * 0.3
        buf.append(int(_square(175, t) * env * 0.50 * 32767))
    return _samples_to_sound(buf)


def make_miss_sound() -> pygame.mixer.Sound:
    notes = [440, 370, 294]
    buf = array.array("h")
    note_len = int(SR * 0.12)
    for freq in notes:
        for i in range(note_len):
            t   = i / SR
            env = 1.0 - i / note_len
            buf.append(int(_sine(freq, t) * env * 0.55 * 32767))
    return _samples_to_sound(buf)


def make_gameover_sound() -> pygame.mixer.Sound:
    notes = [392, 370, 349, 330, 262]
    buf = array.array("h")
    note_len = int(SR * 0.20)
    for freq in notes:
        for i in range(note_len):
            t   = i / SR
            env = max(0.0, 1.0 - i / (note_len * 1.1))
            sq  = _square(freq, t)
            buf.append(int(sq * env * 0.50 * 32767))
    return _samples_to_sound(buf)


def load_sounds() -> dict:
    """Load all synthesised sound effects; returns {} if mixer unavailable."""
    if not pygame.mixer.get_init():
        return {}
    try:
        return {
            "laser":    make_laser_sound(),
            "explode":  make_explosion_sound(),
            "correct":  make_correct_sound(),
            "wrong":    make_wrong_sound(),
            "miss":     make_miss_sound(),
            "gameover": make_gameover_sound(),
        }
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────────────────────
#  STAR — twinkling background dot
# ─────────────────────────────────────────────────────────────────────────────
_STAR_COLOURS = [WHITE, (200, 200, 255), (255, 200, 200), (200, 255, 200), (255, 255, 200)]


class Star:
    def __init__(self):
        self.x     = random.randint(0, W)
        self.y     = random.randint(0, H)
        self.size  = random.choice([1, 1, 1, 2, 2])
        self.col   = random.choice(_STAR_COLOURS)
        self._timer   = random.randint(0, 100)
        self._visible = True

    def update(self):
        self._timer -= 1
        if self._timer <= 0:
            self._timer   = random.randint(40, 130)
            self._visible = not self._visible

    def draw(self, surface: pygame.Surface):
        if self._visible:
            pygame.draw.circle(surface, self.col, (self.x, self.y), self.size)


# ─────────────────────────────────────────────────────────────────────────────
#  ASTEROID — spinning polygon with a math question
# ─────────────────────────────────────────────────────────────────────────────
_ASTEROID_SHAPES = [
    [(0.0, -1.0), (0.6, -0.5), (0.9,  0.2), ( 0.4, 0.9),
     (-0.4, 1.0), (-0.9, 0.3), (-0.7, -0.6)],
    [(0.2, -1.0), (0.8, -0.3), (1.0,  0.4), ( 0.3, 1.0),
     (-0.5, 0.8), (-1.0, 0.1), (-0.6, -0.7)],
    [(0.0, -0.9), (0.7, -0.6), (1.0,  0.1), ( 0.5, 1.0),
     (-0.3, 0.9), (-0.9, 0.4), (-0.8, -0.5)],
    [(0.3, -1.0), (0.9, -0.2), (0.8,  0.6), ( 0.1, 1.0),
     (-0.6, 0.8), (-1.0, 0.0), (-0.5, -0.8)],
]
_ASTEROID_COLOURS = [
    ((123,  94,  58), (196, 162, 106)),
    (( 90,  90, 106), (153, 153, 187)),
    ((107, 107,  58), (176, 176, 112)),
    ((106,  58,  58), (187, 112, 112)),
]


class Asteroid:
    def __init__(self, question: str, answer: int, speed: float,
                 font: pygame.font.Font):
        self.answer   = answer
        self.x        = float(random.randint(80, W - 80))
        self.y        = -70.0
        self.size     = random.randint(48, 66)
        self.speed    = speed
        self._angle   = random.uniform(0, 360)
        self._spin    = random.uniform(-1.5, 1.5)
        self._shape   = random.choice(_ASTEROID_SHAPES)
        self._fill, self._outline = random.choice(_ASTEROID_COLOURS)
        # Pre-render question text
        self._text = font.render(question, True, WHITE)

    def _poly(self) -> list[tuple[float, float]]:
        a = math.radians(self._angle)
        cos_a, sin_a = math.cos(a), math.sin(a)
        return [
            (self.x + (fx * cos_a - fy * sin_a) * self.size,
             self.y + (fx * sin_a + fy * cos_a) * self.size)
            for fx, fy in self._shape
        ]

    def update(self):
        self.y      += self.speed
        self._angle += self._spin

    def draw(self, surface: pygame.Surface):
        pts = self._poly()
        pygame.draw.polygon(surface, self._fill,    pts)
        pygame.draw.polygon(surface, self._outline, pts, 2)
        r = self._text.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(self._text, r)

    @property
    def past_bottom(self) -> bool:
        return self.y > GROUND_Y + 70


# ─────────────────────────────────────────────────────────────────────────────
#  EXPLOSION — particle burst
# ─────────────────────────────────────────────────────────────────────────────
_SPARK_COLOURS = [
    (255, 136,   0), (255, 255,   0), (255,  68,   0),
    (255, 204,   0), (255, 255, 255), (255, 102, 102),
]


class Explosion:
    MAX_LIFE = 28

    def __init__(self, x: float, y: float):
        self._particles = []
        for _ in range(30):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(2.5, 10.0)
            self._particles.append({
                "x":    float(x),          "y":    float(y),
                "dx":   math.cos(ang) * spd, "dy":   math.sin(ang) * spd,
                "col":  random.choice(_SPARK_COLOURS),
                "sz":   random.randint(3, 9),
                "life": random.randint(15, self.MAX_LIFE),
            })

    def update(self):
        alive = []
        for p in self._particles:
            p["x"]    += p["dx"]
            p["y"]    += p["dy"]
            p["dy"]   += 0.35          # gravity
            p["life"] -= 1
            if p["life"] > 0:
                alive.append(p)
        self._particles = alive

    def draw(self, surface: pygame.Surface):
        for p in self._particles:
            alpha = p["life"] / self.MAX_LIFE
            col   = tuple(int(c * alpha) for c in p["col"])
            pygame.draw.circle(surface, col,
                               (int(p["x"]), int(p["y"])), p["sz"])

    @property
    def done(self) -> bool:
        return not self._particles


# ─────────────────────────────────────────────────────────────────────────────
#  ROCKET — player's ship
# ─────────────────────────────────────────────────────────────────────────────
class Rocket:
    def __init__(self, x: int, y: int):
        self.x, self.y = x, y

    def draw(self, surface: pygame.Surface):
        x, y = self.x, self.y

        # Engine flame — flickering tip
        tip_y = y + 22 + random.randint(14, 28)
        tip_x = x + random.randint(-4, 4)
        flame_col = random.choice([ORANGE, (255, 204, 0), (255, 68, 0)])
        pygame.draw.polygon(surface, flame_col,
                            [(x - 10, y + 22), (x + 10, y + 22), (tip_x, tip_y)])

        # Body
        pygame.draw.polygon(surface, (221, 221, 221),
                            [(x, y - 46), (x + 22, y + 22), (x - 22, y + 22)])
        pygame.draw.polygon(surface, (170, 170, 170),
                            [(x, y - 46), (x + 22, y + 22), (x - 22, y + 22)], 2)

        # Fins
        pygame.draw.polygon(surface, (204, 34, 34),
                            [(x - 22, y + 22), (x - 40, y + 42), (x - 22, y + 8)])
        pygame.draw.polygon(surface, (204, 34, 34),
                            [(x + 22, y + 22), (x + 40, y + 42), (x + 22, y + 8)])

        # Cockpit window
        pygame.draw.ellipse(surface, (0, 204, 255), (x - 11, y - 23, 22, 22))
        pygame.draw.ellipse(surface, WHITE,         (x - 11, y - 23, 22, 22), 2)

        # Laser barrel
        pygame.draw.rect(surface, GRAY, (x - 3, y - 52, 6, 6))

    @property
    def barrel_tip(self) -> tuple[int, int]:
        return (self.x, self.y - 52)


# ─────────────────────────────────────────────────────────────────────────────
#  LASER BEAM — brief line from rocket to target
# ─────────────────────────────────────────────────────────────────────────────
class Beam:
    def __init__(self, x1: int, y1: int, x2: int, y2: int, frames: int = 14):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self._life = frames
        self._max  = frames

    def update(self):
        self._life -= 1

    def draw(self, surface: pygame.Surface):
        if self._life <= 0:
            return
        alpha = self._life / self._max
        # Core bright beam
        pygame.draw.line(surface, CYAN,
                         (self.x1, self.y1), (self.x2, self.y2), 3)
        # Soft glow (semi-transparent overlay)
        glow = pygame.Surface((W, H), pygame.SRCALPHA)
        glow_col = (0, 229, 255, int(60 * alpha))
        pygame.draw.line(glow, glow_col,
                         (self.x1, self.y1), (self.x2, self.y2), 9)
        surface.blit(glow, (0, 0))

    @property
    def done(self) -> bool:
        return self._life <= 0


# ─────────────────────────────────────────────────────────────────────────────
#  FLASH MESSAGE — fades out after a few seconds
# ─────────────────────────────────────────────────────────────────────────────
class FlashMsg:
    def __init__(self, text: str, colour: tuple, duration: int = 90):
        self.text    = text
        self.colour  = colour
        self._life   = duration
        self._max    = duration
        self._font   = pygame.font.SysFont("Arial", 22, bold=True)

    def update(self):
        self._life -= 1

    def draw(self, surface: pygame.Surface):
        alpha = max(0, min(255, int(255 * self._life / max(self._max * 0.5, 1))))
        surf  = self._font.render(self.text, True, self.colour)
        surf.set_alpha(alpha)
        surface.blit(surf, surf.get_rect(center=(W // 2, H // 2 - 120)))

    @property
    def done(self) -> bool:
        return self._life <= 0


# ─────────────────────────────────────────────────────────────────────────────
#  NUMBER PAD — calculator-style on-screen touch buttons
#  Layout (iPad-friendly):
#    Row 0:  7   8   9   ⌫
#    Row 1:  4   5   6   (-)
#    Row 2:  1   2   3    0
#    Row 3:  [   FIRE! 🚀  ]    (full width)
# ─────────────────────────────────────────────────────────────────────────────
class NumPad:
    BTN_W  = 60
    BTN_H  = 42
    GAP    = 6
    COLS   = 4

    _GRID = [
        ["7", "8", "9", "<"],
        ["4", "5", "6", "-"],
        ["1", "2", "3", "0"],
    ]
    _FIRE_LABEL = "FIRE!"

    def __init__(self, top_y: int):
        self._top_y = top_y
        self._btn_font  = pygame.font.SysFont("Arial", 18, bold=True)
        self._ans_font  = pygame.font.SysFont("Arial", 20, bold=True)
        self._fire_font = pygame.font.SysFont("Arial", 20, bold=True)
        self._grid_rects: list[list[pygame.Rect]] = []
        self._fire_rect: pygame.Rect | None        = None
        self._build()

    def _build(self):
        bw, bh, g = self.BTN_W, self.BTN_H, self.GAP
        total_w = self.COLS * bw + (self.COLS - 1) * g
        sx = (W - total_w) // 2
        y  = self._top_y

        self._grid_rects = []
        for row in self._GRID:
            row_rects = []
            for col_i, _ in enumerate(row):
                row_rects.append(pygame.Rect(sx + col_i * (bw + g), y, bw, bh))
            self._grid_rects.append(row_rects)
            y += bh + g

        # FIRE button spans full width
        self._fire_rect = pygame.Rect(sx, y, total_w, bh)

    def draw(self, surface: pygame.Surface, current: str):
        bw, bh, g = self.BTN_W, self.BTN_H, self.GAP
        mouse = pygame.mouse.get_pos()

        # Answer display bar
        disp  = current if current else "_"
        label = self._ans_font.render(f"Answer:  {disp}", True, YELLOW)
        surface.blit(label, label.get_rect(
            center=(W // 2, self._top_y - 14)))

        # Grid buttons
        for row_i, (row_lbl, row_rects) in enumerate(
                zip(self._GRID, self._grid_rects)):
            for lbl, rect in zip(row_lbl, row_rects):
                hover = rect.collidepoint(mouse)
                if lbl == "<":
                    bg_col  = (100, 30, 30)
                    brd_col = RED
                elif lbl == "-":
                    bg_col  = (30, 30, 100)
                    brd_col = (100, 100, 255)
                else:
                    bg_col  = DIM_GRAY
                    brd_col = CYAN if hover else (80, 80, 160)
                pygame.draw.rect(surface, bg_col,  rect, border_radius=8)
                pygame.draw.rect(surface, brd_col, rect,
                                 3 if hover else 2, border_radius=8)
                txt = self._btn_font.render(lbl, True, WHITE)
                surface.blit(txt, txt.get_rect(center=rect.center))

        # FIRE button
        if self._fire_rect:
            hover     = self._fire_rect.collidepoint(mouse)
            fire_bg   = (0, 80, 160) if not hover else (0, 120, 220)
            fire_brd  = YELLOW if hover else CYAN
            pygame.draw.rect(surface, fire_bg,  self._fire_rect, border_radius=10)
            pygame.draw.rect(surface, fire_brd, self._fire_rect,
                             3 if hover else 2, border_radius=10)
            ft = self._fire_font.render(self._FIRE_LABEL, True, WHITE)
            surface.blit(ft, ft.get_rect(center=self._fire_rect.center))

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        """Returns label string, 'BACKSPACE', 'FIRE', or None."""
        for row_lbl, row_rects in zip(self._GRID, self._grid_rects):
            for lbl, rect in zip(row_lbl, row_rects):
                if rect.collidepoint(pos):
                    return "BACKSPACE" if lbl == "<" else lbl
        if self._fire_rect and self._fire_rect.collidepoint(pos):
            return "FIRE"
        return None


# ─────────────────────────────────────────────────────────────────────────────
#  HELPER: draw rounded rectangle
# ─────────────────────────────────────────────────────────────────────────────
def draw_rounded_rect(surface: pygame.Surface, colour: tuple,
                      rect: pygame.Rect, border: int = 0,
                      border_col: tuple = WHITE, radius: int = 12):
    pygame.draw.rect(surface, colour,     rect, border_radius=radius)
    if border:
        pygame.draw.rect(surface, border_col, rect, border, border_radius=radius)


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN GAME CLASS
# ─────────────────────────────────────────────────────────────────────────────
_HIT_MSGS = [
    "How dare you look at my masterpiece and say that",
    "You think blowing up Asteroids is easy?",
    "I'll burn the skin off your bones!",
    "Your king has returned!",
    "That's the old Bowser talking",
    "Open the Gates",
    "Do you yield?",
    "I finally found it",
    "Peaches",
    "You can't escape me",
]
_MISS_MSGS = [
    "Asteroid escaped!  -1 Life",
    "Oh no -- it got through!  -1 Life",
    "Shields hit!  -1 Life",
]


class SpaceMathGame:
    S_TITLE    = "title"
    S_PLAYING  = "playing"
    S_GAMEOVER = "gameover"

    def __init__(self, screen: pygame.Surface, sounds: dict):
        self._screen = screen
        self._sounds = sounds
        self._clock  = pygame.time.Clock()

        # Fonts
        self._f_big   = pygame.font.SysFont("Arial Black", 46, bold=True)
        self._f_med   = pygame.font.SysFont("Arial",        28, bold=True)
        self._f_small = pygame.font.SysFont("Arial",        17, bold=True)
        self._f_ast   = pygame.font.SysFont("Arial",        15, bold=True)
        self._f_btn   = pygame.font.SysFont("Arial",        16, bold=True)

        # Background stars (persistent across screens)
        self._stars = [Star() for _ in range(200)]

        # ── Game objects / state ──────────────────────────────────────────────
        self._state       = self.S_TITLE
        self._level       = 1
        self._score       = 0
        self._lives       = 3
        self._speed       = 0.0
        self._spawn_timer = 0
        self._spawn_ivl   = 120
        self._frame       = 0

        self._asteroids:  list[Asteroid]  = []
        self._explosions: list[Explosion] = []
        self._beams:      list[Beam]      = []
        self._flashes:    list[FlashMsg]  = []
        self._rocket:     Rocket | None   = None
        self._numpad:     NumPad | None   = None

        self._input_str = ""        # current typed answer

        # Clickable button rects built per-screen
        self._title_btns:   list[tuple] = []  # (rect, level, colour)
        self._gameover_btns: list[tuple] = []  # (rect, label, callback, colour)

        self._mixer_inited = False   # deferred until first user gesture

        self._build_title_btns()

    # ── Lazy mixer init (browsers block audio before user gesture) ────────────
    def _ensure_mixer(self):
        if self._mixer_inited:
            return
        self._mixer_inited = True
        try:
            pygame.mixer.init(frequency=SR, size=-16, channels=1, buffer=512)
            self._sounds = load_sounds()
            print("=== mixer init on gesture OK ===")
        except Exception as e:
            print(f"=== mixer init on gesture failed: {e} ===")

    # ── Sound helper ─────────────────────────────────────────────────────────
    def _play(self, key: str):
        if key in self._sounds:
            try:
                self._sounds[key].play()
            except Exception:
                pass

    # ─────────────────────────────────────────────────────────────────────────
    #  TITLE SCREEN
    # ─────────────────────────────────────────────────────────────────────────
    def _build_title_btns(self):
        items = [
            ("4th Grade",  1, (26, 102,  50)),
            ("5th Grade",  2, (102, 102,  0)),
            ("6th Grade",  3, (136,  34, 34)),
        ]
        bw, bh = 200, 55
        y      = H - 115
        total  = len(items) * bw + (len(items) - 1) * 20
        sx     = (W - total) // 2
        self._title_btns = []
        for i, (lbl, lv, col) in enumerate(items):
            r = pygame.Rect(sx + i * (bw + 20), y, bw, bh)
            self._title_btns.append((r, lbl, lv, col))

    def _draw_title(self):
        s = self._screen

        # Planet (right side)
        pygame.draw.ellipse(s, (51, 68, 136),   (570, 35,  210, 210))
        pygame.draw.ellipse(s, (102, 153, 255),  (570, 35,  210, 210), 3)
        pygame.draw.ellipse(s, (170, 187, 255),  (555, 128, 248,  30), 4)

        # Moon (left side)
        pygame.draw.circle(s, (136, 136, 136), (72, 140), 44)
        pygame.draw.circle(s, (187, 187, 187), (72, 140), 44, 2)
        for cx, cy, r in [(52, 122, 7), (86, 148, 5), (46, 158, 5)]:
            pygame.draw.circle(s, (110, 110, 110), (cx, cy), r)

        # Title text
        t = self._f_big.render("SPACE  MATH", True, CYAN)
        s.blit(t, t.get_rect(center=(W // 2, 88)))
        t2 = self._f_med.render("A D V E N T U R E", True, YELLOW)
        s.blit(t2, t2.get_rect(center=(W // 2, 150)))
        t3 = pygame.font.SysFont("Arial", 18, italic=True).render(
            "starring  Isaiah", True, PINK)
        s.blit(t3, t3.get_rect(center=(W // 2, 186)))

        # Decorative rocket
        Rocket(W // 2, 300).draw(s)

        # Instructions
        inst = self._f_small.render(
            "Tap the answer buttons then press  FIRE!  to blast asteroids",
            True, (140, 140, 160))
        s.blit(inst, inst.get_rect(center=(W // 2, 390)))

        # Level buttons
        mouse = pygame.mouse.get_pos()
        for rect, lbl, lv, col in self._title_btns:
            hover   = rect.collidepoint(mouse)
            brd_col = YELLOW if hover else WHITE
            brd_w   = 3 if hover else 2
            draw_rounded_rect(s, col, rect, brd_w, brd_col, radius=12)
            t = self._f_btn.render(lbl, True, WHITE)
            s.blit(t, t.get_rect(center=rect.center))

    # ─────────────────────────────────────────────────────────────────────────
    #  HUD  (shown during play)
    # ─────────────────────────────────────────────────────────────────────────
    def _draw_hud(self):
        s = self._screen
        lvl_name = {1: "4th Grade", 2: "5th Grade", 3: "6th Grade"}[self._level]

        score_t = self._f_small.render(f"Score: {self._score}", True, GREEN)
        lives_t = self._f_small.render(
            "* " * self._lives + "- " * (3 - self._lives), True, RED)
        lvl_t   = self._f_small.render(f"— {lvl_name} —", True, YELLOW)

        s.blit(score_t, (10, 8))
        s.blit(lvl_t,   lvl_t.get_rect(center=(W // 2, 14)))
        s.blit(lives_t, (W - lives_t.get_width() - 10, 8))

        # Ground line
        pygame.draw.line(s, (34, 68, 34), (0, GROUND_Y), (W, GROUND_Y), 2)

    # ─────────────────────────────────────────────────────────────────────────
    #  GAME OVER SCREEN
    # ─────────────────────────────────────────────────────────────────────────
    def _build_gameover_btns(self):
        bw, bh = 180, 52
        y      = H - 90
        self._gameover_btns = [
            (pygame.Rect(W // 2 - bw - 20, y, bw, bh),
             "Play Again", lambda: self._start(self._level), (26, 68, 34)),
            (pygame.Rect(W // 2 + 20, y, bw, bh),
             "Main Menu",  self._go_menu,                    (26, 26, 68)),
        ]

    def _draw_gameover(self):
        s = self._screen

        # Panel
        panel = pygame.Rect(100, 100, W - 200, H - 175)
        draw_rounded_rect(s, DARK_BLUE, panel, 3, CYAN, radius=20)

        # Title
        mission_txt = "MISSION COMPLETE" if self._lives > 0 else "MISSION FAILED"
        mission_col = GREEN if self._lives > 0 else RED
        t = pygame.font.SysFont("Arial Black", 28, bold=True).render(
            mission_txt, True, mission_col)
        s.blit(t, t.get_rect(center=(W // 2, 165)))

        # Score
        st = pygame.font.SysFont("Arial", 34, bold=True).render(
            f"Score:  {self._score}", True, YELLOW)
        s.blit(st, st.get_rect(center=(W // 2, 230)))

        # Grade
        if   self._score >= 150: grade, gc = "S  RANK — LEGENDARY!",  YELLOW
        elif self._score >= 100: grade, gc = "A  RANK — Outstanding!", GREEN
        elif self._score >=  60: grade, gc = "B  RANK — Great job!",   CYAN
        elif self._score >=  30: grade, gc = "C  RANK — Good effort!", ORANGE
        else:                    grade, gc = "Keep practising, Cadet!", WHITE

        gt = self._f_med.render(grade, True, gc)
        s.blit(gt, gt.get_rect(center=(W // 2, 285)))

        msg = self._f_small.render(
            "Isaiah, you're an awesome Math Commander!", True, PINK)
        s.blit(msg, msg.get_rect(center=(W // 2, 330)))

        # Buttons
        mouse = pygame.mouse.get_pos()
        for rect, lbl, _, col in self._gameover_btns:
            hover   = rect.collidepoint(mouse)
            brd_col = YELLOW if hover else WHITE
            brd_w   = 3 if hover else 2
            draw_rounded_rect(s, col, rect, brd_w, brd_col, radius=10)
            t = self._f_btn.render(lbl, True, WHITE)
            s.blit(t, t.get_rect(center=rect.center))

    # ─────────────────────────────────────────────────────────────────────────
    #  STATE TRANSITIONS
    # ─────────────────────────────────────────────────────────────────────────
    def _start(self, level: int):
        self._level       = level
        self._score       = 0
        self._lives       = 3
        self._speed       = BASE_SPEED[level]
        self._spawn_ivl   = SPAWN_FRAMES[level]
        self._spawn_timer = 0
        self._input_str   = ""

        self._asteroids.clear()
        self._explosions.clear()
        self._beams.clear()
        self._flashes.clear()

        self._rocket = Rocket(W // 2, ROCKET_Y)
        self._numpad = NumPad(PAD_TOP)
        self._state  = self.S_PLAYING

    def _go_menu(self):
        self._asteroids.clear()
        self._explosions.clear()
        self._beams.clear()
        self._flashes.clear()
        self._input_str = ""
        self._rocket    = None
        self._numpad    = None
        self._state     = self.S_TITLE
        self._build_title_btns()

    # ─────────────────────────────────────────────────────────────────────────
    #  QUESTION GENERATOR
    # ─────────────────────────────────────────────────────────────────────────
    def _make_question(self) -> tuple[str, int]:
        lv = self._level

        if lv == 1:
            # 4th grade: addition & subtraction, numbers 1–20 (answer always >= 0)
            n1, n2 = random.randint(1, 20), random.randint(1, 20)
            op = random.choice(["+", "-"])
            if op == "-" and n1 < n2:
                n1, n2 = n2, n1
            ans = n1 + n2 if op == "+" else n1 - n2

        elif lv == 2:
            # 5th grade: add/sub up to 50, multiplication up to 12x12
            op = random.choice(["+", "-", "x"])
            if op == "+":
                n1, n2 = random.randint(10, 50), random.randint(1, 40)
                ans = n1 + n2
            elif op == "-":
                n1, n2 = random.randint(10, 50), random.randint(1, 40)
                if n1 < n2:
                    n1, n2 = n2, n1
                ans = n1 - n2
            else:  # multiplication
                n1, n2 = random.randint(2, 12), random.randint(2, 12)
                ans = n1 * n2

        else:
            # 6th grade: larger add/sub (negatives OK), multiply up to 15x15, divide
            op = random.choice(["+", "-", "x", "÷"])
            if op == "+":
                n1, n2 = random.randint(20, 100), random.randint(20, 100)
                ans = n1 + n2
            elif op == "-":
                n1, n2 = random.randint(20, 100), random.randint(20, 100)
                ans = n1 - n2        # intentionally allow negative answers
            elif op == "x":
                n1, n2 = random.randint(3, 15), random.randint(3, 15)
                ans = n1 * n2
            else:  # division — always produces a whole number
                n2  = random.randint(2, 12)
                ans = random.randint(2, 12)
                n1  = n2 * ans

        return f"{n1} {op} {n2} = ?", ans

    # ─────────────────────────────────────────────────────────────────────────
    #  GAMEPLAY ACTIONS
    # ─────────────────────────────────────────────────────────────────────────
    def _fire(self):
        raw = self._input_str.strip()
        self._input_str = ""
        if not raw or not raw.lstrip("-").isdigit():
            return

        player_ans = int(raw)

        # Target the lowest asteroid with a matching answer
        target: Asteroid | None = None
        for ast in sorted(self._asteroids, key=lambda a: -a.y):
            if ast.answer == player_ans:
                target = ast
                break

        if target and self._rocket:
            bx, by = self._rocket.barrel_tip
            self._beams.append(Beam(bx, by, int(target.x), int(target.y)))
            self._play("laser")
            self._blast(target)
        else:
            self._flashes.append(FlashMsg("Wrong answer — try again!", RED, 75))
            self._play("wrong")

    def _blast(self, ast: Asteroid):
        self._asteroids.remove(ast)
        self._explosions.append(Explosion(ast.x, ast.y))
        pts            = {1: 15, 2: 20, 3: 30}[self._level]
        self._score   += pts
        self._speed    = min(self._speed + SPEED_BOOST, 4.0)
        self._spawn_ivl = max(self._spawn_ivl - 1, MIN_SPAWN)
        self._flashes.append(FlashMsg(random.choice(_HIT_MSGS), GREEN))
        self._play("correct")
        self._play("explode")

    def _asteroid_escaped(self, ast: Asteroid):
        if ast not in self._asteroids:
            return
        self._asteroids.remove(ast)
        self._lives -= 1
        self._flashes.append(FlashMsg(random.choice(_MISS_MSGS), RED))
        self._play("miss")
        if self._lives <= 0 and self._state == self.S_PLAYING:
            self._state = self.S_GAMEOVER
            self._build_gameover_btns()
            self._play("gameover")

    # ─────────────────────────────────────────────────────────────────────────
    #  EVENT HANDLER  (called once per event)
    # ─────────────────────────────────────────────────────────────────────────
    def handle_event(self, event: pygame.event.Event):
        # Init mixer on first click — satisfies browser autoplay policy
        if event.type == pygame.MOUSEBUTTONDOWN:
            self._ensure_mixer()

        if self._state == self.S_TITLE:
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                for rect, lbl, lv, col in self._title_btns:
                    if rect.collidepoint(pos):
                        self._start(lv)
                        return

        elif self._state == self.S_PLAYING:
            # Keyboard
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self._fire()
                elif event.key == pygame.K_BACKSPACE:
                    self._input_str = self._input_str[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self._go_menu()
                elif event.unicode.isdigit() or (
                        event.unicode == "-" and not self._input_str):
                    if len(self._input_str) < 4:
                        self._input_str += event.unicode

            # Touch / mouse
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if self._numpad:
                    result = self._numpad.handle_click(pos)
                    if result == "FIRE":
                        self._fire()
                    elif result == "BACKSPACE":
                        self._input_str = self._input_str[:-1]
                    elif result:
                        if len(self._input_str) < 4:
                            self._input_str += result

        elif self._state == self.S_GAMEOVER:
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                for rect, lbl, fn, col in self._gameover_btns:
                    if rect.collidepoint(pos):
                        fn()
                        return

    # ─────────────────────────────────────────────────────────────────────────
    #  MAIN TICK  (called every frame)
    # ─────────────────────────────────────────────────────────────────────────
    def tick(self):
        self._frame += 1
        s = self._screen
        s.fill(BG)

        # ── Stars (always on) ──────────────────────────────────────────────
        if self._frame % 4 == 0:
            for star in random.sample(self._stars, 6):
                star.update()
        for star in self._stars:
            star.draw(s)

        # ── Title ─────────────────────────────────────────────────────────
        if self._state == self.S_TITLE:
            self._draw_title()

        # ── Playing ───────────────────────────────────────────────────────
        elif self._state == self.S_PLAYING:
            self._draw_hud()

            # Spawn asteroids
            self._spawn_timer -= 1
            if (self._spawn_timer <= 0 and
                    len(self._asteroids) < MAX_ASTEROIDS[self._level]):
                self._spawn_timer = self._spawn_ivl
                q, ans = self._make_question()
                self._asteroids.append(
                    Asteroid(q, ans, self._speed, self._f_ast))

            # Update & draw asteroids; collect escaped ones
            escaped = [a for a in list(self._asteroids) if a.past_bottom]
            for a in escaped:
                self._asteroid_escaped(a)
            for a in self._asteroids:
                a.update()
                a.draw(s)

            # Explosions
            for ex in list(self._explosions):
                ex.update()
                ex.draw(s)
                if ex.done:
                    self._explosions.remove(ex)

            # Beams
            for b in list(self._beams):
                b.update()
                b.draw(s)
                if b.done:
                    self._beams.remove(b)

            # Rocket
            if self._rocket:
                self._rocket.draw(s)

            # Flash messages
            for f in list(self._flashes):
                f.update()
                f.draw(s)
                if f.done:
                    self._flashes.remove(f)

            # Number pad + answer display
            if self._numpad:
                self._numpad.draw(s, self._input_str)

        # ── Game Over ─────────────────────────────────────────────────────
        elif self._state == self.S_GAMEOVER:
            self._draw_gameover()
            for f in list(self._flashes):
                f.update()
                f.draw(s)
                if f.done:
                    self._flashes.remove(f)

        pygame.display.flip()
        self._clock.tick(FPS)


# ─────────────────────────────────────────────────────────────────────────────
#  ASYNC ENTRY POINT  (required by Pygbag)
# ─────────────────────────────────────────────────────────────────────────────
async def main():
    print("=== MAIN STARTING ===")
    try:
        pygame.init()
        print("=== pygame.init() OK ===")

        screen = pygame.display.set_mode((W, H))
        print("=== display.set_mode() OK ===")
        pygame.display.set_caption("Isaiah's Space Math Adventure!")

        # Mixer is initialised lazily on first click (browser autoplay policy)
        print("=== Creating game... ===")
        game   = SpaceMathGame(screen, {})
        print("=== Game created OK ===")

        running = True
        frame_count = 0
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    game.handle_event(event)

            try:
                game.tick()
                frame_count += 1
                if frame_count <= 3:
                    print(f"=== Frame {frame_count} OK ===")
            except Exception as frame_err:
                print(f"=== TICK ERROR frame {frame_count}: {frame_err} ===")
                import traceback
                traceback.print_exc()
                running = False

            await asyncio.sleep(0)   # Pygbag requires this every frame

        pygame.quit()
    except Exception as e:
        print(f"=== MAIN CRASH: {e} ===")
        import traceback
        traceback.print_exc()


asyncio.run(main())
