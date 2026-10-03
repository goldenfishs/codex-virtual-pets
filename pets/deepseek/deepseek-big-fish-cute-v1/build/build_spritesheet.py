#!/usr/bin/env python3
"""Build a transparent Codex v2 sprite atlas from the approved master mascot."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps

CELL_W, CELL_H = 192, 208
COLS, ROWS = 8, 11
ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source.png"
OUT = ROOT / "spritesheet.png"


def trim(image: Image.Image) -> Image.Image:
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError("source sprite is fully transparent")
    return image.crop(bbox)


def clean_transparent_rgb(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = list(rgba.getdata())
    rgba.putdata([(r, g, b, a) if a else (0, 0, 0, 0) for r, g, b, a in pixels])
    return rgba


def make_base() -> Image.Image:
    source = trim(Image.open(SOURCE).convert("RGBA"))
    source.thumbnail((166, 166), Image.Resampling.LANCZOS)
    return clean_transparent_rgb(source)


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
    blink: bool = False,
    sleepy: bool = False,
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
    if blink or sleepy:
        eye_y = y + round(sprite.height * 0.38)
        eye_gap = round(sprite.width * 0.20)
        eye_w = max(10, round(sprite.width * 0.14))
        eye_h = 4 if blink else 7
        for center_x in (CELL_W // 2 - eye_gap, CELL_W // 2 + eye_gap):
            Image.Image.alpha_composite(
                cell,
                Image.new("RGBA", (eye_w, eye_h), (10, 24, 66, 230)),
                (center_x - eye_w // 2, eye_y),
            )
    return clean_transparent_rgb(cell)


def direction_frame(base: Image.Image, degree: float) -> Image.Image:
    # Horizontal squash indicates sideways attention while preserving the mascot identity.
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


def main() -> None:
    base = make_base()
    atlas = Image.new("RGBA", (CELL_W * COLS, CELL_H * ROWS), (0, 0, 0, 0))

    idle = [
        dict(dy=0, scale_y=1.00),
        dict(dy=1, scale_y=0.98),
        dict(dy=2, scale_y=0.96, blink=True),
        dict(dy=1, scale_y=0.98, blink=True),
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
        paste(atlas, 3, col, frame(base, **options))

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
        dict(dy=4, scale_y=.90, scale_x=1.04, brightness=.80, sleepy=True),
        dict(dy=5, scale_y=.87, scale_x=1.06, brightness=.76, sleepy=True),
        dict(dy=5, scale_y=.87, scale_x=1.06, brightness=.76, sleepy=True),
        dict(dy=4, scale_y=.90, scale_x=1.04, brightness=.80, sleepy=True),
        dict(dy=2, scale_y=.96, brightness=.90),
        dict(dy=0, scale_y=1.00),
    ]
    for col, options in enumerate(failed):
        paste(atlas, 5, col, frame(base, **options))

    waiting = [
        dict(dx=0, dy=0),
        dict(dx=1, dy=-1, angle=-3),
        dict(dx=2, dy=-2, angle=-6),
        dict(dx=2, dy=-2, angle=-6, blink=True),
        dict(dx=1, dy=-1, angle=-3),
        dict(dx=0, dy=0),
    ]
    for col, options in enumerate(waiting):
        paste(atlas, 6, col, frame(base, **options))

    working = [
        dict(dy=1, angle=2, scale_y=.98),
        dict(dy=0, angle=-2, scale_y=1.00),
        dict(dy=1, angle=2, scale_y=.98),
        dict(dy=0, angle=-2, scale_y=1.00),
        dict(dy=1, angle=2, scale_y=.98),
        dict(dy=0, angle=-2, scale_y=1.00),
    ]
    for col, options in enumerate(working):
        paste(atlas, 7, col, frame(base, **options))

    review = [
        dict(dx=0, dy=0),
        dict(dx=1, dy=0, angle=-2),
        dict(dx=2, dy=-1, angle=-5, blink=True),
        dict(dx=1, dy=0, angle=-2),
        dict(dx=0, dy=0),
        dict(dx=-1, dy=0, angle=2),
    ]
    for col, options in enumerate(review):
        paste(atlas, 8, col, frame(base, **options))

    for index in range(16):
        degree = index * 22.5
        paste(atlas, 9 + index // 8, index % 8, direction_frame(base, degree))

    clean_transparent_rgb(atlas).save(OUT)


if __name__ == "__main__":
    main()
