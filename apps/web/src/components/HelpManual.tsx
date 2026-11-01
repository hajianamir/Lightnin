import { useState } from 'react'

interface HelpProps {
  isOpen: boolean
  onClose: () => void
}

export default function HelpManual({ isOpen, onClose }: HelpProps) {
  const [section, setSection] = useState<'standards' | 'formulas' | 'guide'>('standards')

  if (!isOpen) return null

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
      backgroundColor: 'rgba(0, 0, 0, 0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000, backdropFilter: 'blur(5px)'
    }}>
      <div style={{
        width: '840px', height: '85vh', background: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px',
        display: 'flex', flexDirection: 'column', color: '#f8fafc', overflow: 'hidden'
      }}>
        {/* Modal Header */}
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #1e293b', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#0d1527' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '18px', color: '#38bdf8' }}>AegisLPS Engineering Help & Standards Manual</h3>
            <span style={{ fontSize: '12px', color: '#94a3b8' }}>IEC 62305:2024 Reference & Operational Documentation</span>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '20px', cursor: 'pointer' }}>×</button>
        </div>

        {/* Section Navigation Tabs */}
        <div style={{ display: 'flex', borderBottom: '1px solid #1e293b', background: '#111827', padding: '0 20px' }}>
          {[
            { id: 'standards', label: '1. Standards Reference (IEC 62305)' },
            { id: 'formulas', label: '2. Calculation Formulas & Theory' },
            { id: 'guide', label: '3. User Guide & Modeling Workflow' }
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setSection(t.id as any)}
              style={{
                padding: '12px 18px',
                background: 'transparent',
                border: 'none',
                borderBottom: section === t.id ? '2px solid #38bdf8' : '2px solid transparent',
                color: section === t.id ? '#38bdf8' : '#94a3b8',
                fontWeight: 600,
                fontSize: '13px',
                cursor: 'pointer'
              }}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Content Body */}
        <div style={{ flex: 1, padding: '28px', overflowY: 'auto', fontSize: '13px', lineHeight: '1.7', color: '#cbd5e1' }}>
          {section === 'standards' && (
            <div>
              <h4 style={{ color: '#38bdf8', marginTop: 0, fontSize: '15px' }}>IEC 62305:2024 Standards Suite Overview</h4>
              <p>
                AegisLPS is built around the latest International Electrotechnical Commission (IEC) 62305 standards suite:
              </p>
              <ul style={{ paddingLeft: '20px' }}>
                <li><b>IEC 62305-1 (General Principles):</b> Defines lightning parameters, 10/350 us and 8/20 us waveforms, and LPS Classes I through IV.</li>
                <li><b>IEC 62305-2 (Risk Management):</b> Formulates loss of human life (R1), physical damage (R2), cultural heritage (R3), and economic value (R4).</li>
                <li><b>IEC 62305-3 (Physical Damage & Life Hazard):</b> Governs air-termination systems (Rolling sphere, Protective angle, Mesh method), down-conductors, separation distance (s), and earthing systems (Type A and Type B).</li>
                <li><b>IEC 62305-4 (Electrical & Electronic Systems):</b> Details Lightning Protection Zones (LPZ 0A, 0B, 1, 2, 3), SPD selection, and cable decoupling.</li>
              </ul>

              <h4 style={{ color: '#38bdf8', marginTop: '20px', fontSize: '15px' }}>LPS Class Parameters (IEC 62305-3 Table 1 & 2)</h4>
              <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '10px', fontSize: '12px' }}>
                <thead>
                  <tr style={{ background: '#1e293b', color: '#fff', textAlign: 'left' }}>
                    <th style={{ padding: '8px', border: '1px solid #334155' }}>LPS Class</th>
                    <th style={{ padding: '8px', border: '1px solid #334155' }}>ki Factor</th>
                    <th style={{ padding: '8px', border: '1px solid #334155' }}>Rolling Sphere Radius (R)</th>
                    <th style={{ padding: '8px', border: '1px solid #334155' }}>Mesh Grid Size</th>
                    <th style={{ padding: '8px', border: '1px solid #334155' }}>Max Angle Height (H)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td style={{ padding: '8px', border: '1px solid #334155' }}><b>Class I</b></td>
                    <td style={{ padding: '8px', border: '1px solid #334155' }}>0.08</td>
                    <td style={{ padding: '8px', border: '1px solid #334155' }}>20 m</td>
                    <td style={{ padding: '8px', border: '1px solid #334155' }}>5 m x 5 m</td>
                    <td style={{ padding: '8px', border: '1px solid #334155' }}>20 m</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', border: '1px solid #334155' }}><b>Class II</b></td>
                    <td style={{ padding: '8px', border: '1px solid #334155' }}>0.06</td>
                    <td style={{ padding: '8px', border: '1px solid #334155' }}>30 m</td>
                    <td style={{ padding: '8px', border: '1px solid #334155' }}>10 m x 10 m</td>
                    <td style={{ padding: '8px', border: '1px solid #334155' }}>30 m</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', border: '1px solid #334155' }}><b>Class III</b></td>
                    <td style={{ padding: '8px', border: '1px solid #334155' }}>0.04</td>
                    <td style={{ padding: '8px', border: '1px solid #334155' }}>45 m</td>
                    <td style={{ padding: '8px', border: '1px solid #334155' }}>15 m x 15 m</td>
                    <td style={{ padding: '8px', border: '1px solid #334155' }}>45 m</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', border: '1px solid #334155' }}><b>Class IV</b></td>
                    <td style={{ padding: '8px', border: '1px solid #334155' }}>0.04</td>
                    <td style={{ padding: '8px', border: '1px solid #334155' }}>60 m</td>
                    <td style={{ padding: '8px', border: '1px solid #334155' }}>20 m x 20 m</td>
                    <td style={{ padding: '8px', border: '1px solid #334155' }}>60 m</td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {section === 'formulas' && (
            <div>
              <h4 style={{ color: '#38bdf8', marginTop: 0, fontSize: '15px' }}>Core Engineering Formulations</h4>

              <div style={{ background: '#1e293b', padding: '14px', borderRadius: '6px', marginBottom: '14px' }}>
                <b style={{ color: '#38bdf8' }}>1. Separation Distance (IEC 62305-3 Section 6.3):</b>
                <pre style={{ color: '#eab308', margin: '6px 0' }}>s = ki * (kc / km) * l</pre>
                <span>Where ki is class coefficient (0.08, 0.06, 0.04), kc is current sharing factor (0.25 - 1.0), km is material insulation factor (1.0 for air, 0.5 for solid), and l is conductor length to ground.</span>
              </div>

              <div style={{ background: '#1e293b', padding: '14px', borderRadius: '6px', marginBottom: '14px' }}>
                <b style={{ color: '#38bdf8' }}>2. Nodal Current Admittance System:</b>
                <pre style={{ color: '#eab308', margin: '6px 0' }}>Y * V = I,   where Z = sqrt(R_dc^2 + (omega * L)^2)</pre>
                <span>Solves sparse conductance matrix with Kirchhoff Current Law (KCL) conservation verification sum(I_k) = 0.</span>
              </div>

              <div style={{ background: '#1e293b', padding: '14px', borderRadius: '6px', marginBottom: '14px' }}>
                <b style={{ color: '#38bdf8' }}>3. Dwight Formulation for Type B Closed Ring Earth Electrode:</b>
                <pre style={{ color: '#eab308', margin: '6px 0' }}>R = (rho / (2 * pi^2 * D)) * [ ln(8*D/r) + ln(4*D/h) ]</pre>
                <span>Calculates stationary resistance R_dc, followed by Corson/Bellaschi soil ionization impulse reduction Z_p.</span>
              </div>

              <div style={{ background: '#1e293b', padding: '14px', borderRadius: '6px', marginBottom: '14px' }}>
                <b style={{ color: '#38bdf8' }}>4. 3D Rolling Sphere Sagitta Penetration:</b>
                <pre style={{ color: '#eab308', margin: '6px 0' }}>z_protect = h_rod - [ R - sqrt(max(0, R^2 - d_horiz^2)) ]</pre>
                <span>Evaluates analytical contact clearance without visual tessellation mesh errors.</span>
              </div>
            </div>
          )}

          {section === 'guide' && (
            <div>
              <h4 style={{ color: '#38bdf8', marginTop: 0, fontSize: '15px' }}>User Guide & Operational Workflow</h4>
              <ol style={{ paddingLeft: '20px' }}>
                <li><b>Project Initialization:</b> Click "New Project Wizard" in the top bar to walk through a 5-step guided design setup.</li>
                <li><b>3D Parametric Modeling:</b> Adjust building length, width, and height in the left panel. Use camera presets (Iso, Top, Front, Side) to inspect your structure.</li>
                <li><b>Layer Visibility:</b> Toggle engineering display layers (Mesh Grid, Air Terminations, Down Conductors, Rolling Sphere Envelope, and Current Heatmap).</li>
                <li><b>Separation Clearance Assessment:</b> Enter your target equipment coordinates and available physical clearance to observe real-time Pass/Fail vector overlays.</li>
                <li><b>Multi-Discipline Analysis:</b> Use the top workspace tabs to inspect 2D CAD Plans, Nodal Currents, Earthing System impedance, and UQ Monte Carlo Sensitivity distributions.</li>
                <li><b>Export Documentation:</b> Visit the "Reports & Export" tab to download editable Word (.docx) formal reports, vector PDF calculation packages, 2D AutoCAD (.dxf) drawings, and 3D glTF models.</li>
                <li><b>Save & Open (.lps):</b> Save your project directly to your PC as a versioned `.lps` JSON file, and reopen it anytime using the "Open Project" button.</li>
              </ol>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div style={{ padding: '14px 24px', borderTop: '1px solid #1e293b', background: '#0d1527', display: 'flex', justifyContent: 'flex-end' }}>
          <button onClick={onClose} style={{ padding: '8px 20px', background: '#0284c7', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer', fontSize: '13px' }}>
            Close Manual
          </button>
        </div>
      </div>
    </div>
  )
}
