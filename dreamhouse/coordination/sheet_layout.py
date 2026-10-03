"""Recompose inherited screening sheets without changing their source geometry."""

from xml.etree import ElementTree as ET

from dreamhouse.coordination.model import CoordinationError

NS = "http://www.w3.org/2000/svg"

REFERENCES = {
    "architecture-ground-floor": (
        ("architecture-ground-floor-core", "Enlarged service core"),
        ("architecture-roof-longitudinal-section", "Longitudinal datum section"),
    ),
    "architecture-upper-floor": (
        ("architecture-p2-hall-edge", "Open family edge detail"),
        ("architecture-roof-transverse-section", "Transverse datum profile"),
    ),
    "architecture-ground-floor-core": (("architecture-ground-floor", "Ground-floor location"),),
    "architecture-roof-longitudinal-section": (
        ("architecture-ground-floor", "Ground-floor plan"),
        ("architecture-roof-transverse-section", "Transverse datum profile"),
    ),
    "architecture-roof-transverse-section": (
        ("architecture-upper-floor", "Upper-floor plan"),
        ("architecture-roof-longitudinal-section", "Longitudinal datum section"),
    ),
    "architecture-roof-plan": (
        ("architecture-roof-daylight-section", "Rooflight projection"),
        ("architecture-roof-longitudinal-section", "Longitudinal datum section"),
    ),
    "architecture-roof-daylight-section": (("architecture-roof-plan", "Roof plan"),),
    "structure-coordination-plan": (
        ("structure-lateral-a", "Structural Side A screening"),
        ("structure-vertical-continuity", "Stair-core continuity study"),
    ),
    "structure-lateral-a": (("structure-coordination-plan", "Structural plan and transverse profile"),),
    "structure-great-wall": (
        ("architecture-great-wall-elevation", "Great Wall architectural finish"),
        ("architecture-ground-floor-core", "Service-core plan"),
    ),
    "structure-vertical-continuity": (
        ("architecture-ground-floor-core", "Service-core plan"),
        ("architecture-upper-floor", "Upper-floor plan"),
    ),
    "structure-e1-synthesis": (("structure-coordination-plan", "Structural plan and transverse profile"),),
}


def append_view_references(svg: str, view_id: str) -> str:
    references = REFERENCES.get(view_id)
    if references is None and view_id.startswith("architecture-pb-"):
        references = (("architecture-ground-floor", "Ground-floor plan"),)
    if references is None and view_id.startswith("architecture-p2-"):
        references = (("architecture-upper-floor", "Upper-floor plan"),)
    if references is None and view_id in {
        "architecture-access-egress", "architecture-owner-priorities", "architecture-window-schedule"
    }:
        references = (
            ("architecture-ground-floor", "Ground-floor plan"),
            ("architecture-upper-floor", "Upper-floor plan"),
        )
    if references is None and view_id.startswith("architecture-") and "elevation" in view_id:
        references = (
            ("architecture-ground-floor", "Ground-floor plan"),
            ("architecture-upper-floor", "Upper-floor plan"),
        )
    if not references:
        return svg
    root = ET.fromstring(svg)
    x, y, width, height = map(float, root.get("viewBox").split())
    root.set("viewBox", f"{x:g} {y:g} {width:g} {height + 50:g}")
    root.set("height", f"{height + 50:g}")
    panel = ET.SubElement(root, f"{{{NS}}}g", {"data-view-references": view_id})
    ET.SubElement(panel, f"{{{NS}}}rect", {
        "x": str(x), "y": str(y + height), "width": str(width), "height": "50",
        "fill": "#edf2f1",
    })
    label = ET.SubElement(panel, f"{{{NS}}}text", {
        "x": "30", "y": str(y + height + 18), "font-size": "10", "fill": "#31474f",
    })
    label.text = "VIEW REFERENCES · Project X = front to rear; Y = Side A to Side B. Datum profiles are not solid cuts."
    for i, (target, title) in enumerate(references):
        link = ET.SubElement(panel, f"{{{NS}}}g", {"data-related-view": target})
        text = ET.SubElement(link, f"{{{NS}}}text", {
            "x": str(30 + i * 350), "y": str(y + height + 37),
            "font-size": "12", "fill": "#096479",
        })
        text.text = title
    return ET.tostring(root, encoding="unicode")


def recompose_screening(svg: str, view_id: str) -> str:
    if view_id not in {"structure-coordination-plan", "structure-lateral-a"}:
        return svg
    root = ET.fromstring(svg)
    groups = root.findall(f"{{{NS}}}g")
    if len(groups) < 2:
        raise CoordinationError("Missing inherited structural drawing group")
    drawing = groups[1]
    if view_id == "structure-coordination-plan":
        root.set("height", "1320")
        root.set("viewBox", "0 0 1400 1320")
        root.find(f"{{{NS}}}rect").set("height", "1320")
        section = ET.SubElement(drawing, f"{{{NS}}}g", {
            "data-layout-panel": "section-b-b", "transform": "translate(-840 500) scale(1.2)"
        })
        started = False
        for child in list(drawing):
            if child is section:
                continue
            text = child.text or ""
            if text.startswith("CORTE TRANSVERSAL ESTRUCTURAL B-B"):
                started = True
            if started:
                drawing.remove(child)
                section.append(child)
            elif text.startswith("ALTERNATIVA CERCHA"):
                child.set("x", "150")
                child.set("y", "675")
                child.set("text-anchor", "start")
            elif text.startswith("P2 ·"):
                child.set("x", "150")
                child.set("y", "650")
                child.set("text-anchor", "start")
            elif text.startswith("P2 D-043:"):
                child.set("x", "650")
                child.set("y", "650")
                child.set("text-anchor", "start")
        if not started:
            raise CoordinationError("Missing inherited B-B section")
        # The inherited evidence box remains intact below both drawing panels.
        after = False
        notes = ET.Element(f"{{{NS}}}g", {"transform": "translate(0 390)"})
        for child in list(root):
            if child is drawing:
                after = True
            elif after:
                root.remove(child)
                notes.append(child)
        root.append(notes)
    else:
        geometry = ET.SubElement(drawing, f"{{{NS}}}g", {
            "data-layout-panel": "side-a", "transform": "translate(-75 -470) scale(1.65)"
        })
        for child in list(drawing):
            if child is geometry:
                continue
            text = child.text or ""
            if child.tag.endswith("text") and (
                text.startswith("PARED HÍBRIDA") or "CRIBADO GRAVITACIONAL" in text
            ):
                child.attrib.pop("transform", None)
                child.set("x", "700")
                child.set("y", "235" if text.startswith("PARED HÍBRIDA") else "205")
                child.set("text-anchor", "middle")
                child.set("font-size", "11")
            elif child.tag.endswith("text") and float(child.get("y", "0")) < 200:
                child.set("x", "700")
            else:
                drawing.remove(child)
                geometry.append(child)
    return ET.tostring(root, encoding="unicode")
