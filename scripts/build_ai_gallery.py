#!/usr/bin/env python3
"""Render the three new pets from their installed-format atlases at native size."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CELL_W, CELL_H = 192, 208
PETS = (
    ("openai", "OpenAI", "Mint helper", "#EAF8F1", "#17735D"),
    ("claude", "Claude", "Coral scribe", "#FFF2E7", "#A35031"),
    ("grok", "Grok", "Cosmic mischief", "#EBF3FA", "#31576F"),
)
WORK_DURATIONS = [120, 120, 120, 120, 120, 220]


def render(atlases: list[Image.Image], row: int, column: int) -> Image.Image:
    canvas = Image.new("RGB", (696, 300), "#FAFAF8")
    draw = ImageDraw.Draw(canvas)
    title = ImageFont.load_default(size=22)
    subtitle = ImageFont.load_default(size=13)
    for index, (_, label, caption, background, ink) in enumerate(PETS):
        left = 12 + index * 228
        draw.rounded_rectangle((left, 12, left + 215, 287), radius=18, fill=background)
        draw.text((left + 108, 37), label, font=title, fill=ink, anchor="mm")
        draw.text((left + 108, 60), caption, font=subtitle, fill=ink, anchor="mm")
        sprite = atlases[index].crop(
            (column * CELL_W, row * CELL_H, (column + 1) * CELL_W, (row + 1) * CELL_H)
        )
        canvas.paste(sprite, (left + 12, 73), sprite)
    return canvas


def main() -> None:
    atlases = []
    for category, *_ in PETS:
        path = ROOT / "pets" / category / f"{category}-cute-v1" / "spritesheet.webp"
        with Image.open(path) as image:
            atlases.append(image.convert("RGBA"))
    output = ROOT / "assets"
    output.mkdir(exist_ok=True)
    render(atlases, 0, 6).save(output / "ai-companions.png")
    frames = [render(atlases, 7, column) for column in range(6)]
    # One shared palette keeps the card backgrounds stable between GIF frames.
    palette_strip = Image.new("RGB", (696, 300 * len(frames)))
    for index, frame in enumerate(frames):
        palette_strip.paste(frame, (0, index * 300))
    palette = palette_strip.quantize(colors=256)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    indexed[0].save(
        output / "ai-companions-working.gif",
        save_all=True,
        append_images=indexed[1:],
        duration=WORK_DURATIONS,
        loop=0,
        disposal=2,
        optimize=False,
    )


if __name__ == "__main__":
    main()
