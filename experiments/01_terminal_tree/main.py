"""
目的:
  rich を使って「きらきら豪華に光る」クリスマスツリーをターミナルに描画する。

実行:
  uv run python experiments/01_terminal_tree/main.py

終了:
  Ctrl+C
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from math import sin

from rich.console import Console
from rich.live import Live
from rich.text import Text

console = Console()


SKY_TOP = (6, 8, 12)
SKY_BOTTOM = (18, 22, 32)
GROUND_TOP = (28, 30, 36)
GROUND_BOTTOM = (10, 11, 16)
TREE_TONES = {
    "light": "#cfd2da",
    "mid": "#8e939f",
    "dark": "#5f646f",
}
ORNAMENT_TONES = ["#f5f5f5", "#d9d9d9", "#bfbfbf", "#9d9d9d"]
GARLAND_TONES = ["#ececec", "#9aa7b7"]
STAR_TONES = ("#f7f7f7", "#dcdcdc")


def lerp_rgb(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    """RGB補間の内部ユーティリティ。"""
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.strip().lstrip("#")
    if len(color) != 6:
        raise ValueError("invalid hex color")
    return (int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16))


def lerp_color(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> str:
    """RGB補間して #rrggbb を返す。"""
    return rgb_to_hex(lerp_rgb(a, b, t))


def animated_sky_color(y: int, x: int, rows: int, tick: int) -> str:
    """ゆっくり揺れる夜空の色。"""
    base_ratio = y / max(1, rows - 1)
    wave = sin((x / max(1, rows)) * 2.6 + tick * 0.02 + y * 0.07) * 0.05
    ratio = min(1.0, max(0.0, base_ratio + wave))
    return lerp_color(SKY_TOP, SKY_BOTTOM, ratio)


def ground_color(offset: int, rows: int) -> str:
    ratio = offset / max(1, rows - 1)
    return lerp_color(GROUND_TOP, GROUND_BOTTOM, ratio)


def extract_fg(style: str | None) -> str | None:
    if not style:
        return None
    tokens = style.split()
    idx = 0
    while idx < len(tokens):
        piece = tokens[idx]
        if piece == "on":
            idx += 2  # skip background color
            continue
        if piece.startswith("#") and len(piece) == 7:
            return piece
        idx += 1
    return None


def lighten_hex(color: str, amount: float) -> str:
    """color を白方向に少し寄せて柔らかい反射を作る。"""
    base = hex_to_rgb(color)
    white = (255, 255, 255)
    return rgb_to_hex(lerp_rgb(base, white, amount))


@dataclass(frozen=True)
class Config:
    height: int = 18
    fps: int = 14
    ornament_rate: float = 0.16  # 葉のうちオーナメントの割合
    twinkle_rate: float = 0.35  # オーナメントが光る確率（フレームごと）
    snow_rate: float = 0.05  # 遠景の雪
    snow_near_rate: float = 0.025  # 手前の雪
    glitter_rate: float = 0.04  # グリッターの出現確率（フレームごと）
    ground_height: int = 5
    reflection_fade: float = 0.55


CFG = Config()


def build_tree_coords(height: int) -> list[tuple[int, int]]:
    """ツリーの葉部分の座標 (x,y) を返す。幅は height*2-1 の座標系。"""
    w = height * 2 - 1
    coords: list[tuple[int, int]] = []
    for y in range(height):
        width = y * 2 + 1
        start = (w - width) // 2
        for x in range(start, start + width):
            # 少しだけギザギザ（豪華さ/自然さ）
            if y > 2 and (x == start or x == start + width - 1) and random.random() < 0.25:
                continue
            coords.append((x, y))
    return coords


def pick_ornaments(coords: list[tuple[int, int]], rate: float) -> set[tuple[int, int]]:
    """葉の中からオーナメント座標を固定で選ぶ。"""
    coords2 = coords[:]
    random.shuffle(coords2)
    n = max(1, int(len(coords2) * rate))
    return set(coords2[:n])


