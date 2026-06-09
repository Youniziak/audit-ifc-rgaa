# audit-ifc-rgaa

> **Built-environment accessibility auditing, by the auditors directly concerned.**
>
> An open pipeline that goes from the BIM model (IFC) to a BCF discrepancy
> report exchangeable with architects, by way of physical measurement tools
> designed blind-first.

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
> **French regulations** (arrêté of 8 December 2014, RGAA). The pipeline
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

### Software part — `audit_ifc_rgaa.py`, `comparaison_terrain.py`, `bcf_export.py`

- Parses a project's IFC file
- Automatically checks compliance with the requirements of the French arrêté of
  8 December 2014 (doors, stairs, ramps, corridors, sanitary facilities)
- Generates a structured Markdown report readable by screen readers
- Compares declared values against on-site measurements (JSON file)
- Exports discrepancies in the standard BCF 2.1 format, exchangeable with Revit,
  ArchiCAD, BIMcollab, Solibri, BlenderBIM

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
    │  Automated geometric audit against the arrêté of 8 Dec 2014 │
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
clone https://github.com/Youniziak/audit-ifc-rgaa.git
cd audit-ifc-rgaa
pip install -r requirements.txt

Single dependency: IfcOpenShell (LGPL).

## Quick start

### 1. Compliance audit from the BIM model alone

python3 audit_ifc_rgaa.py exemples/test_erp_avec_espaces.ifc

Generates `exemples/test_erp_avec_espaces_audit.md` listing all detected
non-compliances with severity and regulatory article.

### 2. BIM ↔ on-site comparison + BCF export

python3 comparaison_terrain.py exemples/test_house.ifc 
exemples/mesures_exemple.json 
--bcf retours_architecte.bcfzip

Produces the discrepancy report in Markdown and a `.bcfzip` file to hand
directly to the architect.

### 3. Regenerate the test IFC file
python3 generer_exemple_espaces.py

## What is checked (v0.3)

| Element | Check | Article |
| --- | --- | --- |
| Doors | Width ≥ 0.80 m (rooms) or 0.90 m (main ERP) | Art. 10 |
| Doors | Clear height ≥ 2.00 m | Art. 10 |
| Stairs | Tread depth ≥ 0.28 m | Art. 7-1 |
| Stairs | Riser height ≤ 0.16 m | Art. 7-1 |
| Ramps | Slope ≤ 5% normal, 8% tolerated over 2 m | Art. 7-2 |
| Corridors | Width ≥ 1.40 m (1.20 m at a localized narrowing) | Art. 6 |
| Sanitary | Smallest dimension ≥ 1.50 m (Ø 1.50 m turning circle) | Art. 12 |
| Sanitary | Area ≥ 3.00 m² (recommendation) | Art. 12 |

*(Articles refer to the French arrêté of 8 December 2014.)*

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
├── VERSION                      Current version (0.3.0)
├── LICENSE                      GPL-3.0 for the code
├── requirements.txt             Python dependencies
│
├── audit_ifc_rgaa.py            Main module — IFC compliance audit
├── comparaison_terrain.py       BIM ↔ on-site measurement comparison
├── bcf_export.py                BCF 2.1 file generation
├── generer_exemple_espaces.py   Test IFC generation helper
│
├── exemples/                    Demonstration files
│   ├── test_house.ifc           Simple house (1 door)
│   ├── test_erp_avec_espaces.ifc  Fictional ERP (corridors + sanitary)
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
- [ ] v0.4 — Maneuvering spaces, accessible elevators
- [ ] v0.5 — Accessible PDF export (PDF/UA, ISO 14289)
- [ ] v0.6 — Automatic tactile floor-plan generation (STL)
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
  version = {0.3.0},
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



