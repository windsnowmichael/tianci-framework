# TianciNS-JSC: Operator-Based Navier-Stokes Solver with Extrapolation Tower

**Tianci Paradigm** — Axiom-Driven Operator Architecture for Computational Fluid Dynamics

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![C++](https://img.shields.io/badge/C++-17-blue.svg)]()
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)]()

## Overview

This repository contains the source code accompanying the manuscript submitted to **Journal of Scientific Computing (JSC)**. The code implements a novel axiom-driven operator framework for solving the 2D incompressible Navier-Stokes equations, featuring an **Extrapolation Tower** (multi-level Richardson extrapolation) for systematic grid convergence.

### Key Features

- **Extrapolation Tower**: Multi-level Richardson extrapolation from 128 to 512 grids, with cloud memory inter-level coordination
- **Operator Self-Decision Pipeline**: All operators are always online; execution operators are physics-triggered, not step-driven
- **15+ Core Operators**: Monitor committee (Xi, Sigma, Lambda, Phi, Psi, VortLoc, EnergyBudget) + Execution pipeline (Rain, MAC, Boundary correction)
- **Triple-Track RAIN Trigger**: Energy / PhaseLock / Gamma parallel tracks with dual-gating (absolute threshold + cooldown)
- **Cloud Memory**: Cross-level state transfer with vortex-center drift-adaptive update intervals
- **Ghia Benchmark Validation**: Lid-driven cavity at Re=100, 400, 1000

## Mathematical Framework

### Governing Equations

The solver addresses the 2D incompressible Navier-Stokes equations in vorticity-streamfunction form:

```
dw/dt + u * grad(w) = (1/Re) * laplacian(w)
laplacian(psi) = -w
u = dpsi/dy,  v = -dpsi/dx
```

### Five Axioms

The operator architecture is grounded in five axioms that guarantee convergence:

1. **[Xi, Lambda] = 0**: Anchor operator commutes with deviation warning — anchoring does not interfere with instability detection
2. **[Gamma, Sigma] = 0**: Variable-coefficient Poisson commutes with uncertainty — Gamma preconditioning does not mask model error
3. **Energy Closed-Loop**: Rain energy is accounted for; no energy is created or destroyed by stabilization
4. **Sigma 3-Component Clip**: Uncertainty is bounded by data/model/shock components independently
5. **Phi Triple-Gate Consensus**: Stabilization (RAIN) requires consensus from ZFC compliance, non-CH anomaly, and Phi gating

### Operator Set

| Symbol | Name | Type | Function |
|--------|------|------|----------|
| Xi | AnchorOp | Monitor | Boundary anchoring + deviation computation |
| Theta | GradientOp | Monitor | Velocity gradient reconstruction (2nd-order) |
| Gamma | GTRPoissonOp | Execution | Variable-coefficient Poisson + MAC projection |
| Sigma | SpectralOp | Monitor | 3-component uncertainty (data/model/shock) |
| Lambda | GlobalOp | Monitor | Deviation warning (L0/L1/L2 levels) |
| Phi | PhiGate | Monitor | Triple-gate convergence detection |
| Psi | ReconstructOp | Monitor | Field reconstruction + dt suggestion |
| Tau | RollbackOp | Execution | State rollback on instability |
| VortLoc | VortLocOp | Monitor | Vortex-center tracking + drift rate |
| EnergyBudget | EnergyBudgetOp | Monitor | Rain energy closed-loop accounting |
| RAIN | RainOp | Execution | Stabilization via vortex perturbation |
| MAC | MACProjection | Execution | Divergence-free correction |
| DRI | BoundaryOp | Execution | Thom/Briley boundary condition |
| RK4 | TimeOp | Execution | 4th-order Runge-Kutta time stepping |
| Interp | InterpolationOp | Execution | Inter-level field interpolation |

### Extrapolation Tower

The tower runs sequential levels: **128 -> 256 -> 512** grid resolution.

