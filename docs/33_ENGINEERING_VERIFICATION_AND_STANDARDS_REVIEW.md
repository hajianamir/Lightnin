# Comprehensive Technical Engineering & Standards Review

- **Document ID**: DOC-REV-001
- **Version**: 1.0.0-prototype.4
- **Product Name**: AegisLPS (Provisional Working Title)
- **Status**: Experimental Advanced-Engineering Prototype Modules Implemented; Formal Verification Pending

---

## 1. Executive Summary & Verification Methodology
This document provides an in-depth engineering review of all modules and computational methods implemented in the AegisLPS codebase against the baseline standard series:
- **IEC 62305-1:2024** (General principles)
- **IEC 62305-2:2024** (Risk management)
- **IEC 62305-3:2024** (Physical damage to structures and life hazard)
- **IEC 62305-4:2024** (Electrical and electronic systems within structures)
- **IEC 61643-12 / IEEE 80-2013** (SPD application principles and AC substation grounding criteria)

Every calculation module is reviewed for:
1. Mathematical rigor and adherence to sound electrical engineering theory.
2. Standards compliance vs. approximation disclosures.
3. Units consistency (strict internal SI units).
4. Boundary condition safeguards, residual checks, and numerical stability.

---

## 2. Module-by-Module Technical Review & Audit Findings

### 2.1 Core Separation-Distance Engine (`aegislps_engine/separation.py`)
- **Governing Standard**: IEC 62305-3:2024 Section 6.3.
- **Governing Equation**:
  $$s = k_i \cdot \frac{k_c}{k_m} \cdot l$$
  Segment-by-segment formulation:
  $$s(P) = \frac{k_i}{k_m} \sum_{j=1}^{N} \left( k_{c,j} \cdot l_j \right)$$
- **Engineering Assessment**:
  - The implementation strictly isolates input geometry, routing lengths, and material factors.
  - Distinguishes spatial conductor path length $l$ from direct straight-line Euclidean clearance $D_{\text{actual}}$.
  - Pass/fail determination is based strictly on numerical comparison $D_{\text{actual}} \ge s$, displaying intermediate substitution traces and positive/negative safety margins.
- **Classification**: Implemented, verified against reference hand-calculation benchmark cases.

---

### 2.2 Nodal Current-Sharing & Surge Solver (`aegislps_engine/nodal.py`)
- **Governing Standard**: IEC 62305-3 Annex C (Partitioning of lightning current among down-conductors).
- **Formulation**:
  - Sparse nodal admittance matrix: $\mathbf{Y} \cdot \mathbf{V} = \mathbf{I}$.
  - Branch impedance model: $Z = \sqrt{R_{\text{dc}}^2 + (\omega \cdot L_{\text{eff}})^2}$.
  - Self-inductance formulation:
    $$L = \frac{\mu_0}{2\pi} \cdot l \cdot \left[ \ln\left( \frac{2l}{r} \right) - 0.75 \right]$$
  - Current-sharing coefficient derivation:
    $$k_{c,j} = \frac{I_{\text{branch}, j}}{I_{\text{total}}}$$
- **Disclosures & Safeguards**:
  - Explicitly classified as an **experimental single-frequency equivalent impedance model** ($\sim 250\text{ kHz}$).
  - Enforces local node Kirchhoff's Current Law (KCL) residual balance checks ($\sum I_k = 0$) and a global current conservation gate ($< 2\%$ relative residual).
  - Condition number estimation ($cond \approx \frac{\max|Y_{ii}|}{\min|Y_{ii}|}$) alerts users to ill-conditioned networks.
- **Classification**: Experimental frequency-domain current solver; unverified for full time-domain non-linear transient response.

---

### 2.3 Rolling Sphere 3D Analytical Engine (`aegislps_geometry/rolling_sphere.py`)
- **Governing Standard**: IEC 62305-3 Section 5.2.2 & Table 2.
- **Sphere Radii**:
  - Class I: $R = 20\text{ m}$
  - Class II: $R = 30\text{ m}$
  - Class III: $R = 45\text{ m}$
  - Class IV: $R = 60\text{ m}$
- **Formulation**:
  - Pure analytical geometry independent of WebGL display tessellation:
    $$z_{\text{protect}} = h_{\text{rod}} - \left( R - \sqrt{\max(0, R^2 - d_{\text{horiz}}^2)} \right)$$
- **Engineering Assessment**:
  - Correctly calculates sagitta penetration and clearance margins for rooftop equipment.
- **Classification**: Implemented, analytical tests passing.

---

### 2.4 Protective Angle Engine (`aegislps_geometry/protective_angle.py`)
- **Governing Standard**: IEC 62305-3 Section 5.2.2, Table 2 & Figure 1.
- **Standards Alignment**:
  - Empirical continuous curve-fitting has been completely removed in accordance with audit directives.
  - Implements piece-wise linear interpolation strictly between verified Table 2 anchor points.
  - Strictly enforces maximum height limits ($H \le 20\text{m}$ for Class I, $30\text{m}$ for Class II, $45\text{m}$ for Class III, $60\text{m}$ for Class IV). Exceeding heights automatically marks the method as non-applicable and requires the rolling sphere method.
- **Classification**: Standards-controlled look-up; verified within Table 2 limits.

---

