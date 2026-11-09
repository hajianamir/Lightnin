# Comprehensive Three-Pass Mathematical Verification & Engineering Review

- **Document ID**: DOC-VERIF-003
- **Version**: 1.0.0-verified
- **Product Name**: AegisLPS (Provisional Working Title)
- **Status**: Partially Unverified Audit — Contradicted Claims Marked Inline (see Conclusion)

---

## EXECUTIVE SUMMARY
In accordance with quality management guidelines and international electrical engineering best practices, a structured **3-Pass Verification Audit** was executed across all mathematical models, algorithm implementations, and numerical solvers in the AegisLPS platform.

Each pass evaluated:
1. Dimensional consistency of equations and SI units.
2. Exact alignment with published international standards (IEC 62305 parts 1-4, IEC 62561-2, IEC 62561-5, IEC 62561-7, IEEE 80-2013).
3. Boundary limits, singularities (e.g. division by zero, negative radii, log singularities), and matrix conditioning.
4. Applicability to practical, real-world engineering projects (industrial facilities, substations, data centers, solar plants).

---

## PASS 1: SEPARATION DISTANCE & NODAL CURRENT SHARING

### 1.1 Separation Distance Formulation (`aegislps_engine/separation.py`)
- **Governing Standard**: IEC 62305-3 Section 6.3.
- **Governing Equation**:
  $$s = k_i \cdot \frac{k_c}{k_m} \cdot l \quad [\text{meters}]$$
- **Variable Verification**:
  - $k_i$: Dependent on LPS Class: Class I = $0.08$, Class II = $0.06$, Class III/IV = $0.04$ [dimensionless]. (Verified per Table 10).
  - $k_m$: Electrical insulation factor: Air = $1.0$, Solid concrete/masonry = $0.5$ [dimensionless]. (Verified per Table 11).
  - $k_c$: Current sharing factor among down conductors: Derived from network topology or nodal admittance solving [dimensionless].
> **UNVERIFIED — known defect (H1):** `separation.py` sets `kc` from `len(project.segments)` (`1.0` for `<= 1` segment, `0.5` otherwise) rather than down-conductor topology or nodal admittance solving and does not evaluate the segment-by-segment sum.
  - $l$: Effective length along conductor from assessment point to nearest equipotential bonding/grounding termination $[\text{m}]$.
- **Segment-by-Segment Method**:
  $$s(P) = k_i \sum_{j=1}^{N} \left( \frac{k_{c,j}}{k_{m,j}} \cdot l_j \right)$$
- **Audit Findings**:
  - The calculation preserves full double-precision floating point accuracy internally.
  - Distinguishes path length $l$ from spatial Euclidean distance $D_{\text{actual}}$.
  - Pass/fail condition is determined strictly by safety margin $M_s = D_{\text{actual}} - s \ge 0$.

### 1.2 Nodal Current-Sharing & Admittance Matrix Solver (`aegislps_engine/nodal.py`)
- **Governing Theory**: Maxwell quasi-magnetostatics & Kirchhoff's Current Law (KCL).
- **Formulation**:
  $$\mathbf{Y} \cdot \mathbf{V} = \mathbf{I}$$
  - Branch impedance: $Z = \sqrt{R_{\text{dc}}^2 + (\omega L)^2}$, with $\omega = 2\pi f$ ($f = 250\text{ kHz}$).
  - Self-inductance of circular conductor segment:
    $$L = \frac{\mu_0}{2\pi} \cdot l \cdot \left[ \ln\left( \frac{2l}{r} \right) - 0.75 \right] \quad [\text{Henry}]$$
- **Verification & Conservation Safeguards**:
  - Node-by-node KCL residual verification: $\sum_{k} I_k = 0$ for all internal nodes.
  - Global current conservation check: $|I_{\text{injected}} - \sum I_{\text{earth}}| < 0.02 \cdot I_{\text{injected}}$ ($< 2\%$ relative residual).
  - Disconnected component handling: Graphs without paths to earth are rejected with diagnostic warnings.
  - Condition number estimation alerts engineers to ill-conditioned conductor loops.

---

## PASS 2: EARTHING SYSTEM, EARTH PITS & ROD SIZING

### 2.1 Earthing System Analytical Formulations (`aegislps_engine/earthing.py`)
- **Type B Circular Ring (Dwight Formulation)**:
  $$R = \frac{\rho}{2\pi^2 D} \left[ \ln\left( \frac{8D}{r} \right) + \ln\left( \frac{4D}{h} \right) \right] \quad [\Omega]$$
  Where $D = 2R_{\text{ring}}$ is the ring diameter, $r$ is conductor radius, and $h$ is burial depth.
