#!/usr/bin/env python3
"""Build a transparent Codex v2 sprite atlas from the Coral Scribe art."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageOps

CELL_W, CELL_H = 192, 208
COLS, ROWS = 8, 11
ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source.png"
POSES = ROOT / "poses"
WRITING = POSES / "writing.png"
EUREKA = POSES / "eureka.png"
OUT = ROOT / "spritesheet.png"
PACKAGE = ROOT.parent
QA = PACKAGE / "qa"
ROW_NAMES = ["idle", "running-right", "running-left", "waving", "jumping",
             "failed", "waiting", "running", "review", "look 000-157.5", "look 180-337.5"]
USED_COUNTS = [7, 8, 8, 4, 5, 8, 6, 6, 6, 8, 8]


def trim(image: Image.Image) -> Image.Image:
    alpha = image.getchannel("A")
    # Ignore almost invisible generation fringes when matching pose sizes.
    bbox = alpha.point(lambda value: 255 if value > 16 else 0).getbbox()
    if bbox is None:
        raise ValueError("source sprite is fully transparent")
    return image.crop(bbox)


def clean_transparent_rgb(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = list(rgba.getdata())
    rgba.putdata([(r, g, b, a) if a else (0, 0, 0, 0) for r, g, b, a in pixels])
    return rgba


def make_sprite(path: Path) -> Image.Image:
    source = trim(Image.open(path).convert("RGBA"))
    source.thumbnail((166, 166), Image.Resampling.LANCZOS)
    return clean_transparent_rgb(source)


def make_base() -> Image.Image:
    return make_sprite(SOURCE)


def transform_sprite(
    base: Image.Image,
    *,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    angle: float = 0.0,
    flip: bool = False,
    brightness: float = 1.0,
) -> Image.Image:
    image = ImageOps.mirror(base) if flip else base.copy()
    width = max(1, round(image.width * scale_x))
    height = max(1, round(image.height * scale_y))
    image = image.resize((width, height), Image.Resampling.LANCZOS)
    if angle:
        image = image.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    if brightness != 1.0:
        image = ImageEnhance.Brightness(image).enhance(brightness)
    return clean_transparent_rgb(image)


def frame(
    base: Image.Image,
    *,
    dx: int = 0,
    dy: int = 0,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    angle: float = 0.0,
    flip: bool = False,
    brightness: float = 1.0,
) -> Image.Image:
    sprite = transform_sprite(
        base,
        scale_x=scale_x,
        scale_y=scale_y,
        angle=angle,
        flip=flip,
        brightness=brightness,
    )
    cell = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    x = (CELL_W - sprite.width) // 2 + dx
    y = (CELL_H - sprite.height) // 2 + dy
    cell.alpha_composite(sprite, (x, y))
    return clean_transparent_rgb(cell)


def direction_frame(base: Image.Image, degree: float) -> Image.Image:
    # Horizontal squash indicates sideways attention while preserving character identity.
    radians = math.radians(degree)
    sideways = abs(math.sin(radians))
    vertical = math.cos(radians)
    scale_x = 1.0 - sideways * 0.20
    scale_y = 1.0 + sideways * 0.05
    dx = round(math.sin(radians) * 8)
    dy = round(-vertical * 5)
    angle = math.sin(radians) * 7
    brightness = 0.88 if 90 < degree < 270 else 1.0
    return frame(
        base,
        dx=dx,
        dy=dy,
        scale_x=scale_x,
        scale_y=scale_y,
        angle=angle,
        flip=90 < degree < 270,
        brightness=brightness,
    )


def paste(atlas: Image.Image, row: int, col: int, cell: Image.Image) -> None:
    atlas.alpha_composite(cell, (col * CELL_W, row * CELL_H))


def checker(size: tuple[int, int]) -> Image.Image:
    image = Image.new("RGB", size, "#ffffff")
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], 12):
        for x in range(0, size[0], 12):
            if (x // 12 + y // 12) % 2:
                draw.rectangle((x, y, x + 11, y + 11), fill="#ece9e5")
    return image


def save_previews(atlas: Image.Image) -> None:
    QA.mkdir(parents=True, exist_ok=True)
    preview = clean_transparent_rgb(Image.open(SOURCE).convert("RGBA"))
    preview.save(PACKAGE / "preview.png")
    atlas.crop((0, 0, CELL_W, CELL_H)).save(QA / "readability-192.png")

    cell_w, cell_h, label_h = CELL_W // 2, CELL_H // 2, 22
    sheet = Image.new("RGB", (COLS * cell_w, ROWS * (cell_h + label_h)), "#f7f7f7")
    draw = ImageDraw.Draw(sheet)
    for row, name in enumerate(ROW_NAMES):
        y = row * (cell_h + label_h)
        draw.rectangle((0, y, sheet.width, y + label_h - 1), fill="#202020")
        draw.text((6, y + 5), f"row {row}: {name}", fill="white")
        for col in range(COLS):
            cell = atlas.crop((col * CELL_W, row * CELL_H,
                               (col + 1) * CELL_W, (row + 1) * CELL_H))
            cell = cell.resize((cell_w, cell_h), Image.Resampling.LANCZOS)
            tile = checker((cell_w, cell_h))
            tile.paste(cell, (0, 0), cell)
            x = col * cell_w
            sheet.paste(tile, (x, y + label_h))
            color = "#18a058" if col < USED_COUNTS[row] else "#cc3344"
            draw.rectangle((x, y + label_h, x + cell_w - 1, y + label_h + cell_h - 1), outline=color)
            draw.text((x + 3, y + label_h + 3), str(col), fill="#333333")
    sheet.save(QA / "contact-sheet.png")
    sheet.save(PACKAGE / "spritesheet-preview.png")

    work = atlas.crop((0, 7 * CELL_H, 6 * CELL_W, 8 * CELL_H))
    work.save(QA / "work-row-192.png")
    frames = []
    for col in range(6):
        sprite = work.crop((col * CELL_W, 0, (col + 1) * CELL_W, CELL_H))
        canvas = checker((CELL_W, CELL_H))
        canvas.paste(sprite, (0, 0), sprite)
        frames.append(canvas)
    frames[0].save(QA / "work-row-192.gif", save_all=True, append_images=frames[1:],
                   duration=[120, 120, 120, 120, 120, 220], loop=0, disposal=2)


def main() -> None:
    base = make_base()
    writing = make_sprite(WRITING)
    eureka = make_sprite(EUREKA)
    atlas = Image.new("RGBA", (CELL_W * COLS, CELL_H * ROWS), (0, 0, 0, 0))

    idle = [
        dict(dy=0, scale_y=1.00),
        dict(dy=1, scale_y=0.98),
        dict(dy=2, scale_y=0.96),
        dict(dy=1, scale_y=0.98),
        dict(dy=0, scale_y=1.00),
        dict(dy=-1, scale_y=1.02),
    ]
    for col, options in enumerate(idle):
        paste(atlas, 0, col, frame(base, **options))
    # Codex v2 reserves idle row column 6 as the neutral look fallback.
    paste(atlas, 0, 6, frame(base))

    right_run = [
        dict(dx=-4, dy=2, angle=4, scale_y=.95),
        dict(dx=-2, dy=0, angle=2, scale_y=.98),
        dict(dx=0, dy=-3, angle=0, scale_y=1.03),
        dict(dx=3, dy=-1, angle=-3, scale_y=1.01),
        dict(dx=5, dy=2, angle=-5, scale_y=.95),
        dict(dx=3, dy=0, angle=-2, scale_y=.98),
        dict(dx=0, dy=-3, angle=0, scale_y=1.03),
        dict(dx=-2, dy=-1, angle=3, scale_y=1.01),
    ]
    for col, options in enumerate(right_run):
        paste(atlas, 1, col, frame(base, **options))
        mirror = dict(options)
        mirror["dx"] = -mirror["dx"]
        mirror["angle"] = -mirror["angle"]
        mirror["flip"] = True
        paste(atlas, 2, col, frame(base, **mirror))

    wave = [
        dict(dx=0, dy=0, angle=0),
        dict(dx=2, dy=-1, angle=-8),
        dict(dx=4, dy=-2, angle=-13),
        dict(dx=1, dy=0, angle=-5),
    ]
    for col, options in enumerate(wave):
        paste(atlas, 3, col, frame(eureka if col in (1, 2) else base, **options))

    jump = [
        dict(dy=4, scale_y=.94, scale_x=1.06),
        dict(dy=0, scale_y=1.00),
        dict(dy=-9, scale_y=.99),
        dict(dy=-3, scale_y=1.02),
        dict(dy=3, scale_y=.95, scale_x=1.05),
    ]
    for col, options in enumerate(jump):
        paste(atlas, 4, col, frame(base, **options))

    failed = [
        dict(dy=0, scale_y=1.00),
        dict(dy=2, scale_y=.96, brightness=.90),
        dict(dy=4, scale_y=.90, scale_x=1.04, brightness=.80),
        dict(dy=5, scale_y=.87, scale_x=1.06, brightness=.76),
        dict(dy=5, scale_y=.87, scale_x=1.06, brightness=.76),
        dict(dy=4, scale_y=.90, scale_x=1.04, brightness=.80),
        dict(dy=2, scale_y=.96, brightness=.90),
        dict(dy=0, scale_y=1.00),
    ]
    for col, options in enumerate(failed):
        paste(atlas, 5, col, frame(base, **options))

    waiting = [
        dict(dx=0, dy=0),
        dict(dx=1, dy=-1, angle=-3),
        dict(dx=2, dy=-2, angle=-6),
        dict(dx=2, dy=-2, angle=-6),
        dict(dx=1, dy=-1, angle=-3),
        dict(dx=0, dy=0),
    ]
    for col, options in enumerate(waiting):
        paste(atlas, 6, col, frame(base, **options))

    # Work is a readable loop: pause, write, review the page, then find an idea.
    working = [
        (base, dict(dy=2)),
        (base, dict(dx=-2, dy=7, angle=-4)),
        (writing, dict(dx=0, dy=5)),
        (writing, dict(dx=2, dy=6, angle=2)),
        (eureka, dict(dx=0, dy=8)),
        (base, dict(dy=2)),
    ]
    for col, (sprite, options) in enumerate(working):
        paste(atlas, 7, col, frame(sprite, **options))

    review = [
        dict(dx=0, dy=0),
        dict(dx=1, dy=0, angle=-2),
        dict(dx=2, dy=-1, angle=-5),
        dict(dx=1, dy=0, angle=-2),
        dict(dx=0, dy=0),
        dict(dx=-1, dy=0, angle=2),
    ]
    for col, options in enumerate(review):
        paste(atlas, 8, col, frame(writing, **options))

    for index in range(16):
        degree = index * 22.5
        paste(atlas, 9 + index // 8, index % 8, direction_frame(base, degree))

    atlas = clean_transparent_rgb(atlas)
    atlas.save(OUT)
    # exact=True preserves zero RGB values beneath fully transparent pixels.
    atlas.save(PACKAGE / "spritesheet.webp", "WEBP", lossless=True, exact=True, method=6)
    save_previews(atlas)


if __name__ == "__main__":
    main()
