#!/usr/bin/env python3
"""
Generates PLACEHOLDER assets so the mod runs end-to-end before you have a real model:
  - geo model (blocky Godzilla with 12 dorsal plates + 12 'plate_glow_NN' overlay bones + mouth_glow)
  - animation file (idle/walk/roar/charge/fire/vent/bite/tail_swipe/death, durations match GodzillaTuning)
  - texture + glowmask
  - entity/PlateProfile.java (world offsets of each plate, used for particles)

Replace the geo/texture/animation files with your Blockbench export when you have it.
Keep the bone names and animation names (see README) and everything keeps working.
Run from the project root:  python3 tools/gen_placeholder_assets.py
"""
import json, math, os, random
from PIL import Image

random.seed(1954)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODID = "godzilla_mod"
RES = f"{ROOT}/src/main/resources/assets/{MODID}"
JAVA = f"{ROOT}/src/main/java/com/example/godzilla/entity"
for d in (f"{RES}/geo", f"{RES}/animations", f"{RES}/textures/entity", JAVA):
    os.makedirs(d, exist_ok=True)

# ---------------------------------------------------------------- texture (64x64, four 16x16 swatches)
A, B, C, D = (0, 0), (16, 0), (32, 0), (48, 0)   # body, dark plate, blue glow, amber eye
img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
glow = Image.new("RGBA", (64, 64), (0, 0, 0, 0))

def fill(region, base, jitter, im=img):
    rx, ry = region
    for x in range(16):
        for y in range(16):
            j = random.randint(-jitter, jitter)
            im.putpixel((rx + x, ry + y), (max(0, min(255, base[0] + j)), max(0, min(255, base[1] + j)), max(0, min(255, base[2] + j)), 255))

fill(A, (72, 74, 78), 14)
fill(B, (32, 32, 36), 8)
fill(C, (90, 200, 255), 35)
fill(D, (255, 170, 40), 20)
for region, base, jit in ((C, (110, 210, 255), 30), (D, (255, 180, 50), 15)):
    fill(region, base, jit, glow)
img.save(f"{RES}/textures/entity/godzilla_minus_one.png")
glow.save(f"{RES}/textures/entity/godzilla_minus_one_glowmask.png")

# ---------------------------------------------------------------- geometry (1 unit = 1/16 block, model faces -Z)
def face_uv(region):
    return {f: {"uv": list(region), "uv_size": [16, 16]} for f in ("north", "east", "south", "west", "up", "down")}

def cube(origin, size, region=A, inflate=0):
    c = {"origin": origin, "size": size, "uv": face_uv(region)}
    if inflate:
        c["inflate"] = inflate
    return c

bones = []
def bone(name, parent, pivot, cubes=None):
    b = {"name": name, "pivot": pivot}
    if parent:
        b["parent"] = parent
    if cubes:
        b["cubes"] = cubes
    bones.append(b)

bone("root", None, [0, 0, 0])
bone("body", "root", [0, 110, 0], [cube([-40, 110, -36], [80, 130, 72])])
bone("leg_left", "root", [-26, 120, 0], [cube([-44, 0, -26], [36, 124, 52]), cube([-48, 0, -54], [44, 14, 30])])
bone("leg_right", "root", [26, 120, 0], [cube([8, 0, -26], [36, 124, 52]), cube([4, 0, -54], [44, 14, 30])])
bone("torso", "body", [0, 200, 0], [cube([-36, 200, -40], [72, 96, 64])])
bone("arm_left", "torso", [-38, 270, -26], [cube([-58, 214, -38], [22, 60, 26]), cube([-58, 196, -50], [22, 18, 24])])
bone("arm_right", "torso", [38, 270, -26], [cube([36, 214, -38], [22, 60, 26]), cube([36, 196, -50], [22, 18, 24])])
bone("head", "torso", [0, 288, -30], [
    cube([-24, 284, -72], [48, 40, 52]),
    cube([-18, 290, -90], [36, 24, 20]),
    cube([-25, 310, -73], [8, 6, 3], D),
    cube([17, 310, -73], [8, 6, 3], D),
])
bone("jaw", "head", [0, 288, -40], [cube([-16, 276, -88], [32, 14, 52])])
bone("mouth_glow", "head", [0, 288, -60], [cube([-12, 286, -82], [24, 6, 32], C)])
bone("tail_1", "body", [0, 130, 34], [cube([-28, 100, 30], [56, 60, 60])])
bone("tail_2", "tail_1", [0, 120, 90], [cube([-20, 96, 88], [40, 44, 60])])
bone("tail_3", "tail_2", [0, 115, 148], [cube([-12, 92, 146], [24, 32, 60])])

