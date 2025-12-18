import os
from pathlib import Path
import cairosvg

# Change this to your folder path
SVG_FOLDER = "out"

svg_folder = Path(SVG_FOLDER)

for svg_file in svg_folder.glob("*.svg"):
    # Remove spaces from filename (but keep extension logic clean)
    clean_name = svg_file.stem.replace(" ", "")
    pdf_file = svg_folder / f"{clean_name}.pdf"

    try:
        cairosvg.svg2pdf(
            url=str(svg_file),
            write_to=str(pdf_file)
        )
        print(f"Converted: {svg_file.name} -> {pdf_file.name}")
    except Exception as e:
        print(f"Failed to convert {svg_file.name}: {e}")
