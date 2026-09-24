#!/usr/bin/env python3
"""
Generates src/components/icons/food-icons.json - flat vector icon geometry for
every product and category in the app (replaces emoji, which render differently
on each device).

Same JSON is consumed by:
  - src/components/icons/FoodIcon.tsx      (react-native-svg, in the app)
  - scripts/icon-sheet.mjs                 (contact sheet PNG for visual review)

Shape spec (viewBox is always 0 0 64 64):
  {"t":"c","cx","cy","r","f"}                          circle
  {"t":"e","cx","cy","rx","ry","f","rot"?}             ellipse (rot = degrees)
  {"t":"r","x","y","w","h","rx"?,"f","rot"?}           rect
  {"t":"p","d","f"?,"s"?,"sw"?,"cap"?}                 path (s = stroke colour)
  {"t":"l","x1","y1","x2","y2","s","sw","cap"?}        line
  {"t":"poly","p":"x,y x,y ...","f"?,"s"?,"sw"?}       polygon
"""
import json
import os

W = H = 64

# ---------------------------------------------------------------- palette
C = {
    "red": "#e2432f", "redDark": "#b52f22", "tomato": "#e5322a",
    "orange": "#f08a24", "orangeDeep": "#d96f12", "yellow": "#f4c02e",
    "yellowLight": "#ffdd6b", "green": "#3f9b48", "greenDark": "#2d7a37",
    "greenLight": "#7cc576", "greenPale": "#b6dc9a", "leaf": "#3f8f3f",
    "purple": "#7b3fa0", "purpleLight": "#a86cc4", "maroon": "#8b2f52",
    "cream": "#f6e6c4", "creamDark": "#e2cfa4", "white": "#fdfdff",
    "brown": "#8a5a2b", "brownLight": "#c08a4e", "beige": "#e7d3a8",
    "pink": "#f09a9a", "pinkDeep": "#e0674f", "grey": "#a9b6bd",
    "greyDark": "#7d8b93", "silver": "#c8d4d9", "blue": "#2f6fa8",
    "blueDark": "#1f4a72", "blueGrey": "#5b7c94", "sand": "#e9d58f",
    "black": "#26313a", "brownBread": "#a9702f", "amber": "#e9973f",
    "meat": "#d2544a", "meatDark": "#a83a34", "fat": "#f3ded2",
    "bone": "#f2ecdf", "water": "#cfe9f3", "eggWhite": "#fbf7ee",
    "eggYolk": "#f5b73d", "shell": "#e6d7bd",
}


def c(cx, cy, r, f):
    return {"t": "c", "cx": cx, "cy": cy, "r": r, "f": f}


def e(cx, cy, rx, ry, f, rot=None):
    d = {"t": "e", "cx": cx, "cy": cy, "rx": rx, "ry": ry, "f": f}
    if rot:
        d["rot"] = rot
    return d


def r(x, y, w, h, f, rx=0, rot=None):
    d = {"t": "r", "x": x, "y": y, "w": w, "h": h, "rx": rx, "f": f}
    if rot:
        d["rot"] = rot
    return d


def p(d, f=None, s=None, sw=None, cap=None, rot=None, px=32, py=32):
    sh = {"t": "p", "d": d}
    if f:
        sh["f"] = f
    if s:
        sh["s"] = s
    if sw:
        sh["sw"] = sw
    if cap:
        sh["cap"] = cap
    if rot:
        sh["rot"] = rot
        sh["px"] = px
        sh["py"] = py
    return sh


def line(x1, y1, x2, y2, s, sw=3, cap="round"):
    return {"t": "l", "x1": x1, "y1": y1, "x2": x2, "y2": y2, "s": s, "sw": sw, "cap": cap}


def poly(points, f=None, s=None, sw=None):
    sh = {"t": "poly", "p": points}
    if f:
        sh["f"] = f
    if s:
        sh["s"] = s
    if sw:
        sh["sw"] = sw
    return sh


# ------------------------------------------------------------- helpers
def stem(x, y, color=C["greenDark"], h=8, w=3):
    """small stalk going up-right from a fruit"""
    return [line(x, y, x + w, y - h, color, w)]


def leaf(x, y, color=C["leaf"], scale=1.0, flip=False):
    """single leaf pointing up-right (or up-left when flipped)"""
    s = scale
    if not flip:
        d = f"M{x},{y} C{x + 4 * s},{y - 8 * s} {x + 14 * s},{y - 10 * s} {x + 18 * s},{y - 4 * s} C{x + 14 * s},{y + 2 * s} {x + 5 * s},{y + 3 * s} {x},{y} Z"
    else:
        d = f"M{x},{y} C{x - 4 * s},{y - 8 * s} {x - 14 * s},{y - 10 * s} {x - 18 * s},{y - 4 * s} C{x - 14 * s},{y + 2 * s} {x - 5 * s},{y + 3 * s} {x},{y} Z"
    return p(d, color)


def leaf_pair(cx, cy, color=C["leaf"], scale=1.0, spread=10):
    return [leaf(cx, cy, color, scale), leaf(cx, cy, color, scale, flip=True)]


def face_highlight(cx, cy, r_, color="#ffffff", op=None):
    """specular highlight blob to give volume"""
    return e(cx, cy, r_ * 0.42, r_ * 0.3, color, rot=-35)


def bottle(body, liquid, cap_color, label=None, tall=False):
    """bottle silhouette with neck + cap; body/liquid colours parametrised"""
    shapes = [
        r(28, 12, 8, 8, cap_color, rx=2),
        r(29, 20, 6, 8, body, rx=2),
        p("M22,27 C22,24 26,24 26,27 L38,27 C38,24 42,24 42,27 L42,52 C42,55 39,57 37,57 L27,57 C25,57 22,55 22,52 Z", body),
        p("M24,34 L40,34 L40,52 C40,54.5 38,56 36,56 L28,56 C26,56 24,54.5 24,52 Z", liquid),
    ]
    if label:
        shapes.append(r(25, 40, 14, 9, label, rx=2))
    return shapes


def bowl(rice, rim, extras=None):
    """rice bowl: mound + bowl body"""
    shapes = [
        e(32, 30, 17, 11, rice),
        p("M12,33 L52,33 C52,47 44,55 32,55 C20,55 12,47 12,33 Z", rim),
        p("M15,38 L49,38 C47,48 40,53 32,53 C24,53 17,48 15,38 Z", C["white"]),
    ]
    return shapes + (extras or [])


def fish_body(body, belly, fin, eye_ring=True, tail=True, gill=True):
    """classic side-view fish, nose left"""
    shapes = [
        poly("14,32 26,32 22,20 30,20 34,32 34,32", fin, None),
        e(34, 32, 18, 13, body),
        p("M20,34 C26,42 44,42 50,34 C44,44 26,44 20,34 Z", belly),
        poly("52,32 62,22 62,42", fin),
    ]
    if gill:
        shapes.append(p("M28,24 C24,30 24,36 28,42", None, body, 1.6, "round"))
    shapes.append(c(24, 28, 3.4, C["white"]))
    if eye_ring:
        shapes.append(c(24, 28, 1.8, C["black"]))
    return shapes


def chili(color, curve=1.0, thick=0.0):
    """single chili pointing down-left"""
    d = f"M40,16 C46,24 42,34 34,40 C28,44.5 24,44 {22},{40} C{20},{36 - 2 * curve} 26,34 30,30 C34,26 36,20 34,15 Z"
    return p(d, color)


