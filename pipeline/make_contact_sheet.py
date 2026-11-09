from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


BACKGROUND = (17, 24, 32)
FOREGROUND = (225, 231, 237)
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def make_sheet(
    items: list[tuple[str, Path]],
    columns: int,
    output: Path,
    title: str,
) -> Path:
    if columns < 1 or not items:
        raise ValueError("A contact sheet requires items and at least one column")
    opened = [(label, Image.open(path).convert("RGB")) for label, path in items]
    cell_width = max(image.width for _, image in opened)
    cell_height = max(image.height for _, image in opened)
    font = ImageFont.truetype(FONT_PATH, 20)
    title_font = ImageFont.truetype(FONT_PATH, 26)
    pad = 12
    title_height = 52
    label_height = 34
    rows = (len(opened) + columns - 1) // columns
    sheet = Image.new(
        "RGB",
        (
            columns * cell_width + (columns + 1) * pad,
            title_height + rows * (cell_height + label_height) + (rows + 1) * pad,
        ),
        BACKGROUND,
    )
    draw = ImageDraw.Draw(sheet)
    draw.text((pad, 12), title, font=title_font, fill=FOREGROUND)
    for index, (label, source) in enumerate(opened):
        column = index % columns
        row = index // columns
        x = pad + column * (cell_width + pad)
        y = title_height + pad + row * (cell_height + label_height + pad)
        image_x = x + (cell_width - source.width) // 2
        image_y = y + (cell_height - source.height) // 2
        sheet.paste(source, (image_x, image_y))
        draw.text((x + 6, y + cell_height + 6), label.replace("_", " "), font=font, fill=FOREGROUND)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, optimize=True)
    return output
