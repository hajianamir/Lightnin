# ADR-003: Graph-Based Current-Sharing Solver Formulation

- **Status**: Approved
- **Date**: 2025-05-15
- **Deciders**: Electrical Network Engineer, Computational Geometry Engineer

## Context
Calculating the lightning current distribution ($k_c$) across meshed down-conductor networks requires a mathematically rigorous graph solver.

## Decision
Represent the conductor network as a directional graph $G=(V, E)$. NetworkX will manage graph topology, connectivity validation, and loop detection. The sparse admittance system $Y \cdot V = I$ will be solved using `scipy.sparse.linalg` to evaluate current distribution and current-sharing factors ($k_c$).
