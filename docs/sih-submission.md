# SIH 2026 — both entries, and every resource behind them

> **Superseded on 30 September.** SatQuery was dropped and GHOST went to SIH26209; Angaraka was
> submitted to SIH26226. The live state is in [`sih-decision.md`](sih-decision.md). This page is
> the 15 September snapshot, kept for its sources: §5 on ISRO's instruments is the part still used.

Reference document, not a narrative one. It exists so a cold conversation can pick up
either track without re-deriving anything. Written 2026-09-15, the day the idea PPTs are due.

**The thesis that joins them:** a language model decides, a frozen specialist executes, and the
specialist's competence envelope is something the model knows rather than guesses. Reflex Arc is
that architecture pointed at **actuation**. SatQuery is the same architecture pointed at
**perception**. Two submissions, one idea — say so rather than hoping nobody notices.

---

## 1. The two entries

| | Reflex Arc | SatQuery AI |
|---|---|---|
| PS | **SIH26226** (AICTE, Student Innovation) | **SIH26167** (ISRO) |
| Theme | Space Technology | Space Technology |
| Category | **Hardware** | Software |
| Title | Student Innovation — space tech | SatQuery AI — An Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis through Text Queries |
| Ideas submitted (2026-09-15) | 5 / 500 | 11 / 500 |
| Owner for refinement | Abhishek | Ishan |

Status: college nomination done, internal rounds passed. **Only portal submission remains.**

- **PPT idea submission: 15 September 2026 — today.** Drive links inside the PPT are acceptable;
  the demo video can follow.
- Portal-level idea deadline was reported as 30 September. Treat today's as binding.
- The per-PS cap (500) is the reason the counters above matter. Both are far from it, so the
  cap is **not** a live risk — this was checked and closed.