- Each level runs to steady-state convergence with operator self-decision pipeline
- Cloud memory transfers converged state to the next finer level
- Vortex-center drift-adaptive intervals control memory update frequency
- Richardson extrapolation combines multi-level results for improved accuracy

## Repository Structure

```
TianciNS-JSC/
├── src/
│   ├── Tianci_NSDT_Tower_v2.6_JSC.cpp   # Main solver: Extrapolation Tower v2.6
│   ├── Tianci_NS80000.cpp                # Legacy: 80000-step single-level solver
│   ├── tianci_256.cpp                    # Legacy: 256x256 grid version
│   ├── tianci_257.cpp                    # Legacy: 257x257 grid version
│   ├── tianci_258.cpp                    # Legacy: 258x258 grid version
│   └── tianci_QDXPC.cpp                  # Legacy: QDXPC variant
├── tests/
│   ├── verify_256.py                     # 256x256 Ghia benchmark verification
│   ├── verify_257.py                     # 257x257 verification
│   ├── verify_258.py                     # 258x258 verification
│   └── verify_medal.py                   # Medal accuracy verification
├── data/
│   ├── operator_log_256.txt              # Operator execution logs
│   ├── operator_log_257.txt
│   ├── operator_log_258.txt
│   ├── u_centerline_256.txt              # Velocity centerline profiles
│   ├── u_centerline_257.txt
│   └── u_centerline_258.txt
├── CMakeLists.txt                        # CMake build configuration
├── run_all.bat                           # Windows batch: compile + run Re=100,400,1000
├── requirements.txt                      # Python dependencies for verification
├── LICENSE                               # MIT License
└── README.md                             # This file
```

## Build and Run

### Prerequisites

- C++17 compatible compiler (GCC 8+, MSVC 2017+, Clang 7+)
- Python 3.8+ (for verification scripts)
- NumPy, Matplotlib (for plotting)

### Quick Start (Windows)

```batch
run_all.bat
```

This compiles and runs the tower for Re=100, 400, 1000 sequentially.

### Manual Compilation

**GCC (Linux/MinGW):**
```bash
g++ -O3 -std=c++17 -Wl,--stack,134217728 -o tower_v26 src/Tianci_NSDT_Tower_v2.6_JSC.cpp
./tower_v26 --Re 100
```

**CMake:**
```bash
mkdir build && cd build
cmake ..
make
./TianciNS_Tower_v26 --Re 100
```

### Command-Line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--Re` | 100 | Reynolds number (supported: 100, 400, 1000) |

### Output

Results are saved to `results/Re{N}/` directories containing:
- `convergence_log.txt` — Iteration-by-iteration convergence metrics
- `u_centerline.txt` — Horizontal velocity along vertical centerline
- `v_centerline.txt` — Vertical velocity along horizontal centerline
- `operator_log.txt` — Operator activation and trigger history

## Verification

Verify results against the Ghia et al. (1982) benchmark:

```bash
python tests/verify_256.py
python tests/verify_medal.py
```

## Citation

If you use this code in your research, please cite:

```bibtex
@article{tianci_jsc_2026,
  title={Axiom-Driven Operator Architecture for the Navier-Stokes Equations:
         Convergence Guarantees and Extrapolation Tower},
  author={TianCi Paradigm Research Team},
  journal={Journal of Scientific Computing},
  year={2026},
  note={Under review}
}
```

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Changelog

### v2.6 (2026-06-17)
- Extrapolation Tower: 128 -> 256 -> 512 multi-level Richardson extrapolation
- Cloud memory with vortex-center drift-adaptive update intervals
- Triple-track RAIN trigger with dual-gating (v2.6.2 fix)
- All Chinese comments translated to English for JSC compliance

### v2.5
- Operator self-decision pipeline: removed EvolutionStage enum
- Physics-triggered execution (not step-driven)
- MAC projection driven by divergence residual
- Sigma 3-component clip model

### v1.0
- Initial release: 15-operator architecture
- Single-level solver at 256x256, 257x257, 258x258 grids
- Ghia benchmark validation (0.996 medal accuracy)
