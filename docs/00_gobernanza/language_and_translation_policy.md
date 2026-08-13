# Language and translation policy

**Status:** active  
**Version:** 0.1  
**Date:** 2026-08-12  
**Source:** owner instruction and decision D-044.

## Working language

English is the working language for all project-authored and derived documentation. The
required register is clear, technically accurate, professional English suitable for
architects, engineers, quantity surveyors, contractors, reviewers, and the owner.

This is a controlled editorial migration. Translation does not change design intent,
scope, geometry, cost, status, or authority. Any wording that could change one of those
items must be handled as a decision or conflict, not silently resolved by the translator.

## Original sources

Every file under `docs/BORN_Legacy/` remains in its original Spanish and must not be
translated, rewritten, reformatted, or normalized. These files are preserved evidence,
not working translations.

When an English derived document cites a BORN source:

- keep the original filename and path;
- translate the source title only in visible link text when useful;
- clearly identify quotations translated from Spanish;
- consult the Spanish original if an English term is ambiguous; and
- open a conflict if the ambiguity can affect scope, performance, cost, or geometry.

## Stable project identifiers

File and folder names, drawing numbers, decision IDs, conflict IDs, cost codes, model
keys, and revision identifiers remain unchanged during the language migration. This
protects links, manifests, scripts, and historical traceability.

Established project abbreviations such as `PB`, `P2`, `F1`, `F2`, `DCV`, `E0`, and `IFC`
may remain in use. On first use in a public-facing document, explain them in English when
their meaning is not obvious.

## Terminology and notation

Use one technical term consistently within a document. Preferred translations include:

| Spanish source term | Preferred English term |
|---|---|
| nave | industrial hall / hall, according to context |
| planta baja (PB) | ground floor (PB) |
| segundo piso (P2) | upper floor (P2) |
| núcleo | service core / core |
| gran muro | Great Wall, when naming the project element |
| anteproyecto | schematic design |
| predimensionamiento | preliminary sizing |
| emitido para coordinación | issued for coordination |
| no apto para construir | not for construction |
| presupuesto de control | control estimate |
| partida | cost item / work item |
| puerta de fase | stage gate |

Derived English documents use a decimal point and English number formatting. Monetary
values retain `COP` and their original magnitude. Conversion of `18,00 m` to `18.00 m`,
for example, is editorial only; the value is unchanged.

## Migration and review

Documents are translated by authority and use, not simply by folder order:

1. repository entry points and project governance;
2. active brief, program, and discipline bases;
3. active drawings and coordination reports;
4. cost, site, regulatory, and delivery controls;
5. templates, research, and historical derived material.

Each translated document must retain its status, version, date, source, assumptions, and
open issues. Links must remain valid. A translation is complete only after terminology,
numbers, identifiers, and cross-references have been checked against the Spanish source.