def render_frame(
    tick: int,
    height: int,
    leaf_coords: list[tuple[int, int]],
    ornaments: set[tuple[int, int]],
    snow_far: list[list[float]],
    snow_near: list[list[float]],
    glitter: list[list[int]],
) -> Text:
    """
    1フレーム分の描画結果を Text として返す。
    ここで「描画(見た目)」を組み立てる。
    """
    w = height * 2 - 1
    total_height = height + CFG.ground_height + 6
    ground_start = total_height - CFG.ground_height

    # 雪/グリッター更新
    for p in snow_far:
        p[0] = (p[0] + p[3]) % w
        p[1] += p[2]
    snow_far[:] = [p for p in snow_far if p[1] < ground_start]

    for p in snow_near:
        p[0] = (p[0] + p[3]) % w
        p[1] += p[2]
    snow_near[:] = [p for p in snow_near if p[1] < total_height]

    for g in glitter:
        g[2] -= 1
    glitter[:] = [g for g in glitter if g[2] > 0]

    # 画面セル（文字・スタイル）
    # 先に「空」を作って、後から上書きしていく
    ch: list[list[str]] = [[" " for _ in range(w)] for _ in range(total_height)]
    st: list[list[str | None]] = [[None for _ in range(w)] for _ in range(total_height)]
    ground_colors = [
        ground_color(i, CFG.ground_height) for i in range(CFG.ground_height)
    ]

    def background_color(y: int, x: int) -> str:
        if y < ground_start:
            return animated_sky_color(y, x, ground_start, tick)
        return ground_colors[y - ground_start]

    for y in range(total_height):
        for x in range(w):
            bg = background_color(y, x)
            st[y][x] = f"on {bg}"
            ch[y][x] = " "
            if y < ground_start:
                st[y][x] = f"on {bg}"
                noise = (x * 928371 + y * 689287 + tick * 19349663) % 137
                if noise < 2:
                    star_chars = ["·", "˚", "✶"]
                    star_colors = ["#d0d0d0", "#f5f5f5", "#a0a0a0"]
                    ch[y][x] = star_chars[noise % len(star_chars)]
                    st[y][x] = f"{star_colors[noise % len(star_colors)]} on {bg}"

    # 星（点滅）
    star_x, star_y = w // 2, 0
    star_style = f"bold {STAR_TONES[tick % len(STAR_TONES)]}"
    ch[star_y][star_x] = "★"
    star_bg = background_color(star_y, star_x)
    st[star_y][star_x] = f"{star_style} on {star_bg}"

    # ツリーの葉（yを1行下げて星の下に）
    for (x, y0) in leaf_coords:
        y = y0 + 1

        # 緑：上下で少し色味を変えて立体感
        # （richは16進カラー指定が簡単）
        if y0 < height * 0.35:
            leaf_style = TREE_TONES["light"]
        elif y0 < height * 0.7:
            leaf_style = TREE_TONES["mid"]
        else:
            leaf_style = TREE_TONES["dark"]

        # オーナメントは明滅＆色変化
        if (x, y0) in ornaments and random.random() < CFG.twinkle_rate:
            colors = ORNAMENT_TONES
            shapes = ["●", "◆", "◉", "◍"]
            c = random.choice(colors)
            s = random.choice(shapes)
            ch[y][x] = s
            bg = background_color(y, x)
            st[y][x] = f"bold {c} on {bg}"
        else:
            # たまにライトが瞬く
            if random.random() < 0.006:
                ch[y][x] = "✳"
                bg = background_color(y, x)
                st[y][x] = f"bold #f3f3f3 on {bg}"
            else:
                ch[y][x] = "▲"
                bg = background_color(y, x)
                st[y][x] = f"{leaf_style} on {bg}"

    # 幹
    trunk_h = max(3, height // 6)
    trunk_w = max(5, w // 7)
    tx0 = (w - trunk_w) // 2
    ty0 = height + 1
    for yy in range(ty0, ty0 + trunk_h):
        for xx in range(tx0, tx0 + trunk_w):
            ch[yy][xx] = "█"
            # 木目っぽい濃淡
            wood = "#7a7f86" if (xx + tick) % 3 else "#a3a8b0"
            bg = background_color(yy, xx)
            st[yy][xx] = f"{wood} on {bg}"

    # 土台（プレゼント帯っぽく）
    gy = ty0 + trunk_h + 1
    if gy < len(ch):
        for xx in range(w):
            ch[gy][xx] = "▇"
            band = "#8d8d8d" if xx % 2 == 0 else "#cfcfcf"
            bg = background_color(gy, xx)
            st[gy][xx] = f"{band} on {bg}"

    # ガーランド（波打つリボン）
    garland_colors = GARLAND_TONES
    for idx, phase_offset in enumerate((0.0, 1.2)):
        color = garland_colors[idx % len(garland_colors)]
        amplitude = max(2, w // 5)
        for y0 in range(height):
            y = y0 + 1
            wave = sin((y0 / height) * 3.2 + tick * 0.15 + phase_offset)
            x = int(w // 2 + wave * amplitude)
            x = max(1, min(w - 2, x))
            if ch[y][x] != " ":
                char = "╱" if wave > 0 else "╲"
                ch[y][x] = char
                bg = background_color(y, x)
                st[y][x] = f"bold {color} on {bg}"

    # 地面の反射
    for offset in range(CFG.ground_height):
        src_y = ground_start - 1 - offset
        dst_y = ground_start + offset
        if src_y < 0 or dst_y >= total_height:
            continue
        fade = max(0.0, 1.0 - offset / max(1, CFG.ground_height))
        for x in range(w):
            src_char = ch[src_y][x]
            if not src_char.strip():
                continue
            fg = extract_fg(st[src_y][x]) or "#8a8a8a"
            tint = lighten_hex(fg, CFG.reflection_fade * fade + 0.2)
            bg = ground_colors[dst_y - ground_start]
            ch[dst_y][x] = random.choice(["▁", "▂", "▃"])
            st[dst_y][x] = f"{tint} on {bg}"

    # 雪面テクスチャ
    for y in range(ground_start, total_height):
        for x in range(w):
            if ch[y][x].strip():
                continue
            bg = ground_colors[y - ground_start]
            if (x + y + tick) % 9 == 0:
                ch[y][x] = random.choice(["░", "▒"])
                st[y][x] = f"#dcdfe5 on {bg}"

    # 雪（遠景・近景）
    snow_layers = (
        (snow_far, ["·", "•", "˙"], ground_start),
        (snow_near, ["✻", "✦"], total_height),
    )
    for layer, palette, limit in snow_layers:
        for px, py, _, _ in layer:
            ix = int(px) % w
            iy = int(py)
            if 0 <= iy < limit:
                ch[iy][ix] = random.choice(palette)
                bg = background_color(iy, ix)
                st[iy][ix] = f"#f6fbff on {bg}"

    # グリッター（上書き）
    for gx, gy2, life in glitter:
        if 0 <= gy2 < len(ch) and 0 <= gx < w:
            ch[gy2][gx] = random.choice(["✧", "✦"])
            glow = "bold #f0f0f0" if life > 1 else "bold #dcdcdc"
            bg = background_color(gy2, gx)
            st[gy2][gx] = f"{glow} on {bg}"

    # Text組み立て
    t = Text()
    for y in range(len(ch)):
        for x in range(w):
            style = st[y][x]
            if style:
                t.append(ch[y][x], style=style)
            else:
                t.append(ch[y][x])
        t.append("\n")

    t.append(f"fps={CFG.fps}  Ctrl+C to quit", style="dim")
    return t


def main() -> None:
    leaf_coords = build_tree_coords(CFG.height)
    ornaments = pick_ornaments(leaf_coords, CFG.ornament_rate)

    snow_far: list[list[float]] = []  # [x, y, speed, drift]
    snow_near: list[list[float]] = []  # [x, y, speed, drift]
    glitter: list[list[int]] = []  # [x, y, life]

    tick = 0
    w = CFG.height * 2 - 1

    with Live(console=console, refresh_per_second=CFG.fps, screen=True) as live:
        try:
            while True:
                # 雪発生
                if random.random() < CFG.snow_rate:
                    snow_far.append(
                        [
                            random.uniform(0, w),
                            0.0,
                            random.uniform(0.04, 0.12),
                            random.uniform(-0.03, 0.03),
                        ]
                    )
                if random.random() < CFG.snow_near_rate:
                    snow_near.append(
                        [
                            random.uniform(0, w),
                            -2.0,
                            random.uniform(0.18, 0.45),
                            random.uniform(-0.1, 0.1),
                        ]
                    )

                # グリッター発生（ツリー周辺）
                if random.random() < CFG.glitter_rate and len(glitter) < CFG.height:
                    gx = random.randrange(0, w)
                    gy = random.randrange(0, CFG.height + 3)
                    glitter.append([gx, gy, random.randint(2, 5)])

                frame = render_frame(
                    tick=tick,
                    height=CFG.height,
                    leaf_coords=leaf_coords,
                    ornaments=ornaments,
                    snow_far=snow_far,
                    snow_near=snow_near,
                    glitter=glitter,
                )
                live.update(frame)

                tick += 1
                time.sleep(1.0 / CFG.fps)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