def meat_slab(top, bottom, fat=C["fat"]):
    return [
        p(f"M16,22 C22,15 44,14 50,21 C56,28 54,44 46,50 C38,56 22,54 16,46 C11,39 11,28 16,22 Z", top),
        p("M20,30 C26,25 40,25 46,30 C50,34 48,44 42,47 C34,50 24,48 20,43 C17,39 17,33 20,30 Z", bottom),
        line(24, 36, 40, 36, fat, 3),
        line(26, 42, 38, 42, fat, 2.4),
    ]


def drumstick(meat=C["amber"], bone=C["bone"]):
    return [
        e(30, 28, 16, 15, meat, rot=-20),
        p("M38,40 C46,44 50,50 47,54 C44,58 36,56 32,50 Z", meat),
        line(48, 50, 58, 58, bone, 6),
        c(59, 59, 4, bone),
    ]


def shrimp_body():
    return [
        p("M44,20 C52,26 50,40 40,46 C30,52 20,48 18,40 C16,32 22,24 30,22 C34,21 40,18 44,20 Z", C["pinkDeep"]),
        p("M26,26 C34,22 44,24 48,30 C50,36 46,44 38,46 C28,48 20,42 22,34 C23,30 23,28 26,26 Z", C["pink"]),
        line(30, 30, 24, 24, C["redDark"], 4),
        c(24, 23, 3, C["redDark"]),
        line(18, 40, 10, 46, C["pinkDeep"], 3),
        line(20, 44, 12, 52, C["pinkDeep"], 3),
    ]


def chili_pod(color, x=32, y=32, rot=0):
    return e(x, y, 7, 20, color, rot=rot)




def steak(meat, dark, bone=None, marbling="#f6ddd6"):
    """irregular steak slab with a fat cap and marbling (reads as karne)"""
    shapes = [
        p("M14,28 C18,18 32,12 44,16 C56,20 58,32 53,42 C48,52 32,56 22,51 C13,46 10,38 14,28 Z", dark),
        p("M17,30 C21,21 33,16 43,19 C53,23 55,33 51,41 C47,49 33,52 25,48 C17,44 14,37 17,30 Z", meat),
        p("M12,30 C12,24 18,20 24,22 C20,26 18,30 19,35 C15,35 12,33 12,30 Z", bone or "#f3ded2"),
        p("M26,26 C34,24 44,26 48,32", None, marbling, 2.4, "round"),
        p("M22,40 C30,38 40,40 45,44", None, marbling, 2.2, "round"),
        c(30, 34, 2.4, marbling),
    ]
    return shapes


def drumstick(meat="#e9973f", meatLight="#f2b35c", bone="#f2ecdf"):
    """roast drumstick: meat head, tapering shank, knuckle bone"""
    return [
        p("M18,20 C28,12 44,17 47,30 C50,42 42,50 33,51 C24,52 15,46 14,38 C13,30 14,24 18,20 Z", meat),
        p("M23,23 C30,18 41,21 43,30 C45,38 39,44 32,45 C25,46 19,41 19,34 C18,29 19,26 23,23 Z", meatLight),
        p("M33,50 C40,52 47,54 49,52 C51,50 46,46 41,44 Z", meat),
        line(49, 52, 58, 58, bone, 7),
        c(59, 59, 4.5, bone),
        c(52, 60, 3.6, bone),
    ]


def spade_leaf(x, y, size=1.0, color="#3f9b48", rot=-20):
    """leaf with a midrib, anchored at (x,y)"""
    d = f"M{x},{y} C{x + 5 * size},{y - 13 * size} {x + 19 * size},{y - 16 * size} {x + 26 * size},{y - 6 * size} C{x + 20 * size},{y + 3 * size} {x + 5 * size},{y + 4 * size} {x},{y} Z"
    return [
        p(d, color, rot=rot, px=x, py=y),
        p(f"M{x},{y} C{x + 9 * size},{y - 7 * size} {x + 18 * size},{y - 8 * size} {x + 24 * size},{y - 6 * size}", None, "#2d7a37", 1.4, "round", rot=rot, px=x, py=y),
    ]


def pod(color, colorDark, cx=32, cy=34, rx=7.5, ry=21, rot=-8):
    """bean/chili style pod with ridges and a stalk"""
    return [
        e(cx, cy, rx, ry, colorDark, rot=rot),
        e(cx, cy - 1, rx - 2, ry - 2, color, rot=rot),
        line(cx - 2, cy - 14, cx - 2, cy + 14, colorDark, 1.4),
        line(cx + 3, cy - 12, cx + 3, cy + 12, colorDark, 1.2),
        line(cx + 1, cy - ry - 1, cx + 5, cy - ry - 9, "#2d7a37", 3),
    ]


def rice_bowl(rice, rim, extras=None, steam=True):
    shapes = [
        e(32, 30, 17, 11, rice),
        p("M12,33 L52,33 C52,47 44,55 32,55 C20,55 12,47 12,33 Z", rim),
        p("M15,38 L49,38 C47,48 40,53 32,53 C24,53 17,48 15,38 Z", "#fdfdff"),
    ]
    if steam:
        shapes += [
            p("M22,22 C20,18 24,16 22,12", None, "#cfe0ea", 2.4, "round"),
            p("M32,20 C30,15 34,13 32,8", None, "#cfe0ea", 2.4, "round"),
            p("M42,22 C40,18 44,16 42,12", None, "#cfe0ea", 2.4, "round"),
        ]
    return shapes + (extras or [])

# =====================================================================
#  CATEGORIES
# =====================================================================
CATEGORY_ICONS = {
    "vegetables": {
        "label": "Gulay",
        "shapes": [
            *spade_leaf(28, 44, 1.35, C["green"], -18),
            *spade_leaf(38, 42, 1.25, C["greenLight"], 22),
            p("M32,50 C29,38 33,26 40,18 C44,28 41,42 34,50 Z", C["greenDark"]),
            p("M22,52 C19,44 21,34 27,26", None, C["greenDark"], 2.6, "round"),
        ],
    },
    "fruits": {
        "label": "Prutas",
        "shapes": [
            c(30, 40, 16, C["orange"]),
            face_highlight(23, 33, 16),
            *stem(33, 25, C["brown"], 7),
            leaf(35, 27, C["leaf"], 1.05),
            p("M20,46 C26,52 38,52 44,46 C40,54 24,54 20,46 Z", C["orangeDeep"]),
        ],
    },
    "meat": {"label": "Karne", "shapes": steak("#d2544a", "#a83a34")},
    "poultry": {"label": "Manok", "shapes": drumstick()},
    "seafood": {
        "label": "Isda",
        "shapes": fish_body(C["blueGrey"], C["silver"], C["blueDark"]),
    },
    "rice": {"label": "Bigas", "shapes": rice_bowl(C["white"], "#4a86c8")},
    "eggDairy": {
        "label": "Itlog & Gatas",
        "shapes": [
            e(24, 38, 14, 18, "#f6eedd"),
            e(24, 38, 14, 18, "#fdf7ea"),
            e(20, 32, 5, 6.5, "#ffffff"),
            r(38, 22, 17, 32, C["white"], rx=4),
            p("M38,22 L46.5,12 L55,22 Z", "#c9dbe8"),
            r(40, 30, 13, 14, "#4a86c8", rx=2),
            c(46.5, 37, 3, C["white"]),
            r(38, 20, 17, 5, "#8fb8d8", rx=2),
        ],
    },
    "pantry": {
        "label": "Panimpla",
        "shapes": [
            p("M27,22 C27,15 30,12 34,12 C38,12 41,15 41,22 Z", "#c8d4d9"),
            p("M24,22 L44,22 L42,52 C42,55 38,56 34,56 C30,56 26,55 26,52 Z", "#fdfdff"),
            p("M26,52 C30,55 38,55 42,52 L42,54 C42,56 38,57 34,57 C30,57 26,56 26,54 Z", "#e2ecf0"),
            r(26, 32, 16, 6, "#4a86c8", rx=1.5),
            c(31, 18, 1.8, C["black"]), c(37, 18, 1.8, C["black"]),
            c(34, 12, 1.6, "#c8d4d9"),
            c(34, 60, 2, "#e2ecf0"), c(28, 61, 1.6, "#e2ecf0"), c(40, 61, 1.6, "#e2ecf0"),
        ],
    },
}
# =====================================================================
#  PRODUCTS
# =====================================================================
V = C  # shorthand

