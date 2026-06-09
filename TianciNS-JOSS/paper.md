---
title: "A Deterministic Bias Verification Tool for Vorticity-Streamfunction Solvers"
tags:
  - computational-fluid-dynamics
  - numerical-verification
  - navier-stokes
  - open-source
authors:
  - name: Huan Wang
    orcid: 0000-0000-0000-0000
    affiliation: 1
affiliations:
  - name: Independent Researcher
    index: 1
date: 9 June 2026
bibliography: paper.bib
---

# Summary

This is an open-source verification tool for detecting and correcting deterministic grid-dependent bias in vorticity-streamfunction lid-driven cavity flow solvers. The tool implements an operator-based framework for solving the 2D incompressible Navier-Stokes equations and includes automated verification scripts for benchmarking against the Ghia reference data.

During the development and application of this verification tool, we discovered a deterministic numerical phenomenon: the maximum deviation from the Ghia benchmark exhibits an exact algebraic formula $\text{Deviation}(N_y) = (N_y-2)/(N_y-1)$, where $N_y$ is the grid dimension. This bias is predictable, reproducible, and exactly correctable by the factor $(N_y-1)/(N_y-2)$.

The tool provides:
- Multiple grid resolution support (256×256, 257×257, 258×258)
- Standard RK4 time integration with Poisson substeps
- Automated Ghia benchmark verification scripts
- Cross-code reproducibility testing framework
- Complete operator monitoring and logging system

# Statement of Need

Numerical verification in computational fluid dynamics (CFD) has traditionally focused on achieving increasingly close agreement with benchmark data, treating residual discrepancies as random numerical noise or incomplete convergence. This tool addresses a critical gap in CFD verification by demonstrating that some discrepancies are not random, but deterministic and exactly predictable.

The core contributions of this verification tool are:

1. **Algebraic Generalization**: The tool reveals that the grid-dependent bias follows an exact mathematical formula $(N_y-2)/(N_y-1)$ for any integer $N_y > 2$, which was predicted prior to experimental verification.

2. **Three-Mesh Zero-Error Verification**: Pre-experiment predictions for 257×257 and 258×258 meshes (based on the 末-digit pattern from 256×256) were verified with zero deviation between prediction and measurement across all three mesh sizes.

3. **Cross-Code Bit-Identical Reproducibility**: Two independent implementations (NS80000 and QDXPC) produced bit-identical outputs at every printed line over 80,000 timesteps, confirming both the deterministic nature of the bias and the exactness of the correction factor.

This tool is particularly valuable for:
- CFD researchers validating vorticity-streamfunction solvers
- Numerical analysts studying discretization errors
- Software developers requiring reproducibility verification
- Educators demonstrating numerical verification concepts

The complete source code, experimental data, and verification scripts are openly available at three repositories (GitHub, Gitee, AtomGit) for independent verification and educational use.

# References
