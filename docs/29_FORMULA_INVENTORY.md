# Formula Inventory

- **Document ID**: DOC-FORM-001
- **Version**: 1.0.0-prototype
- **Status**: Implemented Engineering Prototype
- **Product Name**: AegisLPS (Provisional Working Title)

## 1. Separation Distance Equation
Governing Equation:
$$s = k_i \cdot \frac{k_c}{k_m} \cdot l$$

Where:
- $s$: Required separation distance [m]
- $k_i$: LPS Class coefficient ($0.08, 0.06, 0.04$)
- $k_c$: Current sharing factor derived from conductor topology or graph admittance matrix
> **UNVERIFIED — known defect (H1):** `separation.py` sets `kc` from `len(project.segments)` (`1.0` for `<= 1` segment, `0.5` otherwise) rather than conductor topology or the nodal admittance matrix and uses `assoc_node.z` instead of route length `l`.
- $k_m$: Insulating material factor ($1.0$ for air, $0.5$ for solid concrete)
- $l$: Spatial route length along conductor to nearest earth or equipotential bonding point [m]

## 2. Nodal Current Admittance System
$$\mathbf{Y} \cdot \mathbf{V} = \mathbf{I}$$

Where $\mathbf{Y}$ is the sparse nodal conductance matrix, $\mathbf{I}$ is the lightning impulse current injection vector, and $\mathbf{V}$ is the solved node potential vector.