P = {}

# ------------------------------------------------------- GULAY
P["ampalaya"] = [
    e(32, 34, 12, 20, V["greenLight"], rot=-8),
    e(32, 34, 12, 20, "#8fd08a", rot=-8),
    p("M22,26 C28,30 36,30 42,26", None, "#6fbf6a", 1.6, "round"),
    p("M22,34 C28,38 36,38 42,34", None, "#6fbf6a", 1.6, "round"),
    p("M24,42 C29,45 35,45 40,42", None, "#6fbf6a", 1.6, "round"),
    c(26, 22, 2, "#bfe3b5"), c(36, 50, 2, "#bfe3b5"), c(40, 30, 2, "#bfe3b5"),
    line(32, 15, 36, 8, V["greenDark"], 3),
]
P["talong"] = [
    e(30, 36, 14, 19, V["purple"], rot=-18),
    e(27, 32, 12, 16, V["purpleLight"], rot=-18),
    p("M40,17 C46,12 52,12 56,16 C50,20 44,20 40,17 Z", V["greenDark"]),
    line(43, 17, 48, 12, V["greenDark"], 3),
]
P["kamatis"] = [
    c(32, 36, 18, V["tomato"]),
    e(26, 30, 7, 5, "#f4776a", rot=-30),
    p("M20,25 L32,30 L44,25 L36,20 L28,20 Z", V["greenDark"]),
    line(32, 28, 32, 20, V["greenDark"], 2.6),
    *leaf_pair(32, 22, V["green"], 0.75, 8),
]
P["sibuyas-pula"] = [
    p("M32,20 C42,22 48,30 48,38 C48,46 41,52 32,52 C23,52 16,46 16,38 C16,30 22,22 32,20 Z", "#9b3a68"),
    p("M32,22 C40,24 45,31 45,38 C45,45 39,50 32,50 C25,50 19,45 19,38 C19,31 24,24 32,22 Z", "#c25f8c"),
    p("M32,22 C37,26 39,33 39,40", None, "#a84a76", 1.6, "round"),
    p("M32,22 C27,26 25,33 25,40", None, "#a84a76", 1.6, "round"),
    p("M32,22 C32,30 32,40 32,49", None, "#b4577f", 1.4, "round"),
    p("M30,20 C28,12 30,7 34,5 C36,11 34,17 32,20 Z", "#d9b98a"),
    line(32, 20, 33, 8, "#c9a978", 1.6),
]


P["sibuyas-puti"] = [
    p("M32,20 C42,22 48,30 48,38 C48,46 41,52 32,52 C23,52 16,46 16,38 C16,30 22,22 32,20 Z", "#d9c8a4"),
    p("M32,22 C40,24 45,31 45,38 C45,45 39,50 32,50 C25,50 19,45 19,38 C19,31 24,24 32,22 Z", "#f7f1e2"),
    p("M32,22 C37,26 39,33 39,40", None, "#ddd0b4", 1.6, "round"),
    p("M32,22 C27,26 25,33 25,40", None, "#ddd0b4", 1.6, "round"),
    p("M32,22 C32,30 32,40 32,49", None, "#e8ddc6", 1.4, "round"),
    p("M30,20 C28,12 30,7 34,5 C36,11 34,17 32,20 Z", "#d9b98a"),
    line(32, 20, 33, 8, "#c9a978", 1.6),
]


P["bawang"] = [
    # bulb: fat cloves, papery skin, dry stalk on top
    p("M20,34 C20,26 25,21 32,21 C39,21 44,26 44,34 C44,43 39,50 32,50 C25,50 20,43 20,34 Z", "#fdf7ea"),
    p("M32,23 C37,25 41,29 41,35 C41,43 37,49 32,50 C27,49 23,43 23,35 C23,29 27,25 32,23 Z", "#f6eedd"),
    p("M27,25 C24,30 23,40 25,48", None, "#ded2ba", 1.8, "round"),
    p("M37,25 C40,30 41,40 39,48", None, "#ded2ba", 1.8, "round"),
    p("M32,24 C32,34 32,42 32,49", None, "#e8dcc4", 1.6, "round"),
    p("M22,42 C26,46 38,46 42,42 C40,48 24,48 22,42 Z", "#e6d9c0"),
    p("M30,21 C29,13 33,9 38,8 C38,14 35,19 32,21 Z", "#c9a06a"),
]


P["luya"] = [
    # ginger hand: two lobes + small knob, tapered ends
    p("M14,36 C10,32 11,26 16,24 C21,22 26,25 27,29 C32,24 40,25 43,30 C47,28 52,30 53,35 C54,40 50,45 44,44 C40,49 31,50 26,46 C22,48 16,45 14,36 Z", "#dcae72"),
    p("M17,36 C14,33 15,29 18,27 C22,26 25,28 26,31 C30,27 37,28 39,32 C42,30 46,32 47,35 C48,39 45,42 41,42 C37,45 30,46 27,43 C23,45 19,42 17,36 Z", "#ecc389"),
    p("M20,31 C24,29 27,31 27,34", None, "#c08f4e", 1.6, "round"),
    p("M33,30 C37,29 40,31 40,34", None, "#c08f4e", 1.6, "round"),
    c(21, 28, 2.2, "#b98a49"), c(37, 30, 2, "#b98a49"), c(47, 34, 1.8, "#b98a49"),
    line(28, 26, 31, 20, "#c08f4e", 2.4),
]


