"""Bounded graphic checks and explicit outstanding visual-review coverage."""

from __future__ import annotations

import hashlib
import math
import re
from html.parser import HTMLParser
from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

from dreamhouse.coordination.model import CoordinationError
from dreamhouse.svg.style import has_svg_css_variables

SVG = "{http://www.w3.org/2000/svg}"


def _authority_text(root: ET.Element) -> str:
    """Inspect text content excluding explicitly hidden or definition-only subtrees.

    This is not CSS cascade, clipping, viewport or rendered-visibility certification.
    """
    texts = []

    def visit(node: ET.Element) -> None:
        if node.tag.rsplit("}", 1)[-1] in {"defs", "symbol", "clipPath", "mask"}:
            return
        style = dict(part.split(":", 1) for part in node.get("style", "").split(";") if ":" in part)
        values = {
            key.strip(): value.strip().removesuffix("!important").strip()
            for key, value in style.items()
        }
        if values.get("display", node.get("display")) == "none":
            return
        if values.get("visibility", node.get("visibility")) in {"hidden", "collapse"}:
            return
        if values.get("opacity", node.get("opacity")) is not None:
            try:
                if float(values.get("opacity", node.get("opacity"))) <= 0:
                    return
            except ValueError:
                pass
        if node.tag in {SVG + "text", SVG + "tspan"} and node.text:
            texts.append(node.text)
        for child in node:
            visit(child)
            if node.tag in {SVG + "text", SVG + "tspan"} and child.tail:
                texts.append(child.tail)

    visit(root)
    return " ".join(" ".join(texts).split())


class _DocumentIds(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.ids.update(value for key, value in attrs if key == "id" and value)


def _check_navigation(files: dict[str, str]) -> int:
    """Check every generated SVG navigation destination, not fetched resources."""
    ids = {}
    roots = {}
    for name, content in files.items():
        if name.endswith(".svg"):
            root = ET.fromstring(content)
            roots[name] = root
            ids[name] = {node.get("id") for node in root.iter() if node.get("id")}
        elif name.endswith(".html"):
            parser = _DocumentIds()
            parser.feed(content)
            ids[name] = parser.ids
    count = 0
    for name, root in roots.items():
        for link in root.iter(SVG + "a"):
            href = link.get("href", link.get("{http://www.w3.org/1999/xlink}href", ""))
            address = urlsplit(href)
            if (
                address.scheme
                or address.netloc
                or address.query
                or unquote(address.path) != address.path
            ):
                raise CoordinationError(f"Unsupported SVG navigation destination in {name}: {href}")
            path = PurePosixPath(address.path)
            if path.is_absolute() or ".." in path.parts or "\\" in address.path:
                raise CoordinationError(f"Unsafe SVG navigation destination in {name}: {href}")
            target = (PurePosixPath(name).parent / path).as_posix() if address.path else name
            if (
                target not in ids
                or not address.fragment
                or unquote(address.fragment) not in ids[target]
            ):
                raise CoordinationError(f"Missing SVG navigation destination in {name}: {href}")
            count += 1
    return count


def visual_quality_report(files: dict[str, str], snapshot: dict) -> dict:
    """Fail on broken delivery fundamentals; never infer full visual acceptance.

    The report inventories literal/style and accessible-root coverage. It deliberately
    does not certify computed contrast, text collisions, physical scale or human reading.
    Those require the separate renderer probes, annotation contracts and visual review.
    """
    rows, errors = [], []
    for name, content in sorted(files.items()):
        if not name.endswith(".svg"):
            continue
        root = ET.fromstring(content)
        title, description = root.find(SVG + "title"), root.find(SVG + "desc")
        accessible = all(
            node is not None and "".join(node.itertext()).strip() for node in (title, description)
        )
        vb = root.get("viewBox", "").split()
        try:
            viewport = (
                len(vb) == 4
                and all(math.isfinite(float(v)) for v in vb)
                and all(float(v) > 0 for v in vb[2:])
            )
        except ValueError:
            viewport = False
        unresolved = has_svg_css_variables(root)
        visible_text = _authority_text(root)
        authority = "NOT FOR CONSTRUCTION" in visible_text.upper()
        faults = []
        if not accessible:
            faults.append("missing nonempty title or description")
        if not viewport:
            faults.append("invalid viewBox")
        if unresolved:
            faults.append("uncompiled CSS colour/style variable")
        if not authority:
            faults.append("missing authority wording outside explicitly hidden/definition subtrees")
        errors += [f"{name}: {fault}" for fault in faults]
        native = name.startswith("drawings/")
        tasks = [
            {
                "id": "local-computed-contrast",
                "state": "manual_or_profile_review_required",
                "reason": "Static literal counts do not resolve every local background and opacity.",
            },
            {
                "id": "reading-and-print",
                "state": "reader_review_required",
                "reason": "Small previews and fit-to-page printing do not certify detailed readability.",
            },
        ]
        if native:
            tasks.append(
                {
                    "id": "inherited-model-style",
                    "state": "retained_source_meaning",
                    "reason": "Native material/wall/force hues keep their local keys; no blanket recolour.",
                }
            )
        annotation_review = []
        for ordinal, node in enumerate(root.iter(SVG + "text"), 1):
            value = " ".join("".join(node.itertext()).split())
            if not value:
                continue
            # Every inherited annotation is addressable; never certify a whole
            # legacy layer merely because its root metadata is present.
            annotation_review.append({
                "element": node.get("id", f"text[{ordinal}]"),
                "text": value,
                "declared_role": node.get("data-text-role", node.get("data-dimension-role")),
                "font_size_attribute": node.get("font-size"),
                "fill_attribute": node.get("fill"),
                "x": node.get("x"), "y": node.get("y"),
                "review_state": "computed local contrast and rendered bounds not certified by this inventory",
            })
        rows.append(
            {
                "file": name,
                "sha256": hashlib.sha256(content.encode()).hexdigest(),
                "purpose": root.get(
                    "data-view-purpose",
                    "native architectural/discipline consumer"
                    if native
                    else "source-entity coordination projection",
                ),
                "visual_language_version": root.get(
                    "data-visual-language-version", "shared delivery v1"
                ),
                "accessible_root": accessible,
                "valid_viewbox": viewport,
                "literal_style_delivery": not unresolved,
                "authority_wording_present": authority,
                "authority_visibility": "requires rendered review; CSS cascade and clipping not certified",
                "text_elements": len(list(root.iter(SVG + "text"))),
                "literal_colours": len(set(re.findall(r"#[0-9a-fA-F]{6}\b", content.upper()))),
                "review_tasks": tasks,
                "annotation_review": annotation_review,
            }
        )
    if errors:
        raise CoordinationError("Graphic delivery checks failed: " + "; ".join(errors))
    navigation_count = _check_navigation(files)
    return {
        "schema_version": 1,
        "format_date": "2026-10-03",
        "source_model_hash": snapshot["model_hash"],
        "scope": "generated connected SVG delivery fundamentals, not complete aesthetic/accessibility acceptance",
        "status": "fundamentals_pass; visual_acceptance_separate",
        "sheets": rows,
        "summary": {
            "svg_count": len(rows),
            "navigation_links_checked": navigation_count,
            "fundamental_errors": len(errors),
            "unresolved_style_variables": sum(not r["literal_style_delivery"] for r in rows),
        },
        "review_policy": "Each sheet retains explicit review tasks; no inherited layer receives a blanket visual pass.",
    }
