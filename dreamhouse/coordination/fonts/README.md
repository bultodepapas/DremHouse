# Coordination review fonts

**Version:** 0.1<br>
**Date:** 2026-10-02<br>
**Status:** pinned rendering resources; no design authority<br>
**Source:** unmodified IBM Plex Sans regular/bold TrueType files from the installed
`fonts-ibm-plex` distribution; upstream https://github.com/IBM/plex.

These two files are included so coordination PNG previews and their contact sheet do
not depend on fonts installed on a reviewer's machine. The exporter disables system
font discovery and records each file's SHA-256 plus renderer/library versions. SVG
geometry and textual dimensions remain the model-derived source; PNG is a preview.

See `COPYRIGHT.txt` for the distribution's copyright notices and Open Font License.
The fonts have not been renamed, modified or subsetted. Replacing them changes the
rendering configuration and requires new visual comparison evidence.
