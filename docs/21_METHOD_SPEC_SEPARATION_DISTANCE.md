# Engineering Method Specification: Separation Distance Engine

- **Document ID**: DOC-METH-001
- **Version**: 1.0.0-draft
- **Status**: Stage 0 Approved Baseline
- **Product Name**: AegisLPS (Provisional Working Title)

---

## 1. Governing Standard Reference
IEC 62305-3:2024 Section 6.3 - Separation distance of the external lightning protection system.

## 2. Mathematical Formulation
The required separation distance $s$ between an LPS conductor and an internal conductive installation or object is calculated as:

$$s = k_i \cdot \frac{k_c}{k_m} \cdot l$$

Where:
- $s$: Required separation distance in meters [m].
- $k_i$: Coefficient depending on the selected class of LPS ($I, II, III, IV$).
- $k_c$: Coefficient depending on the lightning current flowing through the down-conductors (current sharing factor).
- $k_m$: Coefficient depending on the electrical insulating material of the separation medium.
- $l$: Effective path length in meters [m] along the down-conductor from the point where the separation distance is assessed to the nearest equipotential bonding point or earth termination.

## 3. Segment-by-Segment Method
When evaluating non-uniform media or complex geometry with $N$ conductor segments along the critical current path:

$$s(P) = k_i \cdot \sum_{j=1}^{N} \left( \frac{k_{c,j}}{k_{m,j}} \cdot l_j \right)$$

For each segment $j$:
- $l_j$: Spatial length of conductor segment $j$ [m].
- $k_{c,j}$: Local current sharing factor for segment $j$.
- $k_{m,j}$: Insulation factor for the medium adjacent to segment $j$.

## 4. Compliance Check & Safety Margin
For an evaluated target point $P$ with physical spatial clearance $D_{actual}$:
- **Pass Condition**: $D_{actual} \ge s$
- **Safety Margin**: $M_s = D_{actual} - s$ [m]
- **Relative Margin**: $M_{rel} = \frac{D_{actual} - s}{s} \times 100\%$
