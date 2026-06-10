# TianciNS-CF: Operator-Based Navier-Stokes Solver

**Tianci Paradigm** - A Novel Operator-Resonance Framework for Computational Fluid Dynamics

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![C++](https://img.shields.io/badge/C++-17-blue.svg)]()
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)]()

## Overview

This repository contains the source code accompanying the manuscript submitted to **Computers & Fluids**. The code implements a novel operator-based framework for solving the 2D incompressible Navier-Stokes equations using the vorticity-streamfunction formulation.

### Key Features

- **Operator Resonance Architecture**: 15 specialized operators working in concert
- **Multiple Grid Resolutions**: Support for 256×256, 257×257, and 258×258 grids
- **Standard RK4 Time Integration**: True 4th-order Runge-Kutta with Poisson substeps
- **Adaptive Stability Control**: Λ-alert, Ξ-rollback, and Φ-gate convergence detection
- **Ghia Benchmark Validation**: Achieves 0.996 medal accuracy against Ghia et al. (1982)
- **Deterministic Bias Discovery**: Exact formula for grid-dependent bias

## Mathematical Framework

### Governing Equations

The solver addresses the 2D incompressible Navier-Stokes equations in vorticity-streamfunction form:

```
∂ω/∂t + u·∇ω = (1/Re)∇²ω
∇²ψ = -ω
u = ∂ψ/∂y, v = -∂ψ/∂x
```

### Key Discovery

During the development of this solver, we discovered a deterministic grid-dependent bias phenomenon:

- **Bias Formula**: `Deviation(Ny) = (Ny-2)/(Ny-1)`
- **Correction Factor**: `Correction(Ny) = (Ny-1)/(Ny-2)`
- **Three-Mesh Verification**: Pre-experiment predictions verified with zero error
- **Cross-Code Reproducibility**: Bit-identical outputs from two independent implementations

### Operator Set

The framework implements 15 core operators:

1. **VEL** - Velocity field update
2. **BC** - Boundary condition enforcement
3. **RK4** - Standard RK4 time stepping
4. **POISSON** - Conjugate gradient Poisson solver
5. **Σ** - FFT spectral analysis
6. **V1** - Field variation monitor
7. **V2** - Curvature monitor
8. **Ι** - Topology change detector
9. **MΣ** - Statistical moment monitor
10. **RHO** - Boundary relaxation coefficient
11. **LAMBDA** - Adaptive parameter update
12. **TAU** - Time step adjustment
13. **XI** - State save/rollback
14. **Φ** - Convergence gate
15. **VERIFY** - Result verification

## Repository Structure

```
TianciNS-CF/
├── src/
│   ├── Tianci_NS80000.cpp      # Main solver (80000 timesteps)
│   ├── tianci_256.cpp           # 256×256 grid version
│   ├── tianci_257.cpp           # 257×257 grid version
│   ├── tianci_258.cpp           # 258×258 grid version
│   └── tianci_QDXPC.cpp         # QDXPC variant
├── tests/
│   ├── verify_256.py            # 256×256 verification
│   ├── verify_257.py            # 257×257 verification
│   ├── verify_258.py            # 258×258 verification
│   └── verify_medal.py          # Medal verification
├── data/
│   ├── operator_log_*.txt       # Operator monitoring logs
│   └── u_centerline_*.txt       # Centerline velocity profiles
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Building from Source

### Prerequisites

- C++ compiler with C++17 support (GCC 7+, Clang 5+, MSVC 2017+)
- CMake 3.10+ (optional, for build system)
- Python 3.8+ (for verification scripts)

### Compilation

**Using g++ (simple):**
```bash
g++ -O3 -std=c++17 -o TianciNS_256 src/tianci_256.cpp -lm
```

**Using CMake:**
```bash
mkdir build && cd build
cmake ..
make -j4
```

### Running the Solver

```bash
# Run 256×256 grid simulation
./TianciNS_256

# Run main 80000-step simulation
./TianciNS_80000
```

### Verification

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run verification for 256×256 grid
python tests/verify_256.py
```

## Benchmark Results

### Lid-Driven Cavity Flow (Re = 100)

| Grid Size | Predicted Deviation | Measured Deviation | Error |
|-----------|---------------------|--------------------| ------|
| 256×256   | 254/255             | 0.996078431372549  | 0.0   |
| 257×257   | 255/256             | 0.99609375         | 0.0   |
| 258×258   | 256/257             | 0.9961089494163424 | 0.0   |

All three predictions match measurements exactly to machine precision.

## Physical Interpretation

All operators in this framework are designed with clear physical mappings:

- **V1**: Measures temporal variation of the vorticity field
- **V2**: Quantifies spatial curvature (Frobenius norm of Hessian)
- **Σ**: High-frequency energy ratio (spectral analysis)
- **Ι**: Topology change indicator (vorticity sign changes)
- **MΣ**: Statistical stability measure (standard deviation evolution)

## Code Repositories

The complete source code is available at three repositories for redundancy and accessibility:

- **GitHub**: https://github.com/windsnowmichael/tianci-framework
- **Gitee**: https://gitee.com/windsnowmichael/tianci-framework
- **AtomGit**: https://atomgit.com/gcw_lwUf3sWj/tianci-framework

## Citation

If you use this code in your research, please cite:

```bibtex
@article{wang2026cf,
  title={A Deterministic Grid-Dependent Bias in Vorticity-Streamfunction Solvers: Observation, Model, and Exact Correction},
  author={Huan Wang},
  journal={Computers \& Fluids},
  year={2026},
  note={Submitted}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## Acknowledgments

- Ghia et al. (1982) for the benchmark data
- The computational fluid dynamics community

## Contact

**Author**: Huan Wang  
**Email**: 1239574697@qq.com  
**Affiliation**: Independent Researcher

For questions and issues, please open an issue on GitHub or contact the author.

---

**Note**: This code is released as part of a Computers & Fluids submission. The theoretical framework and mathematical derivations are detailed in the accompanying manuscript.
