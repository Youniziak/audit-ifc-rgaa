# audit-ifc-rgaa

> **Built-environment accessibility auditing, by the auditors directly concerned.**
>
> An open pipeline that goes from the BIM model (IFC) to a BCF discrepancy
> report exchangeable with architects, by way of physical measurement tools
> designed blind-first.

🖥️ **[Watch the live terminal demo](https://youniziak.github.io/audit-ifc-rgaa/demo_terminal.html)** — animated, screen-reader friendly.

[

![Code license: GPL v3](https://img.shields.io/badge/Code-GPLv3-blue.svg)

](LICENSE)
[

![Hardware license: CERN-OHL-P v2](https://img.shields.io/badge/Hardware-CERN--OHL--P%20v2-orange.svg)

](hardware/)
[

![Python 3.9+](https://img.shields.io/badge/Python-3.9+-green.svg)

](https://www.python.org/)
[

![Status: v0.3 functional](https://img.shields.io/badge/Status-v0.3%20functional-success.svg)

](CHANGELOG.md)

> 🇫🇷 **Version française : [README.fr.md](README.fr.md)**
>
> ⚠️ **Regulatory scope:** the compliance rules implemented here are based on
> **French regulations** (arrêtés of 20 April 2017 and 8 December 2014). The pipeline
> architecture is reusable and can be adapted to any country's accessibility
> standards.

## The problem

Built-environment accessibility auditing today relies on graphical floor plans
and visual inspection. Two problems follow from this:

1. **Auditors with visual impairments** — who are the people most directly
   concerned by accessibility issues — have no direct access to the data.
2. **Discrepancies between the BIM model and reality are never systematically
   verified.** A ramp declared at 4.8% may actually be 6.3% on site; nobody
   measures it, everybody signs off.

Yet all the necessary data already exists in the BIM model, in the open IFC
format (ISO 16739). It simply needs to be made usable and checked against
reality.

## The proposal

`audit-ifc-rgaa` is a complete pipeline with two parts:

### Software part — `audit_ifc_rgaa.py`, `comparaison_terrain.py`, `bcf_export.py`, `plan_tactile.py`

- Parses a project's IFC file
- Automatically checks compliance with the French regulation the auditor
  chooses for each audit: the arrêté of 20 April 2017 (new public buildings)
  or the arrêté of 8 December 2014 (existing public buildings) — doors, stairs,
  ramps, corridors, sanitary facilities. Every threshold is sourced in
  [REFERENTIEL.md](REFERENTIEL.md) (French)
- Generates a structured Markdown report readable by screen readers
- Compares declared values against on-site measurements (JSON file)
- Exports discrepancies in the standard BCF 2.1 format, exchangeable with Revit,
  ArchiCAD, BIMcollab, Solibri, BlenderBIM
- Produces a raised tactile floor plan of each level, for 3D printing, with
  the audit's findings marked by a dome on request

### Hardware part — the `hardware/` folder

- **RGAA tactile ruler:** a 3D-printable ruler whose regulatory thresholds are
  marked by distinct tactile notches
- **Voice laser rangefinder:** spoken output in French, vibration feedback,
  ~€32 in components
- **Continuous voice inclinometer:** dynamic slope measurement with audible
  alerts at thresholds, ~€29
- **WCAG built-environment colorimeter:** objective measurement of signage
  contrast, ~€38 — a device with no commercial equivalent to date

All hardware tools follow the **blind-first universal design** principle: the
primary interface is non-visual (audio, vibration, tactile), with a secondary
but present visual interface.

## Complete pipeline
┌─────────────────────────────────────────────────────────────┐
    │                    BIM model (.ifc)                          │
    │              provided by the architect                       │
    └──────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  audit_ifc_rgaa.py                                           │
    │  Geometric audit against the chosen text (new / existing)   │
    └──────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
          Theoretical compliance report (accessible Markdown)
                      + list of elements to measure (GlobalId)
                               │
                               ▼
    ┌─────────────────────────────────────────────────────────────┐
    │   Blind-first physical tools on site                        │
    │   (rangefinder, inclinometer, colorimeter, tactile ruler)   │
    └──────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
                 measurements.json (timestamped, signed)
                               │
                               ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  comparaison_terrain.py                                      │
    │  Compares BIM ↔ on-site, dual evaluation:                   │
    │   1. Concordance with the model                              │
    │   2. Regulatory compliance                                   │
    └──────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
          BIM ↔ on-site report + BCF 2.1 file (.bcfzip)
                               │
                               ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  Architect / project owner (Revit, ArchiCAD…)               │
    │  opens the BCF, sees each discrepancy on the 3D model       │
    └─────────────────────────────────────────────────────────────┘

## Installation

```bash
git clone https://github.com/Youniziak/audit-ifc-rgaa.git
cd audit-ifc-rgaa
pip install -r requirements.txt
```

Dependency: IfcOpenShell (LGPL). For the accessible PDF (`--pdf` option):
`pip install -r requirements-pdf.txt`. For the tactile plan:
`pip install -r requirements-plan.txt`.

## Quick start

Every command needs the applicable regulation: `--neuf` (new building,
arrêté of 20 April 2017) or `--existant` (existing building, arrêté of
8 December 2014). Without one of them, the tool stops and asks for it.

### 1. Compliance audit from the BIM model alone

```bash
python3 audit_ifc_rgaa.py exemples/test_erp_avec_espaces.ifc --existant
```

Generates `exemples/test_erp_avec_espaces_audit.md` listing all detected
non-compliances with severity and regulatory article.

### 2. BIM ↔ on-site comparison + BCF export

```bash
python3 comparaison_terrain.py exemples/test_house.ifc \
                               exemples/mesures_exemple.json \
                               --neuf --bcf retours_architecte.bcfzip
```

Produces the discrepancy report in Markdown and a `.bcfzip` file to hand
directly to the architect.

### 3. Accessible PDF report

Adding `--pdf` to either command also writes the report as a PDF, next to
the Markdown file:

```bash
pip install -r requirements-pdf.txt
python3 audit_ifc_rgaa.py exemples/test_erp_avec_espaces.ifc --existant --pdf
```

The PDF is tagged (headings, lists and links in the structure tree),
declares its language and title, and embeds its fonts: it is the PDF/UA-1
variant of [WeasyPrint](https://weasyprint.org/). If
[veraPDF](https://verapdf.org/) is installed (`verapdf` command), the tool
checks the file against its PDF/UA-1 profile and prints the result. Without
veraPDF, it says so, and the PDF is not declared compliant.

Automated checking does not cover all of PDF/UA: some criteria need human
judgement (meaningful headings, intended reading order). The tool's reports
have no images or tables and read in Markdown order. A long list that runs
across a page break (the limits list, for instance) becomes two lists in
the PDF, so a screen reader announces two list sizes. The PDF has no page
numbers: WeasyPrint does not tag them as artifacts, and they would end up in
the text for anyone reading in page order.

Security: element names come from the IFC file, which may come from a third
party. Any HTML they contain is shown as text, never interpreted, and the
export fetches no file and no address.

The export has not yet been tried on Termux. Untested leads:
`pkg install pango python-pillow ttf-dejavu`, then
`pip install -r requirements-pdf.txt` (pip will have to build cffi).

### 4. Tactile floor plan for 3D printing

```bash
pip install -r requirements-plan.txt
python3 plan_tactile.py exemples/test_house.ifc
```

Writes one STL file per level and a Markdown key (readable with a screen
reader) into `exemples/test_house_plan_tactile/`. On the plate: raised
walls, lower raised windows, doors as gaps in the wall, stairs as ridges,
ramps as a sloping surface, lifts as a plateau, room numbers. Everything written on the plate (title, numbers, scale) is in
braille and in raised ordinary letters, so it can be read with or without
sight. The key gives each room's name, the symbols, the scale and the
direction of every stair and ramp, and says what could not fit on the plate
at that scale (a stair too small, a dome with no room left, a door without
its triangle).

Each plate also gets a **visual plan** (`.svg` file, next to the `.stl`): the
same plate drawn black on white, which can be enlarged without blur
(ZoomText, magnifier, browser). Walls in black, low walls in grey, room
numbers in digits, braille as grey dots, audit markers numbered as in the
key, arrows on ramps pointing uphill. The sighted and the blind reader share
the same plan. The key shows these plans, and so does the `--pdf` PDF, with
alternative text.

- `--neuf` or `--existant`: also runs the audit and marks every
  non-compliant element with a raised dome; the key lists the findings.
- `--echelle 100`: forces the scale; a level that is too large is split
  across several plates. Without it, the tool takes the largest scale at
  which the level fits on one plate, and the key suggests a scale when too
  many rooms could not get their number.
- `--plateau 250x210`: maximum plate size in mm (200 × 200 by default).
- `--eprouvette`: a test plate (wall heights, door gaps, braille dot heights,
  stair ridge spacing and height, letter size) to print and touch before the first plan;
  `--hauteur-murs`, `--hauteur-stries` and `--hauteur-points` then adjust
  the plan.
- `--pdf`: the key also as an accessible PDF, checked with veraPDF when it is installed (as for the audit).

The dimensions, their sources (ISO 17049, ISO 19028, BANA) and what still
has to be checked by touch are in [PLAN_TACTILE.md](PLAN_TACTILE.md)
(French). A tactile plan is not required by the French regulations: it is an
orientation aid, or a working tool for the auditor. Not yet tried on Termux.

### 5. Regenerate the test IFC file

```bash
python3 generer_exemple_espaces.py
```

### 6. Run the tests

```bash
pip install pytest
python3 -m pytest tests/
```

## What is checked (v0.4.3)

Thresholds for new buildings (arrêté of 20 April 2017), then for existing
buildings (arrêté of 8 December 2014). Details and sources:
[REFERENTIEL.md](REFERENTIEL.md).

| Element | New | Existing | Article |
| --- | --- | --- | --- |
| Doors, width | 0.90 m (0.80 m for non-adapted toilets and cubicles) | 0.80 m | Art. 10 |
| Stairs, tread depth | at least 0.28 m | at least 0.28 m | Art. 7-1 (new), 7.1 (existing) |
| Stairs, riser height | at most 0.16 m | at most 0.17 m | Art. 7-1 (new), 7.1 (existing) |
| Stairs, flight width | at least 1.20 m between handrails (to be checked) | at least 1 m between handrails; original dimensions may be kept if no works | Art. 7-1 (new), 7.1 (existing) |
| Ramps, slope and length | 5%; 8% over 2 m; 10% over 0.50 m | 6%; 10% over 2 m; 12% over 0.50 m | Art. 2, applied indoors by Art. 6 |
| Ramps, resting landing | every 10 m from 4%; 1.20 × 1.40 m | every 10 m from 5%; 1.20 × 1.40 m | Art. 2 and Annex 2 |
| Door thresholds (small steps) | 2 cm; 4 cm with a bevel of at most 33% | same | Art. 2, applied indoors by Art. 6 |
| Corridors, width | 1.40 m (1.20 m at a localized narrowing) | 1.20 m (0.90 m at a localized narrowing) | Art. 6, referring to Art. 2 |
| Sanitary, turning space | Ø 1.50 m, inside or else in front of the door | Ø 1.50 m, inside or else in front of the door | Art. 12 and Annex 2 |
| Door manoeuvring space | 1.70 m on the push side, 2.20 m on the pull side | same | Art. 10 and Annex 2 |
| Elevators, car | an occupied wheelchair (0.75 × 1.25 m) must fit; below 1.00 × 1.25 m (type 1 of standard NF EN 81-70:2003), to be checked | same, except under structural constraints: to be checked | Art. 7-2 (new), 7.2 (existing), Annex 1 |
| Platform lifts, platform | 0.90 × 1.40 m (1.10 × 1.40 m for corner access) | same | Art. 7-2 (new), 7.2 (existing) |

## What is not (yet) checked

Automated auditing does not cover — and will never fully cover:

- Visual signage contrast → dedicated tool `colorimetre-wcag`
- Tactile warning surfaces (NF P98-351)
- Handrails (presence, height, extension)
- Audible signals for traffic lights and elevators
- Magnetic induction loops
- Quality of use as experienced by people with disabilities

These items appear in the *Limits of automated checking* section of every
generated report.

## Repository structure
audit-ifc-rgaa/
├── README.md                    This document (English)
├── README.fr.md                 French version
├── CHANGELOG.md                 Version log
├── VERSION                      Current version (0.7.0)
├── REFERENTIEL.md               Applied thresholds, article by article, with sources
├── PLAN_TACTILE.md              Tactile plan: dimensions, sources, choices to validate
├── PLANS_EXISTANTS.md           Planned method for reading a plan without a model (v0.8)
├── LICENSE                      GPL-3.0 for the code
├── requirements.txt             Python dependencies
├── requirements-pdf.txt         PDF export dependencies (--pdf)
├── requirements-plan.txt        Tactile plan dependencies
│
├── audit_ifc_rgaa.py            Main module — IFC compliance audit
├── referentiels.py              Thresholds of both regulations (new / existing)
├── comparaison_terrain.py       BIM ↔ on-site measurement comparison
├── bcf_export.py                BCF 2.1 file generation
├── pdf_accessible.py            Tagged PDF report (PDF/UA-1)
├── plan_tactile.py              Raised tactile plan (STL) and key
├── plan_visuel.py               Visual plan of each plate (SVG)
├── generer_exemple_espaces.py   Test IFC generation helper
│
├── tests/                       Tests (python3 -m pytest tests/)
│
├── exemples/                    Demonstration files
│   ├── test_house.ifc           Simple house (1 door)
│   ├── test_erp_avec_espaces.ifc  Fictional ERP (corridors, toilets, doors)
│   └── mesures_exemple.json     On-site measurement format
│
└── hardware/                    Blind-first physical tools
├── README.md                General index
├── docs/
│   ├── PHILOSOPHIE.md       Blind-first universal design approach
│   └── CONTRIBUTING.md      Contribution guide
├── metre-tactile-rgaa/      3D-printable notched ruler
├── telemetre-vocal/         ESP32-S3 voice laser rangefinder
├── inclinometre-vocal/      ESP32-S3 continuous voice inclinometer
└── colorimetre-wcag/        ESP32-S3 WCAG built-environment colorimeter

## Standards and licenses

| Component | License |
| --- | --- |
| Python code | GPL 3.0 or later |
| Hardware design (PCB, schematics, 3D models) | CERN-OHL-P v2 |
| Embedded firmware | GPL 3.0 or later |
| Documentation | CC BY-SA 4.0 |

Standards used:

- IFC 2x3 / IFC4 / IFC4x3 — buildingSMART / ISO 16739
- BCF 2.1 — buildingSMART, BIM collaboration format
- WCAG 2.1 — W3C, contrast ratio applicable to the built environment
- Arrêté of 8 December 2014 — accessibility of existing public buildings (ERP), France
- Arrêté of 20 April 2017 — accessibility of new public buildings (ERP), France
- Law of 11 February 2005 — equal rights and opportunities, France

## Roadmap

- [x] v0.1 — Basic geometric audit: doors, stairs, ramps
- [x] v0.2 — Horizontal circulation and accessible sanitary facilities
- [x] v0.3 — BIM ↔ on-site comparison + BCF 2.1 export
- [x] v0.3.1 — Choice of applicable regulation (new or existing), sourced thresholds, tests
- [x] v0.4 — Door manoeuvring space (Annex 2)
- [x] v0.4.1 — Elevators and platform lifts (Art. 7.2 or 7-2)
- [x] v0.4.2 — Ramps (length, resting landings) and door thresholds
- [x] v0.4.3 — Stair width, step measurements from geometry
- [x] v0.5 — Accessible PDF export (tagged PDF/UA-1, checked with veraPDF)
- [x] v0.6 — Raised tactile floor plans for 3D printing (STL), with a key and the audit's findings
- [x] v0.7 — Visual plans: each plate drawn as a black-on-white SVG, zoomable, with the same numbers (also in the PDF key)
- [ ] v0.8 — Reading existing plans: vector PDF and DXF first, then scanned plans and photos, redrawn as an IFC model after rescaling on a known dimension; measurements to be confirmed on site (field comparison). Method: [PLANS_EXISTANTS.md](PLANS_EXISTANTS.md) (French)
- [ ] v1.0 — IndoorGML graphs for accessible indoor guidance
- [ ] v1.x — First published hardware prototype (tactile ruler)

## Who it is for

This tool is aimed at:

- **Professional accessibility auditors** (certified or in training), whether or
  not they have a disability
- **Public project owners** who want to make their Ad'AP (programmed
  accessibility agenda) checks objective
- **Architects and engineering offices** who want to integrate accessibility
  verification into their BIM workflows
- **Technical inspection bodies** (Apave, Bureau Veritas, Socotec) who may find
  an automatable building block here
- **Associations** (APF France handicap, Valentin Haüy, FAF…) who need
  enforceable data
- **Students and trainers** in accessibility, BIM, architecture

## Disclaimer

This tool is provided as an aid to auditing and for accessibility awareness. It
is a complement to human expertise, not a substitute for it, and does not
replace the certified auditor's expertise or the mandatory regulatory checks
(Ad'AP, public accessibility register, signed compliance certificates).

## Cite this project

```bibtex
@software{youniziak_audit_ifc_rgaa_2026,
  author  = {Chatellard, Kévin},
  title   = {audit-ifc-rgaa: an open pipeline for built-environment
             accessibility auditing from BIM},
  year    = {2026},
  version = {0.5.0},
  url     = {https://github.com/Youniziak/audit-ifc-rgaa},
  license = {GPL-3.0-or-later}
}

Design and AI collaboration
This project was conceived, directed and validated by Kévin (@Youniziak), an
auditor retraining toward digital accessibility. The angle, the software
architecture, the choice of standards (IFC, BCF, WCAG), the blind-first
philosophy of the hardware tools and the strategic decisions are his own.
The Python code was produced in pair-programming with Claude (Anthropic),
used as an execution accelerator from detailed specifications. This transparency
is deliberate: AI is a legitimate production tool when directed by someone who
knows what they want to build and why.
External contributions (issues, pull requests, usage feedback) are welcome and
will be handled with care — see
hardware/docs/CONTRIBUTING.md for details.
Contact
GitHub: @Youniziak
Issues: to report a bug, suggest a feature, or open a technical discussion
For sensitive matters (sponsoring, partnership, press): see the GitHub profile