P["kalamansi"] = [
    c(30, 36, 15, "#a4c93a"),
    e(25, 31, 6, 4.5, "#c3dc70", rot=-30),
    p("M32,44 C38,48 42,44 44,40", None, "#7fa02b", 1.6, "round"),
    *stem(32, 22, V["greenDark"], 6, 2.6),
    leaf(33, 24, V["leaf"], 0.9),
]
P["sili-labuyo"] = [
    chili("#d8342a", 1.0),
    e(41, 42, 5, 8, "#e8583f", rot=25),
    p("M38,15 C40,10 44,10 46,14 C43,17 40,17 38,15 Z", V["greenDark"]),
    line(36, 18, 42, 22, V["greenDark"], 3),
]
P["siling-haba"] = [
    e(32, 34, 7, 21, "#4aa03f", rot=-12),
    e(31, 30, 5, 17, "#6abf57", rot=-12),
    line(36, 15, 42, 10, V["greenDark"], 3),
]
P["repolyo"] = [
    c(32, 36, 18, "#5aa84f"),
    e(32, 32, 15, 14, "#7cc576"),
    e(32, 34, 10, 12, "#c9e4a8"),
    p("M32,22 C36,30 36,42 32,50", None, "#4c8f42", 2, "round"),
    p("M24,26 C30,32 30,42 26,48", None, "#4c8f42", 2, "round"),
    p("M40,26 C34,32 34,42 38,48", None, "#4c8f42", 2, "round"),
]
P["pechay"] = [
    p("M32,52 C26,42 22,34 22,26 C30,30 34,40 32,52 Z", V["white"]),
    p("M32,52 C38,42 42,34 42,26 C34,30 30,40 32,52 Z", "#f2f6ea"),
    p("M22,26 C16,18 18,10 26,8 C28,16 26,22 22,26 Z", V["green"]),
    p("M42,26 C48,18 46,10 38,8 C36,16 38,22 42,26 Z", V["greenLight"]),
    p("M32,24 C30,16 32,8 38,6 C40,14 37,20 32,24 Z", "#5aa84f"),
    line(32, 52, 32, 40, "#dfe6d2", 2),
]
P["carrots"] = [
    poly("32,54 22,24 42,24", V["orange"]),
    poly("32,50 26,28 38,28", "#f6a447"),
    line(26, 34, 38, 34, "#d96f12", 2),
    line(28, 41, 36, 41, "#d96f12", 2),
    leaf(32, 22, V["green"], 0.95),
    leaf(32, 22, V["greenLight"], 0.9, True),
]
P["sayote"] = [
    # chayote: pear-shaped, pale green, deep furrows
    p("M32,12 C40,18 45,26 45,37 C45,47 39,54 32,54 C25,54 19,47 19,37 C19,26 24,18 32,12 Z", "#a8c97a"),
    p("M32,16 C38,21 42,28 42,37 C42,45 37,51 32,51 C27,51 22,45 22,37 C22,28 26,21 32,16 Z", "#c3e09a"),
    p("M32,16 C34,26 34,44 32,51", None, "#8fae63", 1.8, "round"),
    p("M26,18 C23,26 22,36 23,48", None, "#8fae63", 1.6, "round"),
    p("M38,18 C41,26 42,36 41,48", None, "#8fae63", 1.6, "round"),
    p("M32,12 C30,8 32,5 35,4 C36,8 35,11 32,12 Z", "#7f9e58"),
]


P["kalabasa"] = [
    e(32, 36, 20, 18, "#e07b2a"),
    e(32, 36, 12, 18, "#ef9a3c"),
    e(20, 36, 6, 17, "#d96f12"),
    e(44, 36, 6, 17, "#d96f12"),
    line(32, 18, 32, 54, "#c9660d", 2),
    p("M30,17 C29,10 34,7 39,9 C38,14 34,17 30,17 Z", V["greenDark"]),
]
P["okra"] = [
    e(32, 34, 9, 22, "#57a83f", rot=-10),
    e(30, 32, 6, 19, "#79c25e", rot=-10),
    line(30, 20, 34, 50, "#cfe6a8", 1.6),
    line(36, 20, 39, 46, "#3f8f3f", 1.4),
    line(34, 12, 40, 7, V["greenDark"], 3),
]
P["sitaw"] = [
    *pod("#5aa84f", "#3f8f3f", 30, 34, 7, 20, -12),
    *pod("#6cbb4e", "#4aa03f", 42, 32, 6, 17, 14),
    *pod("#4a9436", "#357a2c", 20, 36, 5.5, 15, -28),
]


P["patatas"] = [
    e(26, 36, 14, 11, V["brownLight"], rot=-15),
    e(41, 30, 11, 9, "#c99a5f", rot=20),
    e(38, 46, 9, 7.5, "#b98449", rot=-8),
    c(20, 32, 2, "#8a5a2b"), c(30, 40, 2, "#8a5a2b"), c(45, 30, 1.8, "#8a5a2b"),
]
P["monggo"] = [
    c(24, 30, 7, "#8a9a3b"), c(40, 28, 7, "#9aa845"), c(32, 42, 7.5, "#7d8c33"),
    c(46, 42, 6, "#8a9a3b"), c(18, 43, 5.5, "#9aa845"),
    e(22, 28, 3, 1.6, "#c3d08a", rot=-30),
]
P["kangkong"] = [
    line(22, 52, 26, 18, V["greenDark"], 3),
    line(32, 54, 34, 16, V["green"], 3),
    line(42, 52, 40, 20, V["greenDark"], 3),
    leaf(26, 18, V["green"], 1.05),
    leaf(34, 16, "#5aa84f", 1.1, True),
    leaf(40, 20, V["greenLight"], 1.0),
]

