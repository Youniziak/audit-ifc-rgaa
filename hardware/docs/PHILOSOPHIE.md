# Philosophy — blind-first universal design

> 🇫🇷 **Version française : [PHILOSOPHIE.md](PHILOSOPHIE.md)**

## The problem

Existing built-environment accessibility auditing tools — rangefinders, levels,
measuring tapes, colorimeters — are designed by sighted people for sighted
people. When an auditor with a visual impairment wants to use them, two options
are available:

1. **Not use them** and delegate measurement to a sighted partner
2. **Adapt them** with makeshift means (third-party voice synthesis, OCR apps
   pointed at the instrument's screen, etc.)

Neither option is satisfactory. The first dispossesses the auditor of the raw
data. The second introduces a layer of improvisation that degrades reliability.

## The proposal

Design tools whose primary interface is **non-visual** and which produce
measurements that are:

- **Announced by voice** (embedded synthesis, no cloud dependency)
- **With vibration feedback** indicating regulatory thresholds
- **Timestamped and signed** for traceability and enforceability
- **Exportable** to the `audit-ifc-rgaa` pipeline (JSON consumed by
  `comparaison_terrain.py`)

These tools remain usable by sighted people — but the reverse is not true. This
is a deliberate and meaningful asymmetry.

## Why not adapt existing tools

Three practical reasons:

1. **Dependency:** a visually impaired auditor cannot depend on a chain whose
   every link is liable to fail (Bluetooth disconnecting, an OCR app misreading
   a digit).
2. **Forensic reliability:** for a measurement to be enforceable in an Ad'AP
   dispute, it must be recorded by the instrument itself, not reconstructed from
   OCR.
3. **Affordability:** an industrial talking laser rangefinder costs €200–400. An
   open-hardware equivalent costs €25 in components. The barrier to entry must
   be low.

## Why not wait for the industry

Because they don't build it. Because the market of visually impaired auditors is
too small to interest them. And because even if it did interest them, the
solutions would be proprietary, closed, and not interoperable with an open BIM
audit pipeline like `audit-ifc-rgaa`.

Open hardware fills exactly this gap.

## Common design principles

All tools in the `hardware/` folder share the following principles:

### User interface

- **Large primary physical button** (≥ 15 mm) easily found by touch, distinct
  from other buttons by its shape or position
- **No critical information in visual form only:** anything shown on screen is
  also announced in audio
- **Distinct vibration feedback** for regulatory thresholds (for example: 1
  short vibration = compliant, 3 long vibrations = blocking non-compliance)
- **Local French neural voice** (Piper TTS, fr_FR-siwis-medium or equivalent)
  embedded — no network dependency

### Connectivity

- **USB-C** for power and data transfer
- **Bluetooth Low Energy** optional, for pairing with a smartphone
- **Local storage** of measurements (microSD card or internal flash) with JSON
  export conforming to the `mesures_exemple.json` format

### Mechanics

- **3D-printable enclosure** (PETG or PLA, requiring no exotic material) with
  differentiating tactile textures
- **Grip** adapted for one-handed use, the other hand often being occupied by
  the white cane or a wall reference point

### Power

- **Rechargeable LiPo battery**, USB-C, minimum 8 h of intensive-use autonomy
- **Status LED** paired with periodic audio feedback indicating remaining
  battery life

### Identity

- **Unique serial number** physically engraved and stored in EEPROM
- **Cryptographic timestamp** (RFC 3161 or chained SHA-256 hash) for each
  exported measurement — legal enforceability

## Reuse

Any individual, association or company is authorized to manufacture these tools
according to the provided design files. The only constraints:

- Credit the origin of the design (CERN-OHL-P v2 requires passing on modified
  design files)
- Do not use the registered trademark name (Exylia Project) without agreement

## Link with the overall strategy

These devices are not an end in themselves. They are the **field building
block** of a larger pipeline:
