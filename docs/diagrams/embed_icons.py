"""Embed the PNG icons referenced by a diagrams-generated SVG as data URIs,
so the SVG renders anywhere (GitHub, browsers) without the local icon files."""

import base64
import re
from pathlib import Path


def embed_icons(svg_path: Path) -> None:
    svg = svg_path.read_text(encoding="utf-8")

    def to_data_uri(match: re.Match) -> str:
        attr, href = match.group(1), match.group(2)
        icon = Path(href)
        if not icon.is_file():
            return match.group(0)
        data = base64.b64encode(icon.read_bytes()).decode("ascii")
        return f'{attr}="data:image/png;base64,{data}"'

    svg = re.sub(r'((?:xlink:)?href)="([^"]+\.png)"', to_data_uri, svg)
    svg_path.write_text(svg, encoding="utf-8")