# 12 dorsal plates, tail tip (0) -> neck (11): (z, base_y, parent)
PLATES = [(200, 120, "tail_3"), (172, 120, "tail_3"), (140, 136, "tail_2"), (110, 136, "tail_2"),
          (80, 156, "tail_1"), (56, 156, "tail_1"), (34, 200, "body"), (30, 236, "body"),
          (20, 264, "torso"), (14, 290, "torso"), (0, 294, "torso"), (-16, 296, "torso")]
fwd_list, up_list = [], []
for i, (z, base, parent) in enumerate(PLATES):
    h = 24 + round(18 * math.sin(math.pi * (i + 1) / 13))
    w = 8 + round(4 * math.sin(math.pi * (i + 1) / 13))
    origin = [-w / 2, base - 2, z - 7]
    size = [w, h, 14]
    pivot = [0, base + h / 2, z]
    bone(f"plate_{i:02d}", parent, pivot, [cube(origin, size, B)])
    bone(f"plate_glow_{i:02d}", parent, pivot, [cube(origin, size, C, inflate=1.5)])
    fwd_list.append(-z / 16.0)
    up_list.append((base - 2 + h / 2) / 16.0)

geo = {
    "format_version": "1.12.0",
    "minecraft:geometry": [{
        "description": {
            "identifier": "geometry.godzilla_minus_one",
            "texture_width": 64, "texture_height": 64,
            "visible_bounds_width": 48, "visible_bounds_height": 40, "visible_bounds_offset": [0, 10, 0],
        },
        "bones": bones,
    }],
}
with open(f"{RES}/geo/godzilla_minus_one.geo.json", "w") as f:
    json.dump(geo, f, indent=1)

# ---------------------------------------------------------------- Java plate profile
def arr(v):
    return ", ".join(f"{x:.3f}" for x in v)
with open(f"{JAVA}/PlateProfile.java", "w") as f:
    f.write(f"""package com.example.godzilla.entity;

/**
 * GENERATED by tools/gen_placeholder_assets.py - where each dorsal plate sits, in blocks, relative to the entity.
 * Index 0 = tail tip ... index {len(PLATES) - 1} = neck. FORWARD is along the facing direction (negative = behind).
 * If you replace the model, edit these numbers to match your plates (only used for particles/flashes).
 */
public final class PlateProfile {{
    private PlateProfile() {{}}
    public static final double[] FORWARD = {{{arr(fwd_list)}}};
    public static final double[] UP = {{{arr(up_list)}}};
}}
""")

# ---------------------------------------------------------------- animations
def t(x):
    return str(float(x))

class Anim:
    def __init__(self, name, length, loop):
        self.name, self.length, self.loop, self.b = name, length, loop, {}
    def rot(self, bone, keys):
        self.b.setdefault(bone, {})["rotation"] = {t(k): v for k, v in keys}
        return self
    def pos(self, bone, keys):
        self.b.setdefault(bone, {})["position"] = {t(k): v for k, v in keys}
        return self
    def out(self):
        return {f"animation.godzilla_minus_one.{self.name}": {"loop": self.loop, "animation_length": self.length, "bones": self.b}}

def shake(start, end, step, amp0, amp1, axis=2):
    keys, k, i = [], start, 0
    while k <= end + 1e-6:
        a = amp0 + (amp1 - amp0) * ((k - start) / max(1e-6, end - start))
        v = [0, 0, 0]
        v[axis] = a if i % 2 == 0 else -a
        keys.append((round(k, 3), v))
        k += step
        i += 1
    return keys

Z = [0, 0, 0]
anims = []

a = Anim("idle", 4.0, True)
a.rot("body", [(0, Z), (2, [1.2, 0, 0]), (4, Z)])
a.rot("torso", [(0, Z), (2, [-1.5, 0, 0]), (4, Z)])
a.rot("head", [(0, Z), (1, [0, 4, 0]), (2, Z), (3, [0, -4, 0]), (4, Z)])
a.rot("jaw", [(0, Z), (2, [3, 0, 0]), (4, Z)])
a.rot("tail_1", [(0, Z), (1, [0, 3, 0]), (2, Z), (3, [0, -3, 0]), (4, Z)])
a.rot("tail_2", [(0, Z), (1, [0, -5, 0]), (2, Z), (3, [0, 5, 0]), (4, Z)])
a.rot("arm_left", [(0, Z), (2, [4, 0, 0]), (4, Z)])
a.rot("arm_right", [(0, Z), (2, [-4, 0, 0]), (4, Z)])
anims.append(a)

