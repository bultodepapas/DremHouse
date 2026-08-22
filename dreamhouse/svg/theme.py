"""Controlled presentation colours for Dream House SVG drawing pilots."""

from __future__ import annotations


THEME_COLOURS = {
    "paper": "#F4F0E7",
    "panel": "#FFFDFA",
    "ink": "#172A32",
    "muted": "#536168",
    "info": "#1D7480",
    "open": "#8A5A16",
    "conflict": "#A33F31",
    "hypothesis": "#66538A",
    "material": "#74543C",
    "on-dark-muted": "#DDE4E2",
    "on-dark-alert": "#FFB4A8",
    "sheet-rule": "#B9C0BD",
    "panel-rule": "#CBD0CC",
    "open-surface": "#FBF0D9",
    "hypothesis-surface": "#F0ECF6",
    "table-row": "#EEF2F0",
    "table-row-alt": "#F8F6F0",
    "program-technical": "#E9F0F2",
    "program-buffer": "#F7F4EC",
    "program-living": "#F2E8DE",
    "program-kitchen": "#F5E8D4",
    "rooflight-surface": "#9CC6CC",
    "structure-gravity": "#3D7186",
    "trial": "#BD7626",
    "material-new-board": "#AEB8B5",
    "material-reclaimed": "#E5DED2",
    "material-insulated": "#E1EEE7",
    "material-insulation-edge": "#39765A",
    "material-air": "#FFFFFF",
    "material-air-marker": "#798582",
}

APPROVED_PRESENTATION_COLOURS = frozenset(
    value.upper() for value in THEME_COLOURS.values()
)


def colour(token: str) -> str:
    """Return one controlled colour and fail closed on unknown semantic tokens."""

    try:
        return THEME_COLOURS[token]
    except KeyError as error:
        raise ValueError(f"Unknown SVG theme colour token: {token}") from error


def css_variable_block() -> str:
    """Serialize the complete palette as deterministic CSS custom properties."""

    return "\n".join(f"  --{token}: {value};" for token, value in THEME_COLOURS.items())
