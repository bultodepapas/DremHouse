# Contributing to Dream House

This repository is a living technical project record, not a collection of
unconnected ideas. Every contribution must preserve traceability across source,
decision, assumption, drawing, and cost.

## Before making a change

1. Read the [project-record index](docs/README.md), the
   [Project Constitution](docs/00_gobernanza/constitucion_del_proyecto.md), and the
   [document precedence](docs/00_gobernanza/fuentes_precedencia_y_conflictos.md).
2. Determine whether the information is a hard rule, a control value, an
   assumption, or an open matter.
3. Never resolve a contradiction silently: record the conflict or open a
   decision.
4. If the change affects scope or cost, update the
   [Cost Baseline and Control](docs/04_costos/base_y_control_de_costos.md).
5. Follow the
   [Language and Translation Policy](docs/00_gobernanza/language_and_translation_policy.md).
   Do not translate or edit files under `docs/BORN_Legacy/`.

## Recommended workflow

- Open a **decision** issue for a change in criteria, or an **RFI** for a
  technical query.
- Work on a short-lived branch and keep each pull request to one coordinable
  change.
- State the source, date, version, status, assumptions, and affected documents.
- When issuing a drawing, retain its `manifest.json` and limitation-of-use note.
- Validate the presentation before submitting changes:

```powershell
python .github/scripts/build_showcase.py --write-readme --site-dir .build/showcase
python .github/scripts/build_showcase.py --check-readme
```

## Acceptance criteria

A contribution is ready when it is traceable, does not violate hard rules,
states its uncertainties, updates every affected document, and clearly
distinguishes concept work, coordination information, and construction-ready
documentation.