Portal: [sih.gov.in](https://www.sih.gov.in/). The circulating PS PDF has **scrambled theme
labels** (descriptions are correct, labels are not) — verify any theme claim on the portal.

---

## 2. Directories, repos, and what is actually in them

### Reflex Arc — `/home/ishu/Projects/llm_rl`
Remote: `git@github.com:IshuIsAwake/reflex-arc.git`

- **Built through prototype 10**, committed (`58ec3d7`). Hardware seam merged at `3d6b80c`
  — *"Merge Abhishek's rover-link: the route reaches the real motors."* The dummy rover
  follows the exact paths the simulation drives.
- Abhishek's *hardware build* files are still unpushed; the software link is in git.
- Reading order: [`README.md`](../README.md) → [`ROVER.md`](../ROVER.md) →
  [`ARCHITECTURE.md`](../ARCHITECTURE.md) → [`work_division.md`](../work_division.md) →
  [`repo_rules.md`](../repo_rules.md)
- [`prototype10a/DESIGN.md`](../prototype10a/DESIGN.md) — full scope of the current build
- [`docs/pitch.md`](pitch.md) — explains the project from nothing, in eight beats. **PPT source material.**
- [`docs/novelty.md`](novelty.md) — prior art checked against primary sources
- [`docs/sih-decision.md`](sih-decision.md) — how the two entries were chosen (decision now closed)

**Reusable pieces that transfer to SatQuery** (this is the real asset, not GHOST's weights):

| File | What it gives |
|---|---|
| `prototype10a/game/skills.py` | `TOOLS` — 9 tool schemas, strict arg validation, `_stuck` (refuses repeated identical calls) |
| `prototype10a/game/chat.py` | `cut_fabrication`, `clean`, the `Conversation` loop, the `Tape` |
| `prototype10a/game/replay.py` | re-issues recorded tool calls with **no model in the loop** |

`replay.py` is the sleeper asset: a demo that cannot flop, and an auditable execution trace —
which is exactly the language 26167 uses. The reasoning is in DESIGN.md's determinism ledger:
*the model is the only thing in the stack that cannot be pinned, so take it out of the loop.*

### GHOST — `/home/ishu/Projects/AI/GHOST`
Remote: `github.com/IshuIsAwake/GHOST` · PyPI: `pip install ghost-hsi` ·
Site: [anakinskywalker0.github.io/GhostWEB](https://anakinskywalker0.github.io/GhostWEB/)

- **v0.1.7 shipped** (`9b64e83`), tags v0.1.3–v0.1.7. Python 3.9–3.12, Linux/macOS/Windows,
  Cython-compiled wheels, CI via GitHub Actions.
- License is **Proprietary, all rights reserved** — except the DA base commit, relicensed MIT.
- `runs/indian_pines/spt_models.pkl` — **the only trained checkpoint that exists.**
- Docs: `README.md`, `architecture.md`, `API_Reference.md`, `commands.md`, `TODO.md`
- `.notes/context.md` — v2 design (partly stale: `ghost_new/` was abandoned)
- `.notes/s2mamba_protocol.md` — the 50/15 per-class eval protocol

### Ummon / DataAnnotation — `/home/ishu/Projects/AI/da_task`

- Task `ghost-spectral-first-encoder-01`: **done and submitted.** `HANDOFF.md` there is stale
  (it still shows the comparison as outstanding).
- Base commit `9caf442`, tag `v0.1.7-da-base`, MIT, spoilers stripped.
- **Two v0.2.0 implementations exist**, both graded 44/45, neither ever trained:
  - `jobs/gsfe-01-final/…__GAGXxtW/artifacts/patch.diff` — **aenea** (gemini), 1511 lines
  - `jobs/gsfe-01-final/…__ePXpGc8/artifacts/patch.diff` — **scylla** (anthropic), 2173 lines
- **Build on scylla's.** It ships `SpectralResNet1DEncoder` reproducing the existing
  `SpectralSSMEncoder` contract `(B,C,H,W) → (B,channels,H,W)`. aenea's 4-D path returns 5-D
  `(B,channels,Bands,H,W)`, which is not that contract and will fight the rest of the repo.
- **Neither has CRF.** Component D was deliberately cut (`pydensecrf` fails to build on 3.12).
- The ENVI / GeoTIFF / HDF5 support in v0.1.7 came out of these tasks.
- A follow-up "Cython conversion" task was discussed but **never written down anywhere.**
  Argued against: it is verifiable only by building, and building is the flakiest part of that
  environment (940s cold vs a 900s budget, warm-cache dependency, `--no-build-isolation`
  load-bearing, `setup.py`'s `StripAfterCompile` deletes `.py` sources).

---

## 3. Data on disk — this is the "G" evidence

`/home/ishu/Projects/AI/GHOST/data/`

| Dataset | Sensor | Bands | Platform class | State |
|---|---|---|---|---|
| Indian Pines | AVIRIS | 200 | airborne | **trained, checkpoint exists** |
| Salinas | AVIRIS | 204 | airborne | benchmarked v0.1.x |
| Pavia University | ROSIS | 103 | airborne | benchmarked v0.1.x |
| LUSC | pathology | 61 | microscopy | benchmarked v0.1.x |
| Mars CRISM | CRISM TRR3 | 400+ | planetary orbiter | benchmarked v0.1.x |
| AVIRIS-3 L1B (2023) | AVIRIS-3 | 284 | airborne | converted, untrained |
| OHID-1 | Orbita | 32, **10 scenes** 512×512 | spaceborne | 1 of 10 converted, labels present |
| Ryugu | Hayabusa2 | cube | **asteroid** | converted |
| NEON | NEON spectrometer | — | airborne | raw |

Nine sensor families, four platform classes, 32 → 400+ bands, remote sensing *and* planetary
*and* medical. **That is the G — width across sensors, not depth down to three bands.**
"We have run this on an asteroid" is the line that lands with a space judge.

OHID-1 raw (all 10 scenes, `201912_1` … `201912_10`) is at
`data/new_data/hrnavy-OHID-1-220e32e/` with a `labels/` directory.

### Published v0.1.x numbers (README)

| Dataset | Config | OA | mIoU | Kappa | Hardware | Time |
|---|---|---|---|---|---|---|
| LUSC | 32/8 | 99.42% | 0.9263 | 0.9876 | RTX 3050 laptop | 1h 08m |
| Salinas | 32/8 | 98.69% | 0.9577 | 0.9855 | Kaggle T4 | 10h 51m |
| Indian Pines | 64/16 | 98.16% | 0.9071 | 0.9790 | RTX 3050 laptop | 2h 20m |
| Pavia U | 32/8 | 97.47% | 0.9531 | 0.9667 | Kaggle T4 | 7h 29m |
| Indian Pines | 32/8 | **97.20%** | 0.8030 | 0.9681 | RTX 3050 laptop | 1h 17m |
| Mars CRISM | 32/8 | 71.70% | 0.5228 | 0.6829 | Kaggle T4 | 6h 44m |

The 97.20% row is the **reference line** for the v0.2.x comparison.

---

## 4. The "G" question, settled

Three claims wear one letter. Keep them apart:

1. **Code agnosticism** — no dataset-specific code; band/class/spatial dims read at runtime.
   Real, shipped, checkable by a judge in thirty seconds. **This is the strongest asset.**
2. **Band-count agnosticism** — the pipeline *runs* 3–400+. Running is true; *performance*
   below 61 bands has never been measured.
3. **Cross-scene / cross-sensor transfer** — marked "in progress (v0.2.x)". Not achieved.

**Known vulnerability:** `README.md:23` claims "works on 3 to 400+ bands — **Achieved**".
The lowest band count anywhere in the results table is LUSC at 61. An ISRO judge works with
multispectral daily and will point at that row. **Restate as the measured range before submitting.**

### Where low band counts actually break (three specific places)

- **The encoder prunes to nothing.** Receptive field is `(kernel_size - 1) * dilation + 1`.
  At `kernel_size=7, dilation=1` that is **7**. With 3 bands, 7 > 3, so the first block already
  prunes and only a stem survives. `kernel_size=3` (RF = 3) is the minimum that leaves an encoder.
  **Check what both v0.2.0 implementations default to.**
- **CR destroys 2 of 3 dimensions.** Simple mode divides by the line from first band to last,
  so `CR(band_0) = spectrum[0]/spectrum[0] = 1.0` — always, and the same at the last band.
  3 bands → `[1.0, x, 1.0]`, one free parameter out of three. Negligible at 200 bands,
  catastrophic at 3. The `off` threshold should probably be far above `<3`.
- **v0.2.x removed the only component that helped RGB.** Per-pixel with no spatial context is
  exactly wrong for 3 bands — a red roof pixel and a red soil pixel are identical vectors.

**Conclusion: RGB is in-domain for the framework and out-of-domain for the thesis.** It runs,
and classifies about as well as a small MLP on raw RGB. Fix with `kernel_size`, the CR threshold,
and claim-grading — **all parameters, not architecture.**

**Do not build a separate RGB module.** It would destroy code agnosticism, which is the one
claim that can actually be proven.

### Graded claims — the design that falls out

Not binary refusal. GHOST runs whatever band count it is handed (the dumb-policy role, exactly
as in Reflex Arc); the LLM's job is knowing what the sensor *licenses*:

- 200 bands → *"Vegetation, 23.4% of scene, confirmed by chlorophyll red-edge absorption at 700–750 nm."*
- 12 bands → *"Vegetation, 23.4%, consistent with NIR/red band ratio. Material identity not confirmable."*
- 3 bands → *"These regions cluster as vegetation by colour. I cannot confirm material identity without SWIR."*

Same call, same mask, different epistemic claim. It reads on the band count and wavelength range
already preserved in `convert.py`'s `metadata.json` sidecar.

**This is Reflex Arc's "errors are reported, not corrected" transplanted.** The rover says
*you are at (3,3), not where you asked to be.* SatQuery says *this sensor cannot answer that.*
Same principle, both submissions — and it is the direct answer to ISRO's stated anxiety that
*"systems require users to understand satellite-data characteristics, GIS workflows, model
selection, and task-specific parameters."*

**Hard rule: every number is computed, never generated.** Pixel counts come from the mask; the
LLM only routes and narrates around values it was handed. That is the defensible version of the
"zero-fabrication / evidence-grounded" claim the PS asks for.

---

## 5. What 26167 asks for, against what GHOST has

ISRO's background, quoted:

> most existing remote-sensing AI solutions are developed as isolated applications for a single
> predefined task… These systems often require users to understand satellite-data characteristics,
> GIS workflows, model selection, and task-specific parameters.

GHOST's own README: *"point it at a hyperspectral image and get a segmentation map without
writing dataset-specific code."* The same sentence, written independently by two parties.

| ISRO asks for | GHOST today |
|---|---|
| Natural-language query interface | ✗ — build from Reflex Arc's `skills.py` |
| Vision-language model / image–text alignment | ✗ |
| VQA, captioning, grounding | ✗ |
| Change detection, multitemporal | ✗ — nearly free as a diff of two masks |
| SAR, co-registered optical–SAR pairs | ✗ — **cut it, and say why** |
| Land-cover classification / segmentation | ✓ **and differentiated** |
| "may employ multiple specialised models" | ✓ the door we walk through |
| BigEarthNet / VRSBench / RSVQA / CDVQA | ✗ — we are on Indian Pines, Pavia, Salinas, LUSC, CRISM |

**GHOST is ~15–20% of the deliverable.** Nobody should say 60–70% in a room. The accurate
version is stronger: *we own a benchmarked spectral backbone that already runs on planetary
spectrometer data, and we build the language layer on top of it.* Every other team will
fine-tune a CLIP or LLaVA variant. None will have that backbone.

### Datasets: the labels problem has an upstream answer

**BigEarthNet already ships per-pixel reference maps** derived from CORINE Land Cover 2018 —
the headline multi-labels were derived *from* those maps. 12-band Sentinel-2 with real pixel
labels, above the CR floor, enough bands for the encoder to survive, and a dataset ISRO named.
Do **not** derive pixel labels from bounding boxes; that is a research problem, not 17-day work.

Source: [BigEarthNet-S2 description](https://bigearth.net/static/documents/Description_BigEarthNet-S2.pdf) · [bigearth.net](https://bigearth.net/)

### The differentiator: ISRO's own hyperspectral instruments

- **HySIS** — ISRO's hyperspectral satellite, PSLV-C43, 29 Nov 2018. VNIR **60 bands**
  (400–900 nm), SWIR **256 bands** (850–2500 nm), 30 m GSD, 30 km swath, global coverage every
  three months. Squarely GHOST's native band count, and no RGB VLM can touch it.
  [eoPortal](https://www.eoportal.org/satellite-missions/hysis)
  **We do not have HySIS data yet** — Bhoonidhi registration is the only item with external lead time.
  [Bhoonidhi](https://bhoonidhi.nrsc.gov.in/bhoonidhi/home.html) ·
  [API spec](https://bhoonidhi.nrsc.gov.in/bhoonidhi-api/) · `bhoonidhi` on PyPI
- **AVIRIS-NG India campaign** — ISRO–NASA joint HYSI programme, **425 bands at 380–2500 nm**,
  5 nm resolution, flown on **ISRO's own B200 aircraft**, 22,840 km² over 57 sites in 84 days
  (16 Dec 2015 – 6 Mar 2016), from nine airport bases including Ahmedabad and Hyderabad.
  So Indian Pines is not a foreign sensor — **AVIRIS is ISRO's own working hyperspectral family.**
  [Phase 1 overview (vedas.sac.gov.in)](https://vedas.sac.gov.in/aviris/pdf/Overview_AVIRIS_NG_Phase_1_campaign.pdf) ·
  [science plan](https://vedas.sac.gov.in/aviris/pdf/ISRO-NASA_AirborneHySI_science_plan_doc_v3_27SEP15.pdf) ·
  [AVIRIS-NG at JPL](https://avirisng.jpl.nasa.gov/)
- **IIRS on Chandrayaan-2** (0.8–5.0 μm) is the same class of instrument as **Mars CRISM**
  (0.362–3.92 μm), which GHOST has already been benchmarked on. Planetary lineage, already earned.

### Three scenes, three jobs, zero new training

- **Indian Pines is the working demo** — the only checkpoint, and AVIRIS is ISRO's house family.
- **HySIS / IIRS is the scaling claim** — load a cube, show the gate say "in domain", plot a
  spectrum. Do **not** promise segmentation; there are no labels and it cannot be trained in time.
- **An RGB tile is where the gate fires** — you don't need to be good at RGB, you need to
  qualify the claim correctly. That is the most memorable moment in the demo.

### Other teams are already public on 26167

Useful for seeing what the field looks like, and what to differentiate against —
they are all RGB/SAR VLM stacks (Grounding DINO, SAM 2.1, ChangeFormer, BigEarthNet ResNet-50):
[nbsayan7-cell](https://github.com/nbsayan7-cell/SatQuery-AI) ·
[shubh000015](https://github.com/shubh000015/satquery-ai) ·
[KrxnTech/SatVistaar](https://github.com/KrxnTech/SatVistaar-SIH)

---

## 6. The experiment that decides the GHOST pitch

**Not started.** This is the first thing after the PPTs.

**Run one: scylla's v0.2.x on Indian Pines, SPT on, no CRF, 50 samples/class**, against the
97.20% reference line.

Why Indian Pines and not OHID-1: Indian Pines is the **control**. A v0.2.x number there is
directly comparable and isolates what deleting the U-Net costs. OHID-1 has no v0.1.7 baseline,
so a bad number there cannot distinguish cross-scene failure from a broken architecture.
Two questions in dependency order — *is the architecture sound?* then *does it transfer?*

**Cost is small.** 16 classes × 50 samples = 800 training pixels of length 200, no spatial
convolution. Seconds per epoch; under an hour end to end. The 7–10h figure is a **v0.1.x**
property (U-Net over full scenes, 400 epochs, 5 ensembles × SPT nodes). **v0.2.x is cheaper to
validate than v0.1.7 ever was** — a full hyperparameter sweep fits in a day.

**Expected band: roughly 75–85% OA**, reasoning from what spectral-only per-pixel methods
typically reach on Indian Pines versus spatial-spectral ones. Indian Pines is the worst case for
inter/intra-class variance — several classes are corn and soybean at different tillage stages,
near-identical spectrally, historically separated by *spatial* context.

- **75–85% → working correctly.** That gap is the known price of dropping spatial context. Proceed to OHID-1.
- **~40% → something is broken.**
- **~95% → suspect leakage in the split.**

Decide this *before* the number exists, so it doesn't anchor you.

**CRF:** neither implementation has it, and CRF is the designed remedy for exactly the
salt-and-pepper that inter/intra-class variance produces. A no-CRF number is the pessimistic
floor, not a verdict. **Run both arms — the CRF delta is itself the result worth reporting.**
`pydensecrf` fails on 3.12; use [SimpleCRF](https://pypi.org/project/SimpleCRF/) or
`simplecrf-binaries`, or fall back to majority-vote-in-a-window. Do not lose a day to a build.

**Then run two: OHID-1, train on 2 scenes, test on 8** — the cross-scene number nobody else on
26167 will have. Caveat to state out loud: 32 bands is below the 64-band threshold, so it
exercises *simple* CR, not the convex-hull path.

Protocol: `.notes/s2mamba_protocol.md` (50/15 per class). **Check scylla's split matches it** —
if it doesn't, the comparison against v0.1.7 isn't clean and the run has to be redone.

---

## 7. Build order after the PPTs

1. Indian Pines v0.2.x run (§6) — **gates everything**
2. Fix `README.md:23` to the measured range
3. GHOST Python API — Ummon-shaped work. **Return evidence, not pictures**: class→pixel-count,
   per-class confidence, band count and wavelength range used, CR mode selected, raw mask.
   A separate renderer makes the overlay. If the API returns a PNG, the LLM has to *describe an
   image* and the hallucination you designed out comes straight back.
   (GHOST is CLI-only today; a programmatic interface is still "long-term" in `TODO.md`.)
4. Port `skills.py` TOOLS + `cut_fabrication` + the tape. **Three tools only** —
   `segment`, `quantify`, `describe_sensor`.
5. The capability gate / claim-grading. It is a table.
6. Record a tape, verify `replay.py` reproduces it. **That is the demo video.**
7. HySIS cube for the scaling slide — start Bhoonidhi registration early.

---

## 8. Open — genuinely undecided

- **Which model drives the router.** `gpt-oss:120b-cloud` is proven in prototype 10;
  local `gemma4:e4b` would back an "offline-capable" claim, which ISRO values. Deferred by
  Ishan until after the experiment.
- **The fallback if OHID-1 cross-scene comes back bad** (say 60% OA): pitch spectral-first as
  roadmap anyway, or retreat to v0.1.7's proven single-scene numbers and narrow the claim to
  "sensor-agnostic, single-scene"? Deferred until the number exists.
- **GHOST's license.** Still `Proprietary. All rights reserved.` A deliberate choice is needed
  before anyone else builds on it — and before a hackathon submission implies otherwise.
- **Whether the two PPTs cross-reference each other.** The shared thesis is real; whether
  naming it helps or invites a "same project twice" reading is untested.
