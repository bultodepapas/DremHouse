from __future__ import annotations

import re
import unittest

from dreamhouse.svg.sheet import CSS
from dreamhouse.svg.theme import (
    APPROVED_PRESENTATION_COLOURS,
    THEME_COLOURS,
    colour,
)


class TestSvgTheme(unittest.TestCase):
    def test_tokens_are_unique_uppercase_six_digit_colours(self) -> None:
        values = list(THEME_COLOURS.values())
        self.assertEqual(len(values), len(set(values)))
        self.assertTrue(all(re.fullmatch(r"#[0-9A-F]{6}", value) for value in values))
        self.assertEqual(set(values), set(APPROVED_PRESENTATION_COLOURS))

    def test_shared_css_declares_only_approved_colours(self) -> None:
        css_colours = {value.upper() for value in re.findall(r"#[0-9A-Fa-f]{6}", CSS)}
        self.assertEqual(css_colours, set(APPROVED_PRESENTATION_COLOURS))

    def test_unknown_semantic_token_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown SVG theme colour token"):
            colour("not-a-token")


if __name__ == "__main__":
    unittest.main()
