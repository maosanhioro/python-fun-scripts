#!/usr/bin/env python3
"""
目的: ターミナル上できらきら豪華に光るクリスマスツリーを描画する
特徴:
- 24bit RGBカラー対応（対応してない端末でも大体それっぽく見える）
- オーナメントがランダムに点滅
- たまに雪/グリッターが舞う
実行: python3 main.py
"""

import random
import sys
import time
from math import sin

# ---------- ANSI helpers ----------
ESC = "\033["


def rgb(r, g, b, bg=False):
    # 24-bit color: 38;2;r;g;b (fg) / 48;2;... (bg)
    return f"{ESC}{48 if bg else 38};2;{r};{g};{b}m"


def reset():
    return f"{ESC}0m"


def clear():
    sys.stdout.write(f"{ESC}2J{ESC}H")


def hide_cursor():
    sys.stdout.write(f"{ESC}?25l")


def show_cursor():
    sys.stdout.write(f"{ESC}?25h")


def move_home():
    sys.stdout.write(f"{ESC}H")


# ---------- tree config ----------
TREE_HEIGHT = 24
BASE_WIDTH = TREE_HEIGHT * 2 - 1
TRUNK_HEIGHT = 4
TRUNK_WIDTH = 7

# 色パレット（豪華寄り）
GREEN_DARK = (0, 120, 0)
GREEN_LIGHT = (0, 200, 80)

GOLD = (255, 215, 0)
RED = (255, 70, 70)
BLUE = (80, 170, 255)
PINK = (255, 105, 180)
PURPLE = (180, 90, 255)
WHITE = (245, 245, 245)

ORNAMENTS = [GOLD, RED, BLUE, PINK, PURPLE, WHITE]

STAR_COLORS = [(255, 240, 120), (255, 220, 60), (255, 255, 180)]

# 表示位置
PADDING_TOP = 1
PADDING_LEFT = 4

# 点滅・演出
FPS = 18
SNOW_PROB = 0.12  # 1フレームごとの雪発生確率
GLITTER_PROB = 0.08  # 1フレームごとのグリッター発生確率
ORNAMENT_DENSITY = 0.14  # 葉(緑)のうちオーナメントにする割合


# ---------- model generation ----------
def build_tree_mask():
    """ツリーの形状マスク（葉の部分）を座標集合で返す"""
    coords = set()
    for row in range(TREE_HEIGHT):
        width = row * 2 + 1
        start_x = (BASE_WIDTH - width) // 2
        y = row
        for x in range(start_x, start_x + width):
            # 端のギザギザ感を少し作る
            if (
                row > 2
                and (x == start_x or x == start_x + width - 1)
                and random.random() < 0.35
            ):
                continue
            coords.add((x, y))
    return coords


def build_trunk_coords():
    coords = set()
    trunk_start_x = (BASE_WIDTH - TRUNK_WIDTH) // 2
    trunk_start_y = TREE_HEIGHT
    for y in range(trunk_start_y, trunk_start_y + TRUNK_HEIGHT):
        for x in range(trunk_start_x, trunk_start_x + TRUNK_WIDTH):
            coords.add((x, y))
    return coords


def pick_ornaments(tree_coords):
    """葉の一部をオーナメントとして固定配置（毎フレーム場所が変わると散らかるので固定）"""
    coords = list(tree_coords)
    random.shuffle(coords)
    n = int(len(coords) * ORNAMENT_DENSITY)
    selected = coords[:n]
    # 各座標に色を割当
    ornament_map = {}
    for c in selected:
        ornament_map[c] = random.choice(ORNAMENTS)
    return ornament_map


# ---------- rendering ----------
def lerp(a, b, t):
    return int(a + (b - a) * t)


def shade_green(y, t_phase):
    """縦方向＋時間で緑を微妙に揺らす（豪華に見える）"""
    base_t = y / max(1, TREE_HEIGHT - 1)
    wobble = (sin(t_phase + y * 0.35) + 1) / 2  # 0..1
    mix = 0.55 * base_t + 0.45 * wobble
    r = lerp(GREEN_DARK[0], GREEN_LIGHT[0], mix)
    g = lerp(GREEN_DARK[1], GREEN_LIGHT[1], mix)
    b = lerp(GREEN_DARK[2], GREEN_LIGHT[2], mix)
    return (r, g, b)


