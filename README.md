# tianci-paradigm

**An importable implementation of the TianCi Paradigm (天赐范式) operator-stream technical signature.**

Turns the operator-stream signature accumulated on Days 102 / 115 / 124 / 152 / 188–190 from
"an article you can only read" into "a Python package you can import, call, and audit".
This package is the concrete fix for **carrier mismatch (AP-1)**, as argued in Day 190
*Reverse Plan v1.0*.

> **Language note.** This file is the English entry point. The Chinese version is
> [`README_CN.md`](README_CN.md). Everything under `specs/`, `known-gaps.md` and
> `CHANGELOG.md` is **written in Chinese** and stays that way for now — the code
> docstrings and specs are not translated. If you do not read Chinese, this README and
> the source code are sufficient to install and call the package; consult the spec
> documents with a translation tool.

## Repository and single source of truth

- **Canonical**: <https://github.com/windsnowmichael/tianci-framework>
- **Mirrors (distribution copies, NOT sources of truth)**:
  - AtomGit: <https://atomgit.com/gcw_lwUf3sWj/tianci-framework>
  - Gitee: <https://gitee.com/windsnowmichael/tianci-framework>
- All commits, issues and releases are governed by the canonical repository. The mirrors
  exist for distribution only. **"Three equal repositories" is explicitly rejected** —
  that would be three competing sources of truth.
- **Lineage**: this package succeeds the Day 31 (2026-05-04) `tianci-framework` repository
  (19+ native operators). The old repository is archived and points here. Two installable
  "sources of truth" are deliberately not maintained.

## What is inside

- **Five-part operator contract** — input domain / output domain / preconditions /
  postconditions / side effects, enforced by the `Operator` dataclass. A missing part is
  reported, not silently tolerated.
- **Operator registry** — all 128 operators documented in v7.0 are registered; **25 carry
  a complete contract. Coverage: 19.5%** (stated as-is, not rounded up).
- **Nine-step inference protocol** (Day 124): Θ→Ξ→Θ→Γ→Σ→Λ→τ→R→Ψ, with thresholds 0.3/0.6
  and executable rules for shortcuts, three consecutive reds, and DAG cycles.
- **Seven-organ dynamic runtime** (Day 152): Diode#96 / Φ gate / Amp#95 / R_Lagrange /
  Λ_Bombe / Meta#97 / Portrait#98 — one heartbeat is one complete processing pass.
- **Three domains, zero coupling**: weather / finance / gene adapters; the same machine
  ingests all three; cross-domain warm-start migration; Abel duality check
  `[Θ_ext, Θ_int] ≠ 0`.
- **Terminology anchor table**: 26 bilingual terms with unique IDs, preventing
  same-name-different-meaning collisions (AP-3).
- **No third-party core**: the core runtime depends only on the Python standard library;
  numpy/matplotlib are imported lazily, and only for visualisation.

## Install

```bash
# From the canonical repository (main branch)
pip install "git+https://github.com/windsnowmichael/tianci-framework.git@main"

# Or from a mirror
pip install "git+https://gitee.com/windsnowmichael/tianci-framework.git@main"

# Or: download the wheel from the GitHub Releases page and install it
pip install tianci_paradigm-0.2.0-py3-none-any.whl

# Or: use the source tree directly, no install needed
cd tianci-paradigm && python -c "import tianci; print(tianci.__version__)"
```

> Not published on PyPI yet — `pip install tianci-paradigm` does **not** work today.

## Quick start

```python
from tianci import (
    TianCiRuntime, Observation, run_nine_steps,
    run_heartbeat_with_protocol, default_registry, route,
)

# 1) One runtime, one heartbeat
rt = TianCiRuntime()
out = rt.heartbeat(Observation(
    label="weather/Beijing",
    values=[36.5, 0.45, 12.0, 2.3],
    metadata={"is_rain": True, "is_high_temp": True},
))
print(out["transmitter_triggered"])   # whether the transmitter fired

# 2) Nine-step inference protocol
verdict = run_nine_steps(
    {"f_Θ": 0.8, "f_Γ": 0.6, "f_Σ": 0.8},
    raw_input="...",
)
print(verdict["tau"], verdict["L"], verdict["R_state"])

# 3) Heartbeat stitched to the protocol
flow = run_heartbeat_with_protocol(
    Observation(label="gene/BRCA1", values=[55.0, 5.592, 8.0, 70.0])
)
print(flow["verdict"]["psi"])

# 4) Registry and glossary
reg = default_registry()
print(len(reg.full_contracts()))      # 25
from tianci import glossary
print(glossary.lookup("TC-SYS-003")["en"])   # warm start
```

More examples in [`examples/`](examples/).

