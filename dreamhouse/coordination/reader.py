"""Purpose-led navigation and a vector print companion for the generated review."""

from __future__ import annotations

import html
from pathlib import PurePosixPath
from xml.etree import ElementTree as ET

from dreamhouse.svg.theme import colour

PAIRS = (
    ("Ground floor · PB", "drawings/architecture-ground-floor.svg", "plan-pb.svg"),
    ("Upper floor · P2", "drawings/architecture-upper-floor.svg", "plan-p2.svg"),
    ("Front", "drawings/architecture-front-elevation.svg", "elevation-front.svg"),
    ("Rear", "drawings/architecture-rear-elevation.svg", "elevation-rear.svg"),
    ("Side A", "drawings/architecture-side-a-elevation.svg", "elevation-side-a.svg"),
    ("Side B", "drawings/architecture-side-b-elevation.svg", "elevation-side-b.svg"),
)


def _sheets(files: dict[str, str]) -> list[tuple[str, str, str]]:
    result = []
    for name, content in sorted(files.items()):
        if not name.endswith(".svg"):
            continue
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name or "%" in name:
            raise ValueError(f"Unsafe reader sheet path: {name}")
        root = ET.fromstring(content)
        title = root.find("{http://www.w3.org/2000/svg}title")
        desc = root.find("{http://www.w3.org/2000/svg}desc")
        result.append(
            (
                name,
                "".join(title.itertext()) if title is not None else path.stem,
                "".join(desc.itertext()) if desc is not None else "",
            )
        )
    return result


def attach_reading_guide(page: str, files: dict[str, str]) -> str:
    """Expose paired representations without hiding findings or changing view membership."""
    rows = []
    for label, architecture, coordination in PAIRS:
        if architecture not in files or coordination not in files:
            continue
        rows.append(
            f'<tr><th scope="row">{html.escape(label)}</th>'
            f'<td><a href="{architecture}">Architecture</a></td>'
            f'<td><a href="#section-{coordination[:-4]}">Coordination</a></td></tr>'
        )
    panel = (
        '<section id="reading-guide" aria-labelledby="reading-guide-title">'
        '<h2 id="reading-guide-title">One source · two readings</h2>'
        "<p>Architecture explains spaces and known construction intent. Coordination "
        "shows source envelopes and linked evidence. Dashed space extents are not wall "
        "assemblies. Use the element index to follow the same ID through both.</p>"
        "<table><thead><tr><th>View</th><th>Spatial reading</th><th>Evidence reading</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
        '<p><a href="reading-guide.html">All sheets and text descriptions</a> · '
        '<a href="print.html">Vector print companion</a> · '
        '<a href="visual_quality.json">Graphic coverage and remaining review tasks</a></p>'
        "<p>Selection is blue; OPEN is amber; study is violet. A passed check is only "
        "the named check, never construction acceptance. Native drawings retain local "
        "material and wall-family keys.</p></section>"
    )
    style = f"""<style id="reading-guide-style">
#reading-guide {{ margin: 16px; padding: 20px; background: {colour("panel")}; border: 1px solid {colour("panel-rule")}; }}
#reading-guide table {{ border-collapse: collapse; width: 100%; max-width: 760px; }}
#reading-guide th, #reading-guide td {{ text-align: left; padding: 6px 12px; border-bottom: 1px solid {colour("panel-rule")}; }}
a:focus-visible, button:focus-visible, input:focus-visible, [tabindex]:focus-visible {{ outline: 3px solid #2454A6; outline-offset: 3px; }}
@media print {{ header, aside {{ position: static !important; max-height: none !important; }} .layout {{ display: block; }} aside, #reading-guide {{ display: none; }} .view {{ break-before: page; max-width: none; }} }}
</style>"""
    return page.replace("</head>", style + "</head>", 1).replace(
        "</header>", "</header>" + panel, 1
    )


def companion_pages(files: dict[str, str], snapshot: dict) -> dict[str, str]:
    """Return text descriptions and a fit-to-page (explicitly unscaled) print set."""
    sheets = _sheets(files)
    model = html.escape(snapshot["model_hash"])
    common = """body { font: 16px/1.5 "IBM Plex Sans", sans-serif; color: #172A32; background: #F4F0E7; margin: 24px; }
a { color: #1D7480; } a:focus-visible { outline: 3px solid #2454A6; outline-offset: 3px; }
article { padding: 20px; background: #FFFDFA; border: 1px solid #CBD0CC; margin-bottom: 20px; }
h1 { font-size: 1.8rem; } h2 { font-size: 1.15rem; } code { overflow-wrap: anywhere; }
img { display: block; max-width: 100%; height: auto; } .authority { font-weight: bold; }
@media print { body { background: white; margin: 0; } nav, .screen-only { display: none; } }"""
    header = (
        f'<nav><a href="index.html">Connected reader</a> · '
        '<a href="reading-guide.html">Text guide</a> · <a href="print.html">Print companion</a></nav>'
        '<p class="authority">REVIEW ONLY · NOT FOR CONSTRUCTION</p>'
        f'<p class="screen-only">Physical model <code>{model}</code></p>'
    )
    descriptions = []
    plates = []
    for number, (name, title, description) in enumerate(sheets, 1):
        name, title, description = map(html.escape, (name, title, description))
        family = (
            "Architectural / discipline consumer"
            if name.startswith("drawings/")
            else "Coordination projection"
        )
        caption = (
            f"<h2>{number:02d} · {title}</h2><p>{family}. {description}</p>"
            f'<p><a href="{name}">Open scalable sheet</a> · '
            '<a href="view_inventory.json">Dimensions, anchors and source identity</a></p>'
        )
        descriptions.append(f"<article>{caption}</article>")
        plates.append(
            f'<article class="plate"><h2>{number:02d} · {title}</h2>'
            f'<img src="{name}" alt="{title}">'
            '<p class="print-caption">NOT FOR CONSTRUCTION · Fit to page; no numerical print scale. '
            "Use labelled dimensions. Open the SVG for small annotations.</p></article>"
        )

    def document(title: str, body: str, extra_css: str = "") -> str:
        return (
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>{title}</title><style>{common}{extra_css}</style></head><body>"
            + header
            + f'<h1 class="screen-only">{title}</h1>'
            + body
            + "</body></html>"
        )

    guide = (
        "<p>These descriptions explain view purpose; the complete source values and "
        "findings remain available in the connected reader. No graphical editing is provided.</p>"
        + "".join(descriptions)
    )
    print_note = (
        '<p class="screen-only">A3 landscape review sheets, fitted without a scale claim. '
        "The vector images remain scalable. Browser print settings can suppress backgrounds; "
        "verify one sheet before printing the set. Long detail sheets need full-size digital "
        "review; this companion does not certify annotation legibility or construction plotting.</p>"
    )
    print_css = """@page { size: A3 landscape; margin: 10mm; }
@media print { body > .authority { display: none; } .plate { page-break-after: always; break-inside: avoid; border: 0; padding: 0; margin: 0; height: 270mm; display: flex; flex-direction: column; }
.plate:last-child { page-break-after: auto; } .plate h2 { font-size: 11pt; margin: 0 0 3mm; }
.plate img { flex: 1; min-height: 0; width: 100%; object-fit: contain; }
.print-caption { font-size: 9pt; margin: 3mm 0 0; } }"""
    return {
        "reading-guide.html": document("Drawing reading guide", guide),
        "print.html": document(
            "Vector review print companion", print_note + "".join(plates), print_css
        ),
    }