def draw_frame(
    tree_coords, trunk_coords, ornament_map, snow_particles, glitter_points, tick
):
    move_home()

    # 画面バッファ
    height = TREE_HEIGHT + TRUNK_HEIGHT + PADDING_TOP + 3
    width = BASE_WIDTH + PADDING_LEFT + 8

    # snow/glitter を更新しつつ描画に混ぜる
    # snow_particles: list of [x, y]
    # glitter_points: list of [x, y, life]

    # 雪を落とす
    for p in snow_particles:
        p[1] += 1
    snow_particles[:] = [
        p for p in snow_particles if p[1] < TREE_HEIGHT + TRUNK_HEIGHT + 2
    ]

    # グリッター寿命
    for g in glitter_points:
        g[2] -= 1
    glitter_points[:] = [g for g in glitter_points if g[2] > 0]

    # 文字描画用の辞書（後勝ち）
    cell = {}

    # 雪
    for x, y in snow_particles:
        cell[(x, y)] = (rgb(255, 255, 255), random.choice(["·", "*", "✦"]))

    # グリッター（キラキラ強め）
    for x, y, life in glitter_points:
        # lifeが短いほど明るく
        c = (255, 255, 255) if life <= 2 else (255, 240, 200)
        cell[(x, y)] = (rgb(*c), random.choice(["✧", "✦", "✨"]))

    # 星（点滅）
    star_x = BASE_WIDTH // 2
    star_y = -1
    star_color = STAR_COLORS[tick % len(STAR_COLORS)]
    cell[(star_x, star_y)] = (rgb(*star_color), "★")

    # ツリー本体
    t_phase = tick * 0.23
    for x, y in tree_coords:
        # 緑の色揺らぎ
        gr = shade_green(y, t_phase)

        # オーナメントなら点滅（同じ場所で輝度が変化）
        if (x, y) in ornament_map:
            base = ornament_map[(x, y)]
            blink = (sin(t_phase + x * 0.9 + y * 0.4) + 1) / 2  # 0..1
            # 明滅で少し白寄せして「光ってる感」
            rr = lerp(base[0], 255, int(blink * 0.65 * 100) / 100)
            gg = lerp(base[1], 255, int(blink * 0.65 * 100) / 100)
            bb = lerp(base[2], 255, int(blink * 0.65 * 100) / 100)
            char = random.choice(["●", "◆", "◉", "◍"])
            cell[(x, y)] = (rgb(rr, gg, bb), char)
        else:
            # たまにライトが瞬く
            if random.random() < 0.02:
                cell[(x, y)] = (rgb(220, 255, 220), "✳")
            else:
                cell[(x, y)] = (rgb(*gr), "▲")

    # 幹
    for x, y in trunk_coords:
        # 木目っぽく濃淡
        wobble = (sin(t_phase + x * 0.8) + 1) / 2
        base = (120, 75, 30)
        hi = (170, 120, 60)
        rr = lerp(base[0], hi[0], wobble)
        gg = lerp(base[1], hi[1], wobble)
        bb = lerp(base[2], hi[2], wobble)
        cell[(x, y)] = (rgb(rr, gg, bb), "█")

    # 土台（プレゼントっぽい帯）
    ground_y = TREE_HEIGHT + TRUNK_HEIGHT + 1
    for x in range(BASE_WIDTH):
        if x % 2 == 0:
            cell[(x, ground_y)] = (rgb(255, 60, 60), "▇")
        else:
            cell[(x, ground_y)] = (rgb(255, 215, 0), "▇")

    # 出力
    for row in range(-1, height - PADDING_TOP):
        line = [" "] * width
        color_line = [""] * width

        for col in range(BASE_WIDTH):
            key = (col, row)
            if key in cell:
                c, ch = cell[key]
                x_out = PADDING_LEFT + col
                if 0 <= x_out < width:
                    line[x_out] = ch
                    color_line[x_out] = c

        # 色を差し込みながら連結
        out = []
        current_color = ""
        for i, ch in enumerate(line):
            c = color_line[i]
            if c != current_color:
                out.append(c if c else reset())
                current_color = c
            out.append(ch)
        out.append(reset())
        sys.stdout.write("".join(out) + "\n")

    sys.stdout.flush()


def main():
    random.seed()  # 時刻ベース
    tree_coords = build_tree_mask()
    trunk_coords = build_trunk_coords()
    ornament_map = pick_ornaments(tree_coords)

    snow_particles = []
    glitter_points = []

    # 端末をチラつかせにくくする
    sys.stdout.write(f"{ESC}?1049h")  # alternate screen
    hide_cursor()
    clear()
    try:
        tick = 0
        while True:
            # 雪を発生
            if random.random() < SNOW_PROB:
                snow_particles.append([random.randrange(0, BASE_WIDTH), -1])

            # グリッターを発生（ツリー周辺に散布）
            if random.random() < GLITTER_PROB:
                gx = random.randrange(0, BASE_WIDTH)
                gy = random.randrange(-1, TREE_HEIGHT + 2)
                glitter_points.append([gx, gy, random.randint(2, 5)])

            draw_frame(
                tree_coords,
                trunk_coords,
                ornament_map,
                snow_particles,
                glitter_points,
                tick,
            )
            tick += 1
            time.sleep(1.0 / FPS)
    except KeyboardInterrupt:
        pass
    finally:
        show_cursor()
        sys.stdout.write(reset())
        sys.stdout.write(f"{ESC}?1049l")  # leave alternate screen
        sys.stdout.flush()


if __name__ == "__main__":
    main()