## Layout

```
tianci-paradigm/
├── tianci/
│   ├── operator.py      # Operator dataclass (11 fields + five-part contract)
│   ├── registry.py      # registry (reads data/registry.json + audit)
│   ├── data/registry.json  # single source of truth for operators (extracted from v7.0)
│   ├── protocol.py      # Day 124 four modules, nine steps
│   ├── runtime.py       # Day 152 seven-organ runtime
│   ├── runtime_v2.py    # three-domain adapters + warm start + Abel + visualisation
│   ├── flow.py          # heartbeat/protocol stitching
│   ├── dag_route.py     # Day 102 DAG decision tree
│   ├── glossary.py      # 26 bilingual term anchors
│   ├── existence.py     # Day 138 existence check + existence fuse (v0.2)
│   ├── genome.py        # Day 172 genome persistence (v0.2)
│   ├── cp.py            # Day 92/93 TDP-CP six-step inference (v0.2)
│   ├── drr.py           # Day 94 DRR-R rupture-segment redirection (v0.2)
│   └── consciousness.py # Day 141 self-reference + triple gate (v0.2)
├── specs/               # technical signature / lineage / anti-patterns / handbooks (Chinese)
├── examples/            # minimal + cross-domain examples
├── tests/test_coldstart.py  # T1 cold-start test (AP-4 evidence)
├── known-gaps.md        # contract gaps and coverage wording (19.5%)
├── CHANGELOG.md         # version history (v0.1.0 → v0.2.0)
└── pyproject.toml
```

## Openness and module maturity

Every module is open. Maturity is labelled; no access gate is set.

| Layer | Modules | maturity | Note |
|---|---|---|---|
| L1 public | `registry` / `operator` / `flow` / `dag_route` / `glossary` | `stable` | semantics frozen, safe to depend on |
| L2 runtime | `runtime_v2` / `cp` / `drr` / `protocol` | `stable` | inference protocol |
| L3 life | `existence` / `genome` / `consciousness` | `experimental` | **equally open, equally callable**; semantics still evolving, outside partners are welcome to push it forward |

> `existence` / `genome` / `consciousness` are marked `experimental` — they are **not a
> complete form yet**, but they are worth borrowing from: external partners may freely
> call, modify and feed back.
> This package makes **no claim that consciousness or life has been realised**. It offers a
> **mechanism that can keep being pushed**.

## Documentation (Chinese)

- [`specs/operator-stream.md`](specs/operator-stream.md) — operator-stream technical signature
- [`specs/whitepaper-lineage.md`](specs/whitepaper-lineage.md) — document lineage and milestones
- [`specs/anti-patterns.md`](specs/anti-patterns.md) — AP-1…AP-6 anti-pattern list
- [`specs/abel-handbook.md`](specs/abel-handbook.md) — Abel criterion handbook (v0.2)
- [`specs/community-arc.md`](specs/community-arc.md) — community arc node registry (v0.2)
- [`specs/drr-r.md`](specs/drr-r.md) — DRR-R rupture-segment redirection spec (v0.2)
- [`known-gaps.md`](known-gaps.md) — known gaps (the honest 19.5% coverage wording)
- [`CHANGELOG.md`](CHANGELOG.md) — version history

## Tests

```bash
# T1 cold-start test: simulates an unfamiliar agent calling the package unaided
python tests/test_coldstart.py

# Pre-push cross-check: version / coverage wording / bilingual terms consistent throughout
python scripts/check_consistency.py
```

Pass criterion: finished independently and reproducibly. Fail criterion: asking "what does
this mean", guessing, or copying the example back as the answer. See AP-4 in
[`specs/anti-patterns.md`](specs/anti-patterns.md).

## Honesty constraints (hard rules for this repository)

- Contract coverage is always stated as **19.5%** (25/128). Never 20% or higher.
- Thresholds 0.3/0.6 come from theoretical derivation and are **not empirically calibrated**;
  this is noted in the protocol docs and in code comments.
- Terms always use their unique ID (`glossary.py`); bare same-name concepts are forbidden.
- No platform login state, no scraping, no fabricated data. This package implements the
  technical signature; it does not act on your behalf on any platform.
- Version, coverage, terminology and acceptance wording are verified by
  `scripts/check_consistency.py` (including the 11 E-section checks and cross-process revival).

## License

[Mulan Permissive Software License, Version 2 (MulanPSL2)](LICENSE) — the same license as
the Day 31 `tianci-framework` repository root (single source of truth, established
2026-05-04, reconfirmed by audit on 2026-10-10).

---

TianCi Paradigm (天赐范式). Operator-stream technical signature, implemented.
Contract coverage 19.5% (25/128, stated as-is).
