# TianciNS: A Deterministic Bias Verification Tool for Vorticity-Streamfunction Solvers

**Tianci Paradigm** - Open-Source Verification Framework for Computational Fluid Dynamics

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![C++](https://img.shields.io/badge/C++-17-blue.svg)]()
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)]()

## Overview

This is an open-source verification tool for detecting and correcting deterministic grid-dependent bias in vorticity-streamfunction lid-driven cavity flow solvers. The tool implements an operator-based framework for solving the 2D incompressible Navier-Stokes equations and includes automated verification scripts for benchmarking against the Ghia reference data.

This repository contains the source code accompanying the manuscript submitted to **Journal of Open Source Software (JOSS)**.

### Key Features

- **Deterministic Bias Detection**: Identifies exact grid-dependent bias formula `(Ny-2)/(Ny-1)`
- **Universal Correction Factor**: Provides exact correction `(Ny-1)/(Ny-2)`
- **Multiple Grid Resolutions**: Support for 256×256, 257×257, and 258×258 grids
- **Automated Verification**: Python scripts for Ghia benchmark validation
- **Cross-Code Reproducibility**: Bit-identical outputs from independent implementations

## Mathematical Framework

### Governing Equations

The solver addresses the 2D incompressible Navier-Stokes equations in vorticity-streamfunction form:

```
∂ω/∂t + u·∇ω = (1/Re)∇²ω
∇²ψ = -ω
u = ∂ψ/∂y, v = -∂ψ/∂x
```

### Key Discovery

During the development of this verification tool, we discovered a deterministic grid-dependent bias phenomenon:

- **Bias Formula**: `Deviation(Ny) = (Ny-2)/(Ny-1)`
- **Correction Factor**: `Correction(Ny) = (Ny-1)/(Ny-2)`
- **Three-Mesh Verification**: Pre-experiment predictions verified with zero error
- **Cross-Code Reproducibility**: Bit-identical outputs from two independent implementations

## Repository Structure

```
TianciNS-JOSS/
├── src/
│   ├── Tianci_NS80000.cpp      # Main solver (80000 timesteps)
│   ├── tianci_256.cpp           # 256×256 grid version
│   ├── tianci_257.cpp           # 257×257 grid version
│   ├── tianci_258.cpp           # 258×258 grid version
│   └── tianci_QDXPC.cpp         # QDXPC variant for cross-validation
├── tests/
│   ├── verify_256.py            # 256×256 verification
│   ├── verify_257.py            # 257×257 verification
│   ├── verify_258.py            # 258×258 verification
│   └── verify_medal.py          # Medal verification
├── data/
│   ├── operator_log_*.txt       # Operator monitoring logs
│   └── u_centerline_*.txt       # Centerline velocity profiles
├── paper.md                     # JOSS paper
├── paper.bib                    # Bibliography
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Installation

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

## Usage

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

## Code Repositories

The complete source code is available at three repositories for redundancy and accessibility:

- **GitHub**: https://github.com/windsnowmichael/tianci-framework
- **Gitee**: https://gitee.com/windsnowmichael/tianci-framework
- **AtomGit**: https://atomgit.com/gcw_lwUf3sWj/tianci-framework

## Citation

If you use this software in your research, please cite:

```bibtex
@article{Wang2026,
  author = {Huan Wang},
  title = {A Deterministic Bias Verification Tool for Vorticity-Streamfunction Solvers},
  journal = {Journal of Open Source Software},
  year = {2026},
  volume = {1},
  number = {1},
  pages = {1},
  doi = {10.21105/joss.00000}
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

**Note**: This code is released as part of a JOSS submission. The software provides a verification tool for CFD solvers with demonstrated reproducibility and exact numerical predictions.