# ------------------------------------------------------- PRUTAS
P["saging-lakatan"] = [
    p("M14,26 C14,44 26,54 42,52 C52,50 54,40 52,32 C44,44 30,46 24,38 C20,33 20,28 22,24 C18,24 15,25 14,26 Z", V["yellow"]),
    p("M18,28 C18,42 28,50 40,48 C46,47 48,41 48,36 C42,44 30,44 26,37 C23,33 23,30 24,26 C21,26 19,27 18,28 Z", V["yellowLight"]),
    p("M14,26 C16,20 22,17 30,18 C26,21 22,23 20,26 Z", "#c9a227"),
    line(16, 28, 16, 20, "#8f7a1e", 2.6),
]
P["saging-saba"] = [
    e(30, 34, 11, 19, "#e8b62c", rot=-18),
    e(40, 36, 10, 17, "#f2c851", rot=10),
    e(21, 33, 8, 15, "#d9a520", rot=-32),
    line(26, 14, 30, 10, "#8f7a1e", 2.6),
    line(42, 20, 46, 16, "#8f7a1e", 2.4),
]
P["mangga"] = [
    p("M24,22 C34,16 48,22 50,34 C52,48 42,54 33,54 C22,54 14,44 16,32 C17,26 20,24 24,22 Z", "#f2a531"),
    p("M26,26 C33,22 42,26 44,34 C46,44 39,49 33,49 C25,49 20,42 21,34 C22,30 23,28 26,26 Z", "#f8c05a"),
    *stem(32, 20, V["brown"], 6, 2.6),
    leaf(34, 22, V["green"], 1.0),
]
P["papaya"] = [
    e(32, 34, 15, 20, "#ef9a3c", rot=-6),
    e(32, 34, 11, 16, "#f6b95c", rot=-6),
    e(32, 36, 6, 10, "#8a5a2b", rot=-6),
    c(28, 32, 1.6, "#3a2a1a"), c(34, 30, 1.6, "#3a2a1a"), c(31, 38, 1.6, "#3a2a1a"),
    c(35, 40, 1.4, "#3a2a1a"),
    *stem(32, 20, V["greenDark"], 6, 2.4),
]
P["pinya"] = [
    e(32, 40, 15, 18, "#d9a520"),
    e(30, 38, 12, 15, "#e8b62c"),
    line(24, 30, 40, 30, "#b8860b", 1.6),
    line(22, 38, 42, 38, "#b8860b", 1.6),
    line(24, 46, 40, 46, "#b8860b", 1.6),
    line(28, 24, 26, 54, "#b8860b", 1.4),
    line(36, 24, 38, 54, "#b8860b", 1.4),
    poly("32,22 26,10 34,14 38,8 40,16 46,14 38,22", V["green"]),
]
P["pakwan"] = [
    p("M10,46 C10,26 24,12 44,12 C50,12 54,16 54,22 C54,38 40,50 24,50 C16,50 10,50 10,46 Z", "#e0433c"),
    p("M52,16 C54,18 54,22 54,24 C54,40 40,52 24,52 C14,52 10,50 10,46 C26,48 46,36 52,16 Z", "#f0705f"),
    p("M12,52 C12,44 18,38 26,38 C34,38 40,42 40,52 C34,54 16,54 12,52 Z", V["green"]),
    c(30, 26, 2, V["black"]), c(38, 22, 2, V["black"]), c(24, 34, 2, V["black"]),
    c(42, 30, 1.8, V["black"]),
]
P["melon"] = [
    p("M14,50 C14,30 26,16 44,14 C52,13 54,20 52,26 C48,42 34,52 20,52 C16,52 14,52 14,50 Z", "#8fbf58"),
    p("M20,50 C22,34 32,22 48,18 C46,34 34,48 20,50 Z", "#c3e09a"),
    e(34, 36, 7, 5, "#f6e6c4", rot=-20),
    c(32, 36, 2, "#8a9a3b"), c(38, 34, 1.6, "#8a9a3b"), c(35, 40, 1.6, "#8a9a3b"),
]
P["lanzones"] = [
    c(24, 32, 9, "#e8c76a"), c(40, 30, 9, "#f0d685"), c(32, 44, 9, "#dcb84f"),
    c(46, 42, 7.5, "#e8c76a"), c(18, 44, 7, "#f0d685"),
    c(21, 29, 2.4, "#b89640"), c(37, 27, 2.4, "#b89640"), c(29, 41, 2.4, "#b89640"),
    line(32, 18, 34, 24, V["brownLight"], 2.6),
]
P["rambutan"] = [
    c(32, 36, 15, "#c0352c"),
    c(30, 32, 11, "#d94a3a"),
    line(32, 21, 32, 12, V["greenDark"], 2.8),
    leaf(33, 20, V["green"], 0.9),
]
P["avocado"] = [
    e(32, 36, 16, 19, "#3f7a33"),
    e(32, 36, 13, 16, "#6aa84f"),
    e(32, 36, 8, 9, "#f2e3a0"),
    c(32, 38, 5.5, "#8a5a2b"),
    *stem(32, 20, V["brown"], 6, 2.6),
]
P["buko"] = [
    c(32, 36, 17, "#7a4e24"),
    c(32, 35, 16, "#8a5a2b"),
    p("M20,27 C26,19 38,19 44,27", None, "#6f4420", 2.2, "round"),
    p("M18,38 C24,30 40,30 46,38", None, "#6f4420", 2, "round"),
    p("M21,45 C27,52 37,52 43,45", None, "#6f4420", 2.2, "round"),
    p("M24,23 C26,31 26,44 24,51", None, "#6f4420", 1.6, "round"),
    p("M40,23 C38,31 38,44 40,51", None, "#6f4420", 1.6, "round"),
    c(27, 25, 3.2, "#3f2712"), c(37, 25, 3.2, "#3f2712"), c(32, 32, 3.2, "#3f2712"),
]


P["ubas"] = [
    c(24, 30, 7, V["purple"]), c(38, 30, 7, "#8f4fb0"), c(31, 38, 7.5, V["purple"]),
    c(45, 38, 6.5, "#a86cc4"), c(17, 38, 6, "#8f4fb0"), c(31, 50, 7, "#7b3fa0"),
    c(24, 28, 2.2, "#c9a6dd"), c(38, 28, 2.2, "#c9a6dd"),
    line(31, 22, 33, 16, V["brown"], 2.8),
    leaf(34, 18, V["green"], 0.95),
]

# ------------------------------------------------------- KARNE
P["pork-kasim"] = meat_slab("#e07a72", "#c95b52", "#f7e3dc")
P["pork-liempo"] = [
    p("M16,20 C24,14 44,14 50,20 C56,26 56,44 48,50 C38,56 22,54 16,46 C11,38 11,27 16,20 Z", "#f0c9b4"),
    line(16, 27, 49, 27, "#d2544a", 4.5),
    line(14, 35, 51, 35, "#c2413a", 4),
    line(16, 43, 47, 43, "#d2544a", 4.5),
    line(19, 50, 44, 50, "#c2413a", 3),
]
P["porkchop"] = [
    p("M18,24 C24,16 42,16 48,24 C54,32 52,48 42,52 C32,56 20,52 17,43 C14,37 14,30 18,24 Z", C["meat"]),
    p("M22,29 C28,23 40,23 45,29 C49,35 47,45 40,48 C33,51 24,48 21,42 C19,37 19,33 22,29 Z", "#e2705f"),
    c(46, 30, 7, C["bone"]),
    c(46, 30, 4, "#e2d5c2"),
    line(46, 30, 56, 24, C["bone"], 4),
]
P["pork-ribs"] = [
    p("M12,22 C24,16 44,16 54,22 C56,28 54,34 46,36 C34,39 20,38 12,34 C10,30 10,25 12,22 Z", "#c9503f"),
    line(18, 39, 20, 50, C["bone"], 4.5),
    line(28, 40, 30, 52, C["bone"], 4.5),
    line(38, 39, 40, 51, C["bone"], 4.5),
    line(48, 37, 49, 48, C["bone"], 4),
    line(16, 26, 50, 26, "#e2705f", 3),
]
P["giniling-pork"] = [
    c(24, 34, 10, "#d9615a"), c(40, 32, 9, "#c9503f"), c(32, 44, 9, "#e0705f"),
    c(46, 44, 7, "#d9615a"), c(18, 45, 6.5, "#c9503f"),
    c(21, 30, 2.4, "#f0c9b4"), c(36, 27, 2.2, "#f0c9b4"), c(28, 41, 2.2, "#f0c9b4"),
]
P["beef-sirloin"] = [
    p("M14,26 C20,16 44,14 52,24 C58,32 54,48 44,52 C32,56 18,52 14,42 C11,36 11,30 14,26 Z", "#8f2f34"),
    p("M20,31 C26,24 42,23 47,30 C51,36 48,45 41,47 C33,50 23,47 20,41 C18,37 18,34 20,31 Z", "#a83a40"),
    line(24, 38, 44, 36, "#f3ded2", 3),
    line(26, 45, 40, 43, "#f3ded2", 2.2),
    c(34, 30, 3, "#f3ded2"),
]
P["beef-brisket"] = [
    p("M14,24 C26,18 44,18 52,24 C56,30 54,44 46,50 C34,56 20,54 14,46 C10,39 11,29 14,24 Z", "#9c3a38"),
    line(14, 30, 52, 30, "#f3ded2", 4),
    line(13, 38, 52, 38, "#c9625c", 4),
    line(15, 46, 48, 46, "#f3ded2", 3.5),
]