> **UNVERIFIED — known defect (C4):** `earthing.py` evaluates Type B ring compliance via circumference `2 * pi * r_ring >= l1` instead of equivalent ring radius `r_e >= l1` and uses an unverified `l1(rho)` formula.
> **UNVERIFIED — known defect (H5):** `earthing.py` uses unverified prefactors in the buried ring and horizontal-strip resistance equations that disagree with Dwight and Sunde analytical formulas.
- **Type A Vertical Rod Array (Dwight + Mutual Coupling)**:
  $$R_1 = \frac{\rho}{2\pi L} \left[ \ln\left( \frac{4L}{r} \right) - 1 \right]$$
  $$R_{\text{array}} = \frac{R_1}{N} \left[ 1 + (N-1) \frac{L}{2\pi s} \ln\left( 1 + \frac{s}{L} \right) \right]$$
  Where $s$ is spacing between rods and $L$ is rod length.
> **UNVERIFIED — known defect (H4):** `earthing.py` uses an ad-hoc `(L / (2 * pi * s)) * ln(1 + s / L)` coupling term (for example at `N = 4, s = 5 m, L = 3 m`) that does not match published multi-rod efficiency formulations.
- **Foundation Earth Mesh (Laurent & Nieman)**:
  $$R = \frac{\rho}{4 r_{\text{equiv}}} + \frac{\rho}{P}, \quad r_{\text{equiv}} = \sqrt{\frac{A}{\pi}}$$
- **High-Current Impulse Soil Ionization (Corson / Bellaschi Model)**:
  $$Z_p = \frac{R_{\text{dc}}}{\sqrt{1 + \frac{I_{\text{peak}}}{I_{\text{critical}}}}}, \quad I_{\text{critical}} = \frac{E_c \cdot \rho}{2\pi R_{\text{dc}}^2}$$
  Where $E_c \approx 300\text{ kV/m}$ is critical soil breakdown gradient.

### 2.2 Earth Pit Sizing & Backfill Conditioning (`aegislps_engine/earth_pit.py`)
- **Standards**: IEC 62305-3 Section E.7.2, IEC 62561-5, IEC 62561-7, and EN 124.
- **Inspection Pit Necessity**: Required whenever disconnect test joints or periodic inspection accessibility is mandated.
- **Mechanical Load Classes (EN 124)**:
  - Class A15 ($15\text{ kN}$): Pedestrian areas and green zones ($250\text{ mm}$ dia, $260\text{ mm}$ depth).
  - Class B125 ($125\text{ kN}$): Car parks and commercial driveways ($300\text{ mm}$ dia, $280\text{ mm}$ depth).
  - Class D400 ($400\text{ kN}$): Heavy transport roadways and industrial yards ($320\text{ mm}$ dia, $300\text{ mm}$ depth).
- **Concentric Two-Cylinder Backfill Model**:
  $$R_{\text{conditioned}} = \frac{\rho_c}{2\pi L} \ln\left(\frac{r_{\text{hole}}}{r_{\text{rod}}}\right) + \frac{\rho_{\text{native}}}{2\pi L} \left[\ln\left(\frac{4L}{r_{\text{hole}}}\right) - 1\right]$$
  Calculates required backfill volume $V = \pi(r_{\text{hole}}^2 - r_{\text{rod}}^2)L$ and bag counts ($25\text{ kg}$ sacks of GEM/Bentonite).

### 2.3 Multi-Material Earth Rod Sizing (`aegislps_engine/earth_rod_sizing.py`)
- **Standards**: IEC 62561-2 Table 1.
- **Allowed Materials & Dimensions**:
  - Copper-bonded steel: Minimum $16.0\text{ mm}$ diameter ($5/8''$) with $\ge 250\ \mu\text{m}$ copper coating.
  - Solid copper: Minimum $15.0\text{ mm}$ diameter.
  - Hot-dip galvanized steel: Minimum $20.0\text{ mm}$ diameter with $\ge 50\ \mu\text{m}$ zinc coating.
  - Stainless steel (V4A 1.4571): Minimum $16.0\text{ mm}$ diameter.
- **Spacing & Setback Rules**:
  - Inter-rod spacing rule $s \ge 2 \times L_{\text{rod}}$ enforced to ensure mutual coupling efficiency $\eta > 80\%$.
> **UNVERIFIED — known defect (H4):** `earth_rod_sizing.py` computes multi-rod array resistance with the unverified `(L / (2 * pi * s)) * ln(1 + s / L)` coupling factor, so the claimed `eta > 80%` efficiency at `s >= 2 * L` is not substantiated.
  - Foundation setback distance $d_{\text{bldg}} \ge 1.0\text{ m}$ maintained to prevent stray capacitive interference with structural reinforcement rebar.

---

