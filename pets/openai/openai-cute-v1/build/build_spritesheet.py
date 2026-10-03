#!/usr/bin/env python3
"""Build the Codex v2 atlas for the original mint AI helper mascot."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageOps

CELL_W, CELL_H = 192, 208
COLS, ROWS = 8, 11
ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT.parent
SOURCE = ROOT / "source.png"
THINKING = ROOT / "poses" / "thinking.png"
EUREKA = ROOT / "poses" / "eureka.png"
OUT = ROOT / "spritesheet.png"


def clean_transparent_rgb(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    rgba.putdata([(r, g, b, a) if a else (0, 0, 0, 0) for r, g, b, a in rgba.getdata()])
    return rgba


def trim(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    bbox = rgba.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("source sprite is fully transparent")
    return rgba.crop(bbox)


def make_sprite(path: Path = SOURCE) -> Image.Image:
    sprite = trim(Image.open(path))
    sprite.thumbnail((166, 166), Image.Resampling.LANCZOS)
    return clean_transparent_rgb(sprite)


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
    image = image.resize(
        (max(1, round(image.width * scale_x)), max(1, round(image.height * scale_y))),
        Image.Resampling.LANCZOS,
    )
    if angle:
        image = image.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    if brightness != 1.0:
        image = ImageEnhance.Brightness(image).enhance(brightness)
    return clean_transparent_rgb(image)


def draw_star(draw: ImageDraw.ImageDraw, cx: int, cy: int, radius: int) -> None:
    points = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        r = radius if i % 2 == 0 else radius * 0.38
        points.append((cx + round(math.cos(angle) * r), cy + round(math.sin(angle) * r)))
    draw.polygon(points, fill=(137, 244, 185, 255), outline=(18, 86, 78, 255))


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
    thought_bubbles: bool = False,
    eureka: bool = False,
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
    draw = ImageDraw.Draw(cell)
    if thought_bubbles:
        for center_x, center_y, radius in ((53, 36, 3), (63, 27, 5), (79, 16, 9)):
            draw.ellipse(
                (center_x - radius, center_y - radius, center_x + radius, center_y + radius),
                fill=(231, 255, 242, 255), outline=(18, 86, 78, 255), width=2,
            )
    if eureka:
        draw_star(draw, 144, 31, 13)
        draw.line((144, 10, 144, 2), fill=(18, 86, 78, 255), width=2)
        draw.line((157, 18, 164, 13), fill=(18, 86, 78, 255), width=2)
        draw.line((131, 18, 124, 13), fill=(18, 86, 78, 255), width=2)
    return clean_transparent_rgb(cell)


def direction_frame(base: Image.Image, degree: float) -> Image.Image:
    radians = math.radians(degree)
    sideways = abs(math.sin(radians))
    vertical = math.cos(radians)
    return frame(
        base,
        dx=round(math.sin(radians) * 8),
        dy=round(-vertical * 5),
        scale_x=1.0 - sideways * 0.20,
        scale_y=1.0 + sideways * 0.05,
        angle=math.sin(radians) * 7,
        flip=90 < degree < 270,
        brightness=0.90 if 90 < degree < 270 else 1.0,
    )


def paste(atlas: Image.Image, row: int, col: int, cell: Image.Image) -> None:
    atlas.alpha_composite(cell, (col * CELL_W, row * CELL_H))


def main() -> None:
    base = make_sprite()
    thinking = make_sprite(THINKING)
    eureka = make_sprite(EUREKA)
    atlas = Image.new("RGBA", (CELL_W * COLS, CELL_H * ROWS), (0, 0, 0, 0))

    idle = [
        dict(dy=0), dict(dy=1, scale_y=.98), dict(dy=2, scale_y=.96),
        dict(dy=1, scale_y=.98), dict(dy=0), dict(dy=-1, scale_y=1.02),
    ]
    for col, options in enumerate(idle):
        paste(atlas, 0, col, frame(base, **options))
    paste(atlas, 0, 6, frame(base))

    run = [dict(dx=-4, dy=2, angle=4, scale_y=.95), dict(dx=-2, angle=2), dict(dy=-3, scale_y=1.03), dict(dx=3, angle=-3), dict(dx=5, dy=2, angle=-5, scale_y=.95), dict(dx=3, angle=-2), dict(dy=-3, scale_y=1.03), dict(dx=-2, angle=3)]
    for col, options in enumerate(run):
        paste(atlas, 1, col, frame(base, **options))
        mirror = dict(options, dx=-options.get("dx", 0), angle=-options.get("angle", 0), flip=True)
        paste(atlas, 2, col, frame(base, **mirror))

    wave = [(base, dict()), (eureka, dict(dy=-1)), (eureka, dict(dy=-2, angle=-3)), (base, dict())]
    for col, (pose, options) in enumerate(wave):
        paste(atlas, 3, col, frame(pose, **options))

    jump = [dict(dy=4, scale_y=.94, scale_x=1.06), dict(), dict(dy=-9, scale_y=.99), dict(dy=-3, scale_y=1.02), dict(dy=3, scale_y=.95, scale_x=1.05)]
    for col, options in enumerate(jump):
        paste(atlas, 4, col, frame(base, **options))

    failed = [dict(), dict(dy=2, scale_y=.96, brightness=.90), dict(dy=4, scale_y=.90, brightness=.80), dict(dy=5, scale_y=.87, brightness=.76), dict(dy=5, scale_y=.87, brightness=.76), dict(dy=4, scale_y=.90, brightness=.80), dict(dy=2, scale_y=.96, brightness=.90), dict()]
    for col, options in enumerate(failed):
        paste(atlas, 5, col, frame(base, **options))

    waiting = [dict(), dict(dx=1, dy=-1, angle=-3), dict(dx=2, dy=-2, angle=-6), dict(dx=2, dy=-2, angle=-6), dict(dx=1, dy=-1, angle=-3), dict()]
    for col, options in enumerate(waiting):
        paste(atlas, 6, col, frame(base, **options))

    # Independent pose artwork makes the arm, face and feet change during work.
    working = [
        (base, dict(dy=2)),
        (thinking, dict(dy=2)),
        (thinking, dict(dy=2, thought_bubbles=True)),
        (eureka, dict(dy=2)),
        (eureka, dict(dy=0, eureka=True)),
        (base, dict(dy=2)),
    ]
    for col, (pose, options) in enumerate(working):
        paste(atlas, 7, col, frame(pose, **options))

    review = [(base, dict()), (thinking, dict()), (thinking, dict(dy=-1)), (thinking, dict()), (base, dict()), (base, dict(dy=-1))]
    for col, (pose, options) in enumerate(review):
        paste(atlas, 8, col, frame(pose, **options))

    for index in range(16):
        degree = index * 22.5
        paste(atlas, 9 + index // 8, index % 8, direction_frame(base, degree))

    atlas = clean_transparent_rgb(atlas)
    atlas.save(OUT)
    # ``exact`` keeps RGB at zero for transparent pixels in the WebP encoder.
    atlas.save(PACKAGE / "spritesheet.webp", format="WEBP", lossless=True, exact=True, method=6)

    source = trim(Image.open(SOURCE))
    source.thumbnail((330, 330), Image.Resampling.LANCZOS)
    preview = Image.new("RGBA", (420, 420), (0, 0, 0, 0))
    preview.alpha_composite(source, ((420 - source.width) // 2, (420 - source.height) // 2))
    clean_transparent_rgb(preview).save(PACKAGE / "preview.png")

    scaled = atlas.resize((atlas.width // 2, atlas.height // 2), Image.Resampling.LANCZOS)
    background = Image.new("RGB", scaled.size, (245, 250, 248))
    draw = ImageDraw.Draw(background)
    for y in range(0, background.height, 24):
        for x in range(0, background.width, 24):
            if (x // 24 + y // 24) % 2:
                draw.rectangle((x, y, x + 23, y + 23), fill=(229, 240, 235))
    background.paste(scaled, mask=scaled.getchannel("A"))
    background.save(PACKAGE / "spritesheet-preview.png")
    qa = PACKAGE / "qa"
    qa.mkdir(exist_ok=True)
    background.save(qa / "contact-sheet.png")
    work_row = atlas.crop((0, 7 * CELL_H, 6 * CELL_W, 8 * CELL_H))
    work_row.save(qa / "work-row-192.png")
    atlas.crop((0, 0, CELL_W, CELL_H)).save(qa / "preview-192.png")


if __name__ == "__main__":
    main()