a = Anim("walk", 2.0, True)   # a foot plants every 1.0s = every 20 ticks (GodzillaTuning.STEP_INTERVAL_TICKS)
a.rot("leg_left", [(0, [-24, 0, 0]), (0.5, Z), (1, [24, 0, 0]), (1.5, Z), (2, [-24, 0, 0])])
a.rot("leg_right", [(0, [24, 0, 0]), (0.5, Z), (1, [-24, 0, 0]), (1.5, Z), (2, [24, 0, 0])])
a.pos("leg_left", [(0, Z), (1, Z), (1.5, [0, 8, 0]), (2, Z)])
a.pos("leg_right", [(0, Z), (0.5, [0, 8, 0]), (1, Z), (2, Z)])
a.pos("body", [(0, Z), (0.5, [0, -4, 0]), (1, Z), (1.5, [0, -4, 0]), (2, Z)])
a.rot("body", [(0, [0, 0, 2]), (1, [0, 0, -2]), (2, [0, 0, 2])])
a.rot("torso", [(0, [0, 4, 0]), (1, [0, -4, 0]), (2, [0, 4, 0])])
a.rot("head", [(0, [0, -3, 0]), (1, [0, 3, 0]), (2, [0, -3, 0])])
a.rot("tail_1", [(0, [0, -8, 0]), (1, [0, 8, 0]), (2, [0, -8, 0])])
a.rot("tail_2", [(0, [0, 10, 0]), (1, [0, -10, 0]), (2, [0, 10, 0])])
a.rot("tail_3", [(0, [0, -14, 0]), (1, [0, 14, 0]), (2, [0, -14, 0])])
a.rot("arm_left", [(0, [14, 0, 0]), (1, [-14, 0, 0]), (2, [14, 0, 0])])
a.rot("arm_right", [(0, [-14, 0, 0]), (1, [14, 0, 0]), (2, [-14, 0, 0])])
anims.append(a)

a = Anim("roar", 2.5, False)  # 50 ticks = GodzillaTuning.ROAR_TICKS
a.rot("torso", [(0, Z), (0.6, [-10, 0, 0]), (2.0, [-10, 0, 0]), (2.5, Z)])
a.rot("head", [(0, Z), (0.6, [-28, 0, 0]), (2.0, [-28, 0, 0]), (2.5, Z)])
a.rot("jaw", [(0, Z), (0.7, [42, 0, 0]), (2.0, [42, 0, 0]), (2.4, Z)])
a.rot("arm_left", [(0, Z), (0.6, [-25, 0, 20]), (2.0, [-25, 0, 20]), (2.5, Z)])
a.rot("arm_right", [(0, Z), (0.6, [-25, 0, -20]), (2.0, [-25, 0, -20]), (2.5, Z)])
a.rot("tail_1", [(0, Z), (0.6, [-6, 0, 0]), (2.0, [-6, 0, 0]), (2.5, Z)])
a.rot("body", [(0, Z)] + shake(0.7, 2.0, 0.1, 0.8, 0.8) + [(2.5, Z)])
anims.append(a)

a = Anim("charge", 4.0, "hold_on_last_frame")  # 80 ticks = GodzillaTuning.CHARGE_TICKS
a.rot("torso", [(0, Z), (3.0, [-9, 0, 0]), (4.0, [-9, 0, 0])])
a.rot("head", [(0, Z), (3.0, [-22, 0, 0]), (4.0, [-22, 0, 0])])
a.rot("jaw", [(0, Z), (2.5, Z), (3.5, [28, 0, 0]), (4.0, [28, 0, 0])])
a.rot("arm_left", [(0, Z), (3.0, [-12, 0, 10]), (4.0, [-12, 0, 10])])
a.rot("arm_right", [(0, Z), (3.0, [-12, 0, -10]), (4.0, [-12, 0, -10])])
a.rot("body", [(0, Z)] + shake(0.5, 4.0, 0.125, 0.3, 1.2))
anims.append(a)