## PASS 3: LEMP, THERMAL/ELECTRODYNAMIC, RISK, AND GEOMETRY

### 3.1 LEMP Transient Magnetic Field & Faraday Induction (`aegislps_engine/lemp_engine.py`)
- **Heidler Function Current Generation**:
  $$i(t) = \frac{I}{\eta} \cdot \frac{(t/\tau_1)^n}{1 + (t/\tau_1)^n} \cdot \exp(-t/\tau_2)$$
  Calibrated for $10/350\ \mu\text{s}$ first stroke and $0.25/100\ \mu\text{s}$ subsequent stroke per IEC 62305-1.
> **UNVERIFIED — known defect (C3):** `lemp_engine.py` sets `tau1 = 10 us, tau2 = 350 us` instead of the IEC 62305-1 Heidler parameters (`tau1 = 19 us, tau2 = 485 us`) for the `10/350 us` stroke and computes `di/dt` numerically via `np.gradient`, making peak steepness grid-dependent.
- **Spatial Biot-Savart Field**:
  $$H(r, t) = \frac{i(t)}{2\pi r} \quad [\text{A/m}]$$
- **Spatial Grid Shielding Attenuation (IEC 62305-4 Annex A)**:
  $$K_{MS} \approx 0.01 \cdot w_{\text{mesh}} \quad [\text{dimensionless}]$$
> **UNVERIFIED — known defect (LEMP-K_MS):** `lemp_engine.py` uses `K_MS = 0.01 * w` instead of the IEC 62305-4 Annex A spatial-grid factor (`K_MS = 0.12 * w`), overstating magnetic-field attenuation by roughly an order of magnitude.
- **Faraday-Maxwell Induced Loop Voltage**:
  $$u_i(t) = \mu_0 \cdot K_{MS} \cdot \frac{A_{\text{loop}}}{2\pi r} \cdot \frac{di}{dt} \quad [\text{Volts}]$$

### 3.2 PEEC Mutual Inductance & Thermal Stress (`aegislps_engine/peec_thermal.py`)
- **Neumann's Double Integral for 3D Skew Segments**:
  $$M_{ij} = \frac{\mu_0}{4\pi} \oint \oint \frac{d\vec{l}_i \cdot d\vec{l}_j}{|\vec{r}_i - \vec{r}_j|}$$
  Discretized using 10-point Gauss-Legendre quadrature integration.
- **Adiabatic Temperature Rise (IEC 62305-1 Equation D.1)**:
  $$\Delta\theta = \frac{1}{\alpha} \left[ \exp\left( \frac{(W/R) \cdot \alpha \cdot \rho_0}{q^2 \cdot \gamma \cdot c_w} \right) - 1 \right]$$
  Evaluated under specific energy action integral $W/R = 10.0\text{ MJ}/\Omega$ for Class I.
- **Electrodynamic Force & Fastener Spacing**:
  $$F/L = \frac{\mu_0}{2\pi} \cdot \frac{i_1 \cdot i_2}{d}, \quad s_{\text{clip}} \le \frac{F_{\text{max,holder}}}{F/L}$$

### 3.3 Full IEC 62305-2:2024 8-Component Risk Engine (`aegislps_engine/comprehensive_risk.py`)
- **Primary Risk Evaluated**: Loss of human life:
  $$R_1 = (R_A + R_B + R_C + R_M) + (R_U + R_V + R_W + R_Z)$$
- Structure collection area $A_d = L\cdot W + 6H(L+W) + 9\pi H^2$.
- Service lines collection area $A_l = 40 \cdot L_{\text{line}}$ (aerial) or $8 \cdot L_{\text{line}}$ (buried).
- Evaluated against tolerable threshold $R_T = 1.0 \times 10^{-5}$.

### 3.4 3D Analytical Rolling Sphere & Mesh Method
- Analytical contact point calculation:
  $$z_{\text{protect}} = h_{\text{rod}} - \left( R - \sqrt{\max(0, R^2 - d_{\text{horiz}}^2)} \right)$$
> **UNVERIFIED — known defect (C1):** `rolling_sphere.py` and `mesh_rolling_sphere.py` evaluate `h_rod - (R - sqrt(R^2 - d^2))` rather than the height of a rolling sphere of radius `R` resting simultaneously on the rod tip and the reference plane.
- Mesh method spacing: Class I ($5\times 5\text{m}$), Class II ($10\times 10\text{m}$), Class III ($15\times 15\text{m}$), Class IV ($20\times 20\text{m}$).
- Protrusions $> 30\text{ cm}$ are flagged for supplemental air termination protection.

---

## CONCLUSION
This document's formulation claims are NOT all verified. Items marked UNVERIFIED are known to disagree with the code or with the standard; see the labels in this document.