# ------------------------------------------------------- MANOK
P["chicken-whole"] = [
    p("M16,34 C16,24 26,17 38,19 C50,21 56,30 54,39 C52,48 40,53 28,51 C20,49 16,43 16,34 Z", "#e9973f"),
    p("M20,34 C20,27 28,22 38,24 C47,26 51,32 50,38 C49,44 40,48 31,47 C24,46 20,41 20,34 Z", "#f2b35c"),
    p("M14,40 C8,42 6,48 10,52 C14,50 17,46 18,42 Z", "#d9863a"),
    p("M50,44 C54,48 54,52 50,54 C48,50 48,47 50,44 Z", "#d9863a"),
    c(22, 22, 9, "#f2b35c"),
    p("M16,16 C18,11 24,11 25,16 C22,17 19,17 16,16 Z", "#d94a3a"),
    poly("13,23 5,26 13,29", "#e8a33c"),
    c(21, 21, 2.2, V["black"]),
    line(30, 50, 30, 58, "#e8a33c", 3, "round"),
    line(40, 50, 40, 58, "#e8a33c", 3, "round"),
    line(30, 58, 25, 60, "#e8a33c", 2.4, "round"),
    line(40, 58, 45, 60, "#e8a33c", 2.4, "round"),
]


P["chicken-breast"] = [
    # boneless fillet: long teardrop, wider at one end
    p("M12,34 C12,27 22,22 34,22 C46,22 56,26 56,32 C56,39 46,44 33,44 C22,44 12,41 12,34 Z", "#f2c08a"),
    p("M16,34 C16,28 25,25 35,25 C45,25 52,28 52,32 C52,37 44,41 33,41 C24,41 16,39 16,34 Z", "#f7d3a6"),
    p("M16,33 C26,31 42,31 52,33", None, "#e0a468", 1.8, "round"),
    p("M18,37 C28,39 42,39 50,37", None, "#e0a468", 1.6, "round"),
    p("M12,34 C12,29 16,26 21,25", None, "#dc9a58", 1.8, "round"),
    c(22, 30, 2, "#e8b174"),
]


P["chicken-wings"] = [
    p("M12,26 C18,18 30,17 34,24 C38,31 34,40 26,42 C18,44 12,38 11,32 C10,29 10,27 12,26 Z", "#efa94f"),
    p("M16,29 C20,23 28,22 31,27 C34,32 31,38 25,39 C20,40 16,36 15,31 C15,30 15,29 16,29 Z", "#f7c684"),
    p("M34,30 C40,24 52,25 55,33 C58,41 52,49 43,49 C35,49 31,42 31,36 C31,33 32,31 34,30 Z", "#eba246"),
    p("M38,34 C43,30 51,31 52,36 C54,42 49,46 43,46 C38,46 35,41 35,37 C35,35 36,34 38,34 Z", "#f7c684"),
    p("M33,30 C32,33 32,36 33,39", None, "#d98c33", 2, "round"),
]


P["chicken-leg"] = [
    e(28, 30, 15, 14, "#efa94f", rot=-20),
    p("M36,40 C44,44 48,50 45,54 C42,58 34,56 30,50 Z", "#efa94f"),
    line(46, 50, 57, 58, C["bone"], 6),
    c(58, 59, 4, C["bone"]),
]
P["chicken-feet"] = [
    line(32, 8, 32, 32, "#e8a33c", 6, "round"),
    line(32, 32, 18, 52, "#e8a33c", 5, "round"),
    line(32, 32, 46, 52, "#e8a33c", 5, "round"),
    line(32, 30, 32, 54, "#e8a33c", 5, "round"),
    line(18, 52, 12, 57, "#cf8c2c", 3.4, "round"),
    line(46, 52, 52, 57, "#cf8c2c", 3.4, "round"),
    line(32, 54, 32, 60, "#cf8c2c", 3.4, "round"),
    line(28, 16, 36, 16, "#d18f2f", 1.6, "round"),
    line(28, 23, 36, 23, "#d18f2f", 1.6, "round"),
    line(28, 30, 36, 30, "#d18f2f", 1.6, "round"),
    line(26, 40, 30, 40, "#d18f2f", 1.4, "round"),
    line(34, 40, 38, 40, "#d18f2f", 1.4, "round"),
    c(32, 8, 3.4, "#cf8c2c"),
]


# ------------------------------------------------------- ISDA
P["bangus"] = fish_body("#a9c2cc", "#e6eef2", "#4e7b90") + [
    line(30, 24, 30, 40, "#8aa8b4", 1.6),
    line(36, 22, 36, 42, "#8aa8b4", 1.6),
    line(42, 24, 42, 40, "#8aa8b4", 1.6),
]
P["tilapia"] = fish_body("#7f8b93", "#c2ccd1", "#5b666e") + [
    line(32, 24, 32, 40, "#6b767e", 1.6),
    line(39, 23, 39, 41, "#6b767e", 1.6),
]
P["galunggong"] = fish_body("#5b7c94", "#cfe0ea", "#2f4f66") + [
    line(22, 34, 44, 32, "#3d5a70", 2, "round"),
    line(22, 38, 44, 36, "#3d5a70", 1.6, "round"),
]
P["tuna"] = [
    *fish_body("#2f4f74", "#c9dbe8", "#1f3550"),
    line(28, 26, 28, 40, "#f0b980", 2, "round"),
]
P["hipon"] = [
    p("M46,18 C54,26 52,42 40,48 C28,54 16,48 14,38 C12,28 20,20 30,18 C36,17 42,15 46,18 Z", C["pinkDeep"]),
    p("M26,22 C36,20 46,26 47,34 C48,42 38,48 30,47 C22,46 18,40 19,33 C20,27 22,23 26,22 Z", C["pink"]),
    p("M20,30 C26,28 34,29 40,33", None, "#d9726a", 1.8, "round"),
    p("M19,37 C26,35 34,36 41,40", None, "#d9726a", 1.8, "round"),
    p("M22,44 C28,42 34,43 39,46", None, "#d9726a", 1.6, "round"),
    poly("14,42 4,38 6,46 2,50 12,50", C["pinkDeep"]),
    c(46, 24, 5.5, "#e88a80"),
    line(49, 21, 60, 13, "#c0564e", 2.4),
    line(49, 25, 61, 24, "#c0564e", 2.2),
    line(43, 28, 50, 32, "#c0564e", 2),
    c(47, 23, 2.6, V["black"]),
    c(49, 20, 1.6, "#ffffff"),
]


P["pusit"] = [
    # narrow mantle + fins + thin tentacles
    p("M32,8 C37,14 39,24 38,33 C37,41 34,45 32,45 C30,45 27,41 26,33 C25,24 27,14 32,8 Z", "#c9869a"),
    p("M32,12 C36,17 37,25 36,33 C35,39 33,42 32,42 C31,42 29,39 28,33 C27,25 28,17 32,12 Z", "#e0aeb9"),
    poly("26,20 19,24 26,29", "#c9869a"),
    poly("38,20 45,24 38,29", "#c9869a"),
    c(29, 20, 1.7, V["black"]), c(35, 20, 1.7, V["black"]),
    p("M26,45 C23,51 25,54 22,57", None, "#c9869a", 2.6, "round"),
    p("M29,46 C28,52 30,55 28,59", None, "#c9869a", 2.6, "round"),
    p("M32,46 C32,52 32,56 32,60", None, "#c9869a", 2.6, "round"),
    p("M35,46 C36,52 34,55 36,59", None, "#c9869a", 2.6, "round"),
    p("M38,45 C41,51 39,54 42,57", None, "#c9869a", 2.6, "round"),
]