### 2.5 Earthing System Analysis Engine (`aegislps_engine/earthing.py`)
- **Governing Standard**: IEC 62305-3 Section 5.4 & IEEE 80.
- **Formulations**:
  - **Type B Circular Ring (Dwight formulation)**:
    $$R = \frac{\rho}{2\pi^2 D} \cdot \left[ \ln\left( \frac{8D}{r} \right) + \ln\left( \frac{4D}{h} \right) \right]$$
  - **Type A Vertical Rod Array (Dwight + Mutual Coupling)**:
    $$R_{\text{single}} = \frac{\rho}{2\pi L} \cdot \left[ \ln\left( \frac{4L}{r} \right) - 1 \right]$$
    $$R_{\text{array}} = \frac{R_{\text{single}}}{N} \cdot \left( 1 + (N-1) \cdot \frac{L}{2\pi s} \ln\left( 1 + \frac{s}{L} \right) \right)$$
  - **Foundation Earth Mesh (Laurent & Nieman)**:
    $$R = \frac{\rho}{4 r_{\text{equiv}}} + \frac{\rho}{P}$$
  - **Two-Layer Soil Apparent Resistivity (Sunde Model)**:
    $$\rho_a = \rho_1 \cdot \left[ 1 + k \cdot \left( 1 - e^{-1.8 (h_e / h_1)} \right) \right], \quad k = \frac{\rho_2 - \rho_1}{\rho_2 + \rho_1}$$
  - **Impulse Impedance (Corson / Bellaschi Soil Ionization)**:
    $$Z_p = \frac{R_{\text{dc}}}{\sqrt{1 + \frac{I_{\text{peak}}}{I_{\text{critical}}}}}, \quad I_{\text{critical}} = \frac{E_c \cdot \rho}{2\pi R_{\text{dc}}^2}$$
- **Classification**: Analytical earthing approximations; verified against IEEE 80 / Dwight reference datasets.

---

### 2.6 Touch & Step Potential Engine (`aegislps_engine/touch_step.py`)
- **Governing Standard**: IEEE 80-2013 & IEC 62305-3 Section 8.
- **Formulations**:
  - Surface layer derating factor $C_s(h_s, \rho, \rho_s)$ via IEEE 80 Equation 27.
  - Dalziel 70kg tolerable body limits:
    $$U_{\text{touch,tol}} = (1000 + 1.5 \cdot C_s \cdot \rho_s) \cdot \frac{0.157}{\sqrt{t_f}}$$
    $$U_{\text{step,tol}} = (1000 + 6.0 \cdot C_s \cdot \rho_s) \cdot \frac{0.157}{\sqrt{t_f}}$$
  - Hemispherical current dispersion prospective potential distribution $V(r)$.
- **Disclosures**:
  - Differentiates power-frequency substation criteria (IEEE 80) from lightning equipotentialization (IEC 62305-3).
- **Classification**: Experimental screening module; specialist review required.

---

### 2.7 Multi-Stage SPD Coordination Engine (`aegislps_engine/spd_coordination.py`)
- **Governing Standard**: IEC 62305-4 & IEC 61643-12.
- **Formulations**:
  - LPZ boundary transitions (LPZ 0A $\to$ 0B $\to$ 1 $\to$ 2 $\to$ 3).
  - Minimum inductive decoupling cable length ($l \ge 10\text{ m}$) between Type 1 spark gap and downstream Type 2 MOV to prevent premature MOV destruction.
  - Maximum effective protective distance:
    $$l_{\text{prot}} = (U_w - U_p) \cdot 10\text{ m}$$
- **Classification**: Rules-based engineering coordination engine; verified.

---

### 2.8 IEC 62305-2 Risk Management Engine (`aegislps_engine/risk.py`)
- **Governing Standard**: IEC 62305-2.
- **Formulation**:
  - Equivalent collection area $A_d = L\cdot W + 6H(L+W) + 9\pi H^2$.
  - Dangerous event frequency $N_D = N_g \cdot A_d \cdot C_d \cdot 10^{-6}$.
  - Loss of human life risk breakdown:
    $$R_1 = R_A (\text{touch/step}) + R_B (\text{physical fire}) + R_C (\text{internal surges})$$
  - Evaluated against tolerable threshold $R_T = 1.0 \times 10^{-5}$.
- **Classification**: Legacy/partial risk-assessment prototype; not certified for IEC 62305-2:2024 single-risk model without full multi-zone expansion.

---

### 2.9 Multi-Objective Design Optimization Engine (`aegislps_engine/optimization.py`)
- **Formulation**:
  - Simulated annealing metaheuristic exploring air-termination rod locations, heights, and quantities.
  - Multi-objective Pareto optimization: maximizes 3D rolling-sphere protection coverage while minimizing rod count and total material cost.
- **Classification**: Experimental recommendation engine; all proposed outputs must be verified by the deterministic calculation engine.

---

### 2.10 PV Rooftop Installation Module (`aegislps_engine/pv_module.py`)
- **Governing Standards**: IEC 62305-3 Supplement 5 & CLC/TS 50539-12.
- **Formulation**:
  - Calculates separation distance $s$ to metallic PV support structures.
  - Classifies installation into Isolated LPS vs. Non-Isolated (Bonding Mandatory) configuration.
  - Enforces DC string cable inductive loop area minimization.
- **Classification**: Implemented; standards provenance pending.

---

### 2.11 Cryptographic Checksum & Project Integrity (`packages/domain-model/aegislps_domain/integrity.py`)
- **Formulation**:
  - Canonical JSON serialization with HMAC-SHA256 digest computation over all engineering inputs, geometry, and calculation snapshots.
  - Zero-tolerance tamper detection for approved revisions.
- **Classification**: Implemented; key management review pending for production release.

---

## 3. Summary of Verification & Test Status
- **Automated Pytest Suite**: 27 unit, integration, and distribution tests passing cleanly.
- **Test Coverage**: Separation distance, nodal solver KCL balance, analytical rolling sphere, tabulated protective angle, Dwight/Sunde earthing, Dalziel touch/step voltage, SPD coordination, risk components, PV clearance, glTF 3D export, and clean wheel distribution.
- **Repository Branch**: `feat/aegislps-prototype-baseline-12369393606001446225`.