a = Anim("fire", 1.0, True)
a.rot("torso", [(0, [-8, 0, 0]), (1, [-8, 0, 0])])
a.rot("head", [(0, [-12, 0, 0]), (1, [-12, 0, 0])])
a.rot("jaw", [(0, [45, 0, 0]), (0.5, [48, 0, 0]), (1, [45, 0, 0])])
a.rot("arm_left", [(0, [-10, 0, 14]), (1, [-10, 0, 14])])
a.rot("arm_right", [(0, [-10, 0, -14]), (1, [-10, 0, -14])])
a.rot("body", [(0, [0, 0, 0.7]), (0.25, [0, 0, -0.7]), (0.5, [0, 0, 0.7]), (0.75, [0, 0, -0.7]), (1, [0, 0, 0.7])])
anims.append(a)

a = Anim("vent", 2.0, "hold_on_last_frame")  # 40 ticks = GodzillaTuning.VENT_TICKS
a.rot("torso", [(0, [-8, 0, 0]), (1.5, Z), (2, Z)])
a.rot("head", [(0, [-12, 0, 0]), (1.5, Z), (2, Z)])
a.rot("jaw", [(0, [45, 0, 0]), (1.2, Z), (2, Z)])
anims.append(a)

a = Anim("bite", 1.5, "hold_on_last_frame")  # 30 ticks, jaws snap at 0.7s = tick 14 (BITE_STRIKE_TICK)
a.rot("torso", [(0, Z), (0.6, [-9, 0, 0]), (0.7, [18, 0, 0]), (0.9, [18, 0, 0]), (1.5, Z)])
a.rot("head", [(0, Z), (0.6, [-14, 0, 0]), (0.7, [20, 0, 0]), (0.9, [20, 0, 0]), (1.5, Z)])
a.rot("jaw", [(0, Z), (0.55, [48, 0, 0]), (0.7, Z), (1.5, Z)])
a.pos("body", [(0, Z), (0.6, [0, 0, 4]), (0.7, [0, 0, -14]), (0.9, [0, 0, -14]), (1.5, Z)])
a.rot("arm_left", [(0, Z), (0.6, [-15, 0, 0]), (0.7, [20, 0, 0]), (1.5, Z)])
a.rot("arm_right", [(0, Z), (0.6, [-15, 0, 0]), (0.7, [20, 0, 0]), (1.5, Z)])
anims.append(a)

a = Anim("tail_swipe", 2.2, "hold_on_last_frame")  # 44 ticks, tail connects at 1.1s = tick 22 (TAIL_STRIKE_TICK)
a.rot("body", [(0, Z), (1.0, [0, -45, 0]), (1.1, [0, -45, 0]), (1.35, [0, 70, 0]), (1.6, [0, 70, 0]), (2.2, Z)])
a.rot("tail_1", [(0, Z), (1.0, [0, 35, 0]), (1.1, [0, 35, 0]), (1.35, [0, -55, 0]), (1.6, [0, -55, 0]), (2.2, Z)])
a.rot("tail_2", [(0, Z), (1.0, [0, 30, 0]), (1.1, [0, 30, 0]), (1.35, [0, -70, 0]), (1.6, [0, -70, 0]), (2.2, Z)])
a.rot("tail_3", [(0, Z), (1.0, [0, 40, 0]), (1.1, [0, 40, 0]), (1.35, [0, -90, 0]), (1.6, [0, -90, 0]), (2.2, Z)])
a.rot("torso", [(0, Z), (1.0, [3, 0, 0]), (2.2, Z)])
a.rot("head", [(0, Z), (1.0, [0, -20, 0]), (1.35, [0, 30, 0]), (2.2, Z)])
anims.append(a)

a = Anim("death", 5.0, "hold_on_last_frame")  # 100 ticks = GodzillaEntity.DEATH_TICKS
a.rot("root", [(0, Z), (1.5, [0, 0, -6]), (3.0, [0, 0, -92]), (3.3, [0, 0, -86]), (3.6, [0, 0, -90]), (5, [0, 0, -90])])
a.rot("head", [(0, Z), (1.0, [-30, 0, 0]), (3.0, [10, 0, 0]), (5, [10, 0, 0])])
a.rot("jaw", [(0, Z), (1, [40, 0, 0]), (5, [40, 0, 0])])
a.rot("arm_left", [(0, Z), (2, [-20, 0, 15]), (5, [-20, 0, 15])])
a.rot("arm_right", [(0, Z), (2, [-20, 0, -15]), (5, [-20, 0, -15])])
anims.append(a)

merged = {}
for an in anims:
    merged.update(an.out())
with open(f"{RES}/animations/godzilla_minus_one.animation.json", "w") as f:
    json.dump({"format_version": "1.8.0", "animations": merged}, f, indent=1)

print("placeholder assets written;", len(bones), "bones,", len(merged), "animations")