P["alimango"] = [
    e(32, 38, 16, 11, "#e06a2a"),
    e(32, 36, 13, 9, "#f08a3c"),
    p("M20,28 C10,24 6,30 8,36 C12,40 18,38 20,32 Z", "#e06a2a"),
    p("M44,28 C54,24 58,30 56,36 C52,40 46,38 44,32 Z", "#e06a2a"),
    c(20, 28, 2.6, V["black"]), c(44, 28, 2.6, V["black"]),
    line(26, 48, 20, 56, "#c9541c", 3.4),
    line(32, 49, 32, 57, "#c9541c", 3.4),
    line(38, 48, 44, 56, "#c9541c", 3.4),
]
P["tahong"] = [
    # mussel: fan shell with ribs and a hinge at the base
    p("M32,8 C41,14 50,26 52,42 C46,48 38,50 32,50 C26,50 18,48 12,42 C14,26 23,14 32,8 Z", "#3a4550"),
    p("M32,13 C39,18 46,28 47,41 C43,45 37,47 32,47 C27,47 21,45 17,41 C18,28 25,18 32,13 Z", "#55636f"),
    line(32, 13, 32, 47, "#7d8b93", 1.6),
    line(26, 16, 24, 45, "#7d8b93", 1.4),
    line(38, 16, 40, 45, "#7d8b93", 1.4),
    line(21, 22, 18, 42, "#7d8b93", 1.2),
    line(43, 22, 46, 42, "#7d8b93", 1.2),
    p("M26,50 C30,53 34,53 38,50 C35,55 29,55 26,50 Z", "#a9b6bd"),
    c(32, 52, 2, "#7d8b93"),
]


P["tamban"] = fish_body("#9fb8c4", "#e2ecf0", "#6b8ea0", tail=True) + [
    line(30, 34, 46, 32, "#7f9dad", 1.8, "round"),
    line(30, 38, 46, 36, "#7f9dad", 1.4, "round"),
]

# ------------------------------------------------------- BIGAS
P["rice-regular"] = bowl(V["white"], "#4a86c8")
P["rice-well"] = bowl("#fdfdff", "#3f74b0", [
    p("M50,20 L56,14", None, "#cfe0ea", 2.4, "round"),
    p("M54,24 L60,19", None, "#cfe0ea", 2.4, "round"),
])
P["rice-premium"] = bowl("#fff8e0", "#d9a520", [
    c(46, 20, 3.4, "#f4c02e"),
    p("M20,18 L24,11", None, "#e8c76a", 2.4, "round"),
    p("M30,16 L34,9", None, "#e8c76a", 2.4, "round"),
])
P["rice-jasmine"] = bowl(V["white"], "#3f9b7a", [
    c(32, 20, 4, V["white"]),
    c(40, 22, 3.4, V["white"]),
    c(24, 22, 3.4, V["white"]),
    c(32, 24, 2.4, "#f4c02e"),
])
P["malagkit"] = [
    p("M8,46 C18,39 46,39 56,46 C51,54 13,54 8,46 Z", "#5aa84f"),
    p("M13,46 C20,41 44,41 51,46 C46,51 18,51 13,46 Z", "#7cc576"),
    p("M18,26 C18,19 24,14 32,14 C40,14 46,19 46,26 C46,36 40,43 32,43 C24,43 18,36 18,26 Z", "#fdf7ea"),
    p("M18,26 C18,19 24,14 32,14 C40,14 46,19 46,26 C41,23 36,22 32,22 C28,22 23,23 18,26 Z", "#f2ecdf"),
    c(26, 31, 2, "#3a4550"), c(35, 29, 2, "#3a4550"), c(31, 37, 2, "#3a4550"),
    p("M23,20 C28,17 36,17 41,20", None, "#ded2ba", 1.8, "round"),
]


# ------------------------------------------------------- ITLOG & GATAS
P["egg-medium"] = [
    e(32, 38, 13, 17, "#e9dfc9"),
    e(32, 38, 13, 17, "#fdf8ee"),
    e(27, 31, 4.4, 6, "#ffffff"),
]


P["egg-large"] = [
    e(40, 40, 15, 19, "#e9dfc9"),
    e(40, 40, 15, 19, "#fdf8ee"),
    e(24, 42, 14, 17, "#e6dcc6"),
    e(24, 42, 14, 17, "#fbf5e9"),
    e(20, 36, 4.5, 6, "#ffffff"),
]


P["egg-organic"] = [
    e(32, 36, 15, 19, "#c99a5f"),
    e(32, 36, 15, 19, "#b98449"),
    e(27, 29, 5, 6.5, "#e2bd8a"),
]
P["fresh-milk"] = [
    p("M20,24 L32,10 L44,24 L44,54 C44,56 42,58 40,58 L24,58 C22,58 20,56 20,54 Z", C["white"]),
    p("M20,24 L32,10 L44,24 Z", "#e2ecf0"),
    p("M20,24 L32,30 L44,24", None, "#c9dbe8", 1.4),
    r(22, 30, 20, 14, "#4a86c8", rx=2),
    c(32, 37, 4, C["white"]),
    p("M26,37 C29,34 35,34 38,37", None, "#bcd8ea", 1.6, "round"),
    r(20, 50, 24, 4, "#8fb8d8", rx=1.5),
]


# ------------------------------------------------------- PANIMPLA
P["asin"] = [
    r(24, 26, 16, 26, C["white"], rx=4),
    r(22, 20, 20, 8, "#cfd8dd", rx=3),
    c(28, 16, 2, V["black"]), c(33, 16, 2, V["black"]), c(38, 16, 2, V["black"]),
    r(26, 32, 12, 6, "#4a86c8", rx=2),
    c(40, 46, 2, "#e6eef2"), c(44, 50, 1.6, "#e6eef2"), c(46, 44, 1.6, "#e6eef2"),
]
P["asukal-washed"] = [
    # stacked sugar cubes
    p("M16,32 L26,26 L36,32 L26,38 Z", "#fdf4e3"),
    p("M16,32 L16,44 L26,50 L26,38 Z", "#e8d6b8"),
    p("M36,32 L36,44 L26,50 L26,38 Z", "#d9c4a0"),
    p("M28,20 L38,14 L48,20 L38,26 Z", "#fdf4e3"),
    p("M28,20 L28,32 L38,38 L38,26 Z", "#e8d6b8"),
    p("M48,20 L48,32 L38,38 L38,26 Z", "#d9c4a0"),
    p("M40,40 L48,35 L56,40 L48,45 Z", "#f7f3ea"),
    p("M40,40 L40,50 L48,55 L48,45 Z", "#e0cdad"),
    p("M56,40 L56,50 L48,55 L48,45 Z", "#d0b992"),
]


P["asukal-brown"] = [
    p("M16,32 L26,26 L36,32 L26,38 Z", "#c99a5f"),
    p("M16,32 L16,44 L26,50 L26,38 Z", "#a9702f"),
    p("M36,32 L36,44 L26,50 L26,38 Z", "#8f5e26"),
    p("M28,20 L38,14 L48,20 L38,26 Z", "#d4a869"),
    p("M28,20 L28,32 L38,38 L38,26 Z", "#b98449"),
    p("M48,20 L48,32 L38,38 L38,26 Z", "#9a6a34"),
    p("M40,40 L48,35 L56,40 L48,45 Z", "#c99a5f"),
    p("M40,40 L40,50 L48,55 L48,45 Z", "#a9702f"),
    p("M56,40 L56,50 L48,55 L48,45 Z", "#8f5e26"),
]


