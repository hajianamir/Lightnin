import { useState } from 'react'

interface WizardProps {
  isOpen: boolean
  onClose: () => void
  onComplete: (projectData: any) => void
}

export default function ProjectWizard({ isOpen, onClose, onComplete }: WizardProps) {
  const [step, setStep] = useState(1)

  // Step 1: Info & Class
  const [projectName, setProjectName] = useState('New Industrial Facility')
  const [clientName, setClientName] = useState('Energy Corp')
  const [lpsClass, setLpsClass] = useState<'I' | 'II' | 'III'>('I')

  // Step 2: Building Geometry
  const [length, setLength] = useState(40)
  const [width, setWidth] = useState(25)
  const [height, setHeight] = useState(15)
  const [roofType, setRoofType] = useState('flat')

  // Step 3: Air Termination
  const [airMethod, setAirMethod] = useState<'sphere' | 'angle' | 'mesh'>('sphere')
  const [rodHeight, setRodHeight] = useState(3.0)

  // Step 4: Down Conductors & Earthing
  const [soilResistivity, setSoilResistivity] = useState(100.0)
  const [earthingType, setEarthingType] = useState<'type_b_ring' | 'type_a_vertical'>('type_b_ring')

  // Step 5: Separation Distance Target
  const [targetName, setTargetName] = useState('Rooftop HVAC Chiller')
  const [clearance, setClearance] = useState(1.2)

  if (!isOpen) return null

  const handleFinish = () => {
    onComplete({
      name: projectName,
      client: clientName,
      lpsClass,
      length,
      width,
      height,
      roofType,
      airMethod,
      rodHeight,
      soilResistivity,
      earthingType,
      targetName,
      clearance
    })
    onClose()
  }

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
      backgroundColor: 'rgba(0, 0, 0, 0.75)', display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000, backdropFilter: 'blur(4px)'
    }}>
      <div style={{
        width: '640px', background: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px',
        padding: '28px', color: '#f8fafc', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #1e293b', paddingBottom: '16px', marginBottom: '20px' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '18px', color: '#38bdf8' }}>LPS Project Design Wizard</h3>
            <span style={{ fontSize: '12px', color: '#94a3b8' }}>Step {step} of 5 — IEC 62305:2024 Guided Workflow</span>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '18px', cursor: 'pointer' }}>×</button>
        </div>

        {/* Wizard Steps */}
        {step === 1 && (
          <div>
            <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#e2e8f0' }}>Step 1: Project Information & LPS Class Selection</h4>
            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Project / Facility Name:</label>
              <input type="text" value={projectName} onChange={e => setProjectName(e.target.value)} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', color: '#fff', border: '1px solid #334155', fontSize: '13px' }} />
            </div>
            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Client / Site Authority:</label>
              <input type="text" value={clientName} onChange={e => setClientName(e.target.value)} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', color: '#fff', border: '1px solid #334155', fontSize: '13px' }} />
            </div>
            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Protection Class (IEC 62305-1):</label>
              <select value={lpsClass} onChange={e => setLpsClass(e.target.value as any)} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', color: '#fff', border: '1px solid #334155', fontSize: '13px' }}>
                <option value="I">Class I — Highest Protection (ki = 0.08, Rolling Sphere R = 20m)</option>
                <option value="II">Class II — High Risk Industrial (ki = 0.06, Rolling Sphere R = 30m)</option>
                <option value="III">Class III — Standard Commercial (ki = 0.04, Rolling Sphere R = 45m)</option>
              </select>
            </div>
          </div>
        )}

        {step === 2 && (
          <div>
            <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#e2e8f0' }}>Step 2: Building Geometry & Roof Profile</h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginBottom: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Length (m):</label>
                <input type="number" value={length} onChange={e => setLength(parseFloat(e.target.value))} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', color: '#fff', border: '1px solid #334155' }} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Width (m):</label>
                <input type="number" value={width} onChange={e => setWidth(parseFloat(e.target.value))} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', color: '#fff', border: '1px solid #334155' }} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Height (m):</label>
                <input type="number" value={height} onChange={e => setHeight(parseFloat(e.target.value))} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', color: '#fff', border: '1px solid #334155' }} />
              </div>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Roof Geometry Style:</label>
              <select value={roofType} onChange={e => setRoofType(e.target.value)} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', color: '#fff', border: '1px solid #334155' }}>
                <option value="flat">Flat Roof (Commercial / Industrial)</option>
                <option value="gable">Gable / Pitched Roof</option>
                <option value="hip">Hip Roof</option>
              </select>
            </div>
          </div>
        )}

        {step === 3 && (
          <div>
            <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#e2e8f0' }}>Step 3: Air-Termination Design Method</h4>
            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Primary Protection Assessment Method:</label>
              <select value={airMethod} onChange={e => setAirMethod(e.target.value as any)} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', color: '#fff', border: '1px solid #334155' }}>
                <option value="sphere">Rolling Sphere Method (Universal IEC Compliance)</option>
                <option value="angle">Protective Angle Method (Rods H &lt;= 20m)</option>
                <option value="mesh">Mesh Method (Roof Perimeter & Grid)</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Standard Air-Termination Rod Height (m):</label>
              <input type="number" step="0.5" value={rodHeight} onChange={e => setRodHeight(parseFloat(e.target.value))} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', color: '#fff', border: '1px solid #334155' }} />
            </div>
          </div>
        )}

        {step === 4 && (
          <div>
            <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#e2e8f0' }}>Step 4: Down Conductors & Earthing System</h4>
            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Estimated Soil Resistivity (ohm.m):</label>
              <input type="number" value={soilResistivity} onChange={e => setSoilResistivity(parseFloat(e.target.value))} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', color: '#fff', border: '1px solid #334155' }} />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Earthing Electrode Topology:</label>
              <select value={earthingType} onChange={e => setEarthingType(e.target.value as any)} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', color: '#fff', border: '1px solid #334155' }}>
                <option value="type_b_ring">Type B Closed Perimeter Ring (Recommended)</option>
                <option value="type_a_vertical">Type A Vertical Rod Array (4 Corner Earth Rods)</option>
              </select>
            </div>
          </div>
        )}

        {step === 5 && (
          <div>
            <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#e2e8f0' }}>Step 5: Separation Distance Target & Review</h4>
            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Critical Target Object Name:</label>
              <input type="text" value={targetName} onChange={e => setTargetName(e.target.value)} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', color: '#fff', border: '1px solid #334155' }} />
            </div>
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Available Physical Air Clearance (m):</label>
              <input type="number" step="0.1" value={clearance} onChange={e => setClearance(parseFloat(e.target.value))} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', color: '#fff', border: '1px solid #334155' }} />
            </div>
            <div style={{ background: '#1e293b', padding: '12px', borderRadius: '6px', fontSize: '12px', color: '#94a3b8' }}>
              Ready to generate 3D model, conductor grid, and separation distance calculation snapshot.
            </div>
          </div>
        )}

        {/* Footer Navigation */}
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '24px', paddingTop: '16px', borderTop: '1px solid #1e293b' }}>
          {step > 1 ? (
            <button onClick={() => setStep(s => s - 1)} style={{ padding: '8px 16px', background: '#334155', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', fontWeight: 600 }}>
              Back
            </button>
          ) : <div />}

          {step < 5 ? (
            <button onClick={() => setStep(s => s + 1)} style={{ padding: '8px 20px', background: '#0284c7', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', fontWeight: 700 }}>
              Next Step
            </button>
          ) : (
            <button onClick={handleFinish} style={{ padding: '8px 20px', background: '#10b981', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', fontWeight: 700 }}>
              Initialize Project in 3D
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
