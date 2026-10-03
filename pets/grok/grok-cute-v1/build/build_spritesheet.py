#!/usr/bin/env python3
"""Build a transparent Codex v2 sprite atlas for the original cosmic AI pet."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps, ImageDraw

CELL_W, CELL_H = 192, 208
COLS, ROWS = 8, 11
ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source.png"
THINKING = ROOT / "poses" / "thinking.png"
EUREKA = ROOT / "poses" / "eureka.png"
OUT = ROOT / "spritesheet.png"


def clean(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = list(rgba.getdata())
    rgba.putdata([(r, g, b, a) if a else (0, 0, 0, 0) for r, g, b, a in pixels])
    return rgba


def trimmed(path: Path) -> Image.Image:
    image = clean(Image.open(path))
    box = image.getchannel("A").getbbox()
    if box is None:
        raise ValueError(f"empty transparent source: {path}")
    return image.crop(box)


def make_sprite(path: Path = SOURCE) -> Image.Image:
    image = trimmed(path)
    image.thumbnail((174, 188), Image.Resampling.LANCZOS)
    return clean(image)


def transform(
    base: Image.Image,
    *,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    angle: float = 0.0,
    flip: bool = False,
    brightness: float = 1.0,
) -> Image.Image:
    image = ImageOps.mirror(base) if flip else base.copy()
    image = image.resize(
        (max(1, round(image.width * scale_x)), max(1, round(image.height * scale_y))),
        Image.Resampling.LANCZOS,
    )
    if angle:
        image = image.rotate(angle, Image.Resampling.BICUBIC, expand=True)
    if brightness != 1.0:
        image = ImageEnhance.Brightness(image).enhance(brightness)
    return clean(image)


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
    sprite = transform(
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
    return clean(cell)


def paste(atlas: Image.Image, row: int, col: int, image: Image.Image) -> None:
    atlas.alpha_composite(image, (col * CELL_W, row * CELL_H))


def direction_frame(base: Image.Image, degree: float) -> Image.Image:
    radians = math.radians(degree)
    sideways = abs(math.sin(radians))
    front = math.cos(radians)
    return frame(
        base,
        dx=round(math.sin(radians) * 7),
        dy=round(-front * 4),
        scale_x=1.0 - sideways * 0.17,
        scale_y=1.0 + sideways * 0.035,
        angle=math.sin(radians) * 6,
        flip=90 < degree < 270,
        brightness=0.90 if 90 < degree < 270 else 1.0,
    )


def contact_sheet(atlas: Image.Image, path: Path) -> None:
    scale = 0.5
    sheet = atlas.resize((round(atlas.width * scale), round(atlas.height * scale)), Image.Resampling.NEAREST)
    canvas = Image.new("RGB", sheet.size, (21, 27, 43))
    canvas.paste(sheet, mask=sheet.getchannel("A"))
    draw = ImageDraw.Draw(canvas)
    for col in range(COLS + 1):
        x = round(col * CELL_W * scale)
        draw.line((x, 0, x, canvas.height), fill=(56, 70, 94), width=1)
    for row in range(ROWS + 1):
        y = round(row * CELL_H * scale)
        draw.line((0, y, canvas.width, y), fill=(56, 70, 94), width=1)
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)


def previews(atlas: Image.Image) -> None:
    """Export the character and actual-runtime-size working sequence in one build."""
    source = trimmed(SOURCE)
    source.thumbnail((720, 720), Image.Resampling.LANCZOS)
    preview = Image.new("RGBA", (768, 768), (16, 23, 39, 255))
    preview.alpha_composite(source, ((768 - source.width) // 2, (768 - source.height) // 2))
    preview.convert("RGB").save(ROOT.parent / "preview.png")
    contact_sheet(atlas, ROOT.parent / "spritesheet-preview.png")

    qa = ROOT.parent / "qa"
    qa.mkdir(exist_ok=True)
    cells = []
    row = Image.new("RGB", (CELL_W * 6, CELL_H), (236, 240, 248))
    for col in range(6):
        cell = atlas.crop((col * CELL_W, 7 * CELL_H, (col + 1) * CELL_W, 8 * CELL_H))
        solid = Image.new("RGBA", (CELL_W, CELL_H), (236, 240, 248, 255))
        solid.alpha_composite(cell)
        cells.append(solid.convert("RGB"))
        row.paste(cells[-1], (col * CELL_W, 0))
    row.save(qa / "working-192.png")
    # Match Codex's running row durations to expose the actual playback cadence.
    cells[0].save(qa / "working-192.gif", save_all=True, append_images=cells[1:],
                  duration=[120, 120, 120, 120, 120, 220], loop=0)


def main() -> None:
    base = make_sprite()
    thinking = make_sprite(THINKING)
    eureka = make_sprite(EUREKA)
    atlas = Image.new("RGBA", (CELL_W * COLS, CELL_H * ROWS), (0, 0, 0, 0))

    idle = [
        dict(dy=0, scale_y=1.00),
        dict(dy=1, scale_y=0.985),
        dict(dy=2, scale_y=0.965),
        dict(dy=1, scale_y=0.985, brightness=0.97),
        dict(dy=0, scale_y=1.00),
        dict(dy=-1, scale_y=1.015),
    ]
    for col, opts in enumerate(idle):
        paste(atlas, 0, col, frame(base, **opts))
    paste(atlas, 0, 6, frame(base))

    running_right = [
        dict(dx=-4, dy=2, angle=5, scale_y=.96),
        dict(dx=-2, dy=0, angle=3, scale_y=.99),
        dict(dx=0, dy=-3, angle=0, scale_y=1.03),
        dict(dx=3, dy=-1, angle=-3, scale_y=1.01),
        dict(dx=5, dy=2, angle=-5, scale_y=.96),
        dict(dx=3, dy=0, angle=-2, scale_y=.99),
        dict(dx=0, dy=-3, angle=0, scale_y=1.03),
        dict(dx=-2, dy=-1, angle=3, scale_y=1.01),
    ]
    for col, opts in enumerate(running_right):
        paste(atlas, 1, col, frame(base, **opts))
        mirror = dict(opts, dx=-opts["dx"], angle=-opts["angle"], flip=True)
        paste(atlas, 2, col, frame(base, **mirror))

    waving = [
        dict(dx=0, dy=1, angle=0, scale_y=.99),
        dict(dx=2, dy=0, angle=-7, scale_y=1.01),
        dict(dx=3, dy=-1, angle=-12, scale_x=1.02, scale_y=1.02),
        dict(dx=1, dy=0, angle=-5, scale_y=1.00),
    ]
    for col, opts in enumerate(waving):
        paste(atlas, 3, col, frame(base, **opts))

    jumping = [
        dict(dy=5, scale_y=.94, scale_x=1.05),
        dict(dy=1, scale_y=.99, scale_x=1.01),
        dict(dy=-9, scale_y=1.00),
        dict(dy=-4, scale_y=1.03),
        dict(dy=3, scale_y=.96, scale_x=1.04),
    ]
    for col, opts in enumerate(jumping):
        paste(atlas, 4, col, frame(base, **opts))

    failed = [
        dict(dy=0, scale_y=1.00),
        dict(dy=2, scale_y=.97, brightness=.91),
        dict(dy=5, scale_y=.91, scale_x=1.03, brightness=.82),
        dict(dy=6, scale_y=.88, scale_x=1.06, brightness=.76),
        dict(dy=6, scale_y=.88, scale_x=1.06, brightness=.76),
        dict(dy=5, scale_y=.91, scale_x=1.03, brightness=.82),
        dict(dy=2, scale_y=.97, brightness=.91),
        dict(dy=0, scale_y=1.00),
    ]
    for col, opts in enumerate(failed):
        paste(atlas, 5, col, frame(base, **opts))

    waiting = [
        dict(dx=0, dy=0, angle=0),
        dict(dx=1, dy=-1, angle=-3),
        dict(dx=2, dy=-2, angle=-6),
        dict(dx=2, dy=-1, angle=-6, brightness=.96),
        dict(dx=1, dy=-1, angle=-3),
        dict(dx=0, dy=0),
    ]
    for col, opts in enumerate(waiting):
        paste(atlas, 6, col, frame(base, **opts))

    # Actual regenerated limb and expression poses, held for readable beats.
    # No rotation or translation substitute for a working gesture.
    working = [base, thinking, thinking, eureka, eureka, base]
    for col, sprite in enumerate(working):
        paste(atlas, 7, col, frame(sprite))

    review = [
        dict(dx=0, dy=0, angle=0),
        dict(dx=1, dy=0, angle=-3),
        dict(dx=2, dy=-1, angle=-6, scale_y=1.02),
        dict(dx=1, dy=0, angle=-3),
        dict(dx=0, dy=0, angle=0),
        dict(dx=-1, dy=0, angle=3),
    ]
    for col, opts in enumerate(review):
        paste(atlas, 8, col, frame(base, **opts))

    for index in range(16):
        degree = index * 22.5
        paste(atlas, 9 + index // 8, index % 8, direction_frame(base, degree))

    atlas = clean(atlas)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(OUT)
    # exact=True keeps RGB zeroed under transparent pixels in Pillow's WebP encoder.
    atlas.save(ROOT.parent / "spritesheet.webp", "WEBP", lossless=True, method=6, exact=True)
    previews(atlas)


if __name__ == "__main__":
    main()