P["mantika"] = [
    r(26, 10, 12, 7, "#d9a520", rx=2),
    r(28, 16, 8, 7, "#f2d98a", rx=2),
    p("M20,24 C20,21 24,21 24,24 L40,24 C40,21 44,21 44,24 L44,52 C44,56 41,58 38,58 L26,58 C23,58 20,56 20,52 Z", "#f2d98a"),
    p("M22,32 L42,32 L42,52 C42,54 40,56 38,56 L26,56 C24,56 22,54 22,52 Z", V["yellow"]),
    r(22, 36, 20, 10, C["white"], rx=2),
    c(32, 41, 4, V["yellow"]),
    p("M22,32 L42,32", None, "#d9a520", 1.4),
]


P["suka"] = [
    r(26, 10, 12, 7, "#3f8f3f", rx=2),
    r(28, 16, 8, 7, "#dfe6d2", rx=2),
    p("M20,24 C20,21 24,21 24,24 L40,24 C40,21 44,21 44,24 L44,52 C44,56 41,58 38,58 L26,58 C23,58 20,56 20,52 Z", "#cfe0bf"),
    p("M22,32 L42,32 L42,52 C42,54 40,56 38,56 L26,56 C24,56 22,54 22,52 Z", "#f0f7e8"),
    p("M22,42 L42,42 L42,52 C42,54 40,56 38,56 L26,56 C24,56 22,54 22,52 Z", "#dfe6d2"),
    r(22, 35, 20, 9, "#4aa03f", rx=2),
    c(32, 39.5, 3, C["white"]),
]


P["patis"] = [
    r(26, 10, 12, 7, "#b8860b", rx=2),
    r(28, 16, 8, 7, "#c9a45e", rx=2),
    p("M20,24 C20,21 24,21 24,24 L40,24 C40,21 44,21 44,24 L44,52 C44,56 41,58 38,58 L26,58 C23,58 20,56 20,52 Z", "#c98a2b"),
    p("M22,32 L42,32 L42,52 C42,54 40,56 38,56 L26,56 C24,56 22,54 22,52 Z", V["yellow"]),
    r(22, 36, 20, 10, C["white"], rx=2),
    poly("28,41 33,37 38,41 33,45", "#b8860b"),
]


P["paminta"] = [
    c(24, 34, 6, "#3a4550"), c(36, 32, 5.5, "#55636f"), c(30, 44, 6, "#4a5661"),
    c(42, 42, 4.6, "#3a4550"), c(19, 43, 4.4, "#55636f"),
    c(23, 32, 1.8, "#79868f"), c(35, 30, 1.6, "#79868f"), c(44, 32, 2, "#4a5661"),
    # pepper mill
    p("M46,22 C46,19 48,18 51,18 C54,18 56,19 56,22 L56,50 C56,53 54,54 51,54 C48,54 46,53 46,50 Z", "#a9702f"),
    r(48, 14, 6, 6, "#8a5a2b", rx=1.5),
    p("M48,30 L54,30", None, "#8a5a2b", 1.6, "round"),
    p("M48,38 L54,38", None, "#8a5a2b", 1.6, "round"),
]
P["toyo"] = bottle("#4a3226", "#2f1f18", "#8a5a2b", "#f4c02e") + [
    r(27, 41, 10, 7, "#e2432f", rx=1.6),
]

ALL = {}
for k, v in CATEGORY_ICONS.items():
    ALL[k] = v["shapes"]
ALL.update(P)

# rambutan: generate the spiky hairs programmatically (kept out of the literal above)
import math

hairs = []
for i in range(18):
    a = math.radians(i * 20)
    x1 = 32 + 13.5 * math.cos(a)
    y1 = 36 + 13.5 * math.sin(a)
    x2 = 32 + 18 * math.cos(a)
    y2 = 36 + 18 * math.sin(a)
    hairs.append(line(round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1), "#8f2a24", 2.2))
item = ALL["rambutan"]
ALL["rambutan"] = [item[0]] + hairs + [item[1], item[2], item[3]]

OUT = os.path.join(os.path.dirname(__file__), "..", "src", "components", "icons", "food-icons.json")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
meta = {
    "ampalaya": "Bitter gourd", "talong": "Eggplant", "kamatis": "Tomato",
    "sibuyas-pula": "Red onion", "sibuyas-puti": "White onion", "bawang": "Garlic",
    "luya": "Ginger", "kalamansi": "Calamansi", "sili-labuyo": "Bird's eye chili",
    "siling-haba": "Long green chili", "repolyo": "Cabbage", "pechay": "Bok choy",
    "carrots": "Carrot", "sayote": "Chayote", "kalabasa": "Squash", "okra": "Okra",
    "sitaw": "String beans", "patatas": "Potato", "monggo": "Mung beans",
    "kangkong": "Water spinach", "saging-lakatan": "Lakatan banana", "saging-saba": "Saba banana",
    "mangga": "Mango", "papaya": "Papaya", "pinya": "Pineapple", "pakwan": "Watermelon",
    "melon": "Melon", "lanzones": "Lanzones", "rambutan": "Rambutan", "avocado": "Avocado",
    "buko": "Young coconut", "ubas": "Grapes", "pork-kasim": "Pork shoulder",
    "pork-liempo": "Pork belly", "porkchop": "Pork chop", "pork-ribs": "Pork ribs",
    "giniling-pork": "Ground pork", "beef-sirloin": "Beef sirloin", "beef-brisket": "Beef brisket",
    "chicken-whole": "Whole chicken", "chicken-breast": "Chicken breast",
    "chicken-wings": "Chicken wings", "chicken-leg": "Chicken leg quarter",
    "chicken-feet": "Chicken feet", "bangus": "Milkfish", "tilapia": "Tilapia",
    "galunggong": "Round scad", "tuna": "Yellowfin tuna", "hipon": "Shrimp", "pusit": "Squid",
    "alimango": "Mud crab", "tahong": "Mussels", "tamban": "Sardines",
    "rice-regular": "Regular milled rice", "rice-well": "Well-milled rice",
    "rice-premium": "Premium rice", "rice-jasmine": "Jasmine rice", "malagkit": "Glutinous rice",
    "egg-medium": "Medium egg", "egg-large": "Large egg", "egg-organic": "Organic brown egg",
    "fresh-milk": "Fresh milk", "asin": "Salt", "asukal-washed": "Washed sugar",
    "asukal-brown": "Brown sugar", "mantika": "Cooking oil", "suka": "Vinegar",
    "patis": "Fish sauce", "paminta": "Black pepper", "toyo": "Soy sauce",
    "vegetables": "Gulay", "fruits": "Prutas", "meat": "Karne", "poultry": "Manok",
    "seafood": "Isda", "rice": "Bigas", "eggDairy": "Itlog & Gatas", "pantry": "Panimpla",
}
payload = {"viewBox": "0 0 64 64", "icons": ALL, "labels": meta}
with open(OUT, "w") as fh:
    json.dump(payload, fh, separators=(",", ":"), sort_keys=True)
    fh.write("\n")
print(f"wrote {OUT}: {len(ALL)} icons, {os.path.getsize(OUT)} bytes")
print("ids:", " ".join(sorted(ALL)))
